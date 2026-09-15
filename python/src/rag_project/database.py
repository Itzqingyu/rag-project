"""資料庫存取層 (Data Access Layer) 統一模組。

包含：
1. SQLite 資料庫連線池與自動 Schema 建置（含外鍵約束與索引）。
2. RAG 上傳 Markdown 文件 Metadata 之 CRUD 管理。
3. ChromaDB 向量資料庫單例模式 (Singleton) 之獲取與持久化設定。
"""

import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Iterator, List, Optional
from langchain_chroma import Chroma

# 路徑定義：資料庫統一存放於專案根目錄的 data/ 底下
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "rag_database.sqlite")
CHROMA_DB_DIR = os.path.join(DATA_DIR, "chroma_db")

# 確保 data 目錄存在
os.makedirs(DATA_DIR, exist_ok=True)

# 全域單例：ChromaDB Vectorstore
_vectorstore = None


# ==========================================
# 1. SQLite 連線與 Schema 初始化
# ==========================================

@contextmanager
def get_connection(db_path: Optional[str] = None) -> Iterator[sqlite3.Connection]:
    """提供會自動關閉的共用 SQLite 連線 ContextManager，並強制啟用 PRAGMA foreign_keys = ON。"""
    resolved_path = db_path or DB_PATH
    os.makedirs(os.path.dirname(os.path.abspath(resolved_path)), exist_ok=True)

    conn = sqlite3.connect(resolved_path)
    conn.row_factory = sqlite3.Row  # 讓查詢結果可以用字典 (dict) 方式存取欄位
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()


def init_db(db_path: Optional[str] = None) -> None:
    """初始化 SQLite 所有核心資料表 (documents, activities, meetings, tasks, decisions, schedules, incidents) 與索引。"""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        # 1.1 文件紀錄表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL,
                filename TEXT NOT NULL,
                raw_file_path TEXT,      -- 未經 markdown 解析的原始實體檔案路徑
                markdown_content TEXT,   -- 解析後的完整 Markdown 文字內容
                upload_date DATETIME NOT NULL,
                chunk_count INTEGER NOT NULL
            )
        ''')
        cursor.execute("PRAGMA table_info(documents)")
        existing_doc_cols = [row[1] for row in cursor.fetchall()]
        if "raw_file_path" not in existing_doc_cols:
            cursor.execute("ALTER TABLE documents ADD COLUMN raw_file_path TEXT")
        if "markdown_content" not in existing_doc_cols:
            cursor.execute("ALTER TABLE documents ADD COLUMN markdown_content TEXT")

        # 1.2 活動主表
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
        # 1.3 會議紀錄表 (RESTRICT activity_id)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_id INTEGER NOT NULL,
                source_document_id INTEGER,
                name TEXT NOT NULL,
                date TEXT DEFAULT '',
                start_time TEXT DEFAULT '',
                end_time TEXT DEFAULT '',
                location TEXT DEFAULT '',
                participants TEXT DEFAULT '',
                content TEXT DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(activity_id) REFERENCES activities(id)
                    ON DELETE RESTRICT,
                FOREIGN KEY(source_document_id) REFERENCES documents(id)
                    ON DELETE SET NULL
            )
        ''')

        # 舊版 SQLite 不能直接重建整張表；nullable FK 可安全以 ADD COLUMN
        # 補入，既有 Meeting 會自然維持 NULL，不影響舊資料。
        cursor.execute("PRAGMA table_info(meetings)")
        existing_meeting_cols = [row[1] for row in cursor.fetchall()]
        if "source_document_id" not in existing_meeting_cols:
            cursor.execute(
                """
                ALTER TABLE meetings
                ADD COLUMN source_document_id INTEGER
                    REFERENCES documents(id) ON DELETE SET NULL
                """
            )
        # 1.4 待辦事項表 (SET NULL meeting_id)
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
        # 1.5 決策紀錄表 (SET NULL meeting_id)
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
        # 1.6 流程日程表 (SET NULL meeting_id)
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
        # 1.7 突發事件表 (SET NULL schedule_id)
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
        
        # 1.8 為外鍵欄位自動建立索引以最佳化查詢效能
        indices = [
            ("idx_meetings_activity_id", "meetings(activity_id)"),
            ("idx_meetings_source_document_id", "meetings(source_document_id)"),
            ("idx_tasks_activity_id", "tasks(activity_id)"),
            ("idx_tasks_meeting_id", "tasks(meeting_id)"),
            ("idx_decisions_activity_id", "decisions(activity_id)"),
            ("idx_decisions_meeting_id", "decisions(meeting_id)"),
            ("idx_schedules_activity_id", "schedules(activity_id)"),
            ("idx_schedules_meeting_id", "schedules(meeting_id)"),
            ("idx_incidents_activity_id", "incidents(activity_id)"),
            ("idx_incidents_schedule_id", "incidents(schedule_id)"),
        ]
        for index_name, index_def in indices:
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {index_def}")

        conn.commit()


# 在模組載入時自動初始化資料表
init_db()


# ==========================================
# 2. Documents (文件) CRUD
# ==========================================

def get_doc_by_path(file_path: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """根據檔案路徑查詢文件上傳與切塊紀錄。"""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM documents WHERE file_path = ?', (file_path,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_doc_by_id(doc_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """根據文件流水號 ID 查詢文件紀錄。"""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM documents WHERE id = ?', (doc_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_all_docs(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """取得所有已匯入 RAG 系統的文件紀錄清單。"""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM documents ORDER BY upload_date DESC')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def add_or_update_doc_record(
    file_path: str,
    chunk_count: int,
    raw_file_path: Optional[str] = None,
    markdown_content: Optional[str] = None,
    *,
    db_path: Optional[str] = None,
) -> None:
    """新增或覆蓋更新文件的 Metadata 紀錄。"""
    init_db(db_path)
    filename = os.path.basename(file_path)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
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
    """根據檔案路徑從 SQLite 移除文件紀錄。"""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM documents WHERE file_path = ?', (file_path,))
        conn.commit()


def delete_doc_record_by_id(doc_id: int, db_path: Optional[str] = None) -> None:
    """根據文件流水號 ID 從 SQLite 移除文件紀錄。"""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM documents WHERE id = ?', (doc_id,))
        conn.commit()


# ==========================================
# 3. ChromaDB 向量資料庫單例
# ==========================================

def get_vectorstore(db_dir: Optional[str] = None) -> Chroma:
    """獲取 Chroma 向量資料庫單例模式 (Singleton) 實例。"""
    global _vectorstore
    from rag_project.document_processing.rag_engine import get_embeddings

    target_dir = db_dir or CHROMA_DB_DIR
    if _vectorstore is None or db_dir is not None:
        os.makedirs(target_dir, exist_ok=True)
        store = Chroma(
            collection_name="rag_collection",
            embedding_function=get_embeddings(),
            persist_directory=target_dir
        )
        if db_dir is None:
            _vectorstore = store
        return store
    return _vectorstore
