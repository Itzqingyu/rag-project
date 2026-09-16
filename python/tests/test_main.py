import json
import os
import sys
from typing import Any, List, Optional
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
    file_path = input("\n[?] 請輸入要上傳的檔案絕對路徑 (支援 MD, TXT, PDF, DOCX，如 tests/test_data/ubuntu.pdf):\n> ").strip().strip('\"\'')
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
        print("\n" + "=" * 55)
        print("【階段 1：預覽 JSON 數據 (Preview Data)】")
        print("=" * 55)
        print(json.dumps(extracted, ensure_ascii=False, indent=2))
        print("=" * 55)
        
        ans = input(
            "\n[?] 是否將以上預覽資料逐筆寫入 SQLite？"
            "（若中途失敗，先前成功的資料會保留）(y/n): "
        ).strip().lower()
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
                date=meeting_data.get("date", ""),
                source_document_id=record["id"],
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
                
            print(f"\n[+] 【階段 2：逐筆寫入完成 (Commit Complete)】！")
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
    print("      可用活動列表 (Activity Table)")
    print("-" * 55)
    if not activities:
        print("  (目前資料庫無任何活動紀錄)")
    else:
        for number, act in enumerate(activities, 1):
            print(
                f"  {number}. {act['name']} ({act['year']}) "
                f"[{act['status']}] 地點: {act['venue'] or '未填'} "
                f"(ID: {act['id']})"
            )
    print("-" * 55)
    return activities


def _create_activity_from_cli() -> int:
    """建立 Activity 並回傳 ID，供所有子模組共用目前活動脈絡。"""
    name = input("輸入活動名稱: ").strip()
    year_str = input("輸入活動年份 (預設 2026): ").strip() or "2026"
    status = input("輸入活動狀態 (預設 '準備中'): ").strip() or "準備中"
    created = create_activity(name=name, year=int(year_str), status=status)
    print(f"[成功] 建立活動: {created['name']} (ID: {created['id']})")
    return created["id"]


def select_or_create_activity_id() -> int:
    """以畫面編號選擇 Activity；沒有 Activity 時明確先建立一筆。"""
    activities = print_activities_table()
    if not activities:
        print("\n[提示] 目前沒有 Activity，必須先建立後才能新增子資料。")
        return _create_activity_from_cli()

    selected = input("請輸入活動前方編號: ").strip()
    if not selected.isdigit() or not 1 <= int(selected) <= len(activities):
        raise ValueError("活動選項不存在")
    return activities[int(selected) - 1]["id"]


_KEEP = object()


def _choose_fixed_value(
    label: str,
    values: List[str],
    *,
    default: Optional[str] = None,
    editing: bool = False,
) -> Optional[str]:
    """將既有 enum 以編號呈現；修改時 Enter 代表保留原值。"""
    print(f"{label}:")
    for number, value in enumerate(values, 1):
        print(f"  {number}. {value}")
    hint = "按 Enter 保留" if editing else f"預設 {default or values[0]}"
    selected = input(f"請選擇 ({hint}): ").strip()
    if not selected:
        return None if editing else (default or values[0])
    if not selected.isdigit() or not 1 <= int(selected) <= len(values):
        raise ValueError(f"{label} 選項不存在")
    return values[int(selected) - 1]


def _choose_record(
    records: List[dict],
    entity_name: str,
    summary_field: str,
) -> Optional[dict]:
    """只從目前 Activity 的資料清單選擇，避免用全域 ID 誤操作。"""
    if not records:
        print(f"[提示] 此 Activity 尚無 {entity_name}。")
        return None
    for number, record in enumerate(records, 1):
        print(
            f"  {number}. {record.get(summary_field, '')} "
            f"(ID: {record['id']})"
        )
    selected = input(f"請輸入 {entity_name} 前方編號: ").strip()
    if not selected.isdigit() or not 1 <= int(selected) <= len(records):
        raise ValueError(f"{entity_name} 選項不存在")
    return records[int(selected) - 1]


def _choose_relation_id(
    records: List[dict],
    entity_name: str,
    summary_field: str,
    *,
    editing: bool = False,
) -> Any:
    """用清單設定可選外鍵；修改時 /clear 清除、Enter 保留。"""
    if records:
        for number, record in enumerate(records, 1):
            print(
                f"  {number}. {record.get(summary_field, '')} "
                f"(ID: {record['id']})"
            )
    else:
        print(f"  (此 Activity 尚無可關聯的 {entity_name})")
    hint = "Enter 保留，/clear 清除" if editing else "Enter 不關聯"
    selected = input(f"選擇關聯 {entity_name} ({hint}): ").strip()
    if editing and not selected:
        return _KEEP
    if selected == "/clear" or (not editing and not selected):
        return None
    if not selected.isdigit() or not 1 <= int(selected) <= len(records):
        raise ValueError(f"{entity_name} 選項不存在")
    return records[int(selected) - 1]["id"]


