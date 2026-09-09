from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

def split_markdown(file_path: str) -> List[Document]:
    """
    Reads a markdown file and splits it into fixed-size chunks.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return []

    # Fixed size chunking strategy (500 chars, 50 overlap)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", " ", ""]
    )
    
    docs = text_splitter.create_documents(
        texts=[content],
        metadatas=[{"source": file_path}]
    )
    
    return docs
