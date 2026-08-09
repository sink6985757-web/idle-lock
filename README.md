# Idle Lock

Idle Lock 是一套 Windows 專用的閒置監控與畫面保護工具。程式會持續偵測鍵盤與滑鼠的閒置時間；達到設定門檻後，自動顯示全螢幕鎖定畫面並暫時阻擋輸入。使用者可透過固定快捷鍵解除鎖定，也能在鎖定期間切換回 Windows 桌面顯示，或播放指定資料夾中的圖片。

目前版本：**2.1.0**

> [!IMPORTANT]
> Idle Lock 是應用程式層級的輸入保護工具，不是 Windows 帳號驗證或安全性鎖定機制。它不會要求密碼，也不能取代 `Win + L`、Windows 登入畫面、磁碟加密或其他端點安全措施。

## 功能特色

- 自動偵測 Windows 系統閒置時間，到達門檻後鎖定。
- 可從控制面板或系統匣選單立即鎖定。
- 鎖定時在每一台螢幕建立置頂遮罩，支援多螢幕環境。
- 鎖定期間阻擋一般鍵盤與滑鼠輸入。
- 使用 `Ctrl + Alt + 0` 解鎖，支援主鍵盤與數字鍵盤的 `0`。
- 使用 `F1` 在鎖定畫面與目前 Windows 桌面之間切換；顯示桌面時仍維持輸入鎖定。
- 可遞迴讀取指定資料夾中的圖片，作為全螢幕幻燈片。
- 支援 JPG、JPEG、PNG、BMP、GIF、WebP、TIF 與 TIFF 圖片。
- 系統匣提供目前狀態、立即鎖定、暫停、繼續、重新啟動、設定、日誌與結束功能。
- 單一執行個體設計：再次啟動程式時，會喚醒既有程式的控制面板。
- 若解鎖快捷鍵註冊失敗，程式會停止自動鎖定，避免進入無法解除的狀態。
- 發生未處理錯誤時，優先解除輸入封鎖與關閉遮罩，再進入可復原狀態。
- 啟動時記錄執行檔版本、路徑與 SHA-256，方便追蹤實際執行版本。

## 系統需求

- Windows 作業系統；程式使用 Win32 API，不支援 macOS 或 Linux。
- 從原始碼執行時需要 Python 3.10 以上版本。
- Python 套件：`pystray`、`Pillow`。
- Tkinter；一般 Windows 官方 Python 安裝程式已包含此元件。

## 快速開始

### 使用已建置的執行檔

如果已取得 `IdleLock.exe`，直接雙擊即可啟動。程式會常駐於 Windows 系統匣；關閉控制面板只會隱藏視窗，不會結束監控。

要完整結束程式，請在系統匣圖示上按右鍵，選擇「結束程式」。

### 從原始碼執行

