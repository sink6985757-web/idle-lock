# Changelog

## [Unreleased] - 2026-08-22

### Changed
- 將 `agent/readme-documentation` 的多螢幕／不同 DPI 鎖定修正與生命週期文件合入 `main`。
- 合併時保留 `main` 既有的 `LICENSE` 與 `NOTICE`，並整合 README 的 Agent workflow 說明。

### Validation
- `.venv\Scripts\python.exe -m py_compile idle_lock.py`：通過。
- `.venv\Scripts\python.exe idle_lock.py --no-single-instance --runtime-test`：通過；兩台螢幕的桌面／幻燈片切換、快捷鍵解鎖、重入保護與暫停／恢復結果全為 `True`。
- 測試後輸入 hook 完整釋放，既有系統匣程式已恢復執行。

### Delivery
- GitHub `main`：`VERIFIED`，功能合併 commit `3343dbfbddff424d01972a10eb3ee69ae5d2bdc7` 已以非 force push 交付並回讀一致。
- EXE、tag、GitHub Release 與 repository 可見性未變更。

## [Unreleased] - 2026-08-09

### Changed
- 對齊四檔生命週期、README delivery 規則與外部知識庫邊界。

### Validation
- 本輪只更新治理文件；多螢幕與 DPI 程式未修改。

### Delivery
- GitHub：`VERIFIED`，治理 commit `9c634827dd4883da462ef0bd5bb4dbdb44e79a30` 已推送 `agent/readme-documentation` 並回讀一致。