def _text_change(label: str, *, clear_to: Any = _KEEP) -> Any:
    """更新欄位時 Enter 保留；允許清除的欄位以 /clear 明確處理。"""
    hint = "Enter 保留"
    if clear_to is not _KEEP:
        hint += "，/clear 清除"
    value = input(f"{label} ({hint}): ").strip()
    if not value:
        return _KEEP
    if value == "/clear":
        if clear_to is _KEEP:
            raise ValueError(f"{label} 為必填欄位，不能清除")
        return clear_to
    return value


def _collect_changes(specs: List[tuple]) -> dict:
    changes = {}
    for field_name, label, clear_to in specs:
        value = _text_change(label, clear_to=clear_to)
        if value is not _KEEP:
            changes[field_name] = value
    return changes


def _normalize_options(raw: str) -> str:
    """接受 JSON array 或逗號分隔輸入，統一交給 Decision service。"""
    if raw.lstrip().startswith("["):
        parsed = json.loads(raw)
        if not isinstance(parsed, list):
            raise ValueError("options JSON 必須是 array")
        return json.dumps(parsed, ensure_ascii=False)
    return json.dumps(
        [item.strip() for item in raw.split(",") if item.strip()],
        ensure_ascii=False,
    )


def handle_meeting_menu(activity_id: Optional[int] = None):
    try:
        activity_id = activity_id or select_or_create_activity_id()
    except Exception as exc:
        print(f"\n[錯誤] {exc}")
        return
    print(f"\n--- 會議管理 | {get_activity_label(activity_id)} ---")
    print("1. 新增會議")
    print("2. 查看會議列表")
    print("3. 修改會議")
    print("4. 刪除會議")
    print("0. 回上一層")
    choice = input("選擇操作 (0-4): ").strip()

    if choice == "0":
        return

    if choice == '1':
        try:
            name = input("會議名稱: ").strip()
            start_time = input("開始時間 (可跳過): ").strip()
            end_time = input("結束時間 (可跳過): ").strip()
            location = input("地點 (可跳過): ").strip()
            participants = input("參與人員 (可跳過): ").strip()
            content = input("會議內容: ").strip()
            res = add_meeting(
                activity_id=activity_id,
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
        meetings = get_meetings(activity_id=activity_id)
        print(f"\n--- 會議列表 (共 {len(meetings)} 筆) ---")
        for m in meetings:
            print(
                f"[ID: {m['id']}] 名稱: {m['name']} | "
                f"時間: {m['start_time']}~{m['end_time']} | "
                f"來源文件: {m['source_document_id'] or '無'}"
            )

    elif choice == '3':
        try:
            meeting = _choose_record(
                get_meetings(activity_id=activity_id), "Meeting", "name"
            )
            if not meeting:
                return
            changes = _collect_changes([
                ("name", "新名稱", _KEEP),
                ("start_time", "新開始時間", ""),
                ("end_time", "新結束時間", ""),
                ("location", "新地點", ""),
                ("participants", "新參與人員", ""),
                ("content", "新會議內容", ""),
            ])
            if not changes:
                print("\n[提示] 沒有變更任何欄位。")
            elif update_meeting(meeting["id"], **changes):
                print("\n[成功] 會議更新成功！")
        except Exception as e:
            print(f"\n[錯誤] {e}")

    elif choice == '4':
        try:
            meeting = _choose_record(
                get_meetings(activity_id=activity_id), "Meeting", "name"
            )
            if meeting and delete_meeting(meeting["id"]):
                print("\n[成功] 會議已刪除！")
        except Exception as e:
            print(f"\n[錯誤] {e}")


def handle_task_menu(activity_id: Optional[int] = None):
    try:
        activity_id = activity_id or select_or_create_activity_id()
    except Exception as exc:
        print(f"\n[錯誤] {exc}")
        return
    print(f"\n--- 待辦事項 | {get_activity_label(activity_id)} ---")
    print("1. 新增待辦")
    print("2. 查看待辦列表")
    print("3. 修改待辦")
    print("4. 刪除待辦")
    print("0. 回上一層")
    choice = input("選擇操作 (0-4): ").strip()

    if choice == "0":
        return

    if choice == '1':
        try:
            content = input("待辦內容: ").strip()
            assignee = input("負責人: ").strip()
            due_date = input("期限: ").strip()
            priority = _choose_fixed_value(
                "優先級", ["高", "中", "低"], default="中"
            )
            status = _choose_fixed_value(
                "狀態", ["pending", "completed"], default="pending"
            )
            meeting_id = _choose_relation_id(
                get_meetings(activity_id=activity_id), "Meeting", "name"
            )
            res = add_task(
                activity_id=activity_id,
                content=content,
                assignee=assignee,
                due_date=due_date,
                priority=priority or "中",
                status=status or "pending",
                meeting_id=meeting_id,
            )
            print(f"\n[成功] 新增待辦成功 ID {res['id']}")
        except Exception as e:
            print(f"\n[錯誤] {e}")

    elif choice == '2':
        tasks = get_tasks(activity_id=activity_id)
        print(f"\n--- 待辦列表 (共 {len(tasks)} 筆) ---")
        for t in tasks:
            print(
                f"[ID: {t['id']}] 狀態: [{t['status']}] | "
                f"優先級: [{t['priority']}] | 內容: {t['content']} | "
                f"Meeting: {t['meeting_id'] or '無'}"
            )

    elif choice == '3':
        try:
            task = _choose_record(
                get_tasks(activity_id=activity_id), "Task", "content"
            )
            if not task:
                return
            changes = _collect_changes([
                ("content", "新待辦內容", _KEEP),
                ("assignee", "新負責人", ""),
                ("due_date", "新期限", ""),
            ])
            priority = _choose_fixed_value(
                "新優先級", ["高", "中", "低"], editing=True
            )
            status = _choose_fixed_value(
                "新狀態", ["pending", "completed"], editing=True
            )
            meeting_id = _choose_relation_id(
                get_meetings(activity_id=activity_id),
                "Meeting",
                "name",
                editing=True,
            )
            if priority is not None:
                changes["priority"] = priority
            if status is not None:
                changes["status"] = status
            if meeting_id is not _KEEP:
                changes["meeting_id"] = meeting_id
            if not changes:
                print("\n[提示] 沒有變更任何欄位。")
            elif update_task(task["id"], **changes):
                print("\n[成功] 待辦更新成功！")
        except Exception as e:
            print(f"\n[錯誤] {e}")

    elif choice == '4':
        try:
            task = _choose_record(
                get_tasks(activity_id=activity_id), "Task", "content"
            )
            if task and delete_task(task["id"]):
                print("\n[成功] 待辦已刪除！")
        except Exception as e:
            print(f"\n[錯誤] {e}")


def handle_activity_menu():
    print("\n--- 活動管理 (Activities) ---")
    print("1. 查看所有活動")
    print("2. 新增活動")
    print("3. 修改活動")
    print("4. 刪除活動")
    print("5. 選擇 Activity 並管理其子資料")
    print("0. 回主選單")
    choice = input("選擇操作 (0-5): ").strip()

    if choice == "0":
        return

    if choice == '1':
        print_activities_table()
    elif choice == '2':
        try:
            _create_activity_from_cli()
        except Exception as e:
            print(f"\n[錯誤] {e}")
    elif choice == '3':
        try:
            activity = _choose_record(
                print_activities_table(), "Activity", "name"
            )
            if not activity:
                return
            changes = _collect_changes([
                ("name", "新活動名稱", _KEEP),
                ("status", "新狀態", _KEEP),
                ("start_date", "新開始日期", None),
                ("end_date", "新結束日期", None),
                ("venue", "新地點", None),
                ("activity_type", "新活動類型", None),
                ("coordinator", "新總召", None),
            ])
            year = input("新年份 (Enter 保留): ").strip()
            attendees = input("新預計人數 (Enter 保留，/clear 清除): ").strip()
            budget = input("新預算 (Enter 保留，/clear 清除): ").strip()
            if year:
                changes["year"] = int(year)
            if attendees:
                changes["expected_attendees"] = (
                    None if attendees == "/clear" else int(attendees)
                )
            if budget:
                changes["budget"] = None if budget == "/clear" else int(budget)
            if not changes:
                print("\n[提示] 沒有變更任何欄位。")
            else:
                updated = update_activity(activity["id"], **changes)
                print(f"\n[成功] 已更新活動 {updated['name']}")
        except Exception as e:
            print(f"\n[錯誤] {e}")
    elif choice == '4':
        try:
            activity = _choose_record(
                print_activities_table(), "Activity", "name"
            )
            if not activity:
                return
            deleted = delete_activity(activity["id"])
            if deleted:
                print(f"\n[成功] 已刪除活動 {deleted['name']}")
        except Exception as e:
            print(f"\n[錯誤] {e}")
    elif choice == '5':
        try:
            handle_activity_workspace(select_or_create_activity_id())
        except Exception as e:
            print(f"\n[錯誤] {e}")


def handle_activity_workspace(activity_id: int):
    """固定目前 Activity，連續操作其下五種子資料。"""
    while True:
        print(f"\n--- Activity 工作區 | {get_activity_label(activity_id)} ---")
        print("1. Meeting")
        print("2. Task")
        print("3. Decision")
        print("4. Schedule")
        print("5. Incident")
        print("0. 回主選單")
        choice = input("選擇子模組 (0-5): ").strip()
        if choice == "1":
            handle_meeting_menu(activity_id)
        elif choice == "2":
            handle_task_menu(activity_id)
        elif choice == "3":
            handle_decision_menu(activity_id)
        elif choice == "4":
            handle_schedule_menu(activity_id)
        elif choice == "5":
            handle_incident_menu(activity_id)
        elif choice == "0":
            return
        else:
            print("[提示] 無效選項。")


def handle_decision_menu(activity_id: Optional[int] = None):
    try:
        activity_id = activity_id or select_or_create_activity_id()
    except Exception as exc:
        print(f"\n[錯誤] {exc}")
        return
    print(f"\n--- 決策紀錄 | {get_activity_label(activity_id)} ---")
    print("1. 查看所有決策")
    print("2. 新增決策")
    print("3. 修改決策")
    print("4. 刪除決策")
    print("0. 回上一層")
    choice = input("選擇操作 (0-4): ").strip()

    if choice == "0":
        return

    if choice == '1':
        decisions = list_decisions(activity_id=activity_id)
        print(f"\n--- 決策列表 (共 {len(decisions)} 筆) ---")
        for d in decisions:
            print(
                f"[ID: {d['id']}] 問題: {d['problem']} | "
                f"決策: {d['final_decision']} | 狀態: {d['confirmation_status']} | "
                f"Meeting: {d['meeting_id'] or '無'}"
            )
    elif choice == '2':
        try:
            problem = input("討論問題: ").strip()
            options = _normalize_options(
                input("候選方案 (JSON array 或逗號分隔): ").strip()
            )
            final_decision = input("最終決策: ").strip()
            reason = input("決策原因: ").strip()
            source = input("來源 (例如 '第一次籌備會議'): ").strip() or "CLI 手動新增"
            confirmation_status = _choose_fixed_value(
                "確認狀態", ["pending", "confirmed"], default="pending"
            )
            meeting_id = _choose_relation_id(
                get_meetings(activity_id=activity_id), "Meeting", "name"
            )
            created = create_decision(
                activity_id=activity_id,
                problem=problem,
                options=options,
                final_decision=final_decision,
                reason=reason,
                source=source,
                confirmation_status=confirmation_status or "pending",
                meeting_id=meeting_id,
            )
            print(f"\n[成功] 新增決策成功 ID {created['id']}")
        except Exception as e:
            print(f"\n[錯誤] {e}")
    elif choice == '3':
        try:
            decision = _choose_record(
                list_decisions(activity_id=activity_id), "Decision", "problem"
            )
            if not decision:
                return
            changes = _collect_changes([
                ("problem", "新討論問題", _KEEP),
                ("final_decision", "新最終決策", _KEEP),
                ("reason", "新決策原因", _KEEP),
                ("source", "新來源", _KEEP),
            ])
            raw_options = input("新候選方案 (Enter 保留；JSON array 或逗號分隔): ").strip()
            if raw_options:
                changes["options"] = _normalize_options(raw_options)
            confirmation_status = _choose_fixed_value(
                "新確認狀態", ["pending", "confirmed"], editing=True
            )
            meeting_id = _choose_relation_id(
                get_meetings(activity_id=activity_id),
                "Meeting",
                "name",
                editing=True,
            )
            if confirmation_status is not None:
                changes["confirmation_status"] = confirmation_status
            if meeting_id is not _KEEP:
                changes["meeting_id"] = meeting_id
            if not changes:
                print("\n[提示] 沒有變更任何欄位。")
                return
            updated = update_decision(decision["id"], **changes)
            if updated:
                print("\n[成功] 決策紀錄已成功更新！")
            else:
                print("\n[!] 找不到該決策紀錄或無更新。")
        except Exception as e:
            print(f"\n[錯誤] {e}")
    elif choice == '4':
        try:
            decision = _choose_record(
                list_decisions(activity_id=activity_id), "Decision", "problem"
            )
            if not decision:
                return
            deleted = delete_decision(decision["id"])
            if deleted:
                print(f"\n[成功] 已成功刪除決策 ID {decision['id']}")
            else:
                print("\n[!] 刪除失敗，找不到該決策紀錄。")
        except Exception as e:
            print(f"\n[錯誤] {e}")


def handle_schedule_menu(activity_id: Optional[int] = None):
    try:
        activity_id = activity_id or select_or_create_activity_id()
    except Exception as exc:
        print(f"\n[錯誤] {exc}")
        return
    print(f"\n--- 流程日程 | {get_activity_label(activity_id)} ---")
    print("1. 查看所有流程")
    print("2. 新增流程")
    print("3. 修改流程")
    print("4. 刪除流程")
    print("0. 回上一層")
    choice = input("選擇操作 (0-4): ").strip()

    if choice == "0":
        return

    if choice == '1':
        schedules = list_schedules(activity_id=activity_id)
        print(f"\n--- 流程列表 (共 {len(schedules)} 筆) ---")
        for s in schedules:
            print(
                f"[ID: {s['id']}] 名稱: {s['name']} | "
                f"開始時間: {s['start_time']} | 負責人: {s['owner']} | "
                f"Meeting: {s['meeting_id'] or '無'}"
            )
    elif choice == '2':
        try:
            name = input("流程名稱: ").strip()
            start_time = input("開始時間 (ISO 8601 或 '2026-09-15 09:00:00'): ").strip()
            end_time = input("結束時間 (可跳過): ").strip() or None
            location = input("地點 (預設 '主會場'): ").strip() or "主會場"
            owner = input("負責人 (預設 '總幹事'): ").strip() or "總幹事"
            notes = input("備註 (可跳過): ").strip() or "無"
            category = input("分類: ").strip()
            meeting_id = _choose_relation_id(
                get_meetings(activity_id=activity_id), "Meeting", "name"
            )
            created = create_schedule(
                activity_id=activity_id,
                name=name,
                start_time=start_time,
                end_time=end_time,
                location=location,
                owner=owner,
                notes=notes,
                category=category,
                meeting_id=meeting_id,
            )
            print(f"\n[成功] 新增流程日程成功 ID {created['id']}")
        except Exception as e:
            print(f"\n[錯誤] {e}")
    elif choice == '3':
        try:
            schedule = _choose_record(
                list_schedules(activity_id=activity_id), "Schedule", "name"
            )
            if not schedule:
                return
            changes = _collect_changes([
                ("name", "新名稱", _KEEP),
                ("start_time", "新開始時間", _KEEP),
                ("end_time", "新結束時間", None),
                ("location", "新地點", _KEEP),
                ("owner", "新負責人", _KEEP),
                ("notes", "新備註", _KEEP),
                ("category", "新分類", _KEEP),
            ])
            meeting_id = _choose_relation_id(
                get_meetings(activity_id=activity_id),
                "Meeting",
                "name",
                editing=True,
            )
            if meeting_id is not _KEEP:
                changes["meeting_id"] = meeting_id
            if not changes:
                print("\n[提示] 沒有變更任何欄位。")
                return
            updated = update_schedule(schedule["id"], **changes)
            if updated:
                print("\n[成功] 流程日程已成功更新！")
            else:
                print("\n[!] 找不到該流程日程或無更新。")
        except Exception as e:
            print(f"\n[錯誤] {e}")
    elif choice == '4':
        try:
            schedule = _choose_record(
                list_schedules(activity_id=activity_id), "Schedule", "name"
            )
            if not schedule:
                return
            deleted = delete_schedule(schedule["id"])
            if deleted:
                print(f"\n[成功] 已成功刪除流程日程 ID {schedule['id']}")
            else:
                print("\n[!] 刪除失敗，找不到該流程日程。")
        except Exception as e:
            print(f"\n[錯誤] {e}")


def handle_incident_menu(activity_id: Optional[int] = None):
    try:
        activity_id = activity_id or select_or_create_activity_id()
    except Exception as exc:
        print(f"\n[錯誤] {exc}")
        return
    print(f"\n--- 突發事件 | {get_activity_label(activity_id)} ---")
    print("1. 查看所有突發事件")
    print("2. 新增突發事件")
    print("3. 修改突發事件")
    print("4. 刪除突發事件")
    print("0. 回上一層")
    choice = input("選擇操作 (0-4): ").strip()

    if choice == "0":
        return

    if choice == '1':
        incidents = list_incidents(activity_id=activity_id)
        print(f"\n--- 突發事件列表 (共 {len(incidents)} 筆) ---")
        for inc in incidents:
            print(
                f"[ID: {inc['id']}] 發生時間: {inc['occurred_at']} | "
                f"內容: {inc['content']} | Schedule: {inc['schedule_id'] or '無'}"
            )
    elif choice == '2':
        try:
            content = input("事件內容: ").strip()
            occurred_at = input("發生時間 (ISO 8601 或 '2026-09-15 10:30:00'): ").strip()
            cause = input("原因說明 (可跳過): ").strip() or None
            suggestion = input("處置建議 (可跳過): ").strip() or None
            schedule_id = _choose_relation_id(
                list_schedules(activity_id=activity_id), "Schedule", "name"
            )
            created = create_incident(
                activity_id=activity_id,
                content=content,
                occurred_at=occurred_at,
                schedule_id=schedule_id,
                cause=cause,
                suggestion=suggestion,
            )
            print(f"\n[成功] 新增突發事件成功 ID {created['id']}")
        except Exception as e:
            print(f"\n[錯誤] {e}")
    elif choice == '3':
        try:
            incident = _choose_record(
                list_incidents(activity_id=activity_id), "Incident", "content"
            )
            if not incident:
                return
            changes = _collect_changes([
                ("content", "新事件內容", _KEEP),
                ("occurred_at", "新發生時間", _KEEP),
                ("cause", "新原因說明", None),
                ("suggestion", "新處置建議", None),
            ])
            schedule_id = _choose_relation_id(
                list_schedules(activity_id=activity_id),
                "Schedule",
                "name",
                editing=True,
            )
            if schedule_id is not _KEEP:
                changes["schedule_id"] = schedule_id
            if not changes:
                print("\n[提示] 沒有變更任何欄位。")
                return
            updated = update_incident(incident["id"], **changes)
            if updated:
                print("\n[成功] 突發事件紀錄已成功更新！")
            else:
                print("\n[!] 找不到該突發事件紀錄或無更新。")
        except Exception as e:
            print(f"\n[錯誤] {e}")
    elif choice == '4':
        try:
            incident = _choose_record(
                list_incidents(activity_id=activity_id), "Incident", "content"
            )
            if not incident:
                return
            deleted = delete_incident(incident["id"])
            if deleted:
                print(f"\n[成功] 已成功刪除突發事件紀錄 ID {incident['id']}")
            else:
                print("\n[!] 刪除失敗，找不到該突發事件紀錄。")
        except Exception as e:
            print(f"\n[錯誤] {e}")


def handle_extra_menu(activity_id: Optional[int] = None):
    try:
        activity_id = activity_id or select_or_create_activity_id()
    except Exception as exc:
        print(f"\n[錯誤] {exc}")
        return
    print(
        "\n--- 決策 / 流程 / 突發事件 | "
        f"{get_activity_label(activity_id)} ---"
    )
    print("1. 決策紀錄管理 (Decisions)")
    print("2. 流程日程管理 (Schedules)")
    print("3. 突發事件管理 (Incidents)")
    print("0. 回主選單")
    choice = input("選擇模組 (0-3): ").strip()

    if choice == "0":
        return

    if choice == '1':
        handle_decision_menu(activity_id)
    elif choice == '2':
        handle_schedule_menu(activity_id)
    elif choice == '3':
        handle_incident_menu(activity_id)


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
                try:
                    assistant_reply = chat_with_context(
                        user_query=user_input,
                        history_messages=history_records,
                        mode=current_mode,
                        retrieved_chunks=retrieved_chunks_texts if current_mode == "rag" else None
                    )
                except Exception as exc:
                    print(f"\n[!] AI 呼叫失敗: {exc}")
                    print("[提示] 本次失敗訊息未寫入資料庫，不會影響後續對話記憶。")
                    continue

                # 僅在成功獲得回答後寫入歷史
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

