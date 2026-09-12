import os
import shutil
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any

from rag_project.rag_engine.retriever import add_document, search

app = FastAPI(title="RAG Project Backend")

# [新增] 1. CORS 設定：這是 React 能夠呼叫 FastAPI 的關鍵，沒有它會被瀏覽器阻擋
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 測試階段允許所有來源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# [新增] 2. 設定原始檔案的儲存路徑
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_RAW_DIR = os.path.join(BASE_DIR, "uploads", "raw")
os.makedirs(UPLOAD_RAW_DIR, exist_ok=True)

class PingResponse(BaseModel):
    status: str
    message: str

# (原本的 UploadRequest 已經刪除，因為我們改收實體檔案了)

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

class DocumentChunk(BaseModel):
    content: str
    metadata: Dict[str, Any]

class QueryResponse(BaseModel):
    results: List[DocumentChunk]

@app.get("/ping", response_model=PingResponse)
def ping():
    return {"status": "ok", "message": "Backend is running!"}

# [大改] 3. 改成接收前端傳來的實體檔案 (UploadFile)
@app.post("/upload")
def upload(file: UploadFile = File(...)):
    try:
        # 將前端傳來的檔案，存入 uploads/raw/ 資料夾
        raw_file_path = os.path.join(UPLOAD_RAW_DIR, file.filename)
        with open(raw_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 目前先限定處理 Markdown
        if not file.filename.lower().endswith(".md"):
            raise HTTPException(status_code=400, detail="目前僅支援 .md 檔案")
            
        # 呼叫你更新後的 RAG 引擎，將實體路徑傳遞給底層資料庫
        chunks_added = add_document(
            file_path=raw_file_path, 
            force=True, # 允許覆蓋
            raw_file_path=raw_file_path
        )
        
        return {
            "status": "success", 
            "message": f"成功上傳並向量化 {file.filename}！",
            "chunks_added": chunks_added
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# (原封不動保留你的搜尋邏輯)
@app.post("/query", response_model=QueryResponse)
def query_docs(req: QueryRequest):
    try:
        docs = search(req.query, top_k=req.top_k)
        results = [
            DocumentChunk(
                content=doc.page_content,
                metadata=doc.metadata
            ) for doc in docs
        ]
        return QueryResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)