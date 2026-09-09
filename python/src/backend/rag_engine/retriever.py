import os
from typing import List
from langchain_core.documents import Document
from backend.database.chroma_db import get_vectorstore
from backend.rag_engine.chunker import split_markdown

def add_document(file_path: str) -> int:
    """
    Parses a markdown file, chunks it, and adds it to the Chroma vector store.
    Returns the number of chunks added.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Document not found: {file_path}")
        
    docs = split_markdown(file_path)
    if not docs:
        return 0
        
    vectorstore = get_vectorstore()
    vectorstore.add_documents(docs)
    
    return len(docs)

def search(query: str, top_k: int = 5) -> List[Document]:
    """
    Searches the vector database for the most relevant chunks.
    """
    vectorstore = get_vectorstore()
    # Perform similarity search
    results = vectorstore.similarity_search(query, k=top_k)
    return results
