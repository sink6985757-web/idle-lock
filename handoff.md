# Handoff

## 目前做到哪
已修正立即鎖定畫面在多螢幕／不同 DPI 環境的尺寸與位置偏移，並讓手動或自動鎖定前自動收起控制、設定及通知視窗。新版 EXE 已重建，使用者實際測試正常。

## 目前狀態
- 可執行：是
- 已驗證：2026-08-22 fresh `py_compile` 與原始碼 runtime test 通過；兩台螢幕的桌面／幻燈片顯示、快捷鍵解鎖、重入保護與暫停／恢復全數通過；既有凍結 EXE runtime test 與使用者實機操作證據仍保留
- GitHub：功能合併 commit `3343dbfbddff424d01972a10eb3ee69ae5d2bdc7` 已推送 `main` 並回讀一致
- 未完成：尚未建立新 tag／GitHub Release，也未發布新版 EXE

## 下一步
1. 後續工作從 GitHub `main` 的最新 checkpoint 接續。
2. 若要標記版本、建立 GitHub Release 或發布 EXE，另走 ReadyGate／release 授權。

## 注意事項
- 新版執行檔位於 `dist/IdleLock.exe`，舊版備份位於 `dist/IdleLock-pre-display-fix-20260808.exe`；`dist/` 不納入 Git。
- 多螢幕負座標必須透過 Win32 `SetWindowPos` 定位；Tk 的負 geometry offset 不是絕對座標。

## 最近更新
- 時間：2026-08-22 21:34 +08:00
- 更新者：Codex
- 電腦：YULIN-SFG16-72
- 成果 commit：3343dbfbddff424d01972a10eb3ee69ae5d2bdc7
- Git push：VERIFIED
- 外部知識庫：ON_DEMAND_ONLY

## 2026-08-09 生命週期權威更新

- 上述多螢幕／DPI 修正與測試證據保留；Obsidian 不再屬於收工流程。
- 新增 CHANGELOG，更新 AGENTS／README；程式與安裝包未修改。
- 當時 GitHub 治理 commit `9c634827dd4883da462ef0bd5bb4dbdb44e79a30` 已推送 `agent/readme-documentation` 並回讀一致；此段為歷史狀態。

## 2026-08-22 main 同步

- 依 `RG-IDLELOCK-MAIN-20260822-v1` 將功能分支與 `main` 安全整合，保留 `LICENSE`／`NOTICE`。
- fresh 原始碼 runtime test 實際建立兩台螢幕 overlay，六項驗證全為 `True`，並完成 input hook cleanup。
- 功能合併 commit `3343dbfbddff424d01972a10eb3ee69ae5d2bdc7` 已非 force push 至 GitHub `main`，本機與遠端回讀一致。
- 唯一續跑點：若要發布新版 EXE、tag 或 GitHub Release，另走 release Gate。
