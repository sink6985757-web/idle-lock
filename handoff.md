# Handoff

## 目前做到哪
已修正立即鎖定畫面在多螢幕／不同 DPI 環境的尺寸與位置偏移，並讓手動或自動鎖定前自動收起控制、設定及通知視窗。新版 EXE 已重建，使用者實際測試正常。

## 目前狀態
- 可執行：是
- 已驗證：2026-08-22 fresh `py_compile` 與原始碼 runtime test 通過；兩台螢幕的桌面／幻燈片顯示、快捷鍵解鎖、重入保護與暫停／恢復全數通過；既有凍結 EXE runtime test 與使用者實機操作證據仍保留
- GitHub：功能合併 commit `3343dbfbddff424d01972a10eb3ee69ae5d2bdc7` 已推送 `main` 並回讀一致
- Windows README：已完成下載、解壓、隔離建置與新建 EXE runtime 驗證；文件 commit `a49e23bb7e586a4e52fa7ad360556e42c3702ca9` 已推送 `main` 並回讀一致
- Bundled EXE：已把驗證版放入 `dist\IdleLock.exe` 並開啟精確 Git 例外，目前為 `LOCAL_ONLY/PENDING_GATE`
- 未完成：尚待 commit、本機 ZIP 驗證、GitHub push 與實際 `main.zip` 回讀；不建立 tag／GitHub Release

## 下一步
1. 建立 bundled EXE commit，驗證本機 Git ZIP 後完成 Delivery Gate 與非 force push。
2. 重新下載 GitHub `main.zip`，確認 `dist\IdleLock.exe` 存在且 SHA-256 完全一致。
3. 回填最終證據 checkpoint 並完成 shutdown。

## 注意事項
- Git 只追蹤 `dist/IdleLock.exe`；`dist/IdleLock-pre-bundled-20260822.exe`、`dist/IdleLock-pre-display-fix-20260808.exe`、settings、log 與其他 build 輸出維持忽略。
- Bundled EXE 目前沒有數位簽章，Windows 可能顯示 SmartScreen；README 已揭露且不得建議關閉安全防護。
- 多螢幕負座標必須透過 Win32 `SetWindowPos` 定位；Tk 的負 geometry offset 不是絕對座標。

## 最近更新
- 時間：2026-08-22 22:01 +08:00
- 更新者：Codex
- 電腦：YULIN-SFG16-72
- 成果 commit：a49e23bb7e586a4e52fa7ad360556e42c3702ca9
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

## 2026-08-22 Windows README 重寫

- GitHub 目前沒有 Release／EXE，且 `dist/` 不納入 Git；README 已改為先說明 Source ZIP 與可攜式 EXE 的差異。
- 使用 GitHub 實際 `main.zip` 在全新暫存環境驗證解壓與完整建置指令，成功產生單一 EXE。
- 新建 EXE 的 frozen runtime test 六項全為 `True`，測試後 input hook cleanup 成功，原有常駐 EXE 已恢復。
- 文件 commit `a49e23bb7e586a4e52fa7ad360556e42c3702ca9` 已非 force push 至 GitHub `main`，本機與遠端回讀一致。
- 唯一續跑點：若要提供可直接下載的 EXE，另走 tag／GitHub Release／EXE 發布 Gate。

## 2026-08-22 Bundled EXE 整包交付（交付前）

- 使用者明確要求 GitHub Code ZIP 直接包含可執行 EXE；本輪 ReadyGate 工作單為 `RG-IDLELOCK-BUNDLE-EXE-20260822-v1`。
- 驗證版 `dist\IdleLock.exe` 為 19,318,987 bytes，SHA-256 `3ACB74528887CCA4156B8CB62633BFFBAB8C882C0E91905EC878575E104CC9C0`，frozen runtime 六項全為 `True`。
- 舊本機 EXE 已備份為 `dist/IdleLock-pre-bundled-20260822.exe` 並維持忽略；repository 只放行指定 bundled EXE。
- 目前狀態：`LOCAL_ONLY/PENDING_GATE`；下一步為 commit、本機 ZIP 驗證、GitHub push 與實際 `main.zip` 回讀。
