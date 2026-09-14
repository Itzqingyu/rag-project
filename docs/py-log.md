# 後端 (Python) 模塊分析與架構變更紀錄

## 1. 模塊清單與功能簡述 (扁平化架構)

### 進入點與 API
- `main.py`: FastAPI 應用程式的主程式。提供完整的 REST API 端點，包含：
  - **系統與健康檢查**: `/ping`
  - **RAG 文件管理**: `/upload` (上傳 Markdown 並向量化), `/documents` (GET 清單, DELETE 刪除), `/query` (語意檢索與選填 LLM 回答)
  - **活動管理 (Activity)**: `/activities` (GET, POST), `/activities/{id}` (GET, PUT, DELETE)
  - **會議管理 (Meeting)**: `/meetings` (GET, POST), `/meetings/{id}` (GET, PUT, DELETE)
  - **待辦事項 (Task)**: `/tasks` (GET, POST), `/tasks/{id}` (GET, PUT, DELETE)
  - **決策紀錄 (Decision)**: `/decisions` (GET, POST), `/decisions/{id}` (GET, PUT, DELETE)
  - **流程日程 (Schedule)**: `/schedules` (GET, POST), `/schedules/{id}` (GET, PUT, DELETE)
  - **突發事件 (Incident)**: `/incidents` (GET, POST), `/incidents/{id}` (GET, PUT, DELETE)

- `tests/test_main.py`: 整合了原 `main_test.py` 與 `test_main.py` 的互動式 CLI 測試選單，支援 RAG 文件管理、LLM 回答測試以及 Activity／Meeting／Task 等業務功能的本地 CLI 測試。

### 業務與服務模組 (Domain Services)
- `activity.py`: 負責活動 (Activity) 後端業務邏輯與 SQLite CRUD 操作。
- `meeting_task.py`: 負責會議 (Meeting) 與待辦事項 (Task) 的 SQLite CRUD 與 Activity／Meeting 關聯驗證。
- `decision.py`: 負責決策 (Decision) CRUD、確認狀態、選項 JSON 與 Activity／Meeting 關聯驗證。
- `schedule.py`: 負責活動流程 (Schedule) CRUD、時間範圍與 Activity／Meeting 關聯驗證。
- `incident.py`: 負責臨時紀錄 (Incident) CRUD，並驗證可選 Schedule 與 Activity 的一致性。
- `activity_common.py`: 提供活動管理模組共用的正整數 ID、必填文字、ISO 8601 時間及跨模組關聯驗證工具。

### 核心引擎 (RAG Engine)
- `rag_engine.py`: 整合原 `chunker`, `embedding`, `reranker`, `retriever` 模組。
  - **split_markdown**: 讀取 Markdown 並以 `RecursiveCharacterTextSplitter` 切片 (預設 500 字，50 重疊)。
  - **get_embeddings / get_reranker**: 採用 Lazy Singletons 載入 Jina AI 模型 (`jina-embeddings-v2-base-zh` 與 `jina-reranker-v2-base-multilingual`)。
  - **add_document / search / delete_document / list_documents**: 協調文件向量化、ChromaDB 寫入與 SQLite 紀錄。

### 資料庫 (Database Layer)
- `database.py`: 統一資料庫存取層（結合原 `sqlite_db` 與 `chroma_db`）。
  - 提供共用 SQLite `get_connection`（自動啟用 `PRAGMA foreign_keys = ON`）與 `init_db` 表結構初始化。
  - 管理文件 Metadata 以及 Activity、Meeting、Task、Decision、Schedule、Incident 的 SQLite 資料表與索引。
  - 提供 `get_vectorstore()` 回傳 Chroma 向量資料庫單例。

### 語言模型 (LLM)
- `llm_client.py`: 負責與 LLM 互動。提供 `generate_answer` 函數，使用 `litellm` 將檢索到的文檔片段 (Context) 與使用者問題組合成 Prompt。透過 `.env` 中的 `ACTIVE_MODEL` 變數支援切換雲端模型 (OpenAI, Gemini, DeepSeek) 及本地 llama.cpp。

---

## 2. 模塊關係與資料流向

1. **文檔上傳與檢索流程 (Indexing & Retrieval)**:
   - 用戶上傳 Markdown 或發送 `/upload` API 請求。
   - `rag_engine.add_document` 調用 `database.py` 檢查與記錄檔名，並由 `database.get_vectorstore` 存入 ChromaDB。
   - 搜尋時調用 `rag_engine.search` 透過 ChromaDB 取回初步相似結果後，經 `get_reranker` 進行 Cross-Encoder 重新排序。

2. **活動與業務資料管理流程 (Activity Management)**:
   - `Activity` 為核心主體，其餘 `Meeting`, `Task`, `Decision`, `Schedule`, `Incident` 透過外鍵與其關聯。
   - 所有業務 CRUD 直接經由 `main.py` 的 RESTful API 端點暴露給前端或第三方呼叫。
   - 刪除 Activity 時若存有子紀錄會觸發 `ON DELETE RESTRICT` 保護歷史資料。

3. **回答生成流程 (LLM Generation)**:
   - 在 `/query` 端點若帶入 `generate_answer=True`，FastAPI 會呼叫 `llm_client.generate_answer`，將 RAG 檢索出的片段組合成 Prompt 丟給 `litellm` 產生回答。

---

## 3. 技術細節與變更紀錄
- **架構扁平化重構**: 消除 `rag_engine/`, `database/`, `llm/`, `activity/`, `decision/`, `incident/`, `schedule/` 資料夾，統一收納至 `rag_project/` 根目錄，大幅簡化引用層級。
- **FastAPI 完善**: 新增全套 CRUD REST API 覆蓋所有業務實體，並補上 Pydantic 驗證 Model。
- **測試合併**: 將 `main_test.py` 整合進 `tests/test_main.py`，保持單一 CLI 測試點。
