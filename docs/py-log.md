# 後端 (Python) 模塊分析

## 1. 模塊清單與功能簡述

### 進入點與 API
- `main.py`: FastAPI 應用程式的主程式。定義了 API 端點 `/ping` (健康檢查)、`/upload` (上傳並處理文檔) 以及 `/query` (查詢相關文檔)。
- `main_test.py`: 目前為空的測試檔案。

### 核心引擎 (RAG Engine)
- `rag_engine/chunker.py`: 負責文檔切塊。讀取 Markdown 檔案並使用 `RecursiveCharacterTextSplitter` 將文本切割成固定大小的片段 (預設 500 字元，50 字元重疊)。
- `rag_engine/embedding.py`: 負責生成文本向量。使用 `FastEmbedEmbeddings` 載入 Jina AI 的中文模型 (`jinaai/jina-embeddings-v2-base-zh`)。
- `rag_engine/reranker.py`: 負責查詢結果的重排序 (Reranking)。使用 `TextCrossEncoder` 載入 Jina AI 的多語言模型 (`jinaai/jina-reranker-v2-base-multilingual`)，以提升檢索的準確度。
- `rag_engine/retriever.py`: 檢索與寫入的協調者。提供 `add_document` (整合切塊與向量資料庫寫入) 及 `search` (整合向量初步相似度搜尋與 Rerank 重排序) 兩個主要流程函數。

### 資料庫 (Database)
- `database/chroma_db.py`: 負責管理 Chroma 向量資料庫。使用單例模式 (Singleton) 建立連線，設定儲存路徑為專案根目錄下的 `chroma_db`，並依賴 `embedding.py` 提供向量化功能。

### 語言模型 (LLM)
- `llm/llm_client.py`: 負責與 LLM 互動。提供 `generate_answer` 函數，使用 `litellm` 將檢索到的文檔片段 (Context) 與使用者問題組合成 Prompt，並呼叫模型 (預設配置為 `ollama/qwen`) 生成最終回答。

## 2. 模塊關係與資料流向

1. **文檔上傳流程 (Indexing)**:
   - 用戶請求 `/upload` API (`main.py`)
   - 呼叫 `retriever.add_document` (`retriever.py`)
   - 透過 `chunker.split_markdown` 讀檔並進行文本切塊 (`chunker.py`)
   - 將切塊交給 `chroma_db.get_vectorstore().add_documents` 進行向量化與儲存 (`chroma_db.py` 依賴 `embedding.py` 轉向量)

2. **文檔查詢流程 (Retrieval)**:
   - 用戶請求 `/query` API (`main.py`)
   - 呼叫 `retriever.search` (`retriever.py`)
   - 透過 `chroma_db.py` 進行初步相似度檢索 (預設取回需求數量 top_k 的 3 倍，以增加召回率)
   - 將初步檢索結果交給 `reranker.rerank_documents` 進行 Cross-Encoder 交叉比對並重新評分排序 (`reranker.py`)
   - 回傳最終排序最高的前 K 個最相關結果 (API 回應)。

3. **回答生成流程 (Generation - 尚未串接至 main.py API)**:
   - 在完整 RAG 架構中，系統會呼叫 `llm_client.generate_answer`。
   - 將上述檢索出的片段串接，並與用戶問題組合成 Final Prompt。
   - 透過 `litellm` 將 Prompt 拋給 LLM，最後得到 AI 生成的回應。

## 3. 大致技術細節
- **Web 框架**: FastAPI, Pydantic (用於請求與回應資料驗證)
- **向量資料庫**: ChromaDB (透過 `langchain_chroma` 整合)
- **文本處理與 RAG 框架**: LangChain (`langchain_text_splitters`, `langchain_core`)
- **模型推理與向量化**:
  - **Embedding**: Jina AI (`jina-embeddings-v2-base-zh`) via `fastembed`，負責將文件與查詢轉化為語意向量。
  - **Reranker**: Jina AI (`jina-reranker-v2-base-multilingual`) via `fastembed`，負責對初步檢索結果進行高精度再排序。
  - **LLM**: 統一透過 `litellm` 套件呼叫，支援多種後端模型，目前預設配置對接本地端 Ollama 的 Qwen 模型。
