# idle-lock

## 目標

提供 Windows 閒置自動鎖定與手動鎖定工具，支援多螢幕、不同 DPI、系統匣常駐、全域解鎖快捷鍵與鎖定畫面幻燈片。

## 專案結構

- `README.md`：人類與 Agent／Tool 安裝、使用、版本與公開文案。
- `CHANGELOG.md`：每次收工的近期修改與 delivery 狀態。
- `handoff.md`：目前修正、驗證與唯一續跑點。

## 共用規則

1. 開工只讀本檔、`handoff.md` 與 Git 狀態。
2. 保留既有修改；不提交 secret、credential 或未知檔案。
3. canonical 路徑使用專案相對路徑。
4. 多螢幕與 DPI 修正必須用 runtime test 回讀；不可只以 Tk geometry 推測成功。
5. 每次收工更新 `CHANGELOG.md` 與 `handoff.md`；GitHub delivery 前更新 README。
6. commit、push、tag、release 與安裝包發布須由工作單／ReadyGate 放行。
7. 外部知識庫一律 `ON_DEMAND_ONLY`，不屬於 initial／startup／shutdown。

## 整合

- GitHub：private `sink6985757-web/idle-lock`
- 外部知識庫：`ON_DEMAND_ONLY`
