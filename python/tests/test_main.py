import os
import sys
from typing import List
from dotenv import load_dotenv

# 讀取 .env 檔案中的環境變數
load_dotenv()

# 將 src 目錄加入 sys.path
PYTHON_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PYTHON_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from rag_project.document_processing.rag_engine import add_document, search, list_documents, delete_document
from rag_project.document_processing.llm_service import generate_answer
from rag_project.activity_services.activity import (
    create_activity,
    get_activity,
    list_activities,
    update_activity,
    delete_activity,
)
from rag_project.activity_services.meeting_task import (
    add_meeting,
    get_meetings,
    get_meeting_by_id,
    update_meeting,
    delete_meeting,
    add_task,
    get_tasks,
    get_task_by_id,
    update_task,
    delete_task,
)
from rag_project.activity_services.decision import (
    create_decision,
    get_decision,
    list_decisions,
    update_decision,
    delete_decision,
)
from rag_project.activity_services.schedule import (
    create_schedule,
    get_schedule,
    list_schedules,
    update_schedule,
    delete_schedule,
)
from rag_project.activity_services.incident import (
    create_incident,
    get_incident,
    list_incidents,
    update_incident,
    delete_incident,
)


def print_main_menu():
    print("\n" + "=" * 60)
    print("       RAG & Activity 整合 CLI 測試選單")
    print("=" * 60)
    print(" [ RAG 與 LLM 文件管理 ]")
    print("  1. 列出所有已上傳文件 (List Documents)")
    print("  2. 上傳 / 覆蓋 Markdown 文件 (Upload Document)")
    print("  3. 刪除文件 (Delete Document)")
    print("  4. 搜尋測試 (Search VectorStore)")
    print("  5. AI 生成回答測試 (LLM Generate Answer)")
    print("-" * 60)
    print(" [ 輕量化業務功能管理 ]")
    print("  6. 會議管理 (Meetings)")
    print("  7. 待辦事項 (Tasks)")
    print("  8. 活動管理 (Activities)")
    print("  9. 決策/流程/突發事件 (Decisions, Schedules, Incidents)")
    print("-" * 60)
    print("  0. 離開 (Exit)")
    print("=" * 60)


# ==========================================
# RAG 與 LLM 處理邏輯
# ==========================================

def handle_list_docs():
    docs = list_documents()
    if not docs:
        print("\n[INFO] 尚無任何上傳的檔案。")
        return
    
    print("\n--- 已上傳檔案清單 ---")
    for doc in docs:
        print(f"ID: {doc['id']} | 檔名: {doc['filename']} | 切片數: {doc['chunk_count']} | 時間: {doc['upload_date']}")
        print(f"路徑: {doc['file_path']}")
        print("-" * 30)


def handle_upload_doc():
    file_path = input("\n[?] 請輸入要上傳的 Markdown 檔案絕對路徑 (提示: 可用 tests/test_data 內的檔案):\n> ").strip().strip('\"\'')
    if not file_path:
        return
        
    try:
        chunks = add_document(file_path, force=False)
        print(f"\n[+] 成功匯入，共切成 {chunks} 個片段。")
    except FileExistsError:
        ans = input("\n[!] 檔案已存在，是否覆蓋？(y/n): ").strip().lower()
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


def handle_delete_doc():
    identifier = input("\n[?] 請輸入要刪除的檔案路徑或 ID:\n> ").strip().strip('\"\'')
    if not identifier:
        return
        
    success = delete_document(identifier)
    if success:
        print(f"\n[+] 刪除成功: {identifier}")
    else:
        print(f"\n[!] 刪除失敗，資料庫中找不到該檔案紀錄: {identifier}")


def handle_search_doc():
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


