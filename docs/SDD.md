# SDD: 智能客製化意見助手

## 1. 專案概述
基於 RAG 技術的 AI 助手，使用者上傳文件後可基於文件內容進行對話查詢。

## 2. 技術選型

### 前端
- **框架**: React + TypeScript
- **打包**: Electron (跨平台桌面應用)
- **通訊**: Electron IPC + JSON

### 後端
- **語言**: Python 3.10+
- **套件管理**: uv
- **RAG 套件**: LangChain (流程编排)
- **向量化**: sentence-transformers (all-MiniLM-L6-v2)
- **LLM API**: litellm (統一接口，支援 OpenAI/Claude)

### 資料庫
- **純文字**: Markdown 格式 (非 TXT)，app 管理
- **原始文件**: 與 Markdown 斷開關聯 (使用者刪除原 PDF 不影響 Markdown)
- **切片文字**: Markdown 切片，app 管理
- **向量數據**: ChromaDB persistent mode
- **對話歷史**: SQLite
- **檔案管理**: SQLite (追蹤已導入的 Markdown 文件)

### 模型
- **Embedding**: sentence-transformers/all-MiniLM-L6-v2 (CPU 運行)
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
├── python/                       # Python 後端
│   ├── main.py
│   ├── rag_engine/
│   │   ├── parser.py
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
1. 使用者上傳 PDF/Word/Markdown
2. Electron IPC 接收路徑
3. Python: 解析為 Markdown → 切片 → 向量化 → ChromaDB 儲存
4. 產生 Markdown 文件，儲存到 app 管理目錄
5. 記錄到 SQLite (文件名、大小、處理時間、狀態)

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
uv add langchain sentence-transformers litellm chromadb

# 開發
npm run dev
```

## 6. MVP 範圍
- ✅ 文件上傳 (PDF/Word/Markdown → 轉為 Markdown)
- ✅ 對話互動 (基於已導入的 Markdown)
- ✅ 文件管理 (查看、刪除已導入的 Markdown 文件)
- ❌ 版本控制、複雜設定 (後續)

## 7. 備選方案：Web 服務
- 前端：React
- 後端：Node.js/Python + API
- 資料庫：PostgreSQL + Pinecone/Qdrant
- 適用：多用戶、團隊協作、跨設備

## 8. 總結
- 初版：本地桌面應用，核心功能：上傳→轉 Markdown→對話→文件管理
- 關鍵設計：原始文件與 Markdown 斷開關聯，使用者自主管理 Markdown
- 技術：React + Python + uv + LangChain + sentence-transformers + litellm
- 資料庫：ChromaDB persistent mode + SQLite (追蹤 Markdown 文件)
