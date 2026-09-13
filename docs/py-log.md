# 後端 (Python) 模塊分析

## 1. 模塊清單與功能簡述

### 進入點與 API
- `main.py`: FastAPI 應用程式的主程式。定義了 API 端點 `/ping` (健康檢查)、`/upload` (上傳並處理文檔) 以及 `/query` (查詢相關文檔)。
- `main_test.py`: 活動 (Activity)、會議 (Meeting) 與待辦事項 (Task) 的互動式 CLI 測試選單，支援完整的增刪改查 (CRUD) 測試。
- `activity/service.py`: 負責活動 (Activity) 後端業務邏輯與 SQLite CRUD 操作。
- `meeting_task.py`: 負責會議 (Meeting) 與待辦事項 (Task) 的 SQLite CRUD 與 Activity／Meeting 關聯驗證；只儲存呼叫端提供的內容，不自行讀取 PDF、Markdown 或其他檔案。
- `decision/service.py`: 負責決策 (Decision) CRUD、確認狀態、選項 JSON 與 Activity／Meeting 關聯驗證。
- `schedule/service.py`: 負責活動流程 (Schedule) CRUD、時間範圍與 Activity／Meeting 關聯驗證。
- `incident/service.py`: 負責臨時紀錄 (Incident) CRUD，並驗證可選 Schedule 與 Activity 的一致性。
- `activity_common.py`: 提供活動管理模組共用的正整數 ID、必填文字、ISO 8601 時間及跨模組關聯驗證。
- `test_main.py`: 後端 RAG 模塊的互動式 CLI 測試選單，支援檔案管理 (CRUD) 與搜尋檢索的本地測試。

### 核心引擎 (RAG Engine)
- `rag_engine/chunker.py`: 負責文檔切塊。讀取 Markdown 檔案並使用 `RecursiveCharacterTextSplitter` 將文本切割成固定大小的片段 (預設 500 字元，50 字元重疊)。
- `rag_engine/embedding.py`: 負責生成文本向量。使用 `FastEmbedEmbeddings` 載入 Jina AI 的中文模型 (`jinaai/jina-embeddings-v2-base-zh`)。
- `rag_engine/reranker.py`: 負責查詢結果的重排序 (Reranking)。使用 `TextCrossEncoder` 載入 Jina AI 的多語言模型 (`jinaai/jina-reranker-v2-base-multilingual`)，以提升檢索的準確度。
- `rag_engine/retriever.py`: 檢索與寫入的協調者。提供 `add_document` (包含防呆檢查、切塊、同步寫入向量與關聯資料庫), `search`, `delete_document`, `list_documents` 等完整 RAG 引擎 CRUD 核心函數。

### 資料庫 (Database)
- `database/chroma_db.py`: 負責管理 Chroma 向量資料庫。使用單例模式 (Singleton) 建立連線，設定儲存路徑為專案根目錄下的 `chroma_db`，並依賴 `embedding.py` 提供向量化功能。
- `database/sqlite_db.py`: 提供共用 SQLite context manager，每次連線啟用 foreign key 並自動關閉；管理文件 Metadata 以及 Activity、Meeting、Task、Decision、Schedule、Incident 的正式 schema。初始化在 CRUD 實際執行時進行，不在模組 import 時碰觸正式資料庫。

### 語言模型 (LLM)
- `llm/llm_client.py`: 負責與 LLM 互動。提供 `generate_answer` 函數，使用 `litellm` 將檢索到的文檔片段 (Context) 與使用者問題組合成 Prompt。並透過讀取 `.env` 中的 `ACTIVE_MODEL` 變數，支援動態切換 OpenAI、Gemini、DeepSeek 等雲端模型，以及自動對接本地端的 llama.cpp。

## 2. 模塊關係與資料流向