def handle_generate_answer():
    query = input("\n[?] 請輸入測試查詢問題:\n> ").strip()
    if not query:
        return
        
    try:
        print("\n[*] 正在檢索相關文獻...")
        docs = search(query, top_k=3)
        if not docs:
            print("\n[INFO] 找不到相關結果，無法生成回答。")
            return
            
        print(f"[+] 找到 {len(docs)} 筆相關文獻，正在呼叫 LLM 生成回答...")
        retrieved_chunks = [doc.page_content for doc in docs]
        answer = generate_answer(query, retrieved_chunks)
        
        print("\n" + "="*45)
        print("🤖 AI 回答：")
        print("="*45)
        print(answer)
        print("="*45)
        
    except Exception as e:
        print(f"\n[!] 生成失敗: {e}")


# ==========================================
# 輕量化業務功能處理邏輯 (Activity / Meeting / Task / Decision / etc.)
# ==========================================

def get_activity_label(activity_id: int) -> str:
    act = get_activity(activity_id)
    if act:
        return f"{act['name']} (ID: {act['id']}, 年份: {act['year']}, 狀態: {act['status']})"
    return f"未知活動 (ID: {activity_id})"


def print_activities_table() -> List[dict]:
    activities = list_activities()
    print("\n" + "-" * 55)
    print("      📍 可用活動列表 (Activity Table)")
    print("-" * 55)
    if not activities:
        print("  (目前資料庫無任何活動紀錄)")
    else:
        for act in activities:
            print(f"  [ ID: {act['id']} ] ➡️  {act['name']} ({act['year']}) [{act['status']}] 地點: {act['venue'] or '未填'}")
    print("-" * 55)
    return activities


def select_or_create_activity_id() -> int:
    activities = print_activities_table()
    if not activities:
        print("\n[提示] 資料庫中尚無活動，請先建立一個活動：")
        name = input("輸入活動名稱: ").strip()
        year_str = input("輸入活動年份 (預設 2026): ").strip() or "2026"
        status = input("輸入活動狀態 (預設 '準備中'): ").strip() or "準備中"
        created = create_activity(name=name, year=int(year_str), status=status)
        print(f"[成功] 自動建立活動: {created['name']} (ID: {created['id']})")
        return created['id']
    
    act_str = input("輸入活動 ID (activity_id): ").strip()
    return int(act_str)


def handle_meeting_menu():
    print("\n--- 會議管理 (Meetings) ---")
    print("1. 新增會議")
    print("2. 查看會議列表")
    print("3. 修改會議")
    print("4. 刪除會議")
    choice = input("選擇操作 (1-4): ").strip()

    if choice == '1':
        try:
            act_id = select_or_create_activity_id()
            name = input("會議名稱: ").strip()
            start_time = input("開始時間 (可跳過): ").strip()
            end_time = input("結束時間 (可跳過): ").strip()
            location = input("地點 (可跳過): ").strip()
            participants = input("參與人員 (可跳過): ").strip()
            content = input("會議內容: ").strip()
            res = add_meeting(
                activity_id=act_id,
                name=name,
                start_time=start_time,
                end_time=end_time,
                location=location,
                participants=participants,
                content=content
            )
            print(f"\n[成功] 新增會議成功 ID {res['id']}")
        except Exception as e:
            print(f"\n[錯誤] {e}")

    elif choice == '2':
        meetings = get_meetings()
        print(f"\n--- 會議列表 (共 {len(meetings)} 筆) ---")
        for m in meetings:
            print(f"[ID: {m['id']}] 活動ID: {m['activity_id']} | 名稱: {m['name']} | 時間: {m['start_time']}~{m['end_time']}")

    elif choice == '3':
        try:
            m_id = int(input("會議 ID: ").strip())
            name = input("新名稱 (按 Enter 跳過): ").strip() or None
            location = input("新地點 (按 Enter 跳過): ").strip() or None
            if update_meeting(m_id, name=name, location=location):
                print("\n[成功] 會議更新成功！")
        except Exception as e:
            print(f"\n[錯誤] {e}")

    elif choice == '4':
        try:
            m_id = int(input("刪除會議 ID: ").strip())
            if delete_meeting(m_id):
                print("\n[成功] 會議已刪除！")
        except Exception as e:
            print(f"\n[錯誤] {e}")


