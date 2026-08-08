# idle-lock

## 目標
提供 Windows 閒置自動鎖定與手動鎖定工具，支援多螢幕、不同 DPI
縮放、系統匣常駐、全域解鎖快捷鍵與鎖定畫面幻燈片。

## 路線圖
- [x] 確定專案具體目標與階段任務
- [x] 修正多螢幕鎖定畫面定位與自動鎖定視窗收合
- [ ] 合併目前修正並規劃下一個版本發布

## 專案結構
- `AGENTS.md`：專案 Agent 共用設定
- `handoff.md`：交接紀錄

## 共用規則
1. 每個 Agent 開工先讀本檔與 `handoff.md`。
2. 保留既有修改；不提交 secret、credential 或未知檔案。
3. 所有 canonical 路徑使用專案相對路徑。
4. 開工只讀；收工才更新交接、GitHub 與 Obsidian。
