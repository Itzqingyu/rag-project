import os
import sys

# 將 src 目錄加入 sys.path 以便 import backend
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from rag_project.rag_engine.retriever import add_document, search
from rag_project.database.chroma_db import get_vectorstore

def main():
    test_md_path = os.path.join(BASE_DIR, "tests", "test_data", "sample.md")
    
    print("=== [1] 開始測試：匯入文件 ===")
    try:
        chunks_added = add_document(test_md_path)
        print(f"[Success] 成功匯入文件，共切分為 {chunks_added} 個區塊。")
    except Exception as e:
        print(f"[Error] 匯入失敗: {e}")
        return

    # 確認資料庫內總筆數
    db = get_vectorstore()
    # 根據 chromadb API，目前可以用 _collection.count() 取得總數
    count = db._collection.count()
    print(f"目前 ChromaDB 中的總區塊數量: {count}")

    print("\n=== [2] 開始測試：語意檢索 ===")
    
    queries = [
        "張弈怎麼死的",
        "事件發生在什麼時候",
        "發生什麼災害"
    ]
    
    for q in queries:
        print(f"\n[問題]: {q}")
        results = search(q, top_k=3) # 這裡用 3 來方便檢視
        for i, res in enumerate(results):
            print(f"  > 結果 {i+1} (Source: {res.metadata.get('source')}):")
            print(f"{res.page_content.strip()}...") # 只印前150字
            print("-" * 50)

if __name__ == "__main__":
    main()
