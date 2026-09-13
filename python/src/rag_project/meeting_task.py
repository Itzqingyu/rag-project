from typing import List, Dict, Any, Optional
from rag_project.activity_common import (
    ensure_activity_exists,
    ensure_meeting_matches_activity,
)
from rag_project.database.sqlite_db import get_connection, init_db


_UNSET = object()


def init_meeting_task_tables(db_path: Optional[str] = None) -> None:
    """初始化共用 schema，並補足舊版 Meeting/Task 可能缺少的欄位。"""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # 動態補足舊版 meetings 可能缺少的新欄位
        cursor.execute("PRAGMA table_info(meetings)")
        existing_m_cols = [row[1] for row in cursor.fetchall()]
        for col_name, col_type in [
            ("date", "TEXT DEFAULT ''"),
            ("start_time", "TEXT DEFAULT ''"),
            ("end_time", "TEXT DEFAULT ''"),
            ("location", "TEXT DEFAULT ''"),
            ("participants", "TEXT DEFAULT ''")
        ]:
            if col_name not in existing_m_cols:
                cursor.execute(f"ALTER TABLE meetings ADD COLUMN {col_name} {col_type}")
        
        # 動態補足舊版 tasks 可能缺少的 priority 欄位
        cursor.execute("PRAGMA table_info(tasks)")
        existing_t_cols = [row[1] for row in cursor.fetchall()]
        if "priority" not in existing_t_cols:
            cursor.execute("ALTER TABLE tasks ADD COLUMN priority TEXT DEFAULT '中'")
        
        conn.commit()


# ==========================================
# Meeting (會議) CRUD 函式
# ==========================================

def add_meeting(
    activity_id: int,
    name: str,
    start_time: str = "",
    end_time: str = "",
    location: str = "",
    participants: str = "",
    content: str = "",
    date: str = "",
    *,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """新增一筆會議資料
    
    :param activity_id: 所屬活動 ID
    :param name: 會議名稱
    :param start_time: 開始時間 (如 '2026-09-15 14:00')
    :param end_time: 結束時間 (如 '2026-09-15 16:00')
    :param location: 地點 (如 '管二 201 教室')
    :param participants: 參與人員 (如 '張三, 李四')
    :param content: 已經由統一 upload/Markdown 流程取得的會議文字
    :param date: 相容用日期欄位
    :param db_path: 可選資料庫路徑 (測試用)
    """
    init_meeting_task_tables(db_path)
    if not date and start_time:
        date = start_time.split()[0]
        
    with get_connection(db_path) as conn:
        ensure_activity_exists(conn, activity_id)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO meetings (activity_id, name, date, start_time, end_time, location, participants, content)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (activity_id, name, date, start_time, end_time, location, participants, content))
        conn.commit()
        meeting_id = cursor.lastrowid
        
    return get_meeting_by_id(meeting_id, db_path=db_path)  # type: ignore[return-value]


