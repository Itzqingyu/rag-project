import json
import os
import sys
from typing import List

# 將 src 目錄加入 Python 搜尋路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rag_project.decision import service as decision_service
from rag_project.schedule import service as schedule_service
from rag_project.incident import service as incident_service

from rag_project.activity.service import (
    create_activity,
    get_activity,
    list_activities,
    update_activity,
    delete_activity,
)
from rag_project.meeting_task import (
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
        for act in activities:
            print(f"  [ ID: {act['id']} ] -> {act['name']} ({act['year']}) [{act['status']}] 地點: {act['venue'] or '未填'}")
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

def print_menu():
    print("\n" + "=" * 60)
    print("      Activity, Meeting, Task, Decision, Schedule & Incident CLI 測試選單")
    print("=" * 60)
    print("[ 1 ] 新增會議 (Add Meeting)")
    print("      - 名稱, 開始/結束時間, 地點, 參與人員, 內容文字")
    print("[ 2 ] 查看會議列表 (List Meetings)")
    print("[ 3 ] 修改會議 (Update Meeting)")
    print("[ 4 ] 刪除會議 (Delete Meeting)")
    print("-" * 60)
    print("[ 5 ] 新增待辦 (Add Task)")
    print("      - 內容, 負責人, 期限, 優先級(高/中/低), 綁定活動與會議")
    print("[ 6 ] 查看待辦列表 (List Tasks)")
    print("[ 7 ] 修改待辦 (Update Task)")
    print("[ 8 ] 刪除待辦 (Delete Task)")
    print("-" * 60)
    print("[ 9 ] 活動管理 (Activity CRUD: 查看/新增/修改/刪除)")
    print("[ 10 ] Decision 管理")
    print("[ 11 ] Schedule 管理")
    print("[ 12 ] Incident 管理")
    print("[ 0 ] 離開 (Exit)")
    print("=" * 60)

def handle_activity_menu():
    while True:
        print("\n--- 活動管理 (Activity CRUD) ---")
        print("1. 查看所有活動")
        print("2. 新增活動")
        print("3. 修改活動")
        print("4. 刪除活動")
        print("0. 返回主選單")
        choice = input("請選擇操作 (0-4): ").strip()

        if choice == '1':
            print_activities_table()
        elif choice == '2':
            try:
                name = input("輸入活動名稱: ").strip()
                year_str = input("輸入年份 (預設 2026): ").strip() or "2026"
                status = input("輸入狀態 (預設 '準備中'): ").strip() or "準備中"
                venue = input("輸入地點 (可跳過): ").strip() or None
                act_type = input("輸入類型 (可跳過): ").strip() or None
                coordinator = input("輸入負責人 (可跳過): ").strip() or None
                act = create_activity(
                    name=name,
                    year=int(year_str),
                    status=status,
                    venue=venue,
                    activity_type=act_type,
                    coordinator=coordinator,
                )
                print(f"\n[成功] 已建立活動 ID {act['id']}: {act['name']}")
            except Exception as e:
                print(f"\n[錯誤] {e}")
        elif choice == '3':
            try:
                act_id = int(input("輸入欲修改的活動 ID: ").strip())
                existing = get_activity(act_id)
                if not existing:
                    print(f"\n[失敗] 找不到活動 ID {act_id}")
                    continue
                print(f"目前活動: {existing['name']} (狀態: {existing['status']})")
                name = input("新名稱 (不修改按 Enter): ").strip() or None
                status = input("新狀態 (不修改按 Enter): ").strip() or None
                venue = input("新地點 (不修改按 Enter): ").strip() or None
                changes = {}
                if name: changes["name"] = name
                if status: changes["status"] = status
                if venue: changes["venue"] = venue
                if changes:
                    updated = update_activity(act_id, **changes)
                    print(f"\n[成功] 活動更新成功: {updated}")
                else:
                    print("\n[失敗] 無修改項目")
            except Exception as e:
                print(f"\n[錯誤] {e}")
        elif choice == '4':
            try:
                act_id = int(input("輸入欲刪除的活動 ID: ").strip())
                deleted = delete_activity(act_id)
                if deleted:
                    print(f"\n[成功] 已刪除活動: {deleted['name']}")
                else:
                    print(f"\n[失敗] 找不到活動 ID {act_id}")
            except Exception as e:
                print(f"\n[錯誤] {e}")
        elif choice == '0':
            break

# 三個模組共用選單流程；欄位順序對應使用者輸入順序。
MANAGEMENT_MODULES = {
    '10': ("Decision", decision_service, "decision", [
        ("problem", "問題"), ("options", "候選方案"),
        ("final_decision", "最終決策"), ("reason", "原因"),
        ("source", "來源"),
        ("confirmation_status", "確認狀態 (pending/confirmed，預設 pending)"),
        ("meeting_id", "關聯會議 ID"),
    ]),
    '11': ("Schedule", schedule_service, "schedule", [
        ("name", "流程名稱"),
        ("start_time", "開始時間 (YYYY-MM-DD HH:MM)"),
        ("end_time", "結束時間 (YYYY-MM-DD HH:MM)"),
        ("location", "地點"), ("owner", "負責人"),
        ("notes", "備註"), ("category", "分類"),
        ("meeting_id", "關聯會議 ID"),
    ]),
    '12': ("Incident", incident_service, "incident", [
        ("content", "事件內容"),
        ("occurred_at", "發生時間 (YYYY-MM-DD HH:MM)"),
        ("schedule_id", "關聯流程 ID"),
        ("cause", "原因"), ("suggestion", "建議"),
    ]),
}


def input_management_fields(fields, editing=False):
    """Enter 保留原值；只有服務允許為空的欄位才能用 /clear 清空。"""
    optional_fields = {"meeting_id", "schedule_id", "end_time", "cause", "suggestion"}
    values = {}
    for field, label in fields:
        optional = field in optional_fields
        if editing:
            hint = "不修改按 Enter" + ("，/clear 清空" if optional else "")
        else:
            hint = "可跳過" if optional else "必填"
            if field in {"options", "confirmation_status"}:
                hint = "可按 Enter 使用預設"
        if field == "options":
            # 逐項收集同一筆決策的方案，交由 JSON 編碼處理引號等字元。
            print("逐項輸入候選方案；輸入新方案會替換整份原方案列表。" if editing
                  else "逐項輸入候選方案；直接按 Enter 結束，無方案時儲存 []。")
            options = []
            while True:
                option = input("輸入方案 (Enter 結束): ").strip()
                if not option:
                    break
                if option == '/clear':
                    print("[提示] 候選方案不支援 /clear。")
                    continue
                options.append(option)
            if options or not editing:
                values[field] = json.dumps(options, ensure_ascii=False)
            continue
        while True:
            value = input(f"{label} ({hint}): ").strip()
            if value == '/clear' and not (editing and optional):
                print("[提示] /clear 僅用於修改可選欄位。")
                continue
            break
        if editing and not value:
            continue
        if value == '/clear' or (optional and not value):
            values[field] = None
        elif field in {"meeting_id", "schedule_id"}:
            values[field] = int(value)
        else:
            values[field] = value or ("pending" if field == "confirmation_status" else "")
    return values


def handle_management_menu(choice):
    title, service, entity, fields = MANAGEMENT_MODULES[choice]
    list_records = getattr(service, f"list_{entity}s")
    activity_id = None
    while True:
        try:
            if activity_id is None:
                print_activities_table()
                selected = input("輸入活動 ID (Enter 返回主選單): ").strip()
                if not selected:
                    return
                candidate = int(selected)
                if not get_activity(candidate):
                    print("[失敗] 找不到該活動，請重新選擇。")
                    continue
                activity_id = candidate

            print(f"\n--- {title} 管理 | {get_activity_label(activity_id)} ---")
            records = list_records(activity_id=activity_id)
            print(f"目前資料 (共 {len(records)} 筆):")
            for record in records:
                print(f"  [ID: {record['id']}]", json.dumps(record, ensure_ascii=False))
            print("1. 新增\n2. 查看單筆\n3. 修改\n4. 刪除\n5. 切換活動\n0. 返回主選單")
            action = input("請選擇操作 (0-5): ").strip()
            if action == '0':
                return
            if action == '5':
                activity_id = None
                continue
            if action == '1':
                values = input_management_fields(fields)
                created = getattr(service, f"create_{entity}")(activity_id=activity_id, **values)
                print("[成功] 已新增:", json.dumps(created, ensure_ascii=False))
            elif action in {'2', '3', '4'}:
                record_id = int(input(f"輸入 {title} ID: ").strip())
                record = getattr(service, f"get_{entity}")(record_id)
                # ID 查詢本身不限制活動，讀取後必須檢查，避免跨活動操作。
                if not record or record['activity_id'] != activity_id:
                    print("[失敗] 該活動底下找不到此筆資料。")
                    continue
                print("目前資料:", json.dumps(record, ensure_ascii=False))
                if action == '3':
                    changes = input_management_fields(fields, editing=True)
                    if not changes:
                        print("[提示] 無修改項目。")
                        continue
                    updated = getattr(service, f"update_{entity}")(record_id, **changes)
                    print("[成功] 已更新:", json.dumps(updated, ensure_ascii=False))
                elif action == '4':
                    deleted = getattr(service, f"delete_{entity}")(record_id)
                    print("[成功] 已刪除:", json.dumps(deleted, ensure_ascii=False))
            else:
                print("無效的選擇，請重新輸入！")
        except Exception as e:
            print(f"\n[錯誤] {e}")


def main():
    while True:
        print_menu()
        choice = input("請選擇操作項目 (0-12): ").strip()
        
        if choice == '1':
            try:
                act_id = select_or_create_activity_id()
                name = input("輸入會議名稱: ").strip()
                start_time = input("輸入開始時間 (如 '2026-09-15 14:00', 可跳過): ").strip()
                end_time = input("輸入結束時間 (如 '2026-09-15 16:00', 可跳過): ").strip()
                location = input("輸入會議地點 (如 '管二 201 教室', 可跳過): ").strip()
                participants = input("輸入參與人員 (如 '張三, 李四', 可跳過): ").strip()
                content = input("輸入已取得的會議紀錄/內容文字: ").strip()
                
                res = add_meeting(
                    activity_id=act_id,
                    name=name,
                    start_time=start_time,
                    end_time=end_time,
                    location=location,
                    participants=participants,
                    content=content
                )
                act_label = get_activity_label(res['activity_id'])
                print(f"\n[成功] 已新增會議紀錄！")
                print(f"  [會議 ID: {res['id']}] 所屬活動: {act_label}")
                print(f"  會議名稱: {res['name']}")
                print(f"  時間: {res['start_time']} ~ {res['end_time']} | 地點: {res['location']}")
                print(f"  參與人員: {res['participants']}")
                print(f"  內容預覽: {res['content'][:100]}..." if len(res['content']) > 100 else f"  內容: {res['content']}")
            except Exception as e:
                print(f"\n[錯誤] {e}")

        elif choice == '2':
            print_activities_table()
            act_str = input("過濾活動 ID (直接按 Enter 查詢全部會議): ").strip()
            act_id = int(act_str) if act_str else None
            meetings = get_meetings(act_id)
            
            print(f"\n--- 會議列表 (共 {len(meetings)} 筆) ---")
            if not meetings:
                print("目前沒有任何會議紀錄。")
            for m in meetings:
                act_label = get_activity_label(m['activity_id'])
                c_preview = m['content'].replace('\n', ' ')
                if len(c_preview) > 30:
                    c_preview = c_preview[:30] + "..."
                print(f"[會議 ID: {m['id']}] | 活動: {act_label} | 名稱: {m['name']} | 時間: {m['start_time']}~{m['end_time']} | 地點: {m['location']} | 人員: {m['participants']} | 內容: {c_preview}")

        elif choice == '3':
            try:
                m_id = int(input("輸入欲修改的「會議 ID」: ").strip())
                existing = get_meeting_by_id(m_id)
                if not existing:
                    print(f"\n[失敗] 找不到會議 ID {m_id}。")
                    continue
                
                print(f"目前會議: {existing['name']} | 所屬活動: {get_activity_label(existing['activity_id'])}")
                name = input("新會議名稱 (不修改按 Enter): ").strip() or None
                start_time = input("新開始時間 (不修改按 Enter): ").strip() or None
                end_time = input("新結束時間 (不修改按 Enter): ").strip() or None
                location = input("新地點 (不修改按 Enter): ").strip() or None
                participants = input("新參與人員 (不修改按 Enter): ").strip() or None
                content = input("新內容文字 (不修改按 Enter): ").strip() or None
                
                ok = update_meeting(
                    m_id,
                    name=name,
                    start_time=start_time,
                    end_time=end_time,
                    location=location,
                    participants=participants,
                    content=content
                )
                if ok:
                    updated_m = get_meeting_by_id(m_id)
                    print(f"\n[成功] 會議 ID {m_id} 更新成功！")
                    print("  更新後資料:", updated_m)
                else:
                    print(f"\n[失敗] 無任何修改項目。")
            except Exception as e:
                print(f"\n[錯誤] {e}")

        elif choice == '4':
            try:
                m_id = int(input("輸入欲刪除的「會議 ID」: ").strip())
                if delete_meeting(m_id):
                    print(f"\n[成功] 會議 ID {m_id} 已成功刪除！")
                else:
                    print(f"\n[失敗] 找不到會議 ID {m_id}。")
            except Exception as e:
                print(f"\n[錯誤] {e}")

        elif choice == '5':
            try:
                act_id = select_or_create_activity_id()
                content = input("輸入待辦事項內容: ").strip()
                assignee = input("輸入負責人 (可跳過): ").strip()
                due_date = input("輸入完成期限 YYYY-MM-DD (可跳過): ").strip()
                priority = input("輸入優先級 (高/中/低，預設 '中'): ").strip() or "中"
                
                m_str = input("關聯會議 ID (無關聯請直接按 Enter): ").strip()
                m_id = int(m_str) if m_str else None
                
                res = add_task(
                    activity_id=act_id,
                    content=content,
                    assignee=assignee,
                    due_date=due_date,
                    priority=priority,
                    meeting_id=m_id
                )
                act_label = get_activity_label(res['activity_id'])
                print(f"\n[成功] 已新增待辦 [待辦 ID: {res['id']}]！")
                print(f"  活動: {act_label} | 關聯會議 ID: {res['meeting_id']}")
                print(f"  內容: {res['content']} | 負責人: {res['assignee']} | 期限: {res['due_date']} | 優先級: [{res['priority']}]")
            except Exception as e:
                print(f"\n[錯誤] {e}")

        elif choice == '6':
            act_str = input("過濾活動 ID (直接按 Enter 查詢全部待辦): ").strip()
            act_id = int(act_str) if act_str else None
            m_str = input("過濾會議 ID (直接按 Enter 查詢全部待辦): ").strip()
            m_id = int(m_str) if m_str else None
            
            tasks = get_tasks(activity_id=act_id, meeting_id=m_id)
            print(f"\n--- 待辦事項列表 (共 {len(tasks)} 筆) ---")
            if not tasks:
                print("目前沒有任何待辦事項。")
            for t in tasks:
                act_label = get_activity_label(t['activity_id'])
                m_info = f"關聯會議ID: {t['meeting_id']}" if t['meeting_id'] else "無關聯會議"
                print(f"[待辦 ID: {t['id']}] | 活動: {act_label} | {m_info} | 優先級: [{t['priority']}] | 狀態: [{t['status']}] | 負責人: {t['assignee']} | 期限: {t['due_date']} | 內容: {t['content']}")

        elif choice == '7':
            try:
                t_id = int(input("輸入欲修改的「待辦 ID」: ").strip())
                existing = get_task_by_id(t_id)
                if not existing:
                    print(f"\n[失敗] 找不到待辦 ID {t_id}。")
                    continue
                    
                print(f"目前待辦: [{existing['status']}] (優先級:{existing['priority']}) {existing['content']}")
                content = input("新內容 (不修改按 Enter): ").strip() or None
                assignee = input("新負責人 (不修改按 Enter): ").strip() or None
                due_date = input("新期限 (不修改按 Enter): ").strip() or None
                priority = input("新優先級 (高/中/低，不修改按 Enter): ").strip() or None
                status = input("新狀態 (如 completed/pending，不修改按 Enter): ").strip() or None
                
                ok = update_task(
                    t_id,
                    content=content,
                    assignee=assignee,
                    due_date=due_date,
                    priority=priority,
                    status=status
                )
                if ok:
                    updated_t = get_task_by_id(t_id)
                    print(f"\n[成功] 待辦 ID {t_id} 更新成功！", updated_t)
                else:
                    print(f"\n[失敗] 無任何修改項目。")
            except Exception as e:
                print(f"\n[錯誤] {e}")

        elif choice == '8':
            try:
                t_id = int(input("輸入欲刪除的「待辦 ID」: ").strip())
                if delete_task(t_id):
                    print(f"\n[成功] 待辦 ID {t_id} 已成功刪除！")
                else:
                    print(f"\n[失敗] 找不到待辦 ID {t_id}。")
            except Exception as e:
                print(f"\n[錯誤] {e}")

        elif choice == '9':
            handle_activity_menu()

        elif choice in MANAGEMENT_MODULES:
            handle_management_menu(choice)

        elif choice == '0':
            print("感謝使用，再見！")
            sys.exit(0)
        else:
            print("\n無效的選擇，請重新輸入！")

if __name__ == "__main__":
    main()