def handle_task_menu():
    print("\n--- 待辦事項 (Tasks) ---")
    print("1. 新增待辦")
    print("2. 查看待辦列表")
    print("3. 修改待辦")
    print("4. 刪除待辦")
    choice = input("選擇操作 (1-4): ").strip()

    if choice == '1':
        try:
            act_id = select_or_create_activity_id()
            content = input("待辦內容: ").strip()
            assignee = input("負責人: ").strip()
            due_date = input("期限: ").strip()
            priority = input("優先級 (高/中/低): ").strip() or "中"
            res = add_task(activity_id=act_id, content=content, assignee=assignee, due_date=due_date, priority=priority)
            print(f"\n[成功] 新增待辦成功 ID {res['id']}")
        except Exception as e:
            print(f"\n[錯誤] {e}")

    elif choice == '2':
        tasks = get_tasks()
        print(f"\n--- 待辦列表 (共 {len(tasks)} 筆) ---")
        for t in tasks:
            print(f"[ID: {t['id']}] 活動ID: {t['activity_id']} | 狀態: [{t['status']}] | 優先級: [{t['priority']}] | 內容: {t['content']}")

    elif choice == '3':
        try:
            t_id = int(input("待辦 ID: ").strip())
            status = input("新狀態 (pending/completed): ").strip() or None
            if update_task(t_id, status=status):
                print("\n[成功] 待辦更新成功！")
        except Exception as e:
            print(f"\n[錯誤] {e}")

    elif choice == '4':
        try:
            t_id = int(input("刪除待辦 ID: ").strip())
            if delete_task(t_id):
                print("\n[成功] 待辦已刪除！")
        except Exception as e:
            print(f"\n[錯誤] {e}")


def handle_activity_menu():
    print("\n--- 活動管理 (Activities) ---")
    print("1. 查看所有活動")
    print("2. 新增活動")
    print("3. 刪除活動")
    choice = input("選擇操作 (1-3): ").strip()

    if choice == '1':
        print_activities_table()
    elif choice == '2':
        try:
            name = input("活動名稱: ").strip()
            year = int(input("年份 (預設 2026): ").strip() or "2026")
            status = input("狀態 (預設 '準備中'): ").strip() or "準備中"
            act = create_activity(name=name, year=year, status=status)
            print(f"\n[成功] 建立活動 ID {act['id']}")
        except Exception as e:
            print(f"\n[錯誤] {e}")
    elif choice == '3':
        try:
            act_id = int(input("刪除活動 ID: ").strip())
            deleted = delete_activity(act_id)
            if deleted:
                print(f"\n[成功] 已刪除活動 {deleted['name']}")
        except Exception as e:
            print(f"\n[錯誤] {e}")


