# 後端 (Python) 模塊分析與架構變更紀錄

## 1. 模塊清單與功能簡述 (Package 結構化架構)

### 進入點與 API
- `main.py`: FastAPI 應用程式的主程式。提供完整的 REST API 端點，包含：
  - **系統與健康檢查**: `/ping`
  - **RAG 文件管理與上傳轉碼**: `/upload` (上傳 MD, TXT, PDF, DOCX 並自動轉換儲存與向量化，具備主檔名衝突前置防呆回傳 409 Conflict), `/documents` (GET 清單, DELETE 物理刪除包含 `.md` 與向量庫), `/query` (語意檢索與選填 LLM 回答)
  - **對話會話與上下文記憶 (Session & Chat)**:
    - `/sessions`: GET (列出所有 Sessions), POST (建立新 Session)
    - `/sessions/{id}`: GET (取得 Session 詳情與歷史訊息), PATCH (更新 Session 標題), DELETE (串聯刪除 Session 及其訊息)
    - `/sessions/{id}/messages`: POST (發送訊息，支援指定 `mode='chat'` 普通對話或 `mode='rag'` 知識庫檢索對話)
  - **AI 結構化提取與預覽寫入**: `/extract_summary` (發起 1-shot LLM 解析 SQLite 託管之完整 Markdown 文字並回傳預覽 JSON), `/commit_summary` (將前端校對後的結構化資料逐筆寫入 SQLite；目前可能部分成功)
  - **活動管理 (Activity)**: `/activities` (GET, POST), `/activities/{id}` (GET, PUT, DELETE)
  - **會議管理 (Meeting)**: `/meetings` (GET, POST), `/meetings/{id}` (GET, PUT, DELETE)
  - **待辦事項 (Task)**: `/tasks` (GET, POST), `/tasks/{id}` (GET, PUT, DELETE)
  - **決策紀錄 (Decision)**: `/decisions` (GET, POST), `/decisions/{id}` (GET, PUT, DELETE)
  - **流程日程 (Schedule)**: `/schedules` (GET, POST), `/schedules/{id}` (GET, PUT, DELETE)
  - **突發事件 (Incident)**: `/incidents` (GET, POST), `/incidents/{id}` (GET, PUT, DELETE)

- `tests/test_main.py`: 整合了互動式 CLI 測試選單；Activity Management 先選定 Activity，再操作其 Meeting／Task／Decision／Schedule／Incident，固定狀態與可選關聯以編號清單輸入。CLI 的 AI 文件解析寫入會把目前 `doc_id` 記錄至 Meeting 的 `source_document_id`。同時支援 RAG 文件管理、對話會話 (Chat Session) 多輪對話與模式切換、LLM 回答測試。
- `tests/test_converter.py`: 文件轉換器單元測試，驗證 MD 複製、TXT 轉碼、PDF 解析與 DOCX 提取功能。
- `tests/test_chat_session.py`: 對話會話與上下文記憶單元測試，驗證 Session CRUD、CASCADE 串聯刪除、Clean Context Isolation 防記憶污染機制、以及普通聊天與 RAG 模式切換。
- `tests/test_upload_duplicate.py`: 同主檔名上傳防呆與覆蓋行為單元測試，驗證 409 Conflict 阻擋、資料庫與實體檔案完整性保護、以及底層 FileExistsError 例外機制。
- `tests/test_meeting_extract_commit.py`: AI 會議摘要寫入與來源文檔 source_document_id 自動關聯單元測試，驗證 /commit_summary 與 /meetings 支援 source_document_id 自動注入、資料庫持久化、以及關聯文檔刪除時 ON DELETE SET NULL 外鍵約束保護機制。

### 業務與事項管理微服務套件 (`activity_services/`)
- `activity_services/activity.py`: 負責活動 (Activity) 後端業務邏輯與 SQLite CRUD 操作。
- `activity_services/meeting_task.py`: 負責會議 (Meeting) 與待辦事項 (Task) 的 SQLite CRUD 與 Activity／Meeting 關聯驗證。
  - Meeting 的 nullable `source_document_id` 關聯 `documents.id`；來源文件刪除時以 `ON DELETE SET NULL` 保留 Meeting 及其 Task／Decision。
