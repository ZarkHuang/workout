# ⚡ FitPulse (脈動健身) - 智慧健身訓練與營養追蹤 PWA 系統

> 一款專為重訓與體態管理打造的 **行動優先 PWA 智慧健身應用**。結合「Gemini AI 智能排課、肌肉修復熱力圖、漸進式超負荷追蹤、動態 TDEE 計算機、純文字 AI 飲食解析與 30 天自動滾動清理機制」。

---

## ✨ 核心特色與痛點解決方案

1. **🏋️ 今天不知道練什麼？（AI 智能今日排課）**
   - 視覺化 6 大肌群（胸、背、腿、肩、手、核心）修復熱力圖（已修復 🟢、修復中 🟡、疲勞中 🔴）。
   - 結合性別、體態目標與過去 72 小時訓練量，Gemini 一鍵生成今日推薦課表與熱身要領。
   - 支援「👉 一鍵採用並立即開練」。

2. **📊 進階與新手如何科學進步？（漸進式超負荷 ＋ 1RM 追蹤）**
   - 實時打卡模式，自動灰字顯示「上次重量與次數」，提示突破目標。
   - 內建組間休息倒數計時器（支援聲音與震動回饋）。
   - 自動推算單次最大重量 (1RM) 並繪製歷史成長曲線。

3. **🥗 純文字 AI 飲食解析 ＋ 30 天滾動歸檔（極致省空間、零爆庫風險）**
   - **完全不存圖片**，直接輸入文字（例：`好市多烤雞腿 1 隻 + 地瓜 150g + 無糖豆漿`），AI 秒級精算熱量與三大營養素 (P/C/F)。
   - 近 30 天保存明細，超過 30 天自動彙總為每日摘要，永久保留體態趨勢且資料庫佔用接近 0。

4. **🤖 即問即用 AI 隨身教練（無狀態、不落盤存 DB）**
   - 每次發問自動帶入個人體態、熱量缺口與肌肉修復狀態。
   - 聊天中推薦的菜單可直接點擊「一鍵帶入今日訓練」。

5. **👥 多用戶獨立使用**
   - 原生 JWT 密碼雜湊註冊登入，支援自己、女友、朋友各自獨立管理數據。

---

## 🛠️ 技術架構

- **前端**：Vue 3 (Composition API) + Vite PWA + Pinia + Tailwind CSS + Lucide Icons + Chart.js (部署於 **Vercel**)
- **後端**：FastAPI (Python 3.11+) + SQLAlchemy 2.0 + PyMySQL + PyJWT + Google GenAI SDK (部署於 **Render**)
- **資料庫**：TiDB Serverless (MySQL 8 相容雲端資料庫，免費 5GB 額度)
- **AI 模型**：Google Gemini API (`gemini-2.5-flash` / `gemini-3.1-lite`)

---

## 🚀 本地開發啟動步驟

### 1. 後端啟動 (FastAPI)

```bash
cd backend

# 1. 建立並啟動 Python 虛擬環境 (可選)
python -m venv venv
venv\Scripts\activate

# 2. 安裝依賴套件
pip install -r requirements.txt

# 3. 複製環境變數
cp .env.example .env
# 請編輯 .env 填入你的 GEMINI_API_KEY (可選填 TiDB DATABASE_URL，預設使用本地 SQLite)

# 4. 啟動後端伺服器 (預設在 http://localhost:8000)
uvicorn main:app --reload --port 8000
```

- API 文件 (Swagger UI): `http://localhost:8000/docs`

---

### 2. 前端啟動 (Vue 3 PWA)

```bash
cd frontend

# 1. 安裝前端依賴套件
npm install

# 2. 啟動 Vite 開發伺服器 (預設在 http://localhost:5173)
npm run dev
```

---

## ☁️ 免費雲端架站部署教學

### 🐬 1. TiDB Serverless (雲端資料庫)
1. 前往 [PingCAP TiDB Cloud](https://tidbcloud.com/) 免費註冊。
2. 建立一個免費的 **Serverless Cluster**。
3. 點擊 **Connect** -> 選擇 **SQLAlchemy** 或 **PyMySQL**，複製連線字串。
4. 將連線字串填入後端環境變數 `DATABASE_URL`。

### ⚡ 2. Render (後端 API 部署)
1. 將專案推送到你的 GitHub Repository。
2. 前往 [Render.com](https://render.com/) 免費註冊並點擊 **New Web Service**。
3. 連結你的 GitHub 專案，Root Directory 填寫 `backend`。
4. 設定環境變數 (Environment Variables)：
   - `DATABASE_URL`: 你的 TiDB 連線字串 (或留空使用 SQLite)
   - `SECRET_KEY`: 隨機安全字串
   - `GEMINI_API_KEY`: 你的 Google Gemini API Key
   - `GEMINI_MODEL`: `gemini-2.5-flash`
5. 點擊 **Deploy**，部署完成後取得後端 API 網址 (如 `https://fitpulse-api.onrender.com`)。

### 📱 3. Vercel (前端 PWA 部署)
1. 前往 [Vercel](https://vercel.com/) 登入。
2. 匯入同一個 GitHub 專案，Root Directory 選擇 `frontend`。
3. 設定環境變數：
   - `VITE_API_URL`: `https://your-backend-name.onrender.com/api`
4. 點擊 **Deploy**，即可獲得專屬 HTTPS 網址！
5. 在手機 Safari / Chrome 開啟該網址，點擊「加入主畫面」即可像原生 App 一樣全螢幕使用！
