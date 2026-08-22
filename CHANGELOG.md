# Changelog

## [Unreleased] - 2026-08-22

### Changed
- 將 `agent/readme-documentation` 的多螢幕／不同 DPI 鎖定修正與生命週期文件合入 `main`。
- 合併時保留 `main` 既有的 `LICENSE` 與 `NOTICE`，並整合 README 的 Agent workflow 說明。
- 重寫 README 的 Windows 下載／解壓／EXE 建置流程，明確區分 GitHub Source code ZIP、可攜式 EXE 與 Python 開發模式。

### Validation
- `.venv\Scripts\python.exe -m py_compile idle_lock.py`：通過。
- `.venv\Scripts\python.exe idle_lock.py --no-single-instance --runtime-test`：通過；兩台螢幕的桌面／幻燈片切換、快捷鍵解鎖、重入保護與暫停／恢復結果全為 `True`。
- 測試後輸入 hook 完整釋放，既有系統匣程式已恢復執行。
- 從 GitHub `main.zip` 重新下載並以 `Expand-Archive` 解壓，確認 Source ZIP 含程式與建置規格但不含 `dist/`。
- 在隔離環境依 README 指令使用 Python 3.14.3 與 PyInstaller 6.22.2 建置成功，產生單一 `dist\IdleLock.exe`。
- 新建 EXE frozen runtime test：六項結果全為 `True`，process cleanup 通過；README 的 10 個 PowerShell code block 均無 parser error。

### Delivery
- GitHub `main`：`VERIFIED`，功能合併 commit `3343dbfbddff424d01972a10eb3ee69ae5d2bdc7` 已以非 force push 交付並回讀一致。
- EXE、tag、GitHub Release 與 repository 可見性未變更。
- Windows README 重寫：`VERIFIED`，文件 commit `a49e23bb7e586a4e52fa7ad360556e42c3702ca9` 已非 force push 至 `main` 並回讀一致。

## [Unreleased] - 2026-08-09

### Changed
- 對齊四檔生命週期、README delivery 規則與外部知識庫邊界。

### Validation
- 本輪只更新治理文件；多螢幕與 DPI 程式未修改。

### Delivery
- GitHub：`VERIFIED`，治理 commit `9c634827dd4883da462ef0bd5bb4dbdb44e79a30` 已推送 `agent/readme-documentation` 並回讀一致。
