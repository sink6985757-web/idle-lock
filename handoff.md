# Handoff

## 目前狀態

- 更新：2026-09-05，Codex；工作單 `WO-DRIVE-GITHUB-ALIGN-20260905-v2` 已確認。
- 保留 Code → Download ZIP 直接包含 dist/IdleLock.exe 的交付方式；加入 manual manifest，清除過期 checkpoint 未設定狀態。
- 驗證：Git root／remote identity、四檔與 manifest schema、相對連結及 diff whitespace 檢查；程式與 runtime 未變，不將歷史實機測試標為本輪重跑。
- GitHub：`sink6985757-web/idle-lock`，default branch `main`。本輪成果以本文件所在 commit 識別；完成非 force push 後，以 `git ls-remote origin refs/heads/main` 與 GitHub API 回讀核對。
- Checkpoint：`manual`；三個 authority immutable SHA 已寫入 `.agents/project-lifecycle.json`，不啟用 standing_scoped。

## 風險與保留

既有 EXE 為 19,318,987 bytes，SHA-256 3ACB74528887CCA4156B8CB62633BFFBAB8C882C0E91905EC878575E104CC9C0；本輪不重建、不啟動鎖定程式。原多螢幕／frozen runtime 測試為歷史證據，Authenticode NotSigned。只追蹤此單一 binary，其他設定、log 與 build 產物維持忽略。

既有測試與版本歷史查閱 CHANGELOG／Git；沒有本輪執行的裝置、安裝、部署或帳號驗證不得視為重新通過。

## 唯一續跑點

若下次替換 EXE，從最新 main 建置並跑 frozen runtime test，再更新 hash；本輪核對 GitHub Code ZIP 仍包含相同 EXE。

跨裝置接續先讀 manifest、AGENTS、本檔與 Git 狀態，fetch 並比較 default branch。GitHub SHA 回讀與 Drive 雲端回讀分別記錄；若任一未完成，保留該項 PARTIAL，不推論整體已同步。
