from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

_embeddings = None

def get_embeddings():
    """Returns the FastEmbed instance for generating text embeddings."""
    global _embeddings
    if _embeddings is None:
        # 使用支援中文的 BGE 模型
        _embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-small-zh-v1.5")
    return _embeddings
