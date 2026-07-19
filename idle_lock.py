#!/usr/bin/env python3
"""Idle Lock - Windows system-idle lock utility.

Tk is owned exclusively by the main thread.  Global hotkeys and low-level
hooks are owned by one dedicated Win32 message thread.  Hook callbacks never
touch UI and only enqueue a request for the Tk event loop.
"""
from __future__ import annotations

import argparse
import atexit
import ctypes
import hashlib
import json
import logging
import os
import pathlib
import queue
import sys
import threading
import time
import tkinter as tk
import tkinter.filedialog as fd
import traceback
from ctypes import wintypes

import pystray
from PIL import Image, ImageDraw, ImageOps, ImageTk


APP_VERSION = "2.1.0"
PROJECT_DIR = (pathlib.Path(sys.executable).parent if getattr(sys, "frozen", False)
               else pathlib.Path(__file__).resolve().parent)
LOG_DIR = PROJECT_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "idle-lock.log"
SETTINGS_FILE = PROJECT_DIR / "settings.json"

logging.basicConfig(
    filename=LOG_FILE, filemode="a", encoding="utf-8",
    format="%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("idle_lock")


# Win32 constants and structures ------------------------------------------------
WH_KEYBOARD_LL = 13
WH_MOUSE_LL = 14
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105
WM_HOTKEY = 0x0312
WM_QUIT = 0x0012
VK_CONTROL = 0x11
VK_MENU = 0x12
VK_LCONTROL = 0xA2
VK_RCONTROL = 0xA3
VK_LMENU = 0xA4
VK_RMENU = 0xA5
VK_0 = 0x30
VK_NUMPAD0 = 0x60
VK_F1 = 0x70
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_NOREPEAT = 0x4000
HOTKEY_MAIN_ID = 0x1D10
HOTKEY_NUMPAD_ID = 0x1D11
ERROR_ALREADY_EXISTS = 183
ERROR_HOTKEY_ALREADY_REGISTERED = 1409
WAIT_OBJECT_0 = 0
INFINITE = 0xFFFFFFFF
EVENT_MODIFY_STATE = 0x0002
MUTEX_NAME = "Global\\IdleLockSingleInstance"
WAKE_EVENT_NAME = "Global\\IdleLockWakeExisting"

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
LRESULT = wintypes.LPARAM


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD), ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD), ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p),
    ]


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND), ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM), ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD), ("pt", POINT),
    ]


class RECT(ctypes.Structure):
    _fields_ = [("left", wintypes.LONG), ("top", wintypes.LONG),
                ("right", wintypes.LONG), ("bottom", wintypes.LONG)]


LowLevelKbProc = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, wintypes.WPARAM,
                                    wintypes.LPARAM)
LowLevelMsProc = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, wintypes.WPARAM,
                                    wintypes.LPARAM)
MonitorEnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HMONITOR,
                                    wintypes.HDC, ctypes.POINTER(RECT), wintypes.LPARAM)

# ctypes defaults function arguments to 32-bit integers.  Explicit prototypes
# are required for hook handles and lParam pointers in a 64-bit process.
user32.CallNextHookEx.argtypes = [ctypes.c_void_p, ctypes.c_int,
                                  wintypes.WPARAM, wintypes.LPARAM]
user32.CallNextHookEx.restype = LRESULT
user32.UnhookWindowsHookEx.argtypes = [ctypes.c_void_p]
user32.UnhookWindowsHookEx.restype = wintypes.BOOL
user32.SetWindowsHookExW.restype = ctypes.c_void_p
user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int,
                                  wintypes.UINT, wintypes.UINT]
user32.RegisterHotKey.restype = wintypes.BOOL
user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
user32.UnregisterHotKey.restype = wintypes.BOOL


def _sha256(path: pathlib.Path) -> str:
    try:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return "unavailable"


def _monitor_rects() -> list[tuple[int, int, int, int]]:
    rects: list[tuple[int, int, int, int]] = []

    @MonitorEnumProc
    def callback(_monitor, _hdc, rect_ptr, _data):
        r = rect_ptr.contents
        rects.append((r.left, r.top, r.right - r.left, r.bottom - r.top))
        return True

    if not user32.EnumDisplayMonitors(None, None, callback, 0):
        rects.append((0, 0, user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)))
    return rects


# Single instance ---------------------------------------------------------------
class SingleInstance:
    def __init__(self):
        self.mutex = None
        self.wake_event = None

    def acquire(self) -> bool:
        self.mutex = kernel32.CreateMutexW(None, False, MUTEX_NAME)
        if not self.mutex or kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
            if self.mutex:
                kernel32.CloseHandle(self.mutex)
                self.mutex = None
            return False
        self.wake_event = kernel32.CreateEventW(None, True, False, WAKE_EVENT_NAME)
        return bool(self.wake_event)

    @staticmethod
    def wake_existing() -> None:
        handle = kernel32.OpenEventW(EVENT_MODIFY_STATE, False, WAKE_EVENT_NAME)
        if handle:
            kernel32.SetEvent(handle)
            kernel32.CloseHandle(handle)

    def close(self) -> None:
        if self.wake_event:
            kernel32.SetEvent(self.wake_event)
            kernel32.CloseHandle(self.wake_event)
            self.wake_event = None
        if self.mutex:
            kernel32.ReleaseMutex(self.mutex)
            kernel32.CloseHandle(self.mutex)
            self.mutex = None


# State and settings ------------------------------------------------------------
class State:
    STARTING = "STARTING"
    MONITORING = "MONITORING"
    LOCKING = "LOCKING"
    LOCKED = "LOCKED"
    UNLOCKING = "UNLOCKING"
    UNLOCK_DIALOG = "UNLOCK_DIALOG"
    PAUSED = "PAUSED"
    SHUTTING_DOWN = "SHUTTING_DOWN"
    FAULTED = "FAULTED"


ALLOWED_TRANSITIONS = {
    State.STARTING: {State.MONITORING, State.PAUSED, State.FAULTED, State.SHUTTING_DOWN},
    State.MONITORING: {State.LOCKING, State.PAUSED, State.FAULTED, State.SHUTTING_DOWN},
    State.LOCKING: {State.LOCKED, State.FAULTED, State.SHUTTING_DOWN},
    State.LOCKED: {State.UNLOCKING, State.FAULTED, State.SHUTTING_DOWN},
    State.UNLOCKING: {State.UNLOCK_DIALOG, State.MONITORING, State.FAULTED,
                      State.SHUTTING_DOWN},
    State.UNLOCK_DIALOG: {State.MONITORING, State.PAUSED, State.FAULTED,
                          State.SHUTTING_DOWN},
    State.PAUSED: {State.MONITORING, State.FAULTED, State.SHUTTING_DOWN},
    State.FAULTED: {State.PAUSED, State.MONITORING, State.SHUTTING_DOWN},
    State.SHUTTING_DOWN: set(),
}

DEFAULT_SETTINGS = {
    "idle_threshold_seconds": 60,
    "auto_start_monitoring": True,
    "show_startup_notification": True,
    "show_unlock_dialog": True,
    "show_lock_overlay": True,
    "idle_check_interval_ms": 500,
    "resume_grace_period_seconds": 3,
    "slideshow_folder": "",
    "slideshow_interval_seconds": 10,
    "use_slideshow_on_lock": False,
}