def handle_decision_menu():
    print("\n--- 決策紀錄管理 (Decisions) ---")
    print("1. 查看所有決策")
    print("2. 新增決策")
    print("3. 修改決策")
    print("4. 刪除決策")
    choice = input("選擇操作 (1-4): ").strip()

    if choice == '1':
        decisions = list_decisions()
        print(f"\n--- 決策列表 (共 {len(decisions)} 筆) ---")
        for d in decisions:
            print(f"[ID: {d['id']}] 活動ID: {d['activity_id']} | 問題: {d['problem']} | 決策: {d['final_decision']} | 原因: {d['reason']}")
    elif choice == '2':
        try:
            act_id = select_or_create_activity_id()
            problem = input("討論問題: ").strip()
            options = input("候選方案 (JSON 陣列字串或逗點分隔): ").strip()
            if not options.startswith("["):
                import json
                opts_list = [o.strip() for o in options.split(",") if o.strip()]
                options = json.dumps(opts_list, ensure_ascii=False)
            final_decision = input("最終決策: ").strip()
            reason = input("決策原因: ").strip()
            source = input("來源 (例如 '第一次籌備會議'): ").strip() or "CLI 手動新增"
            created = create_decision(
                activity_id=act_id,
                problem=problem,
                options=options,
                final_decision=final_decision,
                reason=reason,
                source=source
            )
            print(f"\n[成功] 新增決策成功 ID {created['id']}")
        except Exception as e:
            print(f"\n[錯誤] {e}")
    elif choice == '3':
        try:
            d_id = int(input("修改決策 ID: ").strip())
            problem = input("新討論問題 (按 Enter 跳過): ").strip() or None
            final_decision = input("新最終決策 (按 Enter 跳過): ").strip() or None
            reason = input("新決策原因 (按 Enter 跳過): ").strip() or None
            changes = {}
            if problem: changes["problem"] = problem
            if final_decision: changes["final_decision"] = final_decision
            if reason: changes["reason"] = reason
            updated = update_decision(d_id, **changes)
            if updated:
                print("\n[成功] 決策紀錄已成功更新！")
            else:
                print("\n[!] 找不到該決策紀錄或無更新。")
        except Exception as e:
            print(f"\n[錯誤] {e}")
    elif choice == '4':
        try:
            d_id = int(input("刪除決策 ID: ").strip())
            deleted = delete_decision(d_id)
            if deleted:
                print(f"\n[成功] 已成功刪除決策 ID {d_id}")
            else:
                print("\n[!] 刪除失敗，找不到該決策紀錄。")
        except Exception as e:
            print(f"\n[錯誤] {e}")


def handle_schedule_menu():
    print("\n--- 流程日程管理 (Schedules) ---")
    print("1. 查看所有流程")
    print("2. 新增流程")
    print("3. 修改流程")
    print("4. 刪除流程")
    choice = input("選擇操作 (1-4): ").strip()

    if choice == '1':
        schedules = list_schedules()
        print(f"\n--- 流程列表 (共 {len(schedules)} 筆) ---")
        for s in schedules:
            print(f"[ID: {s['id']}] 活動ID: {s['activity_id']} | 名稱: {s['name']} | 開始時間: {s['start_time']} | 負責人: {s['owner']}")
    elif choice == '2':
        try:
            act_id = select_or_create_activity_id()
            name = input("流程名稱: ").strip()
            start_time = input("開始時間 (ISO 8601 或 '2026-09-15 09:00:00'): ").strip()
            location = input("地點 (預設 '主會場'): ").strip() or "主會場"
            owner = input("負責人 (預設 '總幹事'): ").strip() or "總幹事"
            notes = input("備註 (可跳過): ").strip() or ""
            category = input("分類 (預設 '開幕'): ").strip() or "開幕"
            created = create_schedule(
                activity_id=act_id,
                name=name,
                start_time=start_time,
                location=location,
                owner=owner,
                notes=notes,
                category=category
            )
            print(f"\n[成功] 新增流程日程成功 ID {created['id']}")
        except Exception as e:
            print(f"\n[錯誤] {e}")
    elif choice == '3':
        try:
            s_id = int(input("修改流程 ID: ").strip())
            name = input("新名稱 (按 Enter 跳過): ").strip() or None
            location = input("新地點 (按 Enter 跳過): ").strip() or None
            owner = input("新負責人 (按 Enter 跳過): ").strip() or None
            changes = {}
            if name: changes["name"] = name
            if location: changes["location"] = location
            if owner: changes["owner"] = owner
            updated = update_schedule(s_id, **changes)
            if updated:
                print("\n[成功] 流程日程已成功更新！")
            else:
                print("\n[!] 找不到該流程日程或無更新。")
        except Exception as e:
            print(f"\n[錯誤] {e}")
    elif choice == '4':
        try:
            s_id = int(input("刪除流程 ID: ").strip())
            deleted = delete_schedule(s_id)
            if deleted:
                print(f"\n[成功] 已成功刪除流程日程 ID {s_id}")
            else:
                print("\n[!] 刪除失敗，找不到該流程日程。")
        except Exception as e:
            print(f"\n[錯誤] {e}")


