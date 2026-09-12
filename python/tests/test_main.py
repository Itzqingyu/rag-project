import os
import sys
from dotenv import load_dotenv

# 讀取 .env 檔案中的環境變數
load_dotenv()

# 將 src 目錄加入 sys.path，確保可以正確 import rag_project
# 因為目前檔案在 python/tests/，所以 '..' 會到 python/，需要再加上 'src'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from rag_project.rag_engine.retriever import add_document, search
from rag_project.llm.llm_client import generate_answer

def wait_for_user():
    """暫停程式，等待使用者輸入 1 繼續"""
    while True:
        choice = input("\n👉 請輸入 1 繼續下個階段 (輸入 q 退出測試): ").strip()
        if choice == '1':
            break
        elif choice.lower() == 'q':
            print("退出測試。")
            sys.exit(0)

def test_rag_pipeline():
    print("--- 開始 RAG + LLM 互動測試 ---\n")
    
    # 1. 取得測試用的 Markdown 檔案
    test_file_path = input("[?] 請輸入要測試的 Markdown 檔案「絕對路徑」:\n> ").strip()
    
    # 移除可能不小心複製到的引號 (Windows 複製路徑時常會有雙引號)
    test_file_path = test_file_path.strip('\"\'')
    
    if not os.path.exists(test_file_path):
        print(f"[!] 找不到檔案: {test_file_path}")
        return
        
    print(f"[*] 成功讀取檔案路徑: {test_file_path}")
    wait_for_user()
    
    # 2. 測試文檔上傳與切塊 (Indexing)
    print("\n[*] 階段 1: 正在將文件匯入向量資料庫...")
    try:
        chunks_added = add_document(test_file_path)
        print(f"[+] 成功匯入，共切成 {chunks_added} 個片段。")
    except Exception as e:
        print(f"[!] 匯入失敗: {e}")
        return

    wait_for_user()

    # 3. 測試文檔檢索 (Retrieval)
    # 為了讓互動測試更完整，我也把查詢問題改為手動輸入
    user_query = input("\n[?] 請輸入您想檢索的測試問題:\n> ").strip()
    if not user_query:
        print("[!] 問題不能為空")
        return
        
    print(f"\n[*] 階段 2: 正在檢索問題 -> '{user_query}'")
    try:
        retrieved_docs = search(user_query, top_k=2)
        print(f"[+] 檢索完成，找到 {len(retrieved_docs)} 筆相關文獻。")
        
        # 將 LangChain Document 物件轉換成字串列表，供 LLM 模組使用
        retrieved_chunks = [doc.page_content for doc in retrieved_docs]
        for i, chunk in enumerate(retrieved_chunks, 1):
            print(f"  - 片段 {i}: {chunk.replace(chr(10), ' ')[:50]}...")
    except Exception as e:
        print(f"[!] 檢索失敗: {e}")
        return

    wait_for_user()

    # 4. 測試 LLM 回答生成 (Generation)
    system_prompt = "你是一個專業的 AI 助手。請根據【參考資料】回答【使用者問題】。請用繁體中文回答，如果資料中找不到答案，請回答「我不知道」。"
    print(f"\n[*] 階段 3: 正在呼叫 LLM 生成回答...")
    try:
        answer = generate_answer(user_query, system_prompt, retrieved_chunks)
        print("\n=============== LLM 回答 ===============")
        print(answer)
        print("========================================")
    except Exception as e:
        print(f"[!] LLM 呼叫失敗: {e}")

if __name__ == "__main__":
    test_rag_pipeline()
