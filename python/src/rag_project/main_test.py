import os
import sys

# 將 src 目錄加入 Python 搜尋路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rag_project.meeting_task import (
    add_meeting, get_meetings, get_meeting_by_id, update_meeting, delete_meeting,
    add_task, get_tasks, get_task_by_id, update_task, delete_task
)

# 模擬/測試用活動 (Activity) 名稱對照表
MOCK_ACTIVITIES = {
    1: "2026 資管週",
    2: "期初大會",
    3: "秋季迎新晚會",
    4: "學術研討會"
}

def get_activity_label(activity_id: int) -> str:
    name = MOCK_ACTIVITIES.get(activity_id, f"自訂活動 #{activity_id}")
    return f"{name} (ID: {activity_id})"

def print_activities_table():
    print("\n" + "-" * 45)
    print("      📍 可用活動 ID 對照表 (Activity Table)")
    print("-" * 45)
    for act_id, act_name in MOCK_ACTIVITIES.items():
        print(f"  [ ID: {act_id} ] ➡️  {act_name}")
    print("-" * 45)

def print_menu():
    print("\n" + "=" * 60)
    print("        Meeting & Task CLI 測試選單 (最新規格版)")
    print("=" * 60)
    print("[ 1 ] 新增會議 (Add Meeting)")
    print("      - 名稱, 開始/結束時間, 地點, 參與人員, 內容/檔案")
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
    print("[ 9 ] 查看活動 ID 對照表 (Activity Lookup)")
    print("[ 0 ] 離開 (Exit)")
    print("=" * 60)

def main():
    while True:
        print_menu()
        choice = input("請選擇操作項目 (0-9): ").strip()
        
        if choice == '1':
            try:
                print_activities_table()
                act_id = int(input("輸入活動 ID (activity_id): ").strip())
                name = input("輸入會議名稱: ").strip()
                start_time = input("輸入開始時間 (如 '2026-09-15 14:00', 可跳過): ").strip()
                end_time = input("輸入結束時間 (如 '2026-09-15 16:00', 可跳過): ").strip()
                location = input("輸入會議地點 (如 '管二 201 教室', 可跳過): ").strip()
                participants = input("輸入參與人員 (如 '張三, 李四', 可跳過): ").strip()
                content = input("輸入會議紀錄/內容 (可貼純文字，或貼檔案路徑如 C:\\doc.md / .pdf): ").strip()
                
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
                content = input("新內容或新檔案路徑 (不修改按 Enter): ").strip() or None
                
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
                print_activities_table()
                act_id = int(input("輸入活動 ID (activity_id): ").strip())
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
            print_activities_table()

        elif choice == '0':
            print("感謝使用，再見！")
            sys.exit(0)
        else:
            print("\n無效的選擇，請重新輸入！")

if __name__ == "__main__":
    main()