def load_settings() -> dict:
    settings = dict(DEFAULT_SETTINGS)
    try:
        if SETTINGS_FILE.exists():
            loaded = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                settings.update(loaded)
    except Exception:
        log.exception("SETTINGS_LOAD_FAILED")
    return settings


def save_settings(settings: dict) -> None:
    try:
        SETTINGS_FILE.write_text(json.dumps(settings, indent=2, ensure_ascii=False),
                                 encoding="utf-8")
    except Exception:
        log.exception("SETTINGS_SAVE_FAILED")


def make_tray_icon(color: str) -> Image.Image:
    image = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((3, 3, 29, 29), fill=color, outline="#eeeeee", width=2)
    return image


# Input guard -------------------------------------------------------------------
class InputGuard:
    """Own global hotkeys and hooks on one Win32 message-loop thread."""

    def __init__(self, on_unlock, on_display_toggle):
        self.on_unlock = on_unlock
        self.on_display_toggle = on_display_toggle
        self.locked = threading.Event()
        self.ready = threading.Event()
        self.stopped = threading.Event()
        self.thread: threading.Thread | None = None
        self.thread_id = 0
        self.start_error = ""
        self.main_hotkey_registered = False
        self.numpad_hotkey_registered = False
        self.kb_hook = None
        self.ms_hook = None
        self.kb_proc = None
        self.ms_proc = None
        self.hotkey_down = False
        self.unlock_posted = False
        self.ctrl_down = False
        self.alt_down = False
        self.display_key_down = False

    def start(self, timeout: float = 5.0) -> bool:
        self.thread = threading.Thread(target=self._run, name="InputGuard", daemon=True)
        self.thread.start()
        if not self.ready.wait(timeout):
            self.start_error = "Input guard startup timed out"
            return False
        return not self.start_error and self.main_hotkey_registered

    def set_locked(self, locked: bool) -> None:
        if locked:
            self.unlock_posted = False
            self.hotkey_down = False
            self.ctrl_down = False
            self.alt_down = False
            self.display_key_down = False
            self.locked.set()
        else:
            self.locked.clear()
            self.hotkey_down = False
            self.unlock_posted = False
            self.ctrl_down = False
            self.alt_down = False
            self.display_key_down = False

    def _post_unlock_once(self, source: str) -> None:
        if self.locked.is_set() and not self.unlock_posted:
            self.unlock_posted = True
            log.info("UNLOCK_EVENT_RECEIVED source=%s", source)
            self.on_unlock(source)

    def _keyboard_callback(self, n_code, w_param, l_param):
        if n_code >= 0 and self.locked.is_set():
            kbd = ctypes.cast(l_param, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
            is_down = w_param in (WM_KEYDOWN, WM_SYSKEYDOWN)
            is_up = w_param in (WM_KEYUP, WM_SYSKEYUP)
            if kbd.vkCode == VK_F1:
                if is_up:
                    self.display_key_down = False
                elif is_down and not self.display_key_down:
                    self.display_key_down = True
                    log.info("LOCK_DISPLAY_TOGGLE_EVENT_RECEIVED source=F1")
                    self.on_display_toggle("F1")
                return 1
            # Do not rely on GetAsyncKeyState here: keys suppressed by this
            # hook are not guaranteed to update the global async key state.
            if kbd.vkCode in (VK_CONTROL, VK_LCONTROL, VK_RCONTROL):
                if is_down:
                    self.ctrl_down = True
                elif is_up:
                    self.ctrl_down = False
                return 1
            if kbd.vkCode in (VK_MENU, VK_LMENU, VK_RMENU):
                if is_down:
                    self.alt_down = True
                elif is_up:
                    self.alt_down = False
                return 1
            is_zero = kbd.vkCode in (VK_0, VK_NUMPAD0)
            if is_zero and is_up:
                self.hotkey_down = False
                return 1
            if is_zero and is_down:
                if self.ctrl_down and self.alt_down and not self.hotkey_down:
                    self.hotkey_down = True
                    self._post_unlock_once("LOW_LEVEL_HOOK")
                return 1
            return 1
        return user32.CallNextHookEx(None, n_code, w_param, l_param)

    def _mouse_callback(self, n_code, w_param, l_param):
        if n_code >= 0 and self.locked.is_set():
            return 1
        return user32.CallNextHookEx(None, n_code, w_param, l_param)

    def _cleanup_thread_resources(self) -> None:
        self.locked.clear()
        if self.kb_hook:
            ok = user32.UnhookWindowsHookEx(self.kb_hook)
            log.info("KEYBOARD_HOOK_RELEASE result=%s", bool(ok))
            self.kb_hook = None
        if self.ms_hook:
            ok = user32.UnhookWindowsHookEx(self.ms_hook)
            log.info("MOUSE_HOOK_RELEASE result=%s", bool(ok))
            self.ms_hook = None
        if self.main_hotkey_registered:
            user32.UnregisterHotKey(None, HOTKEY_MAIN_ID)
            self.main_hotkey_registered = False
        if self.numpad_hotkey_registered:
            user32.UnregisterHotKey(None, HOTKEY_NUMPAD_ID)
            self.numpad_hotkey_registered = False
        self.kb_proc = None
        self.ms_proc = None

    def _run(self) -> None:
        try:
            self.thread_id = kernel32.GetCurrentThreadId()
            # Force creation of the thread message queue before readiness.
            msg = MSG()
            user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 0)
            if os.environ.get("IDLE_LOCK_SIMULATE_HOTKEY_CONFLICT") == "1":
                self.start_error = "Simulated Ctrl+Alt+0 registration conflict"
                self.ready.set()
                return

            kernel32.SetLastError(0)
            self.main_hotkey_registered = bool(user32.RegisterHotKey(
                None, HOTKEY_MAIN_ID, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, VK_0))
            if not self.main_hotkey_registered:
                err = kernel32.GetLastError()
                self.start_error = f"Ctrl+Alt+0 registration failed (WinError {err})"
                log.error("HOTKEY_REGISTRATION_FAILED main err=%s", err)
                self.ready.set()
                return

            # NumPad 0 is optional; failure does not make the primary hotkey unsafe.
            self.numpad_hotkey_registered = bool(user32.RegisterHotKey(
                None, HOTKEY_NUMPAD_ID, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, VK_NUMPAD0))
            if not self.numpad_hotkey_registered:
                log.warning("HOTKEY_REGISTRATION_FAILED numpad err=%s", kernel32.GetLastError())

            self.kb_proc = LowLevelKbProc(self._keyboard_callback)
            self.ms_proc = LowLevelMsProc(self._mouse_callback)
            self.kb_hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, self.kb_proc, None, 0)
            self.ms_hook = user32.SetWindowsHookExW(WH_MOUSE_LL, self.ms_proc, None, 0)
            if not self.kb_hook or not self.ms_hook:
                self.start_error = "Low-level input hook installation failed"
                log.error("HOOK_INSTALL_FAILED kb=%s mouse=%s", bool(self.kb_hook), bool(self.ms_hook))
                self._cleanup_thread_resources()
                self.ready.set()
                return

            log.info("HOTKEY_REGISTRATION_SUCCESS main=true numpad=%s",
                     self.numpad_hotkey_registered)
            log.info("INPUT_HOOK_INSTALL_SUCCESS")
            self.ready.set()

            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                if msg.message == WM_HOTKEY:
                    self._post_unlock_once("REGISTER_HOTKEY")
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        except Exception:
            self.start_error = traceback.format_exc()
            log.exception("INPUT_GUARD_UNHANDLED_EXCEPTION")
            self.ready.set()
        finally:
            self._cleanup_thread_resources()
            self.stopped.set()

    def stop(self) -> None:
        self.locked.clear()  # input recovery is always first
        if self.thread_id:
            user32.PostThreadMessageW(self.thread_id, WM_QUIT, 0, 0)
        self.stopped.wait(2.0)
        log.info("INPUT_GUARD_STOPPED result=%s", self.stopped.is_set())