- `activity_services/decision.py`: 負責決策 (Decision) CRUD、確認狀態、選項 JSON 與 Activity／Meeting 關聯驗證。
- `activity_services/schedule.py`: 負責活動流程 (Schedule) CRUD、時間範圍與 Activity／Meeting 關聯驗證。
- `activity_services/incident.py`: 負責臨時紀錄 (Incident) CRUD，並驗證可選 Schedule 與 Activity 的一致性。
- `activity_services/activity_common.py`: 提供活動管理模組共用的正整數 ID、必填文字、ISO 8601 時間及跨模組關聯驗證工具。

### AI 與檢索核心服務套件 (`ai_services/`)
- `ai_services/rag_engine.py`: 整合 `chunker`, `embedding`, `reranker`, `retriever` 模組。
  - **split_markdown**: 讀取 Markdown 並以 `RecursiveCharacterTextSplitter` 切片 (預設 500 字，50 重疊)。
  - **get_embeddings / get_reranker**: 採用 Lazy Singletons 載入 Embedding 模型與重排序模型。
  - **add_document / search / delete_document / list_documents**: 協調文件向量化、ChromaDB 寫入、物理 `.md` 檔案清理與 SQLite 紀錄。全面取消 `add_document` 之 `force` 覆蓋參數，遇重複檔案直接拋出 `FileExistsError`，杜絕覆蓋時先刪實體檔案引發崩潰之風險。
- `ai_services/llm_service.py`: 負責與 LLM 互動與 Prompt 檔案動態載入。
  - 提供 `chat_with_context` 函數處理對話與 RAG 問答生成，支援多輪對話上下文記憶、Clean Context Isolation 隔離過往檢索資料、以及普通對話與 RAG 模式動態切換。
  - 提供 `extract_structured_meeting_data` 函數，實現單檔 1-shot 全文 Prompt 結構化提取。
  - 透過 `.env` 中的 `ACTIVE_MODEL` 變數支援切換多供應商相容之大語言模型介面。

### 文件處理與格式轉碼套件 (`document_processing/`)
- `document_processing/converter.py`: 負責多格式文件轉碼與集中託管。支援 `.md`, `.txt`, `.pdf`, `.docx` 格式，自動建立並輸出至 `python/data/markdown/` 目錄。若為 MD 檔案則直接複製，其餘格式提取內文後包裝為標準 Markdown。

### Prompt 範本庫 (`prompts/`)
- `prompts/meeting_extraction.md`: 定義 AI 會議紀錄 1-shot 結構化抽取的 System Prompt 範本（規範會議日期、討論問題、解決方案、最終決策與待辦事項 JSON 格式）。
- `prompts/rag_qa.md`: 定義 RAG 通用問答的 System Prompt 範本。
- `prompts/chat_general.md`: 定義普通對話模式 (General Chat) 下 AI 智能助手的 System Prompt 範本。

### 資料庫 (Database Layer)
- `database.py`: 統一資料庫存取層（結合原 `sqlite_db` 與 `chroma_db`）。
  - 提供共用 SQLite `get_connection`（自動啟用 `PRAGMA foreign_keys = ON`）與 `init_db` 表結構初始化（資料庫檔位在 `python/data/rag_database.sqlite`）。
  - 管理文件 Metadata (包含 `markdown_path` 與 `markdown_content`) 以及 Activity、Meeting、Task、Decision、Schedule、Incident 的 SQLite 資料表與索引。
  - 管理對話會話 (`sessions`) 與對話歷史 (`chat_messages`) 資料表，提供 `create_session`, `get_session`, `list_sessions`, `update_session_title`, `delete_session`, `add_chat_message`, `get_chat_messages` 等 CRUD 函數。
  - 提供 `get_vectorstore()` 回傳 Chroma 向量資料庫單例（儲存位在 `python/data/chroma_db/`）。


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
   - `llm_service.extract_structured_meeting_data` 自 `prompts/meeting_extraction.md` 載入系統提示詞，將 SQLite 中 `markdown_content` 全文 1-shot 餵給 LLM 提取為 JSON。
   - 前端獲得預覽 JSON 供使用者檢視或人工校對修改，並於「關聯目標活動」卡片選擇既有活動或快速建立新活動（必填）。
   - 前端發起 `/commit_summary` 請求帶入所屬 `activity_id` 與來源文件 `doc_id`，`main.py` 自動將 `source_document_id` 注入 Meeting 寫入 SQLite，並依序建立 Decisions 與 Tasks 綁定該活動與會議。各 service 目前各自提交，因此中途失敗時已成功的資料會保留，呼叫端需呈現可能部分成功的結果。

