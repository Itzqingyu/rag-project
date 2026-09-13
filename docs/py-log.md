# 後端 (Python) 模塊分析與架構變更紀錄

## 1. 模塊清單與功能簡述 (扁平化架構)

### 進入點與 API
- `main.py`: FastAPI 應用程式的主程式。提供完整的 REST API 端點，包含：
  - **系統與健康檢查**: `/ping`
  - **RAG 文件管理與上傳轉碼**: `/upload` (上傳 MD, TXT, PDF, DOCX 並自動轉換儲存與向量化), `/documents` (GET 清單, DELETE 物理刪除包含 `.md` 與向量庫), `/query` (語意檢索與選填 LLM 回答)
  - **AI 結構化提取與預覽寫入**: `/extract_summary` (發起 1-shot LLM 解析 SQLite 託管之完整 Markdown 文字並回傳預覽 JSON), `/commit_summary` (將前端校對後的結構化資料原子化寫入 SQLite)
  - **活動管理 (Activity)**: `/activities` (GET, POST), `/activities/{id}` (GET, PUT, DELETE)
  - **會議管理 (Meeting)**: `/meetings` (GET, POST), `/meetings/{id}` (GET, PUT, DELETE)
  - **待辦事項 (Task)**: `/tasks` (GET, POST), `/tasks/{id}` (GET, PUT, DELETE)
  - **決策紀錄 (Decision)**: `/decisions` (GET, POST), `/decisions/{id}` (GET, PUT, DELETE)
  - **流程日程 (Schedule)**: `/schedules` (GET, POST), `/schedules/{id}` (GET, PUT, DELETE)
  - **突發事件 (Incident)**: `/incidents` (GET, POST), `/incidents/{id}` (GET, PUT, DELETE)

- `tests/test_main.py`: 整合了原 `main_test.py` 與 `test_main.py` 的互動式 CLI 測試選單，支援 RAG 文件管理、LLM 回答測試，以及 Activity／Meeting／Task／Decision／Schedule／Incident 的本地 CRUD 操作；Decision／Schedule／Incident 會依 Activity 篩選，並在修改時支援保留或清除可選關聯欄位。
- `tests/test_converter.py`: 文件轉換器單元測試，驗證 MD 複製、TXT 轉碼、PDF 解析與 DOCX 提取功能。

### 業務與服務模組 (Domain Services)
- `converter.py`: 負責文件格式轉碼。支援 `.md`, `.txt`, `.pdf`, `.docx` 格式，自動建立並輸出至 `python/data/markdown/` 目錄。若為 MD 檔案則直接複製，其餘格式提取內文後包裝為標準 Markdown。
- `activity.py`: 負責活動 (Activity) 後端業務邏輯與 SQLite CRUD 操作。
- `meeting_task.py`: 負責會議 (Meeting) 與待辦事項 (Task) 的 SQLite CRUD 與 Activity／Meeting 關聯驗證。
- `decision.py`: 負責決策 (Decision) CRUD、確認狀態、選項 JSON 與 Activity／Meeting 關聯驗證。
- `schedule.py`: 負責活動流程 (Schedule) CRUD、時間範圍與 Activity／Meeting 關聯驗證。
- `incident.py`: 負責臨時紀錄 (Incident) CRUD，並驗證可選 Schedule 與 Activity 的一致性。
- `activity_common.py`: 提供活動管理模組共用的正整數 ID、必填文字、ISO 8601 時間及跨模組關聯驗證工具。

### Prompt 範本庫 (Prompt Templates)
- `prompts/meeting_extraction.md`: 定義 AI 會議紀錄 1-shot 結構化抽取的 System Prompt 範本（規範會議日期、討論問題、解決方案、最終決策與待辦事項 JSON 格式）。
- `prompts/rag_qa.md`: 定義 RAG 通用問答的 System Prompt 範本。

### 核心引擎 (RAG Engine)
- `rag_engine.py`: 整合原 `chunker`, `embedding`, `reranker`, `retriever` 模組。
  - **split_markdown**: 讀取 Markdown 並以 `RecursiveCharacterTextSplitter` 切片 (預設 500 字，50 重疊)。
  - **get_embeddings / get_reranker**: 採用 Lazy Singletons 載入 Jina AI 模型 (`jina-embeddings-v2-base-zh` 與 `jina-reranker-v2-base-multilingual`)。
  - **add_document / search / delete_document / list_documents**: 協調文件向量化、ChromaDB 寫入、物理 `.md` 檔案清理與 SQLite 紀錄。