def handle_incident_menu():
    print("\n--- 突發事件管理 (Incidents) ---")
    print("1. 查看所有突發事件")
    print("2. 新增突發事件")
    print("3. 修改突發事件")
    print("4. 刪除突發事件")
    choice = input("選擇操作 (1-4): ").strip()

    if choice == '1':
        incidents = list_incidents()
        print(f"\n--- 突發事件列表 (共 {len(incidents)} 筆) ---")
        for inc in incidents:
            print(f"[ID: {inc['id']}] 活動ID: {inc['activity_id']} | 發生時間: {inc['occurred_at']} | 內容: {inc['content']}")
    elif choice == '2':
        try:
            act_id = select_or_create_activity_id()
            content = input("事件內容: ").strip()
            occurred_at = input("發生時間 (ISO 8601 或 '2026-09-15 10:30:00'): ").strip()
            cause = input("原因說明 (可跳過): ").strip() or None
            suggestion = input("處置建議 (可跳過): ").strip() or None
            created = create_incident(
                activity_id=act_id,
                content=content,
                occurred_at=occurred_at,
                cause=cause,
                suggestion=suggestion
            )
            print(f"\n[成功] 新增突發事件成功 ID {created['id']}")
        except Exception as e:
            print(f"\n[錯誤] {e}")
    elif choice == '3':
        try:
            inc_id = int(input("修改突發事件 ID: ").strip())
            content = input("新事件內容 (按 Enter 跳過): ").strip() or None
            cause = input("新原因說明 (按 Enter 跳過): ").strip() or None
            suggestion = input("新處置建議 (按 Enter 跳過): ").strip() or None
            changes = {}
            if content: changes["content"] = content
            if cause: changes["cause"] = cause
            if suggestion: changes["suggestion"] = suggestion
            updated = update_incident(inc_id, **changes)
            if updated:
                print("\n[成功] 突發事件紀錄已成功更新！")
            else:
                print("\n[!] 找不到該突發事件紀錄或無更新。")
        except Exception as e:
            print(f"\n[錯誤] {e}")
    elif choice == '4':
        try:
            inc_id = int(input("刪除突發事件 ID: ").strip())
            deleted = delete_incident(inc_id)
            if deleted:
                print(f"\n[成功] 已成功刪除突發事件紀錄 ID {inc_id}")
            else:
                print("\n[!] 刪除失敗，找不到該突發事件紀錄。")
        except Exception as e:
            print(f"\n[錯誤] {e}")


def handle_extra_menu():
    print("\n--- 決策 / 流程 / 突發事件管理選單 ---")
    print("1. 決策紀錄管理 (Decisions)")
    print("2. 流程日程管理 (Schedules)")
    print("3. 突發事件管理 (Incidents)")
    choice = input("選擇模組 (1-3): ").strip()

    if choice == '1':
        handle_decision_menu()
    elif choice == '2':
        handle_schedule_menu()
    elif choice == '3':
        handle_incident_menu()


def main():
    while True:
        print_main_menu()
        choice = input("[?] 請選擇操作 (0-9): ").strip()
        
        if choice == '1':
            handle_list_docs()
        elif choice == '2':
            handle_upload_doc()
        elif choice == '3':
            handle_delete_doc()
        elif choice == '4':
            handle_search_doc()
        elif choice == '5':
            handle_generate_answer()
        elif choice == '6':
            handle_meeting_menu()
        elif choice == '7':
            handle_task_menu()
        elif choice == '8':
            handle_activity_menu()
        elif choice == '9':
            handle_extra_menu()
        elif choice == '0' or choice.lower() == 'q':
            print("\n[INFO] 退出測試系統。")
            sys.exit(0)
        else:
            print("\n[!] 無效的選項，請重試。")


if __name__ == "__main__":
    main()
