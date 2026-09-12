import uvicorn

if __name__ == "__main__":
    # 透過字串指定路徑，Uvicorn 就會聰明地從當前目錄往下找 src
    uvicorn.run(
        "src.rag_project.main:app", 
        host="127.0.0.1", 
        port=8000, 
        reload=True
    )