### 資料庫 (Database Layer)
- `database.py`: 統一資料庫存取層（結合原 `sqlite_db` 與 `chroma_db`）。
  - 提供共用 SQLite `get_connection`（自動啟用 `PRAGMA foreign_keys = ON`）與 `init_db` 表結構初始化（資料庫檔位在 `python/data/rag_database.sqlite`）。
  - 管理文件 Metadata (包含 `markdown_path` 與 `markdown_content`) 以及 Activity、Meeting、Task、Decision、Schedule、Incident 的 SQLite 資料表與索引。
  - 提供 `get_vectorstore()` 回傳 Chroma 向量資料庫單例（儲存位在 `python/data/chroma_db/`）。

### 語言模型 (LLM)
- `llm_client.py`: 負責與 LLM 互動與 Prompt 檔案動態載入。
  - 提供 `generate_answer` 函數處理 RAG 問答。
  - 提供 `extract_meeting_summary` 函數，實現單檔 1-shot 全文 Prompt 結構化提取。
  - 透過 `.env` 中的 `ACTIVE_MODEL` 變數支援切換雲端模型 (OpenAI, Gemini, DeepSeek) 及本地 llama.cpp。

---

## 2. 模塊關係與資料流向

1. **文檔上傳、轉碼與檢索流程 (Indexing & Retrieval)**:
   - 用戶上傳原始文件 (MD, TXT, PDF, DOCX) 至 `/upload` API。
   - `converter.convert_to_markdown` 將文件轉碼並統一存放在 `python/data/markdown/`。
   - `rag_engine.add_document` 調用 `database.py` 記錄檔名、託管路徑與全文內容，並由 `database.get_vectorstore` 存入 ChromaDB。
   - 刪除文件時調用 `rag_engine.delete_document`，同步刪除 SQLite 紀錄、ChromaDB 向量切片與物理 `.md` 檔案。
   - 搜尋時調用 `rag_engine.search` 透過 ChromaDB 取回初步相似結果後，經 `get_reranker` 進行 Cross-Encoder 重新排序。

2. **AI 會議紀錄結構化提取與寫入流程 (Preview & Commit Workflow)**:
   - 前端發起 `/extract_summary` 請求帶入 `document_id`。
   - `llm_client.extract_meeting_summary` 自 `prompts/meeting_extraction.md` 載入系統提示詞，將 SQLite 中 `markdown_content` 全文 1-shot 餵給 LLM 提取為 JSON。
   - 前端獲得預覽 JSON 供使用者檢視或人工校對修改。
   - 前端發起 `/commit_summary` 請求，`main.py` 於單一 SQLite 事務中原子化完成 Meeting、Decisions、Tasks 之寫入與關聯綁定。

3. **活動與業務資料管理流程 (Activity Management)**:
   - `Activity` 為核心主體，其餘 `Meeting`, `Task`, `Decision`, `Schedule`, `Incident` 透過外鍵與其關聯。
   - 所有業務 CRUD 直接經由 `main.py` 的 RESTful API 端點暴露給前端或第三方呼叫。
   - 刪除 Activity 時若存有子紀錄會觸發 `ON DELETE RESTRICT` 保護歷史資料。

4. **回答生成流程 (LLM Generation)**:
   - 在 `/query` 端點若帶入 `generate_answer=True`，FastAPI 會呼叫 `llm_client.generate_answer`，將 RAG 檢索出的片段組合成 Prompt 丟給 `litellm` 產生回答。

---

## 3. 技術細節與變更紀錄
- **架構扁平化重構**: 消除 `rag_engine/`, `database/`, `llm/`, `activity/`, `decision/`, `incident/`, `schedule/` 資料夾，統一收納至 `rag_project/` 根目錄，大幅簡化引用層級。
- **多格式文件轉換**: 新增 `converter.py`，導入 `pypdf` 與 `python-docx` 支援 PDF/DOCX 轉碼，託管檔統一存放至 `python/data/markdown/`。
- **System Prompt 檔分離**: 建立 `prompts/` 資料夾收納 `.md` Prompt 檔，實現提示詞與邏輯代碼解耦。
- **AI 結構化 1-shot 與 Preview-Commit 機制**: 新增 `/extract_summary` 與 `/commit_summary` 端點，解決傳統 RAG 召回不全、Token 浪費與人工不可控問題。
- ** Fast API 完善**: 新增全套 CRUD REST API 覆蓋所有業務實體，並補上 Pydantic 驗證 Model。
- **單元測試完整化**: `tests/test_main.py` CLI 測試與 `tests/test_converter.py` 轉碼單元測試 100% 通過。

