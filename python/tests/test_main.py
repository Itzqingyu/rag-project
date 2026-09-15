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
from rag_project.document_processing.llm_service import (
    extract_structured_meeting_data,
    chat_with_context,
)
from rag_project.database import (
    get_doc_by_id,
    get_doc_by_path,
    create_session,
    get_session,
    list_sessions,
    update_session_title,
    delete_session,
    add_chat_message,
    get_chat_messages,
)
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
    print("  5. AI 生成回答測試 (LLM RAG QA)")
    print("  6. AI 結構化會議解析與寫入 (AI Extract & Commit)")
    print("  7. 對話會話與上下文記憶 (Chat Sessions & Multi-turn)")
    print("-" * 60)
    print(" [ 輕量化業務功能管理 ]")
    print("  8. 會議管理 (Meetings)")
    print("  9. 待辦事項 (Tasks)")
    print("  10. 活動管理 (Activities)")
    print("  11. 決策/流程/突發事件 (Decisions, Schedules, Incidents)")
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
        answer = chat_with_context(
            user_query=query,
            mode="rag",
            retrieved_chunks=retrieved_chunks
        )
        
        print("\n" + "="*45)
        print("🤖 AI 回答：")
        print("="*45)
        print(answer)
        print("="*45)
        
    except Exception as e:
        print(f"\n[!] 生成失敗: {e}")


def handle_ai_extract_and_commit():
    print("\n--- AI 結構化會議解析與寫入 (Preview & Commit) ---")
    docs = list_documents()
    if not docs:
        print("\n[!] 目前資料庫中無任何上傳文件，請先執行選項 2 上傳會議紀錄檔案。")
        return
        
    handle_list_docs()
    identifier = input("\n[?] 請輸入要進行 AI 結構化解析的檔案 ID 或檔案路徑:\n> ").strip().strip('\"\'')
    if not identifier:
        return
        
    record = None
    if identifier.isdigit():
        record = get_doc_by_id(int(identifier))
    else:
        record = get_doc_by_path(identifier)
        
    if not record:
        print(f"\n[!] 找不到該檔案紀錄: {identifier}")
        return
        
    markdown_content = record.get("markdown_content", "")
    if not markdown_content or not markdown_content.strip():
        print("\n[!] 該檔案無內文或尚未解析內文，無法進行 AI 結構化萃取。")
        return
        
    print(f"\n[*] 正在呼叫 LLM 進行全文本 1-shot 結構化萃取 ({record['filename']})...")
    try:
        extracted = extract_structured_meeting_data(markdown_content)
        import json
        print("\n" + "=" * 55)
        print("📋 【階段 1：預覽 JSON 數據 (Preview Data)】")
        print("=" * 55)
        print(json.dumps(extracted, ensure_ascii=False, indent=2))
        print("=" * 55)
        
        ans = input("\n[?] 是否將以上預覽資料原子化寫入 SQLite 資料庫 (meetings, decisions, tasks)？(y/n): ").strip().lower()
        if ans == 'y':
            act_id = select_or_create_activity_id()
            meeting_data = extracted.get("meeting", {})
            m_res = add_meeting(
                activity_id=act_id,
                name=meeting_data.get("name", "未命名會議"),
                start_time=meeting_data.get("start_time", ""),
                end_time=meeting_data.get("end_time", ""),
                location=meeting_data.get("location", ""),
                participants=meeting_data.get("participants", ""),
                content=meeting_data.get("content", ""),
                date=meeting_data.get("date", "")
            )
            m_id = m_res["id"]
            
            d_count = 0
            for d in extracted.get("decisions", []):
                opts = d.get("options", "[]")
                if isinstance(opts, list):
                    opts = json.dumps(opts, ensure_ascii=False)
                create_decision(
                    activity_id=act_id,
                    problem=d.get("problem", ""),
                    options=opts,
                    final_decision=d.get("final_decision", ""),
                    reason=d.get("reason", ""),
                    source=d.get("source", record["filename"]),
                    meeting_id=m_id
                )
                d_count += 1
                
            t_count = 0
            for t in extracted.get("tasks", []):
                add_task(
                    activity_id=act_id,
                    content=t.get("content", ""),
                    assignee=t.get("assignee", ""),
                    due_date=t.get("due_date", ""),
                    priority=t.get("priority", "中"),
                    meeting_id=m_id
                )
                t_count += 1
                
            print(f"\n[+] 【階段 2：寫入成功 (Commit Success)】！")
            print(f"    新增會議 ID: {m_id}")
            print(f"    新增決策數: {d_count} 筆")
            print(f"    新增待辦數: {t_count} 筆")
        else:
            print("\n[INFO] 已取消寫入。")
    except Exception as e:
        print(f"\n[!] 萃取與寫入失敗: {e}")


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


