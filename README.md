# Idle Lock

## 2026-09-05 更新

保留 Code → Download ZIP 直接包含 dist/IdleLock.exe 的交付方式；加入 manual manifest，清除過期 checkpoint 未設定狀態。

## 開工與收工

1. 首次使用或治理缺件才執行 `initial`；既有專案平日直接 `startup`。
2. 開工讀取 [manifest](.agents/project-lifecycle.json)、[AGENTS.md](AGENTS.md)、[handoff.md](handoff.md)，確認 Git root 與 `origin`，fetch 後分別比較目前 upstream 和 default branch `main`。fetch 不會同步工作樹。
3. 在已確認範圍內修改與驗證。未提交內容、版本分叉與 unknown untracked 先保全、辨識，不直接覆蓋或整包 stage。
4. 收工更新 [CHANGELOG.md](CHANGELOG.md) 與 handoff；使用 `manual` checkpoint，沿用當次已確認工作單的 commit／push 授權。只有遠端 SHA 回讀一致才算 GitHub 同步完成；Drive 同步另行回讀。

固定 authority commit、專案 identity 與窄範圍文件 allowlist 見 manifest。一般開工不執行安裝、部署或外部帳號動作；既有 tag／Release、封存來源與私人設定依各自邊界維持。

Idle Lock 是一套 Windows 專用的閒置監控與畫面保護工具。程式會持續偵測鍵盤與滑鼠的閒置時間；達到設定門檻後，自動顯示全螢幕鎖定畫面並暫時阻擋輸入。使用者可透過固定快捷鍵解除鎖定，也能在鎖定期間切換回 Windows 桌面顯示，或播放指定資料夾中的圖片。

目前版本：**2.1.0**

> [!IMPORTANT]
> Idle Lock 是應用程式層級的輸入保護工具，不是 Windows 帳號驗證或安全性鎖定機制。它不會要求密碼，也不能取代 `Win + L`、Windows 登入畫面、磁碟加密或其他端點安全措施。

## 功能特色

- 自動偵測 Windows 系統閒置時間，到達門檻後鎖定。
- 可從控制面板或系統匣選單立即鎖定。
- 鎖定時在每一台螢幕建立置頂遮罩，支援多螢幕環境。
- 鎖定期間阻擋一般鍵盤與滑鼠輸入。
- 使用 `Ctrl + Alt + 0` 解鎖，支援主鍵盤與數字鍵盤的 `0`。
- 使用 `F1` 在鎖定畫面與目前 Windows 桌面之間切換；顯示桌面時仍維持輸入鎖定。
- 可遞迴讀取指定資料夾中的圖片，作為全螢幕幻燈片。
- 支援 JPG、JPEG、PNG、BMP、GIF、WebP、TIF 與 TIFF 圖片。
- 系統匣提供目前狀態、立即鎖定、暫停、繼續、重新啟動、設定、日誌與結束功能。
- 單一執行個體設計：再次啟動程式時，會喚醒既有程式的控制面板。
- 若解鎖快捷鍵註冊失敗，程式會停止自動鎖定，避免進入無法解除的狀態。
- 發生未處理錯誤時，優先解除輸入封鎖與關閉遮罩，再進入可復原狀態。
- 啟動時記錄執行檔版本、路徑與 SHA-256，方便追蹤實際執行版本。

## Windows 下載、解壓縮與 EXE 使用（先看這裡）

> [!IMPORTANT]
> 本專案已將驗證過的 `dist\IdleLock.exe` 直接包進 GitHub repository。即使 GitHub 按鈕顯示 **Source code (zip)**，下載並解壓整包後仍會包含可直接雙擊的 Windows EXE，不需要安裝 Python，也不需要自行建置。

Idle Lock 是 Windows portable app，不是 MSI 或 Setup 安裝精靈。建置完成的單一 `IdleLock.exe` 已包含 Python 程式與相依套件；目標 Windows 電腦不需要另外安裝 Python。

| 你的目的 | 應該下載／執行什麼 | 是否需要 Python |
| --- | --- | --- |
| 只想直接使用 EXE | 下載整包 ZIP，解壓後執行 `dist\IdleLock.exe` | 不需要 |
| 想自行重新建置 EXE | 下載整包 ZIP，依方案 B 建置 | 只有建置電腦需要 |
| 開發或除錯程式 | 解壓 Source code ZIP，執行 `idle_lock.py` | 需要 |

### 方案 A：下載整包後直接執行 EXE（推薦）