# Application -------------------------------------------------------------------
class IdleLock:
    def __init__(self, instance: SingleInstance | None = None, runtime_test=False):
        self.settings = load_settings()
        self.instance = instance
        self.runtime_test = runtime_test
        self.root: tk.Tk | None = None
        self.state = State.STARTING
        self.running = False
        self.unlock_in_progress = False
        self.hotkey_conflict = False
        self.resume_grace_until = 0.0
        self.monitoring_started_at = time.monotonic()
        self.ui_queue: queue.Queue = queue.Queue()
        self.input_guard = InputGuard(self._queue_unlock, self._queue_display_toggle)
        self.overlays: list[tk.Toplevel] = []
        self.main_window: tk.Toplevel | None = None
        self.unlock_dialog: tk.Toplevel | None = None
        self.settings_dialog: tk.Toplevel | None = None
        self.notice_dialog: tk.Toplevel | None = None
        self.main_status_var: tk.StringVar | None = None
        self.main_mode_var: tk.StringVar | None = None
        self.main_folder_var: tk.StringVar | None = None
        self.main_lock_button: tk.Button | None = None
        self.main_pause_button: tk.Button | None = None
        self.main_resume_button: tk.Button | None = None
        self.lock_display_mode = "status"
        self.slideshow_files: list[pathlib.Path] = []
        self.slideshow_index = 0
        self.slideshow_generation = 0
        self.runtime_slide_dir: pathlib.Path | None = None
        self.icon: pystray.Icon | None = None
        self.icons = {
            "green": make_tray_icon("#2cab4b"), "red": make_tray_icon("#d13d3d"),
            "yellow": make_tray_icon("#d0a622"), "gray": make_tray_icon("#777777"),
        }
        self.runtime_results: dict[str, bool] = {}
        self.runtime_verify_unlock = None

    def _transition(self, new_state: str) -> bool:
        old = self.state
        if new_state not in ALLOWED_TRANSITIONS.get(old, set()):
            log.error("ILLEGAL_STATE_TRANSITION %s -> %s", old, new_state)
            return False
        self.state = new_state
        log.info("STATE_%s_TO_%s", old, new_state)
        self._refresh_tray()
        return True

    def _post_ui(self, callback, *args) -> None:
        self.ui_queue.put((callback, args))

    def _queue_unlock(self, source: str) -> None:
        self._post_ui(self._request_unlock, source)

    def _queue_display_toggle(self, source: str) -> None:
        self._post_ui(self._toggle_lock_display, source)

    def _poll_ui_queue(self) -> None:
        if not self.running or not self.root:
            return
        try:
            while True:
                callback, args = self.ui_queue.get_nowait()
                try:
                    callback(*args)
                except Exception:
                    log.exception("UI_QUEUED_ACTION_FAILED callback=%s", callback)
                    self._fault_recovery("UI queued action failed")
        except queue.Empty:
            pass
        self.root.after(25, self._poll_ui_queue)

    def _idle_seconds(self) -> float:
        info = LASTINPUTINFO(ctypes.sizeof(LASTINPUTINFO), 0)
        if not user32.GetLastInputInfo(ctypes.byref(info)):
            return 0.0
        # DWORD subtraction intentionally wraps at 49.7 days.
        elapsed_ms = (kernel32.GetTickCount() - info.dwTime) & 0xFFFFFFFF
        return elapsed_ms / 1000.0

    def _reset_idle_baseline(self) -> None:
        grace = float(self.settings.get("resume_grace_period_seconds", 3))
        self.resume_grace_until = time.monotonic() + grace
        self.monitoring_started_at = time.monotonic()
        log.info("IDLE_BASELINE_RESET grace_seconds=%s current_idle=%.3f",
                 grace, self._idle_seconds())

    def _schedule_monitor(self) -> None:
        if not self.running or not self.root:
            return
        if self.state == State.MONITORING and time.monotonic() >= self.resume_grace_until:
            # GetLastInputInfo may already report a long idle duration when the
            # application starts or monitoring resumes.  Require a full fresh
            # threshold from that point instead of locking immediately.
            monitoring_elapsed = max(0.0, time.monotonic() - self.monitoring_started_at)
            idle = min(self._idle_seconds(), monitoring_elapsed)
            if idle >= float(self.settings["idle_threshold_seconds"]):
                self._lock("IDLE_TIMEOUT")
        interval = max(250, int(self.settings.get("idle_check_interval_ms", 500)))
        self.root.after(interval, self._schedule_monitor)

    def _collect_slideshow_files(self) -> list[pathlib.Path]:
        folder_text = str(self.settings.get("slideshow_folder", "")).strip()
        if not folder_text:
            return []
        folder = pathlib.Path(folder_text)
        if not folder.is_dir():
            log.warning("SLIDESHOW_FOLDER_UNAVAILABLE path=%s", folder)
            return []
        extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tif", ".tiff"}
        try:
            return sorted(p for p in folder.rglob("*")
                          if p.is_file() and p.suffix.lower() in extensions)
        except Exception:
            log.exception("SLIDESHOW_SCAN_FAILED path=%s", folder)
            return []

    def _new_overlay(self, x: int, y: int, width: int, height: int) -> tk.Toplevel:
        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.configure(bg="#17172b", cursor="none")
        win.geometry(f"{width}x{height}+{x}+{y}")
        win.protocol("WM_DELETE_WINDOW", lambda: None)
        return win

    def _show_status_overlays(self) -> None:
        self._hide_overlays()
        self.lock_display_mode = "status"
        for index, (x, y, width, height) in enumerate(_monitor_rects()):
            win = self._new_overlay(x, y, width, height)
            frame = tk.Frame(win, bg="#17172b")
            frame.place(relx=0.5, rely=0.5, anchor="center")
            tk.Label(frame, text="偵測到閒置", font=("Segoe UI", 28, "bold"),
                     fg="white", bg="#17172b").pack(pady=8)
            tk.Label(frame, text="按下 Ctrl + Alt + 0 解除鎖定",
                     font=("Segoe UI", 16), fg="#70dc7c", bg="#17172b").pack()
            tk.Label(frame, text="按 F1 顯示目前 Windows 桌面",
                     font=("Segoe UI", 12), fg="#9da9cf", bg="#17172b").pack(pady=(16, 0))
            win.update_idletasks()
            win.lift()
            self.overlays.append(win)
            log.info("LOCK_STATUS_OVERLAY_CREATED monitor=%s geometry=%sx%s%+d%+d",
                     index, width, height, x, y)

    def _show_desktop_banners(self) -> None:
        self._hide_overlays()
        self.lock_display_mode = "desktop"
        for index, (x, y, width, _height) in enumerate(_monitor_rects()):
            banner_width = min(430, max(340, width - 28))
            banner_height = 70
            banner_x = x + width - banner_width - 14
            banner_y = y + 14
            win = self._new_overlay(banner_x, banner_y, banner_width, banner_height)
            tk.Label(win, text="Idle Lock｜桌面顯示模式",
                     font=("Segoe UI", 10, "bold"), fg="white", bg="#17172b").pack(pady=(7, 1))
            tk.Label(win, text="仍在鎖定｜Ctrl + Alt + 0 解鎖｜F1 切換保護畫面",
                     font=("Segoe UI", 9), fg="#70dc7c", bg="#17172b").pack()
            win.update_idletasks()
            win.lift()
            self.overlays.append(win)
            log.info("LOCK_DESKTOP_MODE_BANNER_CREATED monitor=%s", index)

    def _render_slideshow(self) -> None:
        if self.state not in (State.LOCKING, State.LOCKED):
            return
        self.slideshow_files = self._collect_slideshow_files()
        if not self.slideshow_files:
            log.warning("SLIDESHOW_EMPTY_FALLBACK_TO_STATUS")
            self._show_status_overlays()
            return
        self._hide_overlays()
        self.lock_display_mode = "slideshow"
        generation = self.slideshow_generation
        image_path = self.slideshow_files[self.slideshow_index % len(self.slideshow_files)]
        self.slideshow_index = (self.slideshow_index + 1) % len(self.slideshow_files)
        created = 0
        try:
            with Image.open(image_path) as source:
                source.load()
                source = source.convert("RGB")
                for index, (x, y, width, height) in enumerate(_monitor_rects()):
                    fitted = ImageOps.fit(source, (width, height), method=Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(fitted)
                    win = self._new_overlay(x, y, width, height)
                    label = tk.Label(win, image=photo, borderwidth=0)
                    label.image = photo
                    label.place(x=0, y=0, width=width, height=height)
                    banner = tk.Frame(win, bg="#11111f")
                    banner.place(relx=0.5, rely=0.94, anchor="center")
                    tk.Label(banner, text="Ctrl + Alt + 0 解鎖　｜　F1 顯示 Windows 桌面",
                             font=("Segoe UI", 12, "bold"), fg="white", bg="#11111f",
                             padx=18, pady=9).pack()
                    win.update_idletasks()
                    win.lift()
                    self.overlays.append(win)
                    created += 1
                    log.info("SLIDESHOW_OVERLAY_CREATED monitor=%s image=%s", index, image_path)
        except Exception:
            log.exception("SLIDESHOW_IMAGE_FAILED path=%s", image_path)
            self._show_status_overlays()
            return
        if created and self.root:
            interval_ms = max(3, min(300, int(
                self.settings.get("slideshow_interval_seconds", 10)))) * 1000
            self.root.after(interval_ms, lambda g=generation: self._advance_slideshow(g))

    def _advance_slideshow(self, generation: int) -> None:
        if (self.state == State.LOCKED and self.lock_display_mode == "slideshow"
                and generation == self.slideshow_generation):
            self._render_slideshow()

    def _show_lock_display(self) -> None:
        self.slideshow_files = self._collect_slideshow_files()
        if (self.settings.get("use_slideshow_on_lock", False)
                and self.slideshow_files):
            self._render_slideshow()
        else:
            self._show_status_overlays()

    def _toggle_lock_display(self, source="F1") -> None:
        if self.state != State.LOCKED:
            log.info("LOCK_DISPLAY_TOGGLE_IGNORED state=%s", self.state)
            return
        if self.lock_display_mode == "desktop":
            if self._collect_slideshow_files():
                self._render_slideshow()
            else:
                self._show_status_overlays()
        else:
            self._show_desktop_banners()
        log.info("LOCK_DISPLAY_MODE_CHANGED mode=%s source=%s",
                 self.lock_display_mode, source)

    def _hide_overlays(self) -> None:
        self.slideshow_generation += 1
        for win in self.overlays:
            try:
                win.destroy()
            except Exception:
                log.exception("LOCK_OVERLAY_DESTROY_FAILED")
        self.overlays.clear()

    def _lock(self, source="MANUAL") -> None:
        if self.state != State.MONITORING or self.hotkey_conflict:
            log.info("LOCK_IGNORED state=%s conflict=%s", self.state, self.hotkey_conflict)
            return
        if not self._transition(State.LOCKING):
            return
        try:
            self._show_lock_display()
            self.input_guard.set_locked(True)
            self._transition(State.LOCKED)
            log.info("LOCK_ENTERED source=%s overlays=%s", source, len(self.overlays))
            if self.runtime_test and source == "RUNTIME_TEST":
                self._schedule_runtime_display_sequence()
        except Exception:
            log.exception("LOCK_FAILED")
            self._fault_recovery("無法安全建立鎖定畫面")

    def _request_unlock(self, source="UNKNOWN") -> None:
        log.info("UNLOCK_REQUEST_DISPATCHED source=%s state=%s", source, self.state)
        if self.state != State.LOCKED or self.unlock_in_progress:
            log.info("UNLOCK_REQUEST_IGNORED state=%s in_progress=%s",
                     self.state, self.unlock_in_progress)
            return
        self.unlock_in_progress = True
        if not self._transition(State.UNLOCKING):
            self.unlock_in_progress = False
            return
        log.info("IDLE_MONITOR_PAUSED")
        try:
            log.info("INPUT_BLOCK_RELEASE_BEGIN")
            self.input_guard.set_locked(False)
            log.info("INPUT_BLOCK_RELEASE_SUCCESS")
            log.info("LOCK_WINDOWS_CLOSE_BEGIN")
            self._hide_overlays()
            log.info("LOCK_WINDOWS_CLOSE_SUCCESS")
            if os.environ.get("IDLE_LOCK_SIMULATE_UNLOCK_FAULT") == "1":
                raise RuntimeError("Simulated unlock fault")
            if self.settings.get("show_unlock_dialog", True):
                log.info("UNLOCK_DIALOG_SHOW_BEGIN")
                self._transition(State.UNLOCK_DIALOG)
                self._show_unlock_dialog()
                log.info("UNLOCK_DIALOG_SHOW_SUCCESS")
            else:
                self._reset_idle_baseline()
                self._transition(State.MONITORING)
            log.info("UNLOCK_FLOW_SUCCESS")
        except Exception:
            log.exception("UNLOCK_FLOW_FAILED")
            self._fault_recovery("解除鎖定時發生錯誤")
        finally:
            self.unlock_in_progress = False

    def _show_unlock_dialog(self) -> None:
        self._destroy_window("unlock_dialog")
        win = tk.Toplevel(self.root)
        self.unlock_dialog = win
        win.title("Idle Lock 已解除")
        win.attributes("-topmost", True)
        win.configure(bg="#1e1e2e")
        win.geometry("460x245")
        win.resizable(False, False)
        win.protocol("WM_DELETE_WINDOW", self._continue_monitoring)
        tk.Label(win, text="Idle Lock 已解除", font=("Segoe UI", 18, "bold"),
                 fg="white", bg="#1e1e2e").pack(pady=(20, 8))
        tk.Label(win, text="閒置鎖定已解除。\n請選擇接下來的動作。",
                 font=("Segoe UI", 11), fg="#b8b8c8", bg="#1e1e2e").pack(pady=8)
        buttons = tk.Frame(win, bg="#1e1e2e")
        buttons.pack(pady=14)
        for label, command, color in (
                ("繼續監控", self._continue_monitoring, "#276c3a"),
                ("暫停監控", self._pause_monitoring, "#6c6327"),
                ("結束程式", self._safe_shutdown, "#702d2d")):
            tk.Button(buttons, text=label, command=command, width=12,
                      bg=color, fg="white", font=("Segoe UI", 10)).pack(side="left", padx=6)
        self._center(win, 460, 245)
        win.lift()
        win.focus_force()

    def _continue_monitoring(self) -> None:
        if self.state not in (State.UNLOCK_DIALOG, State.PAUSED, State.FAULTED):
            return
        self._destroy_window("unlock_dialog")
        self._reset_idle_baseline()
        self.hotkey_conflict = not self.input_guard.main_hotkey_registered
        if self.hotkey_conflict:
            self._transition(State.PAUSED)
        else:
            self._transition(State.MONITORING)
            log.info("MONITORING_RESUMED")

    def _pause_monitoring(self) -> None:
        if self.state not in (State.MONITORING, State.UNLOCK_DIALOG, State.FAULTED):
            return
        self._destroy_window("unlock_dialog")
        self.input_guard.set_locked(False)
        self._transition(State.PAUSED)
        log.info("MONITORING_PAUSED")

    def _fault_recovery(self, reason: str) -> None:
        log.error("FAULT_RECOVERY_BEGIN reason=%s", reason)
        self.input_guard.set_locked(False)
        self._hide_overlays()
        self._destroy_window("unlock_dialog")
        self.unlock_in_progress = False
        if self.state != State.SHUTTING_DOWN:
            if not self._transition(State.FAULTED):
                self.state = State.FAULTED
                self._refresh_tray()
            self._show_notice("Idle Lock 發生錯誤",
                              f"{reason}\n\n輸入封鎖與鎖定畫面已解除。\n可從系統匣重新啟動監控或安全結束。")
        log.info("FAULT_RECOVERY_COMPLETE")

    def _destroy_window(self, attribute: str) -> None:
        win = getattr(self, attribute, None)
        if win:
            try:
                if win.winfo_exists():
                    win.destroy()
            except Exception:
                pass
        setattr(self, attribute, None)

    @staticmethod
    def _center(win: tk.Toplevel, width: int, height: int) -> None:
        win.update_idletasks()
        x = (win.winfo_screenwidth() - width) // 2
        y = (win.winfo_screenheight() - height) // 2
        win.geometry(f"{width}x{height}+{x}+{y}")

    def _show_main_window(self) -> None:
        if self.main_window and self.main_window.winfo_exists():
            self.main_window.deiconify()
            self.main_window.lift()
            self.main_window.focus_force()
            self._refresh_main_window()
            return
        win = tk.Toplevel(self.root)
        self.main_window = win
        win.title("Idle Lock 控制面板")
        win.configure(bg="#17172b")
        win.geometry("600x520")
        win.resizable(False, False)
        win.protocol("WM_DELETE_WINDOW", lambda: self._destroy_window("main_window"))

        tk.Label(win, text="Idle Lock 控制面板", font=("Segoe UI", 22, "bold"),
                 fg="white", bg="#17172b").pack(pady=(22, 6))
        self.main_status_var = tk.StringVar()
        self.main_mode_var = tk.StringVar()
        self.main_folder_var = tk.StringVar()
        tk.Label(win, textvariable=self.main_status_var, font=("Segoe UI", 14, "bold"),
                 fg="#70dc7c", bg="#17172b").pack(pady=4)
        tk.Label(win, text="解鎖：Ctrl + Alt + 0　｜　鎖定顯示切換：F1",
                 font=("Segoe UI", 11), fg="#b8c2df", bg="#17172b").pack(pady=(0, 15))

        primary = tk.Frame(win, bg="#17172b")
        primary.pack(pady=4)
        self.main_lock_button = tk.Button(
            primary, text="立即鎖定", command=lambda: self._lock("CONTROL_PANEL"),
            width=18, height=2, bg="#a43636", fg="white",
            font=("Segoe UI", 12, "bold"))
        self.main_lock_button.pack(side="left", padx=7)
        self.main_pause_button = tk.Button(
            primary, text="暫停監控", command=self._pause_monitoring,
            width=14, height=2, bg="#776b28", fg="white", font=("Segoe UI", 11))
        self.main_pause_button.pack(side="left", padx=7)
        self.main_resume_button = tk.Button(
            primary, text="繼續監控", command=self._continue_monitoring,
            width=14, height=2, bg="#2b713e", fg="white", font=("Segoe UI", 11))
        self.main_resume_button.pack(side="left", padx=7)

        display_card = tk.Frame(win, bg="#20203a", padx=16, pady=12)
        display_card.pack(fill="x", padx=34, pady=(18, 8))
        tk.Label(display_card, text="鎖定畫面與幻燈片", font=("Segoe UI", 12, "bold"),
                 fg="white", bg="#20203a").pack(anchor="w")
        tk.Label(display_card, textvariable=self.main_mode_var, font=("Segoe UI", 10),
                 fg="#aeb8d8", bg="#20203a").pack(anchor="w", pady=(5, 1))
        tk.Label(display_card, textvariable=self.main_folder_var, font=("Segoe UI", 9),
                 fg="#8995ba", bg="#20203a", wraplength=500,
                 justify="left").pack(anchor="w")
        tk.Button(display_card, text="選擇幻燈片資料夾", command=self._choose_slideshow_folder,
                  width=20).pack(anchor="w", pady=(8, 0))

        tools = tk.Frame(win, bg="#17172b")
        tools.pack(pady=14)
        for label, command in (("設定", self._show_settings),
                               ("查看日誌", self._open_log),
                               ("隱藏到系統匣", lambda: self._destroy_window("main_window")),
                               ("結束程式", self._safe_shutdown)):
            tk.Button(tools, text=label, command=command, width=14,
                      font=("Segoe UI", 10)).pack(side="left", padx=5)
        tk.Label(win, text="提示：鎖定後按 F1 可在 Windows 桌面與螢幕保護畫面之間切換。",
                 font=("Segoe UI", 9), fg="#7f8aac", bg="#17172b").pack(pady=6)
        self._center(win, 600, 520)
        self._refresh_main_window()
        win.lift()
        win.focus_force()

    def _refresh_main_window(self) -> None:
        if not self.main_window:
            return
        try:
            if not self.main_window.winfo_exists():
                return
            if self.main_status_var:
                self.main_status_var.set(f"目前狀態：{self._status_text()}")
            folder = str(self.settings.get("slideshow_folder", "")).strip()
            files = self._collect_slideshow_files()
            if self.main_mode_var:
                default_mode = ("幻燈片" if self.settings.get("use_slideshow_on_lock", False)
                                and files else "閒置提示")
                self.main_mode_var.set(
                    f"鎖定後預設：{default_mode}　｜　目前找到 {len(files)} 張圖片")
            if self.main_folder_var:
                self.main_folder_var.set(
                    f"資料夾：{folder}" if folder else "資料夾：尚未設定")
            normal = tk.NORMAL
            disabled = tk.DISABLED
            if self.main_lock_button:
                self.main_lock_button.configure(
                    state=normal if self.state == State.MONITORING and not self.hotkey_conflict
                    else disabled)
            if self.main_pause_button:
                self.main_pause_button.configure(
                    state=normal if self.state == State.MONITORING else disabled)
            if self.main_resume_button:
                self.main_resume_button.configure(
                    state=normal if self.state in (State.PAUSED, State.FAULTED)
                    and not self.hotkey_conflict else disabled)
        except Exception:
            log.exception("CONTROL_PANEL_REFRESH_FAILED")

    def _choose_slideshow_folder(self, parent=None) -> str:
        initial = str(self.settings.get("slideshow_folder", "")).strip()
        if not pathlib.Path(initial).is_dir():
            initial = str(pathlib.Path.home())
        chosen = fd.askdirectory(parent=parent or self.main_window or self.root,
                                 title="選擇 Idle Lock 幻燈片資料夾",
                                 initialdir=initial, mustexist=True)
        if chosen:
            self.settings["slideshow_folder"] = chosen
            self.settings["use_slideshow_on_lock"] = True
            save_settings(self.settings)
            count = len(self._collect_slideshow_files())
            log.info("SLIDESHOW_FOLDER_SELECTED path=%s images=%s", chosen, count)
            self._refresh_main_window()
        return chosen

    def _show_notice(self, title: str, message: str, startup=False,
                     offer_exit=False) -> None:
        self._destroy_window("notice_dialog")
        win = tk.Toplevel(self.root)
        self.notice_dialog = win
        win.title(title)
        win.attributes("-topmost", True)
        win.configure(bg="#1e1e2e")
        height = 260 if startup else 220
        win.geometry(f"440x{height}")
        win.resizable(False, False)
        tk.Label(win, text=title, font=("Segoe UI", 17, "bold"), fg="white",
                 bg="#1e1e2e").pack(pady=(22, 10))
        tk.Label(win, text=message, font=("Segoe UI", 10), justify="center",
                 fg="#c8c8d8", bg="#1e1e2e").pack(pady=6)
        row = tk.Frame(win, bg="#1e1e2e")
        row.pack(pady=16)
        tk.Button(row, text="知道了", width=12,
                  command=lambda: self._destroy_window("notice_dialog")).pack(side="left", padx=6)
        if startup:
            tk.Button(row, text="開啟設定", width=12,
                      command=lambda: (self._destroy_window("notice_dialog"),
                                       self._show_settings())).pack(side="left", padx=6)
        if offer_exit:
            tk.Button(row, text="結束程式", width=12,
                      command=self._safe_shutdown).pack(side="left", padx=6)
        win.protocol("WM_DELETE_WINDOW", lambda: self._destroy_window("notice_dialog"))
        self._center(win, 440, height)
        win.lift()

    def _show_settings(self) -> None:
        if self.settings_dialog and self.settings_dialog.winfo_exists():
            self.settings_dialog.lift()
            return
        win = tk.Toplevel(self.root)
        self.settings_dialog = win
        win.title("Idle Lock 設定")
        win.configure(bg="#1e1e2e")
        win.geometry("580x600")
        win.resizable(False, False)
        win.protocol("WM_DELETE_WINDOW", lambda: self._destroy_window("settings_dialog"))
        tk.Label(win, text="Idle Lock 設定", font=("Segoe UI", 16, "bold"),
                 fg="white", bg="#1e1e2e").pack(pady=15)
        threshold = tk.IntVar(value=int(self.settings["idle_threshold_seconds"]))
        interval = tk.IntVar(value=int(self.settings["idle_check_interval_ms"]))
        grace = tk.IntVar(value=int(self.settings["resume_grace_period_seconds"]))
        slide_interval = tk.IntVar(value=int(
            self.settings.get("slideshow_interval_seconds", 10)))
        slideshow_folder = tk.StringVar(value=str(
            self.settings.get("slideshow_folder", "")))
        use_slideshow = tk.BooleanVar(value=bool(
            self.settings.get("use_slideshow_on_lock", False)))
        for text, var, low, high, step in (
                ("閒置鎖定秒數 (10-86400)", threshold, 10, 86400, 1),
                ("檢查間隔毫秒 (250-2000)", interval, 250, 2000, 50),
                ("恢復保護秒數 (0-10)", grace, 0, 10, 1)):
            tk.Label(win, text=text, fg="#c8c8d8", bg="#1e1e2e").pack(pady=(7, 2))
            tk.Spinbox(win, from_=low, to=high, increment=step, textvariable=var,
                       width=12).pack()
        tk.Label(win, text="幻燈片切換秒數 (3-300)",
                 fg="#c8c8d8", bg="#1e1e2e").pack(pady=(8, 2))
        tk.Spinbox(win, from_=3, to=300, textvariable=slide_interval,
                   width=12).pack()
        tk.Checkbutton(win, text="鎖定後預設使用幻燈片",
                       variable=use_slideshow, fg="#d8d8e8", bg="#1e1e2e",
                       selectcolor="#1e1e2e", activebackground="#1e1e2e",
                       activeforeground="white").pack(pady=(12, 4))
        tk.Label(win, text="幻燈片資料夾", fg="#c8c8d8",
                 bg="#1e1e2e").pack()
        folder_row = tk.Frame(win, bg="#1e1e2e")
        folder_row.pack(pady=5)
        tk.Entry(folder_row, textvariable=slideshow_folder, width=50).pack(side="left", padx=4)

        def browse():
            chosen = fd.askdirectory(parent=win, title="選擇 Idle Lock 幻燈片資料夾",
                                     initialdir=(slideshow_folder.get()
                                                 if pathlib.Path(slideshow_folder.get()).is_dir()
                                                 else str(pathlib.Path.home())),
                                     mustexist=True)
            if chosen:
                slideshow_folder.set(chosen)
                use_slideshow.set(True)

        tk.Button(folder_row, text="瀏覽…", command=browse).pack(side="left", padx=4)
        tk.Label(win, text="解鎖：Ctrl + Alt + 0（主鍵盤與 NumPad）　顯示切換：F1",
                 fg="#8fa0c8", bg="#1e1e2e").pack(pady=12)

        def save():
            self.settings["idle_threshold_seconds"] = max(10, min(86400, threshold.get()))
            self.settings["idle_check_interval_ms"] = max(250, min(2000, interval.get()))
            self.settings["resume_grace_period_seconds"] = max(0, min(10, grace.get()))
            self.settings["slideshow_interval_seconds"] = max(
                3, min(300, slide_interval.get()))
            self.settings["slideshow_folder"] = slideshow_folder.get().strip()
            self.settings["use_slideshow_on_lock"] = bool(use_slideshow.get())
            save_settings(self.settings)
            log.info("SETTINGS_SAVED")
            self._destroy_window("settings_dialog")
            self._refresh_main_window()

        tk.Button(win, text="儲存", width=12, command=save).pack()
        self._center(win, 580, 600)

    def _status_text(self) -> str:
        if self.hotkey_conflict:
            return "發生錯誤"
        return {
            State.MONITORING: "監控中", State.LOCKING: "鎖定中", State.LOCKED: "已鎖定",
            State.UNLOCKING: "解鎖中", State.UNLOCK_DIALOG: "選擇中",
            State.PAUSED: "已暫停", State.FAULTED: "發生錯誤",
            State.STARTING: "啟動中", State.SHUTTING_DOWN: "結束中",
        }.get(self.state, self.state)

    def _build_menu(self):
        return pystray.Menu(
            pystray.MenuItem("開啟控制面板",
                             lambda *_: self._post_ui(self._show_main_window),
                             default=True),
            pystray.MenuItem(lambda _: f"目前狀態：{self._status_text()}", None, enabled=False),
            pystray.MenuItem("解鎖快捷鍵：Ctrl + Alt + 0", None, enabled=False),
            pystray.MenuItem("顯示切換：F1", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("立即鎖定", lambda *_: self._post_ui(self._lock, "TRAY"),
                             enabled=lambda _: self.state == State.MONITORING and not self.hotkey_conflict),
            pystray.MenuItem("暫停監控", lambda *_: self._post_ui(self._pause_monitoring),
                             enabled=lambda _: self.state == State.MONITORING),
            pystray.MenuItem("繼續監控", lambda *_: self._post_ui(self._continue_monitoring),
                             enabled=lambda _: self.state == State.PAUSED and not self.hotkey_conflict),
            pystray.MenuItem("重新啟動監控", lambda *_: self._post_ui(self._restart_monitoring),
                             enabled=lambda _: self.state in (State.PAUSED, State.FAULTED)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("設定", lambda *_: self._post_ui(self._show_settings)),
            pystray.MenuItem("查看日誌", lambda *_: self._post_ui(self._open_log)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("結束程式", lambda *_: self._post_ui(self._safe_shutdown)),
        )

    def _refresh_tray(self) -> None:
        self._refresh_main_window()
        if not self.icon:
            return
        try:
            if os.environ.get("IDLE_LOCK_SIMULATE_TRAY_REFRESH_FAILURE") == "1":
                raise OSError("Simulated tray refresh failure")
            if self.hotkey_conflict or self.state == State.FAULTED:
                image = self.icons["gray"]
            elif self.state == State.LOCKED:
                image = self.icons["red"]
            elif self.state == State.PAUSED:
                image = self.icons["yellow"]
            else:
                image = self.icons["green"]
            # Tray rendering can fail independently (for example when the OS
            # temporary directory is full).  It must never interrupt unlock.
            self.icon.icon = image
            self.icon.title = f"Idle Lock｜{self._status_text()}"
            self.icon.menu = self._build_menu()
            self.icon.update_menu()
        except Exception:
            log.exception("TRAY_REFRESH_FAILED_NONFATAL state=%s", self.state)

    def _restart_monitoring(self) -> None:
        if not self.input_guard.main_hotkey_registered:
            self.hotkey_conflict = True
            self._show_notice("Idle Lock 快捷鍵異常",
                              "無法註冊解鎖快捷鍵 Ctrl + Alt + 0。\n"
                              "為避免進入無法解除的鎖定狀態，自動鎖定已暫停。")
            return
        self.hotkey_conflict = False
        if self.state == State.FAULTED:
            self._transition(State.PAUSED)
        self._continue_monitoring()
        log.info("MONITOR_RESTARTED")

    def _open_log(self) -> None:
        try:
            os.startfile(LOG_FILE)
        except Exception:
            log.exception("OPEN_LOG_FAILED")

    def _watch_wake_event(self) -> None:
        if not self.instance or not self.instance.wake_event:
            return
        while self.running:
            if kernel32.WaitForSingleObject(self.instance.wake_event, 500) == WAIT_OBJECT_0:
                kernel32.ResetEvent(self.instance.wake_event)
                if self.running:
                    log.info("EXISTING_INSTANCE_WAKE_RECEIVED")
                    self._post_ui(self._show_main_window)

    def _install_exception_guards(self) -> None:
        def thread_exception(args):
            log.critical("THREAD_UNHANDLED_EXCEPTION", exc_info=(args.exc_type,
                         args.exc_value, args.exc_traceback))
            self._post_ui(self._fault_recovery, "背景執行緒發生未處理錯誤")

        threading.excepthook = thread_exception

        def tk_exception(exc_type, exc_value, exc_tb):
            log.critical("UI_DISPATCHER_UNHANDLED_EXCEPTION",
                         exc_info=(exc_type, exc_value, exc_tb))
            self._fault_recovery("UI 發生未處理錯誤")

        self.root.report_callback_exception = tk_exception

    def _safe_shutdown(self) -> None:
        if self.state == State.SHUTTING_DOWN:
            return
        if not self._transition(State.SHUTTING_DOWN):
            self.state = State.SHUTTING_DOWN
        self.running = False
        log.info("PROCESS_EXIT_CLEANUP_BEGIN")
        self.input_guard.set_locked(False)
        self._hide_overlays()
        for attr in ("main_window", "unlock_dialog", "settings_dialog", "notice_dialog"):
            self._destroy_window(attr)
        self.input_guard.stop()
        if self.runtime_slide_dir:
            try:
                for path in self.runtime_slide_dir.iterdir():
                    path.unlink()
                self.runtime_slide_dir.rmdir()
            except Exception:
                log.exception("RUNTIME_SLIDES_CLEANUP_FAILED")
            self.runtime_slide_dir = None
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                log.exception("TRAY_STOP_FAILED")
            self.icon = None
        if self.instance:
            self.instance.close()
        if self.root:
            self.root.after_idle(self.root.quit)
        log.info("PROCESS_EXIT_CLEANUP_SUCCESS")

    @staticmethod
    def _send_test_hotkey() -> None:
        KEYEVENTF_KEYUP = 0x0002
        for vk, flags in ((VK_CONTROL, 0), (VK_MENU, 0), (VK_0, 0),
                          (VK_0, KEYEVENTF_KEYUP), (VK_MENU, KEYEVENTF_KEYUP),
                          (VK_CONTROL, KEYEVENTF_KEYUP)):
            user32.keybd_event(vk, 0, flags, 0)
            time.sleep(0.03)

    @staticmethod
    def _send_test_f1() -> None:
        user32.keybd_event(VK_F1, 0, 0, 0)
        time.sleep(0.05)
        user32.keybd_event(VK_F1, 0, 0x0002, 0)

    def _prepare_runtime_slides(self) -> None:
        folder = PROJECT_DIR / "_runtime_test_slides"
        folder.mkdir(exist_ok=True)
        image = Image.new("RGB", (1280, 720), "#24557a")
        draw = ImageDraw.Draw(image)
        draw.rectangle((40, 40, 1240, 680), outline="#a8e0ff", width=10)
        draw.text((80, 90), "Idle Lock Slideshow Runtime Test", fill="white")
        image.save(folder / "runtime-slide.png")
        self.runtime_slide_dir = folder
        self.settings["slideshow_folder"] = str(folder)
        self.settings["use_slideshow_on_lock"] = True
        self.settings["slideshow_interval_seconds"] = 3

    def _schedule_runtime_display_sequence(self) -> None:
        def verify_desktop_mode():
            self.runtime_results["f1_desktop_mode"] = (
                self.state == State.LOCKED and self.lock_display_mode == "desktop"
                and len(self.overlays) == len(_monitor_rects()))
            threading.Thread(target=self._send_test_f1,
                             name="DisplayTest2", daemon=True).start()

        def verify_slideshow_mode():
            self.runtime_results["f1_slideshow_mode"] = (
                self.state == State.LOCKED and self.lock_display_mode == "slideshow"
                and bool(self.overlays))
            threading.Thread(target=self._send_test_hotkey,
                             name="HotkeyTest", daemon=True).start()

        self.root.after(250, lambda: threading.Thread(
            target=self._send_test_f1, name="DisplayTest1", daemon=True).start())
        self.root.after(600, verify_desktop_mode)
        self.root.after(1100, verify_slideshow_mode)
        if self.runtime_verify_unlock:
            self.root.after(1900, self.runtime_verify_unlock)

    def _begin_runtime_test(self) -> None:
        self.settings["show_startup_notification"] = False
        self.settings["show_unlock_dialog"] = True
        if os.environ.get("IDLE_LOCK_SIMULATE_HOTKEY_CONFLICT") == "1":
            def verify_conflict():
                self.runtime_results["hotkey_conflict_safety"] = (
                    self.hotkey_conflict and self.state == State.PAUSED
                    and not self.input_guard.locked.is_set() and not self.overlays)
                log.info("RUNTIME_TEST_RESULTS %s", self.runtime_results)
                self._safe_shutdown()
            self.root.after(300, verify_conflict)
            return
        # The current Windows idle time may already exceed the configured
        # threshold; keep the test deterministic until its explicit lock.
        self._prepare_runtime_slides()
        self.resume_grace_until = time.monotonic() + 5.0
        self.root.after(250, lambda: self._lock("RUNTIME_TEST"))

        def verify_unlock():
            if os.environ.get("IDLE_LOCK_SIMULATE_UNLOCK_FAULT") == "1":
                self.runtime_results["fault_recovery"] = (
                    self.state == State.FAULTED and not self.overlays
                    and not self.input_guard.locked.is_set())
                log.info("RUNTIME_TEST_RESULTS %s", self.runtime_results)
                self.root.after(250, self._safe_shutdown)
                return
            unlocked = self.state == State.UNLOCK_DIALOG and not self.overlays \
                       and not self.input_guard.locked.is_set()
            self.runtime_results["hotkey_unlock"] = unlocked
            # Repeated requests must not create a second flow/dialog.
            dialog_id = id(self.unlock_dialog)
            self._request_unlock("REPEATED_TEST_1")
            self._request_unlock("REPEATED_TEST_2")
            self.runtime_results["unlock_reentry"] = id(self.unlock_dialog) == dialog_id
            self._continue_monitoring()
            self.runtime_results["continue_monitoring"] = self.state == State.MONITORING
            self._pause_monitoring()
            self.runtime_results["pause_monitoring"] = self.state == State.PAUSED
            self._continue_monitoring()
            log.info("RUNTIME_TEST_RESULTS %s", self.runtime_results)
            self.root.after(250, self._safe_shutdown)

        self.runtime_verify_unlock = verify_unlock

    def run(self) -> bool:
        executable = pathlib.Path(sys.executable if getattr(sys, "frozen", False) else __file__).resolve()
        log.info("=" * 68)
        log.info("APPLICATION_START version=%s executable=%s sha256=%s",
                 APP_VERSION, executable, _sha256(executable))
        self.root = tk.Tk()
        self.root.withdraw()
        self._install_exception_guards()
        self.running = True

        input_ok = self.input_guard.start()
        self.hotkey_conflict = not input_ok
        self.icon = pystray.Icon("IdleLock", self.icons["green"], "Idle Lock",
                                 self._build_menu())
        self.icon.run_detached()

        if input_ok:
            self._transition(State.MONITORING if self.settings.get("auto_start_monitoring", True)
                             else State.PAUSED)
            if self.state == State.MONITORING:
                self._reset_idle_baseline()
        else:
            self._transition(State.PAUSED)
            log.error("AUTO_LOCK_DISABLED reason=%s", self.input_guard.start_error)

        self._refresh_tray()
        self.root.after(25, self._poll_ui_queue)
        self.root.after(100, self._schedule_monitor)
        if self.instance and self.instance.wake_event:
            threading.Thread(target=self._watch_wake_event, name="InstanceWake",
                             daemon=True).start()

        if self.runtime_test:
            self._begin_runtime_test()
        elif self.hotkey_conflict:
            self.root.after(100, lambda: self._show_notice(
                "Idle Lock：快捷鍵註冊失敗",
                "無法註冊解鎖快捷鍵 Ctrl + Alt + 0。\n"
                "為避免進入無法解除的鎖定狀態，自動鎖定已暫停。"))
        elif self.settings.get("show_startup_notification", True):
            self.root.after(100, self._show_main_window)

        try:
            self.root.mainloop()
        finally:
            if self.state != State.SHUTTING_DOWN:
                self._safe_shutdown()
            try:
                self.root.destroy()
            except Exception:
                pass
        if not self.runtime_test:
            return True
        if os.environ.get("IDLE_LOCK_SIMULATE_HOTKEY_CONFLICT") == "1":
            return self.runtime_results.get("hotkey_conflict_safety", False)
        if os.environ.get("IDLE_LOCK_SIMULATE_UNLOCK_FAULT") == "1":
            return self.runtime_results.get("fault_recovery", False)
        return all(self.runtime_results.get(k, False) for k in
                   ("f1_desktop_mode", "f1_slideshow_mode", "hotkey_unlock",
                    "unlock_reentry", "continue_monitoring", "pause_monitoring"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Idle Lock")
    parser.add_argument("--threshold", type=int)
    parser.add_argument("--no-single-instance", action="store_true")
    parser.add_argument("--runtime-test", action="store_true",
                        help="Run a short real Tk/hook/overlay integration test")
    args = parser.parse_args()

    instance = None if args.no_single_instance else SingleInstance()
    if instance and not instance.acquire():
        SingleInstance.wake_existing()
        log.info("SECONDARY_INSTANCE_EXIT_AFTER_WAKE")
        return 0

    if args.threshold is not None:
        settings = load_settings()
        settings["idle_threshold_seconds"] = max(10, min(86400, args.threshold))
        save_settings(settings)

    app = IdleLock(instance=instance, runtime_test=args.runtime_test)
    try:
        return 0 if app.run() else 2
    except KeyboardInterrupt:
        return 0
    except Exception:
        log.critical("APPDOMAIN_UNHANDLED_EXCEPTION", exc_info=True)
        try:
            app._fault_recovery("程式發生未處理錯誤")
            app._safe_shutdown()
        except Exception:
            log.critical("EMERGENCY_CLEANUP_FAILED", exc_info=True)
        return 1
    finally:
        if instance:
            instance.close()


_exit_logged = False


def _process_exit_log() -> None:
    global _exit_logged
    if not _exit_logged:
        _exit_logged = True
        log.info("PROCESS_EXIT")


atexit.register(_process_exit_log)

if __name__ == "__main__":
    raise SystemExit(main())
