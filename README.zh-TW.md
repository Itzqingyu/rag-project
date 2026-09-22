# DASH (Decision, Activity, Schedule, History)

> **活動管理與知識庫決策輔助系統**  
> 整合活動籌備看板、LLM 文件檢索問答（RAG），以及會議紀錄結構化提煉與資料庫儲存功能。

[English](README.md) | [繁體中文](README.zh-TW.md)

---

## 核心功能介紹 (User Guide)

DASH 包含三大功能模組，協助團隊管理活動歷程、會議內容與相關文件紀錄。

### 核心功能架構

- **1. 活動管理控制面板**：活動總覽、籌備進度、歷次會議、待辦事項、決策紀錄、流程日程與突發事件。
- **2. AI 對話與知識檢索 (RAG)**：雙模式對話（普通聊天 / 知識庫檢索）、切片來源溯源、歷史上下文隔離、多格式文件集中託管。
- **3. AI 結構化會議紀錄整理 (Preview & Commit)**：全文結構化提煉、介面即時微調編輯、確認後寫入資料庫並與活動看板聯動。

---

### 1. 活動、會議、決策、事件與待辦事項控制面板

提供活動籌辦週期的資料管理介面，整合各階段的資訊與紀錄：

- **活動總覽與進度追蹤 (Overview)**：
  - 顯示活動準備完成度與階段狀態（建立活動 -> 準備中 -> 活動執行 -> 成果檢討）。
  - 統整基本資訊（日期、地點、總召負責人、預算與預計人數）與下一步行動。
- **籌備會議管理 (Meetings)**：
  - 記錄歷次籌備會議的時間、地點、出席人員與討論內容。
  - 支援與上傳之來源文件（`source_document_id`）關聯，供檢視原始會議檔案。
- **關鍵決策紀錄 (Decisions)**：
  - 記錄「討論議題（Problem）」、「討論解方（Options）」、「最終決策（Final Decision）」與「考量理由（Reason）」。
  - 支援標記確認狀態（待確認 / 已確認）與資料來源出處。
- **行動待辦清單 (Tasks)**：
  - 支援按狀態分類（全部 / 未完成 / 已完成），並標記優先級（高 / 中 / 低）。
  - 待辦事項可設定負責人、預計完成期限，並關聯所屬活動與會議。
- **日程規劃與突發事件 (Schedule & Incidents)**：
  - 流程時間表規劃（負責人、類別、備註），以及活動執行期間的突發狀況與處置建議紀錄。

---

### 2. LLM + RAG 歷史紀錄與知識庫檢索

提供基於已上傳文件的檢索與問答介面：

- **文件轉換與集中託管**：
  - 支援上傳 `.md`、`.txt`、`.pdf`、`.docx` 格式文件。
  - 系統自動解析並轉碼為 Markdown 文本集中保存，上傳完成後與原始本機檔案獨立。
- **向量化檢索**：
  - 文件由系統進行語意切塊（Chunking），並透過 Embedding 模型產生特徵向量，儲存於 Chroma 向量資料庫。
- **雙對話模式**：
  - **知識庫問答模式 (`RAG`)**：針對使用者的提問檢索相關文件切片，並將切片文字注入 Context 供 LLM 彙整回答，同時提供「參考來源」折疊卡片供查驗。
  - **普通對話模式 (`Chat`)**：不經由文件庫檢索，由 LLM 基於上下文脈絡直接回答。
- **上下文隔離機制 (Clean Context Isolation)**：
  - 對話資料庫僅儲存使用者提問與模型回覆，檢索切片獨立留存於元資料中。
  - 多輪對話時不重複疊加過往檢索片段，避免上下文長度過長。
- **二次確認保護**：
  - 刪除對話會話或移除知識庫檔案時，彈出確認視窗，避免誤刪資料。

---

### 3. AI 會議紀錄結構化整理與看板聯動 (Preview & Commit)

提供會議紀錄文字的結構化萃取與資料庫儲存流程：

- **文件結構化提煉**：
  - 自已上傳的文件清單中選取會議紀錄文本。
  - 透過 System Prompt 引導 LLM 解析全文，提煉出「會議摘要」、「關鍵決策」與「行動待辦事項」。
- **預覽與確認機制 (Preview-Commit)**：
  1. **預覽階段 (Preview)**：提煉結果以表格形式呈現在介面上供檢視。
  2. **欄位編輯**：使用者可直接在介面上修改會議名稱、時間、地點，或編輯決策與待辦項目。
  3. **寫入資料庫 (Commit)**：確認後點擊「確認寫入資料庫」，資料寫入 SQLite 並反映於活動管理控制面板中。

---

## 技術架構與開發指南 (Developer Guide)

### 系統分層架構