1. 在 GitHub 專案首頁按綠色 **Code** 按鈕，再選 **Download ZIP**；也可以直接下載 [完整 main ZIP](https://github.com/sink6985757-web/idle-lock/archive/refs/heads/main.zip)。
2. 對下載的 `idle-lock-main.zip` 按右鍵，選擇 **解壓縮全部**。
3. 打開解壓後的 `idle-lock-main\dist` 資料夾。
4. 雙擊 `IdleLock.exe`。這個 EXE 已包含 Python 程式與相依套件，目標電腦不需要安裝 Python。
5. 程式啟動後會出現在 Windows 系統匣；要完整結束，請在系統匣圖示上按右鍵，選擇「結束程式」。

目前整包內 `dist\IdleLock.exe` 的 SHA-256：

```text
3ACB74528887CCA4156B8CB62633BFFBAB8C882C0E91905EC878575E104CC9C0
```

可在解壓後的專案根目錄用 PowerShell 核對：

```powershell
Get-FileHash .\dist\IdleLock.exe -Algorithm SHA256
```

> [!CAUTION]
> 自行建置或尚未簽章的 EXE 可能觸發 Microsoft Defender SmartScreen。只執行你自行建置或從可信任專案頁面取得的檔案；不要為了執行未知 EXE 而關閉 Windows 安全性功能。

### 方案 B：下載 Source code ZIP 後自行建置 EXE

一般使用者不需要執行本方案。只有要修改程式或重新產生 EXE 時，建置電腦才需要 Windows、Python 3.10 以上版本與網路連線。

#### 1. 下載並真正解壓縮 Source code ZIP

1. 在 GitHub 專案首頁按綠色 **Code** 按鈕，再選 **Download ZIP**；也可以直接下載 [main Source code ZIP](https://github.com/sink6985757-web/idle-lock/archive/refs/heads/main.zip)。
2. 在 Windows 的「下載」資料夾找到 `idle-lock-main.zip`。
3. 對 ZIP 按右鍵，選擇 **解壓縮全部**。不要直接在 ZIP 預覽視窗裡執行 `.py` 檔案。
4. 打開解壓後的 `idle-lock-main` 資料夾；其中應該看得到 `dist\IdleLock.exe`、`idle_lock.py`、`IdleLock.spec` 與 `requirements.txt`。

若 Windows 檔案總管無法解壓，可在 PowerShell 使用：

```powershell
$zipPath = Join-Path $env:USERPROFILE 'Downloads\idle-lock-main.zip'
$extractPath = Join-Path $env:USERPROFILE 'Downloads\idle-lock-source'
Expand-Archive -LiteralPath $zipPath -DestinationPath $extractPath
Set-Location (Join-Path $extractPath 'idle-lock-main')
```

如果 `$extractPath` 已存在，請先改用另一個新的資料夾名稱，避免覆寫舊檔案。

#### 2. 確認 Python 並建立隔離環境

在解壓後的專案資料夾開啟 PowerShell，執行：

```powershell
py -3 --version
py -3 -m venv .venv
```

若系統顯示找不到 `py`，請先安裝 Windows 版 Python；若電腦只有 `python` 指令，可改用：

```powershell
python --version
python -m venv .venv
```

後續直接使用虛擬環境內的 Python，不需要執行 Activate，也不需要修改 PowerShell Execution Policy：

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install pyinstaller
```

#### 3. 建置單一 Windows EXE

確認 PowerShell 目前位於含有 `IdleLock.spec` 的專案根目錄，再執行：

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm IdleLock.spec
```

建置成功後，獨立執行檔位於：

```text
dist\IdleLock.exe
```

這個 `dist\IdleLock.exe` 才是可以複製到其他 Windows 電腦、直接雙擊且不需要 Python 的版本。`build\` 是建置暫存資料夾，不是要交付的程式。

#### 4. 執行建置完成的 EXE

```powershell
Test-Path .\dist\IdleLock.exe
.\dist\IdleLock.exe
```

第一行應顯示 `True`。第二行啟動後可能不會停留在 PowerShell 視窗，請到 Windows 系統匣查看 Idle Lock 圖示。

### 方案 C：只供開發者從 Python 原始碼執行

這種方式不會建立 EXE，而且目標電腦仍需要 Python：

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe idle_lock.py
```

### Windows 下載與建置常見問題

| 問題 | 原因與處理方式 |
| --- | --- |
| ZIP 裡只有 `.py`，沒有 EXE | 確認下載的是最新 `main.zip`，重新解壓後查看 `idle-lock-main\dist\IdleLock.exe`；舊 ZIP 不會自動更新 |
| ZIP 無法解壓 | 重新下載完整 ZIP，使用 Windows「解壓縮全部」或上方 `Expand-Archive`；不要在 ZIP 預覽中執行檔案 |
| 找不到 `py` 或 `python` | 尚未安裝 Python，或安裝程式未加入啟動器／PATH |
| `No module named pystray` | 尚未用 `.venv\Scripts\python.exe` 安裝 `requirements.txt` |
| `No module named PyInstaller` | 執行 `.\.venv\Scripts\python.exe -m pip install pyinstaller` |
| 建置後找不到 EXE | 確認指令沒有錯誤，並到專案根目錄的 `dist\IdleLock.exe` 查看 |
| 雙擊 EXE 沒有主視窗 | 程式可能已常駐系統匣；展開 Windows 隱藏圖示區查看 |

預設啟動行為：

- 啟動後立即進入監控狀態。
- 預設連續閒置 60 秒後鎖定。
- 啟動時開啟控制面板。
- 解鎖後顯示選擇視窗，可繼續監控、暫停監控或結束程式。

## 操作方式

| 操作 | 方法 | 說明 |
| --- | --- | --- |
| 開啟控制面板 | 雙擊系統匣圖示，或在選單中選擇「開啟控制面板」 | 查看狀態與常用功能 |
| 立即鎖定 | 控制面板或系統匣選擇「立即鎖定」 | 只有在正常監控中才能使用 |
| 自動鎖定 | 保持無鍵盤、滑鼠輸入直到超過門檻 | 預設為 60 秒 |
| 解除鎖定 | 按下 `Ctrl + Alt + 0` | 主鍵盤與 NumPad `0` 均可嘗試使用 |
| 切換鎖定顯示 | 鎖定時按 `F1` | 在 Windows 桌面與保護畫面／幻燈片之間切換；不會解除鎖定 |
| 暫停監控 | 控制面板或系統匣選擇「暫停監控」 | 暫停自動鎖定 |
| 繼續監控 | 選擇「繼續監控」 | 重新計算閒置時間，並套用恢復保護秒數 |
| 查看日誌 | 系統匣或控制面板選擇「查看日誌」 | 使用預設文字檢視器開啟日誌 |
| 結束程式 | 系統匣或控制面板選擇「結束程式」 | 解除輸入攔截、關閉遮罩並退出 |

## 系統匣狀態顏色

| 顏色 | 狀態 |
| --- | --- |
| 綠色 | 正常監控中 |
| 紅色 | 已鎖定 |
| 黃色 | 已暫停 |
| 灰色 | 快捷鍵衝突或程式錯誤 |

## 鎖定畫面與幻燈片

未啟用幻燈片時，鎖定後會在所有螢幕顯示閒置提示。啟用幻燈片後，程式會遞迴掃描指定資料夾及其子資料夾，依檔名排序播放支援的圖片，並裁切填滿每台螢幕。

設定方式：

1. 開啟控制面板。
2. 選擇「選擇幻燈片資料夾」，或進入「設定」。
3. 選擇包含圖片的資料夾。
4. 確認「鎖定後預設使用幻燈片」已勾選。
5. 設定圖片切換秒數並儲存。

若資料夾無法存取、沒有支援的圖片或圖片載入失敗，程式會自動退回一般閒置提示畫面。

## 設定項目

| 設定 | 預設值 | 可設定範圍 | 用途 |
| --- | ---: | ---: | --- |
| 閒置鎖定秒數 | 60 秒 | 10–86400 秒 | 無輸入多久後進入鎖定 |
| 檢查間隔 | 500 毫秒 | 250–2000 毫秒 | 重新檢查閒置時間的頻率 |
| 恢復保護秒數 | 3 秒 | 0–10 秒 | 啟動或恢復監控後的緩衝時間 |
| 幻燈片切換秒數 | 10 秒 | 3–300 秒 | 每張圖片顯示多久 |
| 幻燈片資料夾 | 未設定 | 現有資料夾 | 圖片來源位置 |
| 鎖定後使用幻燈片 | 關閉 | 開啟／關閉 | 決定預設鎖定顯示模式 |

設定會儲存在 `settings.json`：

- 從原始碼執行時：專案目錄下的 `settings.json`。
- 從 EXE 執行時：`IdleLock.exe` 所在目錄下的 `settings.json`。

執行日誌位於同一目錄下的 `logs/idle-lock.log`。這些執行期檔案已由 `.gitignore` 排除，不會提交到版本庫。

## 命令列參數

```text
python idle_lock.py [--threshold SECONDS] [--no-single-instance] [--runtime-test]
```

| 參數 | 用途 |
| --- | --- |
| `--threshold SECONDS` | 將閒置門檻限制在 10–86400 秒內，並寫入 `settings.json` |
| `--no-single-instance` | 關閉單一執行個體保護；主要供開發與測試使用 |
| `--runtime-test` | 執行真實 Tk、全域快捷鍵、輸入攔截與遮罩整合測試 |

> [!CAUTION]
> `--runtime-test` 會短暫建立鎖定畫面並操作全域快捷鍵，僅建議在本機互動測試時使用。一般使用者不需要執行此參數。

例如，將閒置門檻改為 5 分鐘：

```powershell
python idle_lock.py --threshold 300
```

## 建置 Windows EXE

GitHub repository 會直接追蹤一份通過 frozen runtime test 的可攜式 EXE；一般使用者下載整包即可使用。需要重新建置時，請依前面的方案 B 操作，輸出位置為：

```text
dist\IdleLock.exe
```

Git 只追蹤指定的 `dist/IdleLock.exe`。`build/`、其他 `dist/` 內容、`logs/`、`__pycache__/`、本機設定與舊 EXE 備份都不納入版本控制。

## 專案結構

```text
idle-lock/
├─ dist/
│  └─ IdleLock.exe    # GitHub 整包內可直接執行的 Windows 版本
├─ idle_lock.py       # 主程式、UI、Win32 輸入攔截與狀態管理
├─ IdleLock.spec      # PyInstaller 建置規格
├─ requirements.txt   # 執行階段 Python 依賴
├─ README.md          # 使用與開發說明
├─ .gitattributes     # 將 bundled EXE 標記為 binary
└─ .gitignore         # 排除建置與執行期檔案
```

## 版本控制與發布

專案採用語意化版本 `MAJOR.MINOR.PATCH`：

- `MAJOR`：不相容的行為或架構變更。
- `MINOR`：向下相容的新功能。
- `PATCH`：向下相容的修正與小幅改善。

目前程式版本定義於 `idle_lock.py` 的 `APP_VERSION`。準備新版本時，建議依序完成：

1. 更新 `APP_VERSION`。
2. 確認 `requirements.txt` 與 `IdleLock.spec` 仍符合實際依賴。
3. 執行語法檢查與互動整合測試。
4. 提交變更，建立對應的 `vX.Y.Z` Git 標籤。
5. 重新建置 EXE，確認版本與日誌資訊正確後再發布。

基本檢查：

```powershell
python -m py_compile idle_lock.py
python idle_lock.py --runtime-test
```

建立版本提交與標籤：

```powershell
git add idle_lock.py requirements.txt IdleLock.spec README.md
git commit -m "Release vX.Y.Z"
git tag -a vX.Y.Z -m "Idle Lock vX.Y.Z"
git push origin main --follow-tags
```

功能開發與修正建議先在獨立分支進行，例如 `feature/slideshow-controls` 或 `fix/hotkey-recovery`，完成檢查後再合併到 `main`。

## 疑難排解

### 顯示快捷鍵衝突或無法開始監控

`Ctrl + Alt + 0` 可能已被其他程式註冊。Idle Lock 會暫停自動鎖定以確保安全。請先關閉或修改衝突程式的快捷鍵，再從系統匣選擇「重新啟動監控」。

### 幻燈片沒有出現

確認資料夾存在、程式具備讀取權限，而且至少包含一張支援格式的圖片。若圖片清單為空，程式會顯示一般閒置提示。

### 關閉視窗後找不到程式

控制面板關閉後，程式仍會在 Windows 系統匣執行。請展開系統匣的隱藏圖示區尋找 Idle Lock。

### 程式發生錯誤

查看 `logs/idle-lock.log`。故障復原流程會先釋放輸入封鎖並關閉鎖定遮罩，可再從系統匣嘗試重新啟動監控或安全結束程式。

## 已知限制

- 僅支援 Windows。
- 解鎖方式固定為 `Ctrl + Alt + 0`，目前沒有密碼驗證或自訂快捷鍵介面。
- 程式不會自動設定「隨 Windows 開機啟動」。
- 這不是作業系統層級的安全鎖；需要安全離席時仍應使用 `Win + L`。

## Agent workflow 與版本紀錄

- GitHub canonical：`sink6985757-web/idle-lock`。
- 本 README 是人類與 Agent／Tool 的安裝、使用、版本與公開文案；近期變更見 [`CHANGELOG.md`](CHANGELOG.md)。
- 每次收工更新 CHANGELOG 與 handoff；GitHub delivery 前更新本 README。
- 外部知識庫為 `ON_DEMAND_ONLY`，不屬於 initial／startup／shutdown。
