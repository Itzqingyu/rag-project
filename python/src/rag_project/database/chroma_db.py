import os
from langchain_chroma import Chroma
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

# Define paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DB_DIR = os.path.join(BASE_DIR, "chroma_db")

# Singleton for embedding and db
_embeddings = None
_vectorstore = None

def get_embeddings():
    global _embeddings
    if _embeddings is None:
        # 使用支援中文的 BGE 模型
        _embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-small-zh-v1.5")
    return _embeddings

def get_vectorstore() -> Chroma:
    """Returns the Chroma vector store instance."""
    global _vectorstore
    if _vectorstore is None:
        # Create directory if it doesn't exist
        os.makedirs(DB_DIR, exist_ok=True)
        _vectorstore = Chroma(
            collection_name="rag_collection",
            embedding_function=get_embeddings(),
            persist_directory=DB_DIR
        )
    return _vectorstore