在 PowerShell 進入專案目錄後執行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe idle_lock.py
```

預設行為：

- 啟動後立即進入監控狀態。
- 預設連續閒置 60 秒後鎖定。
- 啟動時開啟控制面板。
- 解鎖後顯示選擇視窗，可繼續監控、暫停監控或結束程式。

## 操作方式

| 操作 | 方法 | 說明 |
| --- | --- | --- |
| 開啟控制面板 | 雙擊系統匣圖示，或在選單中選擇「開啟控制面板」 | 查看狀態與常用功能 |
| 立即鎖定 | 控制面板或系統匣選擇「立即鎖定」 | 只有在正常監控中才能使用 |
| 自動鎖定 | 保持無鍵盤、滑鼠輸入直到超過門檻 | 預設為 60 秒 |
| 解除鎖定 | 按下 `Ctrl + Alt + 0` | 主鍵盤與 NumPad `0` 均可嘗試使用 |
| 切換鎖定顯示 | 鎖定時按 `F1` | 在 Windows 桌面與保護畫面／幻燈片之間切換；不會解除鎖定 |
| 暫停監控 | 控制面板或系統匣選擇「暫停監控」 | 暫停自動鎖定 |
| 繼續監控 | 選擇「繼續監控」 | 重新計算閒置時間，並套用恢復保護秒數 |
| 查看日誌 | 系統匣或控制面板選擇「查看日誌」 | 使用預設文字檢視器開啟日誌 |
| 結束程式 | 系統匣或控制面板選擇「結束程式」 | 解除輸入攔截、關閉遮罩並退出 |

## 系統匣狀態顏色

| 顏色 | 狀態 |
| --- | --- |
| 綠色 | 正常監控中 |
| 紅色 | 已鎖定 |
| 黃色 | 已暫停 |
| 灰色 | 快捷鍵衝突或程式錯誤 |

## 鎖定畫面與幻燈片

未啟用幻燈片時，鎖定後會在所有螢幕顯示閒置提示。啟用幻燈片後，程式會遞迴掃描指定資料夾及其子資料夾，依檔名排序播放支援的圖片，並裁切填滿每台螢幕。

設定方式：

1. 開啟控制面板。
2. 選擇「選擇幻燈片資料夾」，或進入「設定」。
3. 選擇包含圖片的資料夾。
4. 確認「鎖定後預設使用幻燈片」已勾選。
5. 設定圖片切換秒數並儲存。

若資料夾無法存取、沒有支援的圖片或圖片載入失敗，程式會自動退回一般閒置提示畫面。

## 設定項目

| 設定 | 預設值 | 可設定範圍 | 用途 |
| --- | ---: | ---: | --- |
| 閒置鎖定秒數 | 60 秒 | 10–86400 秒 | 無輸入多久後進入鎖定 |
| 檢查間隔 | 500 毫秒 | 250–2000 毫秒 | 重新檢查閒置時間的頻率 |
| 恢復保護秒數 | 3 秒 | 0–10 秒 | 啟動或恢復監控後的緩衝時間 |
| 幻燈片切換秒數 | 10 秒 | 3–300 秒 | 每張圖片顯示多久 |
| 幻燈片資料夾 | 未設定 | 現有資料夾 | 圖片來源位置 |
| 鎖定後使用幻燈片 | 關閉 | 開啟／關閉 | 決定預設鎖定顯示模式 |

設定會儲存在 `settings.json`：

- 從原始碼執行時：專案目錄下的 `settings.json`。
- 從 EXE 執行時：`IdleLock.exe` 所在目錄下的 `settings.json`。

執行日誌位於同一目錄下的 `logs/idle-lock.log`。這些執行期檔案已由 `.gitignore` 排除，不會提交到版本庫。

## 命令列參數

```text
python idle_lock.py [--threshold SECONDS] [--no-single-instance] [--runtime-test]
```

| 參數 | 用途 |
| --- | --- |
| `--threshold SECONDS` | 將閒置門檻限制在 10–86400 秒內，並寫入 `settings.json` |
| `--no-single-instance` | 關閉單一執行個體保護；主要供開發與測試使用 |
| `--runtime-test` | 執行真實 Tk、全域快捷鍵、輸入攔截與遮罩整合測試 |

> [!CAUTION]
> `--runtime-test` 會短暫建立鎖定畫面並操作全域快捷鍵，僅建議在本機互動測試時使用。一般使用者不需要執行此參數。

例如，將閒置門檻改為 5 分鐘：

```powershell
python idle_lock.py --threshold 300
```

## 建置 Windows EXE

安裝 PyInstaller 後，使用專案內的 `IdleLock.spec` 建置：

```powershell
python -m pip install pyinstaller
pyinstaller --clean --noconfirm IdleLock.spec
```

建置完成後，執行檔位於：

```text
dist\IdleLock.exe
```

`build/`、`dist/`、`logs/`、`__pycache__/` 與本機設定檔不納入 Git 版本控制。

## 專案結構

```text
idle-lock/
├─ idle_lock.py       # 主程式、UI、Win32 輸入攔截與狀態管理
├─ IdleLock.spec      # PyInstaller 建置規格
├─ requirements.txt   # 執行階段 Python 依賴
├─ README.md          # 使用與開發說明
└─ .gitignore         # 排除建置與執行期檔案
```

## 版本控制與發布

專案採用語意化版本 `MAJOR.MINOR.PATCH`：

- `MAJOR`：不相容的行為或架構變更。
- `MINOR`：向下相容的新功能。
- `PATCH`：向下相容的修正與小幅改善。

目前程式版本定義於 `idle_lock.py` 的 `APP_VERSION`。準備新版本時，建議依序完成：

1. 更新 `APP_VERSION`。
2. 確認 `requirements.txt` 與 `IdleLock.spec` 仍符合實際依賴。
3. 執行語法檢查與互動整合測試。
4. 提交變更，建立對應的 `vX.Y.Z` Git 標籤。
5. 重新建置 EXE，確認版本與日誌資訊正確後再發布。

基本檢查：

```powershell
python -m py_compile idle_lock.py
python idle_lock.py --runtime-test
```

建立版本提交與標籤：

```powershell
git add idle_lock.py requirements.txt IdleLock.spec README.md
git commit -m "Release vX.Y.Z"
git tag -a vX.Y.Z -m "Idle Lock vX.Y.Z"
git push origin main --follow-tags
```

功能開發與修正建議先在獨立分支進行，例如 `feature/slideshow-controls` 或 `fix/hotkey-recovery`，完成檢查後再合併到 `main`。

## 疑難排解

### 顯示快捷鍵衝突或無法開始監控

`Ctrl + Alt + 0` 可能已被其他程式註冊。Idle Lock 會暫停自動鎖定以確保安全。請先關閉或修改衝突程式的快捷鍵，再從系統匣選擇「重新啟動監控」。

### 幻燈片沒有出現

確認資料夾存在、程式具備讀取權限，而且至少包含一張支援格式的圖片。若圖片清單為空，程式會顯示一般閒置提示。

### 關閉視窗後找不到程式

控制面板關閉後，程式仍會在 Windows 系統匣執行。請展開系統匣的隱藏圖示區尋找 Idle Lock。

### 程式發生錯誤

查看 `logs/idle-lock.log`。故障復原流程會先釋放輸入封鎖並關閉鎖定遮罩，可再從系統匣嘗試重新啟動監控或安全結束程式。

## 已知限制

- 僅支援 Windows。
- 解鎖方式固定為 `Ctrl + Alt + 0`，目前沒有密碼驗證或自訂快捷鍵介面。
- 程式不會自動設定「隨 Windows 開機啟動」。
- 這不是作業系統層級的安全鎖；需要安全離席時仍應使用 `Win + L`。

## Agent workflow 與版本紀錄

- GitHub canonical：`sink6985757-web/idle-lock`。
- 本 README 是人類與 Agent／Tool 的安裝、使用、版本與公開文案；近期變更見 [`CHANGELOG.md`](CHANGELOG.md)。
- 每次收工更新 CHANGELOG 與 handoff；GitHub delivery 前更新本 README。
- 外部知識庫為 `ON_DEMAND_ONLY`，不屬於 initial／startup／shutdown。
