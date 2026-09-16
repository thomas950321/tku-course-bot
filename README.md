<div align="center">

# TKU_CourseBot

**基於 HTTP 協議與全自動驗證碼辨識的高效淡江大學自動搶課系統**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask: WebUI](https://img.shields.io/badge/Flask-WebUI-green.svg)](https://flask.palletsprojects.com/)

</div>

---

## 專案簡介

TKU_CourseBot 為淡江大學學生設計的高效自動搶課工具。不同於傳統使用 Selenium 或 Puppeteer 等擬真瀏覽器的慢速自動化方案，本專案採用全 HTTP 協議（Python requests）直接與淡江大學選課伺服器進行底層數據互動，具備高併發、極低延遲、無瀏覽器開銷等優勢。

系統內建微型 Web 控制台（Flask），提供可視化的帳密設定、加退選清單配置、預約定時搶課以及即時執行日誌追蹤功能。

---

## 解決痛點

1. **瀏覽器渲染與自動化開銷過大**：傳統 Selenium 工具因需加載完整的 HTML/CSS/JS 資源與頁面渲染，在搶課高峰期容易延遲過高或遭伺服器中斷。
2. **驗證碼人工輸入耗時**：選課系統登入包含動態驗證碼，人工輸入往往錯過最佳搶課時機。
3. **TLS/SSL 協議相容性問題**：淡江大學選課系統採用特定的 TLS 密碼套件限制，本專案針對 Python requests 進行底層 TLS Adapter 與標頭適配，確保連線穩定不中斷。

---

## 核心優勢

1. **全 HTTP 協議極速執行**：直接進行 ASP.NET ViewState 提取、驗證碼雜湊匹配與表單 Post 數據傳輸，回應速度大幅領先瀏覽器自動化方案。
2. **動態驗證碼自動破解**：內建淡江選課系統數字驗證碼雜湊比對機制，無須串接第三方付費 OCR 服務，達成 100% 自動化登入。
3. **安全配置與輕量 Web UI**：帳密資訊獨立使用 `.env` 檔案儲存並納入 Git 忽略清單，搭配視覺化 Web 控制台與全自動輪詢狀態追蹤。

---

## 運作原理

1. **Session 建立與 TLS 降級適配**：透過自訂 `CustomTLSAdapter` 設定 `DEFAULT:@SECLEVEL=1` 與 Chrome User-Agent，通過淡江選課伺服器 IIS 防火牆與加密協定檢驗。
2. **登入資訊解析與驗證碼破解**：自動請求登入頁面與 `/Handler1.ashx` 驗證碼數據，提取 `__VIEWSTATE`、`__VIEWSTATEGENERATOR` 與 `__EVENTVALIDATION`，並比對數字雜湊值生成驗證碼。
3. **搶課表單建構與執行**：帶入學號、密碼及驗證碼發送 `btnLogin` 請求，登入成功後向 `action.aspx` 發送課程加退選表單，並正則解析回應代碼（如 `I000` 成功、`E054` 名額已滿等）。

---

## 快速開始

### 1. 環境需求

- Python 3.10 或更高版本
- Git

### 2. 下載專案與安裝依賴

```bash
git clone https://github.com/YOUR_USERNAME/TKU_CourseBot.git
cd TKU_CourseBot
pip install flask requests beautifulsoup4 python-dotenv urllib3
```

### 3. 配置環境變數 (.env)

複製環境變數範本並填入您的學號與密碼：

```bash
cp .env.example .env
```

編輯 `.env` 檔案：

```env
TKU_ACCOUNT=your_student_id
TKU_PASSWORD=your_password
```

### 4. 啟動 Web 控制台

執行以下指令啟動控制台：

```bash
python web_app.py
```

開啟瀏覽器造訪 `http://localhost:5000` 即可進行視覺化操作與搶課。

---

## 專案結構

```text
TKU_CourseBot/
├── .env                # 帳號密碼環境變數設定檔（忽略版控）
├── .env.example        # 環境變數範本檔
├── .gitignore          # Git 忽略設定
├── LICENSE             # MIT 開源授權條款
├── README.md           # 專案說明文件
├── data/
│   └── courses.json    # 加退選課程代碼清單
├── templates/
│   └── index.html      # Web 控制台前端介面
└── web_app.py          # Flask Web 服務與搶課核心邏輯
```

---

## 授權條款

本專案採用 [MIT License](./LICENSE) 開源授權條款。

---

## 免責聲明與使用規範

本工具僅供學術研究、技術交流與個人自動化測試使用。使用者在操作本軟體時，應遵守淡江大學選課系統之服務條款與相關法律法規。作者不對因使用本軟體導致之選課結果或帳號異常承擔任何責任。
