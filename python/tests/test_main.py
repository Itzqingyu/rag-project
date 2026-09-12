import os
import sys
from dotenv import load_dotenv

# 讀取 .env 檔案中的環境變數
load_dotenv()

# 將 src 目錄加入 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from rag_project.rag_engine.retriever import add_document, search, list_documents, delete_document

def print_menu():
    print("\n" + "="*45)
    print("       RAG Backend CLI 測試選單")
    print("="*45)
    print(" 1. 列出所有已上傳檔案")
    print(" 2. 上傳 / 更新檔案")
    print(" 3. 刪除檔案")
    print(" 4. 搜尋測試 (不呼叫 LLM)")
    print(" 5. 離開")
    print("="*45)

def handle_list():
    docs = list_documents()
    if not docs:
        print("\n[INFO] 尚無任何上傳的檔案。")
        return
    
    print("\n--- 已上傳檔案清單 ---")
    for doc in docs:
        print(f"ID: {doc['id']} | 檔名: {doc['filename']} | 切片數: {doc['chunk_count']} | 時間: {doc['upload_date']}")
        print(f"路徑: {doc['file_path']}")
        print("-" * 30)

def handle_upload():
    file_path = input("\n[?] 請輸入要上傳的 Markdown 檔案絕對路徑 (提示: 可用 tests/test_data 內的檔案):\n> ").strip().strip('\"\'')
    if not file_path:
        return
        
    try:
        chunks = add_document(file_path, force=False)
        print(f"\n[+] 成功匯入，共切成 {chunks} 個片段。")
    except FileExistsError:
        ans = input(f"\n[!] 檔案已存在，是否覆蓋？(y/n): ").strip().lower()
        if ans == 'y':
            try:
                print("\n[*] 正在刪除舊資料並重新匯入...")
                chunks = add_document(file_path, force=True)
                print(f"\n[+] 成功覆蓋匯入，共切成 {chunks} 個片段。")
            except Exception as e:
                print(f"\n[!] 覆蓋失敗: {e}")
        else:
            print("\n[INFO] 已取消上傳。")
    except Exception as e:
        print(f"\n[!] 上傳失敗: {e}")

def handle_delete():
    identifier = input("\n[?] 請輸入要刪除的檔案路徑或 ID:\n> ").strip().strip('\"\'')
    if not identifier:
        return
        
    success = delete_document(identifier)
    if success:
        print(f"\n[+] 刪除成功: {identifier}")
    else:
        print(f"\n[!] 刪除失敗，資料庫中找不到該檔案紀錄: {identifier}")

def handle_search():
    query = input("\n[?] 請輸入測試查詢問題:\n> ").strip()
    if not query:
        return
        
    try:
        docs = search(query, top_k=3)
        if not docs:
            print("\n[INFO] 找不到相關結果。")
            return
            
        print(f"\n[+] 檢索完成，找到 {len(docs)} 筆相關文獻。")
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get('source', 'Unknown')
            content = doc.page_content.replace('\n', ' ')[:100]
            print(f"\n[{i}] 來源: {source}\n    片段預覽: {content}...")
    except Exception as e:
        print(f"\n[!] 檢索失敗: {e}")

def main():
    while True:
        print_menu()
        choice = input("[?] 請選擇操作 (1-5): ").strip()
        
        if choice == '1':
            handle_list()
        elif choice == '2':
            handle_upload()
        elif choice == '3':
            handle_delete()
        elif choice == '4':
            handle_search()
        elif choice == '5' or choice.lower() == 'q':
            print("[INFO] 退出測試系統。")
            break
        else:
            print("\n[!] 無效的選項，請輸入 1 到 5。")

if __name__ == "__main__":
    main()
