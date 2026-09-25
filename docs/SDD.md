# SDD: DASH (Decision, Activity, Schedule, History)

## 1. 專案概述
DASH 是一套結合活動與決策管理、LLM + RAG 歷史檢索問答，以及 AI 結構化會議紀錄整理（Preview & Commit）的現代化智能工作台。使用者可上傳多格式會議紀錄進行問答與提煉，並與活動控制面板聯動。

## 2. 技術選型

### 前端
- **框架**: React + TypeScript
- **打包**: Electron (跨平台桌面應用)
- **通訊**:
  - 前端與主進程: Electron IPC + JSON
  - 主進程與 Python 後端: HTTP API (RESTful)
- **前端實用套件**: react-markdown (對話渲染), lucide-react (圖示庫)

### 後端
- **語言**: Python 3.10+
- **套件管理**: uv
- **套件清單**
    - **Web 框架**: FastAPI + uvicorn (提供本地 API 供 Electron 呼叫)
    - **打包工具**: PyInstaller (編譯為獨立執行檔，無須使用者安裝 Python)
    - **環境變數管理**: python-dotenv (管理雲端模型 API Key 等機密資訊)
    - **RAG 套件**: LangChain (流程编排)
    - **向量化**: fastembed (輕量級、無須 PyTorch 的 ONNX 推理引擎)
    - **LLM API**: litellm (統一接口，支援 OpenAI/Claude)

### 資料庫與檔案儲存
- **純文字 / 託管文件**: 系統統一轉碼為 `.md` (Markdown 格式) 並儲存於 `python/data/markdown/` 目錄
- **原始文件**: 上傳轉換完成後與系統獨立 (使用者刪除或修改原始 PDF/Word 不影響系統內 Markdown)
- **切片文字**: Markdown 切片由 `rag_engine.py` 處理
- **向量數據**: ChromaDB persistent mode 儲存於 `python/data/chroma_db/`
- **對話歷史與元資料**: SQLite 儲存於 `python/data/rag_database.sqlite`
- **檔案與活動管理**: SQLite (追蹤已導入的 Markdown 文件，以及 Activity、Meeting、Task、Decision、Schedule、Incident 等業務資料)

### 模型
- **Embedding**: fastembed（使用 ONNX Runtime 於 CPU 運行之 Embedding 模型）
- **LLM**: 透過 `litellm` 統一介面呼叫雲端或本地相容模型

