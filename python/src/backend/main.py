from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="RAG Project Backend")

class PingResponse(BaseModel):
    status: str
    message: str

@app.get("/ping", response_model=PingResponse)
def ping():
    return {"status": "ok", "message": "Backend is running!"}

if __name__ == "__main__":
    import uvicorn
    # 這裡的 port 可之後移到 config/settings.json 或環境變數
    uvicorn.run(app, host="127.0.0.1", port=8000)
