import os
from typing import List
from langchain_core.documents import Document
from rag_project.database.chroma_db import get_vectorstore
from rag_project.rag_engine.chunker import split_markdown
from rag_project.rag_engine.reranker import rerank_documents

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
    Searches the vector database and reranks the results for higher relevance.
    """
    vectorstore = get_vectorstore()
    
    # 1. Retrieve phase (fetch more documents, e.g., 3x the required amount)
    retrieve_k = top_k * 3
    initial_results = vectorstore.similarity_search(query, k=retrieve_k)
    
    if not initial_results:
        return []
        
    # 2. Rerank phase
    reranked_results = rerank_documents(query, initial_results, top_k=top_k)
    return reranked_results
