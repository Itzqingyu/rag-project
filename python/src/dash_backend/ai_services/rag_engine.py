"""RAG 核心引擎模組 (RAG Engine Core)。

整合 Markdown 文件讀取與切塊、FastEmbed 向量模型初始化、
Cross-Encoder 重排序 (Reranking) 以及向量資料庫檢索與文件增刪查改功能。
"""

import os
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from fastembed.rerank.cross_encoder import TextCrossEncoder

import dash_backend.database as db
from dash_backend.document_processing.converter import convert_to_markdown, DEFAULT_MARKDOWN_DIR

# ==========================================
# 1. Embedding 與 Reranker 模型載入 (Lazy Singletons)
# ==========================================

_embeddings = None
_reranker = None


def get_embeddings() -> FastEmbedEmbeddings:
    """回傳 FastEmbedEmbeddings 向量模型單例 (使用 Jina AI 中文模型 jina-embeddings-v2-base-zh)。"""
    global _embeddings
    if _embeddings is None:
        _embeddings = FastEmbedEmbeddings(model_name="jinaai/jina-embeddings-v2-base-zh")
    return _embeddings


def get_reranker() -> TextCrossEncoder:
    """回傳 FastEmbed TextCrossEncoder 重排序模型單例 (使用 Jina AI 多語言模型 jina-reranker-v2-base-multilingual)。"""
    global _reranker
    if _reranker is None:
        _reranker = TextCrossEncoder(model_name="jinaai/jina-reranker-v2-base-multilingual")
    return _reranker


# ==========================================
# 2. Markdown 切塊與 Rerank 重排序功能
# ==========================================

def split_markdown(file_path: str) -> List[Document]:
    """讀取 Markdown 檔案並使用 RecursiveCharacterTextSplitter 進行固定長度切塊 (500 字，50 字重疊)。
    切塊 metadata 中的 source 統一存放為相對於 data/ 的相對路徑 (格式固定為 markdown/{filename})。
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"[RAG Engine Error] 讀取檔案失敗 {file_path}: {e}")
        return []

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", " ", ""]
    )
    
    filename = os.path.basename(file_path)
    rel_source_path = f"markdown/{filename}"
    
    docs = text_splitter.create_documents(
        texts=[content],
        metadatas=[{"source": rel_source_path}]
    )
    
    return docs


def rerank_documents(query: str, documents: List[Document], top_k: int = 5) -> List[Document]:
    """使用 Cross-Encoder 對初步檢索出的文件片段與查詢問題進行交叉比對評分，回傳前 top_k 個最相關結果。"""
    if not documents:
        return []
        
    reranker = get_reranker()
    doc_texts = [doc.page_content for doc in documents]
    
    scores = list(reranker.rerank(query, doc_texts))
    
    scored_docs = list(zip(scores, documents))
    scored_docs.sort(key=lambda x: x[0], reverse=True)
    
    return [doc for score, doc in scored_docs[:top_k]]


# ==========================================
# 3. RAG 檢索與文件管理 (Retriever API)
# ==========================================

def add_document(file_path: str, *, db_path: Optional[str] = None) -> int:
    """解析 Markdown 檔案、文本切塊、寫入 Chroma 向量庫並將 Metadata 存入 SQLite。
    系統不支援自動覆蓋；若檔案已存在於資料庫中，將拋出 FileExistsError。
    
    :param file_path: 實體檔案路徑 (支援 .md, .txt, .pdf, .docx)
    :return: 成功寫入的切塊數量
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"找不到檔案: {file_path}")

    source_path = os.path.abspath(file_path)

    # 1. 判斷預期的託管 Markdown 檔案路徑
    raw_name = os.path.basename(file_path)
    file_stem, ext = os.path.splitext(raw_name)
    target_md_path = os.path.join(DEFAULT_MARKDOWN_DIR, f"{file_stem}.md")

    # 2. 檢查 SQLite 紀錄是否存在，若已存在則直接拋出 FileExistsError（不支援覆蓋）
    existing_record = db.get_doc_by_path(target_md_path, db_path=db_path)
    if existing_record:
        raise FileExistsError(f"檔案已存在於資料庫中: {target_md_path}")

    # 3. 確保目標託管 Markdown 檔案存在且內容最新 (多格式轉檔 PDF/DOCX/TXT/MD)
    if source_path != os.path.abspath(target_md_path) or ext.lower() != ".md":
        target_md_path = convert_to_markdown(source_path)

    docs = split_markdown(target_md_path)
    if not docs:
        return 0
        
    vectorstore = db.get_vectorstore()
    vectorstore.add_documents(docs)
    
    db.add_or_update_doc_record(
        file_path=target_md_path, 
        chunk_count=len(docs),
        db_path=db_path
    )
    
    return len(docs)


def delete_document(identifier: str, *, db_path: Optional[str] = None) -> bool:
    """根據檔案路徑或 ID 從 ChromaDB、SQLite 以及實體硬碟中同步刪除文件與向量紀錄。"""
    record = None
    if str(identifier).isdigit():
        record = db.get_doc_by_id(int(identifier), db_path=db_path)
    else:
        record = db.get_doc_by_path(identifier, db_path=db_path)
        
    if not record:
        return False
        
    file_path = record["file_path"]
    filename = record["filename"]
    rel_path = f"markdown/{filename}"
    abs_md_path = os.path.join(DEFAULT_MARKDOWN_DIR, filename)
    
    vectorstore = db.get_vectorstore()
    # 支援相對路徑與相容舊版絕對路徑的向量清理
    for src in [rel_path, file_path, abs_md_path]:
        try:
            vectorstore._collection.delete(where={"source": src})
        except Exception:
            pass
        
    db.delete_doc_record_by_path(file_path, db_path=db_path)
    
    # 連帶清理託管於硬碟的實體 .md 檔案
    target_to_remove = abs_md_path if os.path.exists(abs_md_path) else (file_path if os.path.exists(file_path) else None)
    if target_to_remove and os.path.exists(target_to_remove):
        try:
            os.remove(target_to_remove)
        except Exception as e:
            print(f"[Warning] 刪除硬碟實體檔案失敗: {e}")
            
    return True


def list_documents(*, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """取得所有已上傳的 RAG 文件列表。"""
    return db.get_all_docs(db_path=db_path)


def search(query: str, top_k: int = 5) -> List[Document]:
    """執行完整 RAG 檢索流程：先經由向量相似度抓取 3x 候選集，再經由 Reranker 高精度排序取前 top_k 個。"""
    vectorstore = db.get_vectorstore()
    
    retrieve_k = top_k * 3
    initial_results = vectorstore.similarity_search(query, k=retrieve_k)
    
    if not initial_results:
        return []
        
    reranked_results = rerank_documents(query, initial_results, top_k=top_k)
    return reranked_results
