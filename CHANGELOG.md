# Changelog

## [Unreleased] - 2026-08-22

### Changed
- 將 `agent/readme-documentation` 的多螢幕／不同 DPI 鎖定修正與生命週期文件合入 `main`。
- 合併時保留 `main` 既有的 `LICENSE` 與 `NOTICE`，並整合 README 的 Agent workflow 說明。
- 重寫 README 的 Windows 下載／解壓／EXE 建置流程，明確區分 GitHub Source code ZIP、可攜式 EXE 與 Python 開發模式。
- 將驗證版 `dist\IdleLock.exe` 直接納入 repository，讓 GitHub `main.zip` 解壓後可直接執行；`.gitignore` 只放行該檔，`.gitattributes` 將其標記為 binary。
- README 改以「下載整包後執行 `dist\IdleLock.exe`」為推薦路線，並公開 bundled EXE 的 SHA-256 與未簽章提醒。
- AGENTS 新增 bundled EXE 的建置、frozen runtime、SHA-256 與 GitHub ZIP 回讀契約，並校正 repository 為 public。

### Validation
- `.venv\Scripts\python.exe -m py_compile idle_lock.py`：通過。
- `.venv\Scripts\python.exe idle_lock.py --no-single-instance --runtime-test`：通過；兩台螢幕的桌面／幻燈片切換、快捷鍵解鎖、重入保護與暫停／恢復結果全為 `True`。
- 測試後輸入 hook 完整釋放，既有系統匣程式已恢復執行。
- 從 GitHub `main.zip` 重新下載並以 `Expand-Archive` 解壓，確認 Source ZIP 含程式與建置規格但不含 `dist/`。
- 在隔離環境依 README 指令使用 Python 3.14.3 與 PyInstaller 6.22.2 建置成功，產生單一 `dist\IdleLock.exe`。
- 新建 EXE frozen runtime test：六項結果全為 `True`，process cleanup 通過；README 的 10 個 PowerShell code block 均無 parser error。
- Bundled EXE：19,318,987 bytes，SHA-256 `3ACB74528887CCA4156B8CB62633BFFBAB8C882C0E91905EC878575E104CC9C0`；來源 `idle_lock.py` 與目前 `HEAD` Git blob 一致。
- Authenticode：`NotSigned`；此限制已在 README 以 SmartScreen 安全提醒揭露。

### Delivery
- GitHub `main`：`VERIFIED`，功能合併 commit `3343dbfbddff424d01972a10eb3ee69ae5d2bdc7` 已以非 force push 交付並回讀一致。
- tag、GitHub Release 與 repository 可見性未變更。
- Windows README 重寫：`VERIFIED`，文件 commit `a49e23bb7e586a4e52fa7ad360556e42c3702ca9` 已非 force push 至 `main` 並回讀一致。
- Bundled EXE 整包交付：`LOCAL_ONLY/PENDING_GATE`，等待 commit、本機 ZIP 驗證、Delivery Gate、GitHub push 與實際 `main.zip` 回讀。

## [Unreleased] - 2026-08-09

### Changed
- 對齊四檔生命週期、README delivery 規則與外部知識庫邊界。

### Validation
- 本輪只更新治理文件；多螢幕與 DPI 程式未修改。

### Delivery
- GitHub：`VERIFIED`，治理 commit `9c634827dd4883da462ef0bd5bb4dbdb44e79a30` 已推送 `agent/readme-documentation` 並回讀一致。