def get_meetings(activity_id: Optional[int] = None, *, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """取得會議清單"""
    init_meeting_task_tables(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        if activity_id is not None:
            cursor.execute('SELECT * FROM meetings WHERE activity_id = ? ORDER BY id DESC', (activity_id,))
        else:
            cursor.execute('SELECT * FROM meetings ORDER BY id DESC')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_meeting_by_id(meeting_id: int, *, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """根據 ID 取得單一會議資料"""
    init_meeting_task_tables(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM meetings WHERE id = ?', (meeting_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def update_meeting(
    meeting_id: int,
    name: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    location: Optional[str] = None,
    participants: Optional[str] = None,
    content: Optional[str] = None,
    activity_id: Optional[int] = None,
    date: Optional[str] = None,
    *,
    db_path: Optional[str] = None
) -> bool:
    """修改會議內容"""
    init_meeting_task_tables(db_path)
    fields = []
    values = []
    
    if name is not None:
        fields.append("name = ?")
        values.append(name)
    if start_time is not None:
        fields.append("start_time = ?")
        values.append(start_time)
        if date is None:
            fields.append("date = ?")
            values.append(start_time.strip().split(maxsplit=1)[0] if start_time.strip() else "")
    if date is not None:
        fields.append("date = ?")
        values.append(date)
    if end_time is not None:
        fields.append("end_time = ?")
        values.append(end_time)
    if location is not None:
        fields.append("location = ?")
        values.append(location)
    if participants is not None:
        fields.append("participants = ?")
        values.append(participants)
    if content is not None:
        fields.append("content = ?")
        values.append(content)
    if activity_id is not None:
        fields.append("activity_id = ?")
        values.append(activity_id)
        
    if not fields:
        return False
        
    with get_connection(db_path) as conn:
        current = conn.execute(
            "SELECT * FROM meetings WHERE id = ?", (meeting_id,)
        ).fetchone()
        if current is None:
            return False

        if activity_id is not None:
            ensure_activity_exists(conn, activity_id)
            # 改掛 Activity 時，保守地阻止所有既有關聯資料形成跨活動狀態。
            for table_name in ("tasks", "decisions", "schedules"):
                conflict = conn.execute(
                    f"""
                    SELECT 1 FROM {table_name}
                    WHERE meeting_id = ? AND activity_id != ?
                    LIMIT 1
                    """,
                    (meeting_id, activity_id),
                ).fetchone()
                if conflict is not None:
                    raise ValueError(
                        "Meeting 已被其他 Activity 的關聯資料使用，無法變更 activity_id"
                    )

        values.append(meeting_id)
        sql = f"UPDATE meetings SET {', '.join(fields)} WHERE id = ?"
        cursor = conn.cursor()
        cursor.execute(sql, tuple(values))
        conn.commit()
        return cursor.rowcount > 0


def delete_meeting(meeting_id: int, *, db_path: Optional[str] = None) -> bool:
    """刪除會議紀錄"""
    init_meeting_task_tables(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM meetings WHERE id = ?', (meeting_id,))
        if not cursor.fetchone():
            return False
        cursor.execute('DELETE FROM meetings WHERE id = ?', (meeting_id,))
        conn.commit()
        return True


# ==========================================
# Task (待辦事項) CRUD 函式
# ==========================================

def add_task(
    activity_id: int,
    content: str,
    assignee: str = "",
    due_date: str = "",
    priority: str = "中",
    status: str = "pending",
    meeting_id: Optional[int] = None,
    *,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """新增一筆待辦事項
    
    :param priority: 優先級 (高/中/低)
    :param db_path: 可選資料庫路徑 (測試用)
    """
    init_meeting_task_tables(db_path)
    with get_connection(db_path) as conn:
        normalized_activity_id = ensure_activity_exists(conn, activity_id)
        normalized_meeting_id = ensure_meeting_matches_activity(
            conn, meeting_id, normalized_activity_id
        )
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tasks (activity_id, meeting_id, content, assignee, due_date, priority, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            normalized_activity_id,
            normalized_meeting_id,
            content,
            assignee,
            due_date,
            priority,
            status,
        ))
        conn.commit()
        task_id = cursor.lastrowid
        
    return get_task_by_id(task_id, db_path=db_path)  # type: ignore[return-value]


def get_tasks(
    activity_id: Optional[int] = None,
    meeting_id: Optional[int] = None,
    *,
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """取得待辦事項清單"""
    init_meeting_task_tables(db_path)
    conditions = []
    values = []
    
    if activity_id is not None:
        conditions.append("activity_id = ?")
        values.append(activity_id)
    if meeting_id is not None:
        conditions.append("meeting_id = ?")
        values.append(meeting_id)
        
    sql = "SELECT * FROM tasks"
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY id DESC"
    
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(values))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_task_by_id(task_id: int, *, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """根據 ID 取得單一待辦紀錄"""
    init_meeting_task_tables(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def update_task(
    task_id: int,
    content: Optional[str] = None,
    assignee: Optional[str] = None,
    due_date: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    activity_id: Optional[int] = None,
    meeting_id: Any = _UNSET,
    *,
    db_path: Optional[str] = None
) -> bool:
    """修改待辦事項內容"""
    init_meeting_task_tables(db_path)
    fields = []
    values = []
    
    if content is not None:
        fields.append("content = ?")
        values.append(content)
    if assignee is not None:
        fields.append("assignee = ?")
        values.append(assignee)
    if due_date is not None:
        fields.append("due_date = ?")
        values.append(due_date)
    if priority is not None:
        fields.append("priority = ?")
        values.append(priority)
    if status is not None:
        fields.append("status = ?")
        values.append(status)
    if activity_id is not None:
        fields.append("activity_id = ?")
        values.append(activity_id)
    if meeting_id is not _UNSET:
        fields.append("meeting_id = ?")
        values.append(meeting_id)
        
    if not fields:
        return False
        
    with get_connection(db_path) as conn:
        current = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if current is None:
            return False

        next_activity_id = (
            activity_id if activity_id is not None else current["activity_id"]
        )
        next_meeting_id = (
            meeting_id if meeting_id is not _UNSET else current["meeting_id"]
        )
        normalized_activity_id = ensure_activity_exists(conn, next_activity_id)
        ensure_meeting_matches_activity(
            conn, next_meeting_id, normalized_activity_id
        )

        values.append(task_id)
        sql = f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?"
        cursor = conn.cursor()
        cursor.execute(sql, tuple(values))
        conn.commit()
        return cursor.rowcount > 0


def delete_task(task_id: int, *, db_path: Optional[str] = None) -> bool:
    """刪除待辦事項紀錄"""
    init_meeting_task_tables(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM tasks WHERE id = ?', (task_id,))
        if not cursor.fetchone():
            return False
        cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        conn.commit()
        return True