## 3. 專案結構
```
rag-project/
├── react/                        # Electron + Vite + React 前端
│   ├── src/
│   │   ├── App.tsx               # 頂層主畫面與導航路由 (活動工作台 vs AI 對話)
│   │   ├── api/                  # 後端 API 通訊服務層 (camelCase 命名)
│   │   │   ├── apiTypes.ts       # 後端資料結構與 TypeScript 介面定義
│   │   │   ├── apiClient.ts      # HTTP 請求封裝、錯誤攔截與後端斷線處理
│   │   │   ├── chatService.ts    # 對話會話增刪查改與雙模式訊息發送
│   │   │   ├── documentService.ts # 知識庫文件清單、上傳轉檔向量化與刪除
│   │   │   └── meetingExtractService.ts # AI 會議紀錄結構化抽取 (1-shot) 與 Preview-Commit 寫入
│   │   ├── components/           # 組件與同名獨立樣式 (.tsx & .css)
│   │   │   ├── ChatPanel.tsx     # LLM 聊天大面板主組件 (雙欄佈局、模式切換、即時 API 串接與真實錯誤反饋)
│   │   │   ├── MeetingExtractPanel.tsx # AI 會議紀錄整理面板 (Preview-Commit 雙階段工作流，提取會議、決策與待辦)
│   │   │   ├── SessionSidebar.tsx # 對話會話側邊欄 (新對話、切換、刪除)
│   │   │   ├── DocumentDrawer.tsx # 知識庫文檔抽屜 (文件清單、真實上傳與刪除)
│   │   │   ├── MeetingPanel.tsx  # 會議管理面板
│   │   │   └── ...               # 其餘活動管理面板 (Overview, Tasks, Decisions 等各自獨立 CSS)
│   │   └── index.css             # 全域 Design Tokens (:root)、Reset 與 App Shell 樣式
│
├── python/                       # Python 後端 (FastAPI)
│   ├── src/
│   │   └── dash_backend/
│   │       ├── main.py           # FastAPI 伺服器入口 (REST API, 包含 Preview/Commit 預覽寫入端點)
│   │       ├── database.py       # 統一資料庫層 (SQLite 連線池、Schema、Sessions/Messages 與 ChromaDB 向量庫)
│   │       ├── prompts/          # System Prompt Markdown 檔案目錄
│   │       │   ├── meeting_extraction.md # 會議紀錄 1-shot 結構化抽取 Prompt
│   │       │   ├── rag_qa.md             # RAG 通用問答 Prompt
│   │       │   └── chat_general.md       # 普通對話模式 AI 助手 Prompt
│   │       ├── activity_services/# 活動與事項管理微服務套件
│   │       │   ├── activity_common.py # 共用驗證與時間工具
│   │       │   ├── activity.py       # Activity 活動管理 CRUD
│   │       │   ├── meeting_task.py   # Meeting 會議與 Task 待辦事項 CRUD
│   │       │   ├── decision.py       # Decision 決策紀錄 CRUD
│   │       │   ├── schedule.py       # Schedule 流程日程 CRUD
│   │       │   └── incident.py       # Incident 突發事件 CRUD
│   │       ├── ai_services/          # AI 與 RAG 核心服務套件
│   │       │   ├── rag_engine.py     # RAG 核心引擎 (Markdown 切塊, Embedding, Reranker, 語意檢索)
│   │       │   └── llm_service.py    # LLM 統一呼叫與對話介面 (Clean Context Isolation 與結構化提煉)
│   │       └── document_processing/  # 文件格式解析與轉換套件
│   │           └── converter.py      # 多格式文件轉換模組 (MD, TXT, PDF, DOCX -> python/data/markdown/)
│   ├── tests/                    # 測試指令碼與單元測試
│   │   ├── test_main.py          # 整合 CLI 互動測試工具 (含 Session 多輪對話與模式切換測試)
│   │   ├── test_converter.py     # 多格式文件轉換與複製單元測試
│   │   └── test_chat_session.py  # 對話會話、記憶防污染與模式切換單元測試
│   ├── data/                     # 本地 SQLite, Chroma 向量庫與託管 Markdown 目錄
│   │   ├── dash_database.sqlite  # SQLite 資料庫 (含 documents, sessions, chat_messages 及活動業務表)
│   │   ├── chroma_db/            # ChromaDB 向量資料庫
│   │   └── markdown/             # 託管之 Markdown 格式文本庫
│   └── pyproject.toml            # 依賴套件配置
```

## 4. 核心流程

### 文件上傳與轉碼
1. 使用者上傳原始檔案 (MD, TXT, PDF, DOCX)
2. Electron IPC 傳遞路徑給主進程，呼叫 Python REST API (`/upload`)
3. Python `converter.py`: 讀取原始檔案 → 轉換/複製為標準 Markdown 格式並儲存於 `python/data/markdown/`
4. Python `rag_engine.py`: 讀取轉碼後 Markdown → 切片 → 向量化 → ChromaDB 儲存
5. Python `database.py`: 記錄檔案 Metadata 到 SQLite (檔名、託管路徑、處理時間、狀態)

### AI 結構化提取與預覽寫入 (Preview-Commit 流程)
1. 使用者選擇已導入之 Markdown 文件，發起 `/extract_summary` 請求
2. `llm_service.py` 載入 `prompts/meeting_extraction.md`，將 SQLite 託管之完整 Markdown 文字 1-shot 餵給 LLM 進行結構化解析
3. LLM 回傳 JSON (包含 `meeting`, `decisions`, `tasks`)
4. 前端展示預覽結果供使用者校對修改
5. 使用者確認後發起 `/commit_summary` 請求，依序寫入 SQLite `meetings`, `decisions`, `tasks` 表；目前各筆資料各自提交，中途失敗時可能只完成部分寫入

### 對話互動與會話記憶 (Session & Multi-turn Chat)
1. 使用者可透過 `/sessions` 端點建立或管理對話會話。
2. 發送訊息至 `/sessions/{id}/messages`，可自由指定當輪模式：
   - **普通聊天模式 (`mode='chat'`)**：無需經過 RAG 預處理，LLM 基於歷史對話脈絡與使用者問題直接自然回答。
   - **知識庫檢索模式 (`mode='rag'`)**：ChromaDB 檢索相關切片並由 Reranker 重排序，將文本片段注入當前 Prompt 提供總結回答。