3. **活動與業務資料管理流程 (Activity Management)**:
   - `Activity` 為核心主體，其餘 `Meeting`, `Task`, `Decision`, `Schedule`, `Incident` 透過外鍵與其關聯。
   - `Meeting.source_document_id` 可追溯結構化來源文件；刪除 document 時只解除來源連結，不刪除任何活動歷史資料。
   - 所有業務 CRUD 直接經由 `main.py` 的 RESTful API 端點暴露給前端或第三方呼叫。
   - 刪除 Activity 時若存有子紀錄會觸發 `ON DELETE RESTRICT` 保護歷史資料。

4. **回答生成流程 (LLM Generation)**:
   - 在 `/query` 端點若帶入 `generate_answer=True`，FastAPI 會呼叫 `llm_service.chat_with_context(..., mode='rag')`，將 RAG 檢索出的片段組合成 Prompt 丟給 `litellm` 產生回答。

5. **對話會話與模式切換流程 (Chat Sessions & Context Isolation)**:
   - 使用者透過 `/sessions` 建立對話串，每次對話送出至 `/sessions/{id}/messages` 並可指定 `mode` ('chat' 或 'rag')。
   - 系統從 `chat_messages` 載入最近 N 輪純歷史對話，過濾掉歷史舊檢索文本（Clean Context Isolation）。
   - 若為 `rag` 模式，即時透過 `rag_engine.search` 檢索相關切片，將當次切片注入在當前使用者問題 prompt 中；若為 `chat` 模式，直接載入通用提示詞 `chat_general.md` 進行流暢對話。
   - 助理回覆後，兩方訊息分別寫入 `chat_messages`，若為 RAG 回答則額外以 JSON 儲存當次檢索片段 (`retrieved_chunks`)，確保歷史可溯但不會污染後續對話上下文。

---

## 3. 技術細節與變更紀錄
- **對話會話 (Session) 與上下文記憶**: 新增 `sessions` 與 `chat_messages` 資料表，外鍵關聯設定 `ON DELETE CASCADE`。
- **Clean Context Isolation (防記憶污染架構)**: 徹底解決同一 Session 中多次 RAG 或模式切換時，舊檢索資料干擾後續問答與 Token 浪費的問題。
- **普通對話與 RAG 模式切換**: 擴充 `llm_service.chat_with_context`，支援動態加載 `chat_general.md` 與 `rag_qa.md`，並開放前端任意切換。
- **FastAPI 端點擴展**: 新增 `/sessions` 與 `/sessions/{id}/messages` 完整 RESTful 路由。
- **修復非 Markdown 檔案 (PDF/DOCX) 讀取解碼 Bug**: 修復 `rag_engine.add_document` 在執行 `convert_to_markdown` 之前誤以 utf-8 讀取二進位 PDF/DOCX 導致報錯的問題，現在可直接支援傳入 PDF/DOCX/TXT/MD 進行自動轉碼、切片與向量化。
- **修復 LLM 失敗訊息污染上下文 Bug**: 修復 `chat_with_context` 在底層拋錯時誤回傳錯誤字串假裝成功、導致錯誤訊息被寫入 SQLite 污染後續對話記憶的問題。改為明確拋出例外、API 回傳 502，且僅在 LLM 成功產生回答後才寫入 SQLite；同時於歷史載入時加入防禦性過濾，杜絕髒資料進入上下文。
- **單元測試完整化**: 新增 `tests/test_chat_session.py` 單元測試覆蓋率 100%，並在 `tests/test_main.py` 整合 CLI 互動式對話測試選單。
- **後端套件與資料庫全面更名為 `dash_backend` 與 `dash_database.sqlite`**:
  - 將後端核心 Package 目錄由 `rag_project/` 重新命名為 `dash_backend/`，同步更新 `pyproject.toml` 中的 `name = "dash_backend"`。
  - 將 SQLite 資料庫檔案更名為 `dash_database.sqlite`，並加入對既有 `rag_database.sqlite` 的自動平滑相容遷移機制。
  - 全面更新所有後端模組與 10 個測試腳本中所有 import 與 `@patch` 路徑，全套 49 個單元測試 100% 通過。
- **拆分 `ai_services/` 達成單一職責原則**:
  - 新建 `ai_services/` 專門放置 `rag_engine.py`（向量切塊、Embedding、Reranker、檢索）與 `llm_service.py`（Prompt 載入、LiteLLM 調用、多輪對話、結構化提煉）。
  - `document_processing/` 僅保留 `converter.py`，專注於檔案格式解析與轉碼。
  - `database.py` 與各測試調用端更新為 `dash_backend.ai_services...`，全套 49 個單元測試 100% 通過。
