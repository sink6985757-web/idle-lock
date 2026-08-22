# Handoff

## 目前做到哪
GitHub `main` 已直接追蹤驗證版 `dist\IdleLock.exe`；使用者下載並解壓 Code ZIP 後即可直接雙擊，不需要 Python。README、忽略規則、binary 屬性與專案治理已同步完成。

## 目前狀態
- 可執行：是
- 已驗證：原始碼 `py_compile`、兩台螢幕 runtime test、新建 frozen EXE runtime 六項結果、input hook cleanup、本機 Git ZIP，以及實際 GitHub `main.zip` 下載／解壓均通過
- Bundled EXE：19,318,987 bytes；SHA-256 `3ACB74528887CCA4156B8CB62633BFFBAB8C882C0E91905EC878575E104CC9C0`
- GitHub：`VERIFIED`，bundled commit `3a94b7487054e44c19f610198e3d51ddbb3fba62` 已推送 `main` 並完成 remote ref 與 ZIP 內容回讀
- 未完成：本次要求無；未建立 tag／GitHub Release，EXE 尚未數位簽章

## 下一步
1. 下次若要替換 bundled EXE，先從最新 `main` 建置，重跑 frozen runtime test並更新 README SHA-256。
2. push 後重新下載 GitHub `main.zip`，確認 `dist\IdleLock.exe` 是唯一 packaged binary 且 hash 一致。
3. 若要建立 tag、GitHub Release 或程式碼簽章，另走 ReadyGate。

## 注意事項
- Git 只追蹤 `dist/IdleLock.exe`；`dist/IdleLock-pre-bundled-20260822.exe`、`dist/IdleLock-pre-display-fix-20260808.exe`、settings、log 與其他 build 輸出維持忽略。
- Bundled EXE 的 Authenticode 狀態為 `NotSigned`，Windows 可能顯示 SmartScreen；README 已揭露且不應關閉安全防護。
- 多螢幕負座標必須透過 Win32 `SetWindowPos` 定位；Tk 的負 geometry offset 不是絕對座標。

## 最近更新
- 時間：2026-08-22 22:12 +08:00
- 更新者：Codex
- 電腦：YULIN-SFG16-72
- 成果 commit：3a94b7487054e44c19f610198e3d51ddbb3fba62
- GitHub：VERIFIED `main`／實際 `main.zip`
- Checkpoint policy：NOT_CONFIGURED；本輪依確認工作單 `RG-IDLELOCK-BUNDLE-EXE-20260822-v1` 交付
- 外部知識庫：ON_DEMAND_ONLY