- **前端桌面層 (Desktop Client)**
  - **核心技術**：React 19 + TypeScript + Vite + Electron Forge。
  - **模組規範**：組件獨立 CSS 樣式、嚴格繼承 Design Tokens（`:root`），全域禁止 Emoji。
  - **服務通訊**：`apiClient` 統一封裝 HTTP REST 請求並集中處理錯誤與斷線攔截。
- **後端服務層 (Python / FastAPI)**
  - **通訊介面**：本地 HTTP RESTful API（預設監聽 `http://127.0.0.1:8000`）。
  - **主程式入口**：`python/src/rag_project/main.py`。
  - **核心模組劃分**：
    - `activity_services/`：負責 Activity、Meeting、Task、Decision、Schedule、Incident 之 SQLite 業務 CRUD。
    - `document_processing/`：負責文件格式轉換（`converter`）與 Markdown 語意切塊向量化（`rag_engine`）。
    - `llm_service`：透過 LiteLLM 串接大語言模型，並由 `prompts/` 載入 System Prompt 進行結構化提煉。
- **本地儲存層 (Local Data Storage: `python/data/`)**
  - **SQLite 資料庫 (`rag_database.sqlite`)**：儲存文件元資料、對話會話（Sessions）、訊息紀錄（Chat Messages）以及活動業務表。
  - **ChromaDB 向量資料庫 (`chroma_db/`)**：持久化儲存切片文字與特徵向量，供 RAG 語意搜尋。
  - **託管 Markdown 庫 (`markdown/`)**：集中存放轉碼後的標準 Markdown 原始文本。

### 技術選型

| 領域 | 技術棧 / 套件 | 說明 |
| :--- | :--- | :--- |
| **前端應用** | React , TypeScript, Electron, Vite | 跨平台桌面應用程式架構 |
| **圖標與視覺** | Lucide React | 統一圖示系統（全域禁止 Emoji） |
| **Markdown 渲染** | react-markdown | 支援對話訊息排版與清單階層渲染 |
| **後端框架** | Python 3.10+, FastAPI, Uvicorn | 非同步 RESTful API 服務 |
| **套件管理** | uv | Python 套件與依賴管理工具 |
| **RAG 與檢索** | LangChain, FastEmbed, ChromaDB | 提供切塊、向量化與語意檢索功能，支援 CPU 運算 |
| **LLM 呼叫** | LiteLLM | 提供大語言模型統一呼叫介面 |
| **文件轉換** | PyPDF, python-docx, markdown | 解析常見格式並轉換為 Markdown 文本 |
| **資料庫** | SQLite3, ChromaDB Persistent | 本地關聯式資料庫與向量資料庫儲存 |

---

### 本地環境安裝與部署

#### 1. 前置需求
- **Node.js**: v18+ 與 npm
- **Python**: 3.10+ (建議安裝 [uv](https://github.com/astral-sh/uv))
- **LLM API Key (.env)**: 所使用模型服務之 API 金鑰

#### 2. 環境變數設定
在 `python/` 目錄或專案根目錄下建立 `.env` 檔案：
```env
# 依使用之模型服務設定對應的 API 金鑰與模型名稱 (依 LiteLLM 格式)
API_KEY=your_api_key_here
MODEL_NAME=your_model_name_here
```

#### 3. 後端安裝與啟動

優先使用 `uv` 進行依賴同步與執行：

```powershell
# 進入後端目錄
cd python

# 安裝依賴環境
uv sync

# 啟動 FastAPI 後端伺服器 (預設運行於 http://127.0.0.1:8000)
uv run python src/rag_project/main.py
```
> 後端服務啟動後，可於瀏覽器造訪 `http://127.0.0.1:8000/docs` 查看 Swagger 介面測試所有 API。

#### 4. 前端安裝與啟動

另開一個終端機視窗，進入 `react/` 目錄：

```powershell
# 進入前端目錄
cd react

# 安裝 Node 套件
npm install

# 執行測試確認程式碼正確性
npm run test

# 啟動 Electron 開發環境
npm run start
```

---

### 測試規範與目錄約定

- **Python 後端測試**：
  - 測試腳本一律集中於 `python/tests/`。
  - `python/tests/test_main.py`：提供全互動式 CLI 工具，支援端對端測試文件轉換、活動建立、會議提煉與寫入、多輪對話驗證。
- **React 前端測試**：
  - 單元與服務整合測試位於 `react/tests/`，使用 Vitest 執行：`npm run test`。
- **代碼與命名風格**：
  - 檔案與資料夾：一律英文小寫，連接符號使用 `-`（代碼腳本除外，遵從各語言慣例）。
  - CSS 規範：配色統一繼承自 `index.css` 的 `:root` 變數；落實「一個 Component 一個 CSS」。
  - 圖示規範：全域禁止使用 Emoji，圖標一律使用 `lucide-react`。

---

## 授權條款 (License)

本專案採用 [MIT License](LICENSE) 授權開源。
