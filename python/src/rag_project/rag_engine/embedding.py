from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

_embeddings = None

def get_embeddings():
    """Returns the FastEmbed instance for generating text embeddings."""
    global _embeddings
    if _embeddings is None:
        # 使用 Jina 的中文模型 (因為 fastembed 尚未內建 e5-small)
        _embeddings = FastEmbedEmbeddings(model_name="jinaai/jina-embeddings-v2-base-zh")
    return _embeddings
