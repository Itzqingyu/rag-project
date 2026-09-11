from typing import List
from langchain_core.documents import Document
from fastembed.rerank.cross_encoder import TextCrossEncoder

_reranker = None

def get_reranker() -> TextCrossEncoder:
    """Returns the FastEmbed cross encoder for reranking."""
    global _reranker
    if _reranker is None:
        # 使用 Jina AI 的多語言 Reranker 模型
        _reranker = TextCrossEncoder(model_name="jinaai/jina-reranker-v2-base-multilingual")
    return _reranker

def rerank_documents(query: str, documents: List[Document], top_k: int = 5) -> List[Document]:
    """
    Reranks a list of Langchain Document objects based on the query.
    Returns the top_k Document objects sorted by relevance score.
    """
    if not documents:
        return []
        
    reranker = get_reranker()
    doc_texts = [doc.page_content for doc in documents]
    
    # rerank() returns an iterable of floats corresponding to the documents
    scores = list(reranker.rerank(query, doc_texts))
    
    # Combine scores and documents
    scored_docs = list(zip(scores, documents))
    # Sort by score descending
    scored_docs.sort(key=lambda x: x[0], reverse=True)
    
    # Extract just the documents from the sorted tuples
    return [doc for score, doc in scored_docs[:top_k]]