3. **乾淨上下文隔離 (Clean Context Isolation)**：
   - SQLite `chat_messages` 僅保存純粹的「使用者問題」與「AI 回答」，當輪檢索到的參考切片以 JSON 儲存於 `retrieved_chunks` 欄位供前端回溯。
   - 歷史對話傳入 LLM 時，不疊加過往龐大的檢索內容，徹底杜絕同一個 Session 中多次 RAG 或切換模式造成的記憶污染。

## 5. 開發步驟

```bash
# 環境設置 (前端)
npm install
npm install react-markdown lucide-react

# 環境設置 (後端)
uv init
uv add langchain langchain-chroma langchain-community fastembed litellm chromadb fastapi uvicorn pyinstaller python-dotenv pypdf python-docx

# 開發
# 需要同時啟動前端與後端 (可透過 npm script 如 concurrently 整合)
uv run python/src/dash_backend/main.py          # 啟動 FastAPI 後端
npm run dev                                      # 啟動 Electron 前端
```

### 活動管理後端
- Activity 是所有活動資料的根節點；其他模組均以 `activity_id` 關聯。
- Activity 存在任何子資料時禁止刪除，避免連帶遺失歷史脈絡。
- Meeting 可用 nullable `source_document_id` 指向產生它的 Markdown 文件；文件刪除時 Meeting 保留並將此欄位設為 `NULL`，Task／Decision 可再透過 `meeting_id` 追溯來源。
- Meeting 刪除後，Task／Decision／Schedule 保留並將 `meeting_id` 設為 `NULL`。
- Incident 可選擇關聯 Schedule；Schedule 刪除後 Incident 保留並解除關聯。
- Activity Management service 只接收文字或結構化內容；檔案讀取與 Markdown 轉換由 `converter.py` 處理。
- CLI 測試工具會先選擇 Activity，再於該 Activity 範圍內操作 Meeting／Task／Decision／Schedule／Incident，以降低使用全域 ID 誤操作其他活動資料的風險。

## 6. MVP 範圍
- ✅ 文件上傳與轉換 (支援 MD, TXT, PDF, DOCX 格式)
- ✅ 對話互動 (基於已導入之 Markdown 檔案並由 RAG + Reranker 檢索)
- ✅ 文件管理 (查看、刪除已導入之 Markdown 文件，同步物理刪除託管 `.md` 與向量庫)
- ✅ AI 結構化會議分析 (1-shot 摘要抽取與 Preview-Commit 寫入流程)
- ✅ 活動管理 Python／SQLite 核心 CRUD 與關聯驗證
- ✅ 前端 LLM 聊天大面板 UI 框架 (雙欄佈局、會話管理側欄、模式切換 Toggle Pill、極簡空狀態、知識庫文檔抽屜)
- ✅ 前後端 API 串接與端對端整合 (完整接入 Session、Message 雙模式、Document 上傳與向量化，全面剔除模擬假資料並建立嚴格錯誤反饋機制)
- ✅ 前端「AI 功能」側欄下拉折疊導航與 AI 會議紀錄整理面板 (接入 /extract_summary 與 /commit_summary，實現 1-shot 萃取、即時預覽與活動資料庫寫入)
- ⏳ Electron 打包與自動化端對端啟動流程整合 (進行中)
- ❌ 高級權限與團隊協作 (後續)
- ❌ 版本控制與複雜自訂設定 (後續)

## 7. 備選方案：Web 服務
- 前端：React
- 後端：Node.js/Python + API
- 資料庫：PostgreSQL + Pinecone/Qdrant
- 適用：多用戶、團隊協作、跨設備

## 8. 總結
- 初版：本地桌面應用，核心功能：文件轉碼導入→AI 結構化提取與寫入→RAG 對話→活動紀錄管理
- 關鍵設計：以 Markdown 為核心，Python 端以 FastAPI 提供微服務，並透過 PyInstaller 打包
- 技術：React + Python + uv + FastAPI + LangChain + fastembed + litellm + python-dotenv + pypdf + python-docx
- 資料庫：ChromaDB persistent mode + SQLite + 託管 Markdown 檔案庫 (均儲存於 `python/data/`)

