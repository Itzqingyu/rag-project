import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Iterator, List, Optional

# Define paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DB_PATH = os.path.join(BASE_DIR, "data", "rag_database.sqlite")

# 確保 data 目錄存在
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

@contextmanager
def get_connection(db_path: Optional[str] = None) -> Iterator[sqlite3.Connection]:
    """提供會自動關閉的共用 SQLite 連線，並啟用外鍵約束。"""
    resolved_path = db_path or DB_PATH
    os.makedirs(os.path.dirname(os.path.abspath(resolved_path)), exist_ok=True)

    conn = sqlite3.connect(resolved_path)
    conn.row_factory = sqlite3.Row  # 讓查詢結果可以用 dict 方式存取
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()

def init_db(db_path: Optional[str] = None) -> None:
    """初始化資料庫與資料表"""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL,
                filename TEXT NOT NULL,
                raw_file_path TEXT,      -- [新增] 1. 未經 markdown 的原始檔案實體路徑
                markdown_content TEXT,   -- [新增] 2. 經 markdown 解析的完整文字內容
                upload_date DATETIME NOT NULL,
                chunk_count INTEGER NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                year INTEGER NOT NULL CHECK (year > 0),
                status TEXT NOT NULL,
                start_date TEXT,
                end_date TEXT,
                venue TEXT,
                activity_type TEXT,
                coordinator TEXT,
                expected_attendees INTEGER CHECK (
                    expected_attendees IS NULL OR expected_attendees >= 0
                ),
                budget INTEGER CHECK (budget IS NULL OR budget >= 0),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                CHECK (
                    start_date IS NULL
                    OR end_date IS NULL
                    OR end_date >= start_date
                )
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                date TEXT DEFAULT '',
                start_time TEXT DEFAULT '',
                end_time TEXT DEFAULT '',
                location TEXT DEFAULT '',
                participants TEXT DEFAULT '',
                content TEXT DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(activity_id) REFERENCES activities(id)
                    ON DELETE RESTRICT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_id INTEGER NOT NULL,
                meeting_id INTEGER,
                content TEXT NOT NULL,
                assignee TEXT DEFAULT '',
                due_date TEXT DEFAULT '',
                priority TEXT DEFAULT '中',
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(activity_id) REFERENCES activities(id)
                    ON DELETE RESTRICT,
                FOREIGN KEY(meeting_id) REFERENCES meetings(id)
                    ON DELETE SET NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_id INTEGER NOT NULL,
                meeting_id INTEGER CHECK (meeting_id IS NULL OR meeting_id > 0),
                problem TEXT NOT NULL,
                options TEXT NOT NULL,
                final_decision TEXT NOT NULL,
                reason TEXT NOT NULL,
                source TEXT NOT NULL,
                confirmation_status TEXT NOT NULL DEFAULT 'pending'
                    CHECK (confirmation_status IN ('pending', 'confirmed')),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(activity_id) REFERENCES activities(id)
                    ON DELETE RESTRICT,
                FOREIGN KEY(meeting_id) REFERENCES meetings(id)
                    ON DELETE SET NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_id INTEGER NOT NULL,
                meeting_id INTEGER CHECK (meeting_id IS NULL OR meeting_id > 0),
                name TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                location TEXT NOT NULL,
                owner TEXT NOT NULL,
                notes TEXT NOT NULL,
                category TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(activity_id) REFERENCES activities(id)
                    ON DELETE RESTRICT,
                FOREIGN KEY(meeting_id) REFERENCES meetings(id)
                    ON DELETE SET NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_id INTEGER NOT NULL,
                schedule_id INTEGER,
                content TEXT NOT NULL,
                occurred_at TEXT NOT NULL,
                cause TEXT,
                suggestion TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(activity_id) REFERENCES activities(id)
                    ON DELETE RESTRICT,
                FOREIGN KEY(schedule_id) REFERENCES schedules(id)
                    ON DELETE SET NULL
            )
        ''')
        # SQLite 不會自動替外鍵建立索引；這些索引能避免整合後關聯查詢全表掃描。
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_meetings_activity_id "
            "ON meetings(activity_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_tasks_activity_id "
            "ON tasks(activity_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_tasks_meeting_id "
            "ON tasks(meeting_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_decisions_activity_id "
            "ON decisions(activity_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_decisions_meeting_id "
            "ON decisions(meeting_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_schedules_activity_id "
            "ON schedules(activity_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_schedules_meeting_id "
            "ON schedules(meeting_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_incidents_activity_id "
            "ON incidents(activity_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_incidents_schedule_id "
            "ON incidents(schedule_id)"
        )
        conn.commit()

def get_doc_by_path(file_path: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """根據路徑查詢檔案紀錄"""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM documents WHERE file_path = ?', (file_path,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_doc_by_id(doc_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """根據 ID 查詢檔案紀錄"""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM documents WHERE id = ?', (doc_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_all_docs(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """取得所有已上傳的檔案清單"""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM documents ORDER BY upload_date DESC')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

# [修改] 新增 raw_file_path 與 markdown_content 參數
def add_or_update_doc_record(
    file_path: str,
    chunk_count: int,
    raw_file_path: Optional[str] = None,
    markdown_content: Optional[str] = None,
    *,
    db_path: Optional[str] = None,
) -> None:
    """新增或更新檔案紀錄"""
    init_db(db_path)
    filename = os.path.basename(file_path)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        # 使用 UPSERT 語法，若 file_path 存在則更新
        cursor.execute('''
            INSERT INTO documents (file_path, filename, raw_file_path, markdown_content, upload_date, chunk_count)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(file_path) DO UPDATE SET
                raw_file_path = excluded.raw_file_path,
                markdown_content = excluded.markdown_content,
                upload_date = excluded.upload_date,
                chunk_count = excluded.chunk_count
        ''', (file_path, filename, raw_file_path, markdown_content, now, chunk_count))
        conn.commit()

def delete_doc_record_by_path(file_path: str, db_path: Optional[str] = None) -> None:
    """根據路徑刪除檔案紀錄"""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM documents WHERE file_path = ?', (file_path,))
        conn.commit()

def delete_doc_record_by_id(doc_id: int, db_path: Optional[str] = None) -> None:
    """根據 ID 刪除檔案紀錄"""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM documents WHERE id = ?', (doc_id,))
        conn.commit()