1. **文檔上傳流程 (Indexing)**:
   - 用戶請求上傳 API 或 CLI 指令
   - 呼叫 `retriever.add_document` (`retriever.py`)，先透過 `sqlite_db` 檢查檔案是否已存在，若存在則依據 `force` 參數決定是否拋出錯誤或先刪除舊資料。
   - 透過 `chunker.split_markdown` 讀檔並進行文本切塊 (`chunker.py`)
   - 將切塊交給 `chroma_db.get_vectorstore().add_documents` 進行向量化與儲存
   - 寫入完成後，透過 `sqlite_db.add_or_update_doc_record` 將檔案路徑與 chunk 數量記錄到 SQLite 中。

2. **文檔查詢流程 (Retrieval)**:
   - 用戶請求 `/query` API (`main.py`)
   - 呼叫 `retriever.search` (`retriever.py`)
   - 透過 `chroma_db.py` 進行初步相似度檢索 (預設取回需求數量 top_k 的 3 倍，以增加召回率)
   - 將初步檢索結果交給 `reranker.rerank_documents` 進行 Cross-Encoder 交叉比對並重新評分排序 (`reranker.py`)
   - 回傳最終排序最高的前 K 個最相關結果 (API 回應)。

4. **檔案管理流程 (CRUD)**:
   - 透過 `retriever.list_documents()` 從 SQLite 取得已上傳清單。
   - 透過 `retriever.delete_document()`，先利用 `vectorstore._collection.delete(where={"source": file_path})` 從 ChromaDB 清除指定向量片段，再從 SQLite 移除對應的紀錄。

5. **活動管理流程 (Activity Management)**:
   - Activity 是根資料；Meeting、Task、Decision、Schedule、Incident 都以 `activity_id` 關聯。
   - Meeting 可被 Task、Decision、Schedule 選擇性引用，建立或更新時會驗證雙方屬於相同 Activity。
   - 刪除 Meeting 時保留 Task、Decision、Schedule，並以 `ON DELETE SET NULL` 解除 `meeting_id`。
   - Incident 可選擇引用同 Activity 的 Schedule；Schedule 刪除時 Incident 保留並解除 `schedule_id`。
   - 所有 Activity 子資料的 Activity 外鍵使用 `ON DELETE RESTRICT`，避免誤刪歷史資料。
   - 目前 `CREATE TABLE IF NOT EXISTS` 只保證全新資料庫採用上述外鍵；已存在舊版 CASCADE schema 的 SQLite 檔案仍需後續 migration 重建資料表。

3. **回答生成流程 (Generation - 尚未串接至 main.py API)**:
   - 在完整 RAG 架構中，系統會呼叫 `llm_client.generate_answer`。
   - 將上述檢索出的片段串接，並與用戶問題組合成 Final Prompt。
   - 透過 `litellm` 將 Prompt 拋給 LLM，最後得到 AI 生成的回應。

## 3. 大致技術細節
- **Web 框架**: FastAPI, Pydantic (用於請求與回應資料驗證)
- **資料庫架構**:
  - **向量儲存**: ChromaDB (透過 `langchain_chroma` 整合)，用於語意檢索。
  - **檔案狀態追蹤與業務資料**: SQLite (Python 內建 `sqlite3`)，用於 Metadata 與六個 Activity Management 模組；全新資料庫使用 `RESTRICT`／`SET NULL` 保護歷史關聯。
- **文本處理與 RAG 框架**: LangChain (`langchain_text_splitters`, `langchain_core`)
- **模型推理與向量化**:
  - **Embedding**: Jina AI (`jina-embeddings-v2-base-zh`) via `fastembed`，負責將文件與查詢轉化為語意向量。
  - **Reranker**: Jina AI (`jina-reranker-v2-base-multilingual`) via `fastembed`，負責對初步檢索結果進行高精度再排序。
  - **LLM**: 統一透過 `litellm` 套件呼叫，支援透過 `.env` 的 `ACTIVE_MODEL` 變數無縫切換多種雲端模型 (OpenAI, Gemini, DeepSeek) 以及本地 llama.cpp (OpenAI 相容格式)。