- **同主檔名防呆機制與移除覆蓋刪檔邏輯 (409 Conflict & Zero Overwrite)**:
  - **根本問題**: 先前 `/upload` 呼叫 `add_document` 時帶入 `force=True`，而底層覆蓋邏輯因先刪除實體檔案再嘗試切塊，引發 `FileNotFoundError` 導致既有文件被滅失、新文件未能入庫。
  - **核心變更**:
    1. 底層 `rag_engine.add_document` 徹底移除 `force` 參數與覆蓋刪除邏輯，遇檔案已存在嚴格拋出 `FileExistsError`，確保絕不暗中刪除實體檔案。
    2. 後端 `/upload` 端點於最前置（做任何暫存檔或轉碼前）以主檔名檢查 SQLite，若已存在相同主檔名之文件，直接回傳 `HTTP 409 Conflict` 與防呆提示，零副作用保護既有文檔。
    3. 前端（`ChatPanel`, `MeetingExtractPanel`）於 `documentService.ts` 引入 `checkDuplicateFileStem`，選檔後於發起網路請求前即時中斷並於抽屜提示錯誤。
    4. 新增 `tests/test_upload_duplicate.py` 單元測試，後端 52 個單元測試與前端 20 個單元測試 100% 通過。
- **AI 會議紀錄整理面板新增活動必填關聯與建立 UI (`MeetingExtractPanel.tsx`)**:
  - **背景**: 純會議文字紀錄無法自動對應所屬活動，而資料庫中 `meetings`, `decisions`, `tasks` 均有必填之 `activity_id` 外鍵約束。
  - **實作成果**:
    1. 於預覽表格頂端新增「關聯目標活動 (必填)」卡片，提供「選擇現有活動」與「快速建立新活動」雙模式切換。
    2. 串接 `GET /activities` 動態載入活動清單；若資料庫尚無活動，自動友善引導切換至新建活動。
    3. 串接 `POST /activities` 支援即時填妥活動名稱、年份、狀態與地點，支援手動立即建立或於「確認寫入資料庫」時自動連帶建立入庫。
    4. 落實活動必填防呆校驗，未指定活動時立即提示錯誤並阻擋寫入。
    5. 前端 `meetingExtract.test.ts` 新增 `createActivity` 單元測試，前後端全套測試 100% 通過。
- **修復 meetings 表之 source_document_id 自動關聯與持久化缺失**:
  - **根本原因**: 
    1. 後端 `main.py` 中 Pydantic 模型 `MeetingCreate` 與 `MeetingUpdate` 遺漏定義 `source_document_id` 欄位，導致前端傳入或由後端組裝之 `source_document_id` 在 `model_dump()` 時被 Pydantic 自動過濾忽略，無法傳入 `add_meeting()` 寫入資料庫。
    2. 後端 `CommitSummaryRequest` 未定義頂層 `doc_id` 欄位，導致由 `/extract_summary` 產生的文件 ID 在確認寫入時未被接收。
  - **核心變更**:
    1. 後端 `main.py`: 在 `MeetingCreate` 與 `MeetingUpdate` 補上 `source_document_id: Optional[int] = None`；在 `CommitSummaryRequest` 補上 `doc_id: Optional[int] = None` 與 `source_file: Optional[str] = None`。在 `/commit_summary` 端點中，自動將 `doc_id` 注入至 `meeting_dict["source_document_id"]`，落實寫入 SQLite `meetings` 表。
    2. 前端 `meetingExtractService.ts` 與 `MeetingExtractPanel.tsx`: 擴充 `ExtractedMeeting` 與 `CommitSummaryPayload` 包含 `source_document_id`、`doc_id` 與 `source_file`。在點擊「確認寫入資料庫」時，自動帶入該次結構化抽取來源文件的 `doc_id`。並在預覽卡片頂端呈現「來源：{filename}」標籤徽章。
    3. 前端樣式 `MeetingExtractPanel.css`: 新增 `.source-doc-badge` 樣式，符合視覺設計規範。
    4. 新增 `tests/test_meeting_extract_commit.py` 單元測試，全面驗證 `source_document_id` 自動綁定、無來源相容性、RESTful API 支援以及 `ON DELETE SET NULL` 級聯防護。後端 57 個測試與前端 21 個測試 100% 通過。



