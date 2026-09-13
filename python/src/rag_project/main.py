from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import os

from rag_project.rag_engine.retriever import add_document, search

app = FastAPI(title="RAG Project Backend")

class PingResponse(BaseModel):
    status: str
    message: str

class UploadRequest(BaseModel):
    file_path: str

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

@app.post("/upload")
def upload(req: UploadRequest):
    if not os.path.exists(req.file_path):
        raise HTTPException(status_code=404, detail="File not found")
    try:
        chunks_added = add_document(req.file_path)
        return {"status": "success", "chunks_added": chunks_added}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    # 這裡的 port 可之後移到 config/settings.json 或環境變數
    uvicorn.run(app, host="127.0.0.1", port=8000)
