# SDD: 智能客製化意見助手

## 1. 專案概述
基於 RAG 技術的 AI 助手，使用者上傳文件後可基於文件內容進行對話查詢。

## 2. 技術選型

### 前端
- **框架**: React + TypeScript
- **打包**: Electron (跨平台桌面應用)
- **通訊**:
  - 前端與主進程: Electron IPC + JSON
  - 主進程與 Python 後端: HTTP API (RESTful)

### 後端
- **語言**: Python 3.10+
- **套件管理**: uv
- **Web 框架**: FastAPI + uvicorn (提供本地 API 供 Electron 呼叫)
- **打包工具**: PyInstaller (編譯為獨立執行檔，無須使用者安裝 Python)
- **RAG 套件**: LangChain (流程编排)
- **向量化**: fastembed (輕量級、無須 PyTorch 的 ONNX 推理引擎)
- **LLM API**: litellm (統一接口，支援 OpenAI/Claude)

### 資料庫
- **純文字**: Markdown 格式 (非 TXT)，app 管理
- **原始文件**: 與 Markdown 斷開關聯 (使用者刪除原 PDF 不影響 Markdown)
- **切片文字**: Markdown 切片，app 管理
- **向量數據**: ChromaDB persistent mode
- **對話歷史**: SQLite
- **檔案管理**: SQLite (追蹤已導入的 Markdown 文件)

### 模型
- **Embedding**: fastembed (all-MiniLM-L6-v2，使用 ONNX Runtime 於 CPU 運行，輕量且快速)
- **LLM**: GPT-4o (OpenAI) 或 Claude 3.5 Sonnet (litellm)

## 3. 專案結構
```
rag-project/
├── src/                          # Electron 前端
│   ├── main/                     # 主進程 (Node.js)
│   │   ├── index.ts, app.ts
│   │   └── ipc-handlers/
│   │       ├── file-handler.ts
│   │       └── chat-handler.ts
│   └── renderer/                 # 渲染進程 (React)
│       ├── App.tsx
│       ├── components/
│       │   ├── Chat.tsx
│       │   ├── FileUploader.tsx
│       │   └── FileManager.tsx  # 管理已導入的 Markdown 文件
│       └── types/
│
├── python/                       # Python 後端 (FastAPI)
│   ├── main.py                   # FastAPI 伺服器入口
│   ├── rag_engine/
│   │   ├── parser.py             # Markdown 處理與解析
│   │   ├── chunker.py
│   │   ├── embedding.py
│   │   └── llm_client.py
│   └── database/
│       ├── chromadb.py
│       └── sqlite.py
│
├── config/
│   └── settings.json
└── requirements.txt
```

## 4. 核心流程

### 文件上傳
1. 使用者上傳 Markdown 檔案
2. Electron IPC 傳遞路徑給主進程
3. 主進程透過 HTTP POST 呼叫 Python FastAPI 進行處理
4. Python: 讀取 Markdown → 切片 → 向量化 → ChromaDB 儲存
5. 將 Markdown 複製/儲存到 app 管理目錄
6. 記錄到 SQLite (文件名、大小、處理時間、狀態)

### 對話互動
1. 使用者輸入問題
2. ChromaDB 檢索相關 Markdown 切片
3. 構建提示詞
4. litellm 呼叫 LLM API
5. 顯示回應
6. 儲存對話歷史到 SQLite

## 5. 開發步驟

```bash
# 環境設置
npm install                    # Node.js
uv init                        # Python
uv add langchain fastembed litellm chromadb fastapi uvicorn pyinstaller

# 開發
# 需要同時啟動前端與後端 (可透過 npm script 如 concurrently 整合)
uv run python/main.py          # 啟動 FastAPI 後端
npm run dev                    # 啟動 Electron 前端
```

## 6. MVP 範圍
- ✅ 文件上傳 (目前僅支援 Markdown 格式)
- ✅ 對話互動 (基於已導入的 Markdown)
- ✅ 文件管理 (查看、刪除已導入的 Markdown 文件)
- ❌ PDF/Word 轉檔支援 (延遲至下一階段)
- ❌ 版本控制、複雜設定 (後續)

## 7. 備選方案：Web 服務
- 前端：React
- 後端：Node.js/Python + API
- 資料庫：PostgreSQL + Pinecone/Qdrant
- 適用：多用戶、團隊協作、跨設備

## 8. 總結
- 初版：本地桌面應用，核心功能：上傳 Markdown→對話→文件管理
- 關鍵設計：以 Markdown 為核心，Python 端以 FastAPI 提供微服務，並透過 PyInstaller 打包
- 技術：React + Python + uv + FastAPI + LangChain + fastembed + litellm
- 資料庫：ChromaDB persistent mode + SQLite (追蹤 Markdown 文件)
