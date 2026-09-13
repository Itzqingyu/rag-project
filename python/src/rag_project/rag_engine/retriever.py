import os
from typing import List, Dict, Any
from langchain_core.documents import Document
from rag_project.database.chroma_db import get_vectorstore
from rag_project.rag_engine.chunker import split_markdown
from rag_project.rag_engine.reranker import rerank_documents
import rag_project.database.sqlite_db as sqlite_db

def add_document(file_path: str, force: bool = False) -> int:
    """
    Parses a markdown file, chunks it, and adds it to the Chroma vector store.
    If the file exists and force=False, raises FileExistsError.
    If force=True, deletes the old document first.
    Returns the number of chunks added.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Document not found: {file_path}")

    # 檢查是否已存在
    existing_record = sqlite_db.get_doc_by_path(file_path)
    if existing_record:
        if not force:
            raise FileExistsError(f"Document already exists in database: {file_path}")
        else:
            # 刪除舊有向量與紀錄
            delete_document(file_path)
        
    docs = split_markdown(file_path)
    if not docs:
        return 0
        
    vectorstore = get_vectorstore()
    vectorstore.add_documents(docs)
    
    # 更新 SQLite 紀錄
    sqlite_db.add_or_update_doc_record(file_path, len(docs))
    
    return len(docs)

def delete_document(identifier: str) -> bool:
    """
    Deletes a document from both ChromaDB and SQLite.
    identifier can be a file_path (str) or doc_id (str convertible to int).
    """
    record = None
    if str(identifier).isdigit():
        record = sqlite_db.get_doc_by_id(int(identifier))
    else:
        record = sqlite_db.get_doc_by_path(identifier)
        
    if not record:
        return False
        
    file_path = record["file_path"]
    
    # 從 ChromaDB 刪除 (使用 where 條件指定 source metadata)
    vectorstore = get_vectorstore()
    try:
        # langchain-chroma 提供底層 collection 的直接存取
        vectorstore._collection.delete(where={"source": file_path})
    except Exception as e:
        print(f"Warning: Failed to delete from ChromaDB: {e}")
        
    # 從 SQLite 刪除
    sqlite_db.delete_doc_record_by_path(file_path)
    return True

def list_documents() -> List[Dict[str, Any]]:
    """
    Returns a list of all uploaded documents.
    """
    return sqlite_db.get_all_docs()

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