def handle_chat_session_menu():
    while True:
        print("\n" + "-" * 50)
        print("       對話會話 (Chat Session) 與記憶管理選單")
        print("-" * 50)
        print("  1. 列出所有 Sessions (List Sessions)")
        print("  2. 建立新 Session (Create Session)")
        print("  3. 進入 Session 互動對話 (Chat / RAG Mode Switch)")
        print("  4. 查看 Session 歷史對話 (View Message History)")
        print("  5. 修改 Session 標題 (Rename Session)")
        print("  6. 刪除 Session (Delete Session)")
        print("  0. 返回主選單 (Back)")
        print("-" * 50)
        sub_choice = input("[?] 請選擇 Session 操作 (0-6): ").strip()

        if sub_choice == '1':
            sessions = list_sessions()
            if not sessions:
                print("\n[INFO] 目前尚無任何對話會話。")
            else:
                print("\n--- 對話會話清單 ---")
                for s in sessions:
                    print(f"ID: {s['id']} | 標題: {s['title']} | 更新時間: {s['updated_at']}")
        elif sub_choice == '2':
            title = input("\n[?] 請輸入對話會話標題 (留空預設為 '新對話'):\n> ").strip()
            new_s = create_session(title=title if title else None)
            print(f"\n[OK] 成功建立會話 ID: {new_s['id']} | 標題: {new_s['title']}")
        elif sub_choice == '3':
            sessions = list_sessions()
            if not sessions:
                print("\n[!] 目前尚無任何 Session，請先建立新會話。")
                continue
            s_id_str = input("\n[?] 請輸入要進入的 Session ID:\n> ").strip()
            if not s_id_str.isdigit():
                print("[!] 請輸入有效的數字 ID。")
                continue
            session = get_session(int(s_id_str))
            if not session:
                print("[!] 找不到該 Session。")
                continue

            session_id = session["id"]
            current_mode = "chat"
            print(f"\n===== 進入會話 [{session['title']}] (ID: {session_id}) =====")
            print("提示: 輸入 '/mode chat' 切換為普通聊天模式")
            print("提示: 輸入 '/mode rag' 切換為 RAG 知識庫問答模式")
            print("提示: 輸入 '/exit' 退出本次對話互動")
            print(f"[目前模式]: {current_mode.upper()} (普通對話，基於上下文回答)")

            while True:
                user_input = input(f"\n[你 ({current_mode.upper()})]: ").strip()
                if not user_input:
                    continue
                if user_input.lower() == "/exit":
                    print("[INFO] 已結束對話。")
                    break
                if user_input.lower() == "/mode chat":
                    current_mode = "chat"
                    print("[切換模式] 已切換為普通聊天模式 (CHAT MODE) - 純上下文記憶，無 RAG 預處理")
                    continue
                if user_input.lower() == "/mode rag":
                    current_mode = "rag"
                    print("[切換模式] 已切換為知識庫模式 (RAG MODE) - 動態檢索最新片段並總結")
                    continue

                # 取得歷史上下文
                history_records = get_chat_messages(session_id)
                retrieved_chunks_texts = []
                retrieved_chunks_meta = []

                if current_mode == "rag":
                    print("[檢索中] 正在檢索相關文件切片...")
                    docs = search(user_input, top_k=3)
                    retrieved_chunks_texts = [doc.page_content for doc in docs]
                    retrieved_chunks_meta = [
                        {"content": doc.page_content, "metadata": doc.metadata} for doc in docs
                    ]
                    print(f"[檢索完成] 召回 {len(docs)} 個相關切片片段。")

                print("[AI 思考中] 生成回答...")
                assistant_reply = chat_with_context(
                    user_query=user_input,
                    history_messages=history_records,
                    mode=current_mode,
                    retrieved_chunks=retrieved_chunks_texts if current_mode == "rag" else None
                )

                # 寫入歷史
                add_chat_message(
                    session_id=session_id,
                    role="user",
                    content=user_input,
                    mode=current_mode,
                    retrieved_chunks=None
                )
                add_chat_message(
                    session_id=session_id,
                    role="assistant",
                    content=assistant_reply,
                    mode=current_mode,
                    retrieved_chunks=retrieved_chunks_meta if current_mode == "rag" else None
                )

                # 若標題為預設則自動更新標題
                current_sess = get_session(session_id)
                if current_sess and current_sess.get("title") == "新對話" and len(history_records) == 0:
                    auto_t = user_input[:20].replace("\n", " ")
                    update_session_title(session_id, auto_t)

                print(f"\n[AI 助手]:\n{assistant_reply}")
        elif sub_choice == '4':
            s_id_str = input("\n[?] 請輸入要查看的 Session ID:\n> ").strip()
            if not s_id_str.isdigit():
                print("[!] 請輸入有效的數字 ID。")
                continue
            messages = get_chat_messages(int(s_id_str))
            if not messages:
                print("\n[INFO] 該 Session 尚無任何對話訊息。")
            else:
                print(f"\n--- Session {s_id_str} 完整對話歷史 (共 {len(messages)} 則) ---")
                for m in messages:
                    role_str = "使用者" if m["role"] == "user" else "AI 助手"
                    mode_tag = f"[{m['mode'].upper()}]"
                    print(f"[{m['created_at']}] {mode_tag} {role_str}:")
                    print(f"  {m['content']}")
                    if m.get("retrieved_chunks"):
                        print(f"  (附帶檢索切片: {len(m['retrieved_chunks'])} 筆)")
                    print("-" * 40)
        elif sub_choice == '5':
            s_id_str = input("\n[?] 請輸入要修改的 Session ID:\n> ").strip()
            if not s_id_str.isdigit():
                print("[!] 請輸入有效的數字 ID。")
                continue
            new_title = input("[?] 請輸入新的標題:\n> ").strip()
            if new_title:
                updated = update_session_title(int(s_id_str), new_title)
                print(f"[{'OK' if updated else 'FAIL'}] 標題更新{'成功' if updated else '失敗'}")
        elif sub_choice == '6':
            s_id_str = input("\n[?] 請輸入要刪除的 Session ID:\n> ").strip()
            if not s_id_str.isdigit():
                print("[!] 請輸入有效的數字 ID。")
                continue
            confirm = input(f"確認要永久刪除 Session {s_id_str} 及其所有對話歷史嗎？(y/N): ").strip().lower()
            if confirm == 'y':
                deleted = delete_session(int(s_id_str))
                print(f"[{'OK' if deleted else 'FAIL'}] 刪除會話{'成功' if deleted else '失敗'}")
        elif sub_choice == '0':
            break


def main():
    while True:
        print_main_menu()
        choice = input("[?] 請選擇操作 (0-11): ").strip()
        
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
            handle_ai_extract_and_commit()
        elif choice == '7':
            handle_chat_session_menu()
        elif choice == '8':
            handle_meeting_menu()
        elif choice == '9':
            handle_task_menu()
        elif choice == '10':
            handle_activity_menu()
        elif choice == '11':
            handle_extra_menu()
        elif choice == '0' or choice.lower() == 'q':
            print("\n[INFO] 退出測試系統。")
            sys.exit(0)
        else:
            print("\n[!] 無效的選項，請重試。")


if __name__ == "__main__":
    main()

