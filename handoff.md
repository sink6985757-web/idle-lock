# Handoff

## 目前做到哪
已修正立即鎖定畫面在多螢幕／不同 DPI 環境的尺寸與位置偏移，並讓手動或自動鎖定前自動收起控制、設定及通知視窗。新版 EXE 已重建，使用者實際測試正常。

## 目前狀態
- 可執行：是
- 已驗證：`py_compile`、兩台螢幕實際 Tk 座標、原始碼 runtime test、凍結 EXE runtime test，以及使用者實機操作皆通過
- 未完成：尚未合併至 `main` 或建立版本發布

## 下一步
1. 開工後回讀本檔並確認 `agent/readme-documentation` 與 `main` 的差異。
2. 另行確認後再合併、標記版本或發布 EXE。

## 注意事項
- 新版執行檔位於 `dist/IdleLock.exe`，舊版備份位於 `dist/IdleLock-pre-display-fix-20260808.exe`；`dist/` 不納入 Git。
- 多螢幕負座標必須透過 Win32 `SetWindowPos` 定位；Tk 的負 geometry offset 不是絕對座標。

## 最近更新
- 時間：2026-08-08 19:16 +08:00
- 更新者：Codex
- 電腦：YULIN-SFG16-72
- 成果 commit：6b4f0fd69ee58270550686488a2328b079a0cebe
- Git push：VERIFIED
- Obsidian：NOT_CONFIGURED

## 2026-08-09 生命週期權威更新

- 上述多螢幕／DPI 修正與測試證據保留；Obsidian 不再屬於收工流程。
- 新增 CHANGELOG，更新 AGENTS／README；程式與安裝包未修改。
- GitHub：`LOCAL_ONLY`，尚未 commit／push。
- 唯一續跑點：驗證治理 diff 後進入 Delivery Gate。
