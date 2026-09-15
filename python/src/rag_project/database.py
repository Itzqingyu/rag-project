"""資料庫存取層 (Data Access Layer) 統一模組。

包含：
1. SQLite 資料庫連線池與自動 Schema 建置（含外鍵約束與索引）。
2. RAG 上傳 Markdown 文件 Metadata 之 CRUD 管理。
3. ChromaDB 向量資料庫單例模式 (Singleton) 之獲取與持久化設定。
"""

import sqlite3
import os
import json
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

        # 1.8 對話會話表 (Sessions)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        # 1.9 對話訊息紀錄表 (Chat Messages - CASCADE session_id)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                mode TEXT NOT NULL DEFAULT 'chat' CHECK(mode IN ('chat', 'rag')),
                retrieved_chunks TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES sessions(id)
                    ON DELETE CASCADE
            )
        ''')
        
        # 1.10 為外鍵與查詢欄位自動建立索引以最佳化查詢效能
        indices = [
            ("idx_meetings_activity_id", "meetings(activity_id)"),
            ("idx_tasks_activity_id", "tasks(activity_id)"),
            ("idx_tasks_meeting_id", "tasks(meeting_id)"),
            ("idx_decisions_activity_id", "decisions(activity_id)"),
            ("idx_decisions_meeting_id", "decisions(meeting_id)"),
            ("idx_schedules_activity_id", "schedules(activity_id)"),
            ("idx_schedules_meeting_id", "schedules(meeting_id)"),
            ("idx_incidents_activity_id", "incidents(activity_id)"),
            ("idx_incidents_schedule_id", "incidents(schedule_id)"),
            ("idx_chat_messages_session_id", "chat_messages(session_id)"),
            ("idx_sessions_updated_at", "sessions(updated_at)"),
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


# ==========================================
# 4. Sessions & Chat Messages CRUD
# ==========================================

def create_session(title: Optional[str] = None, *, db_path: Optional[str] = None) -> Dict[str, Any]:
    """建立新的對話會話 (Session)。若未指定標題，預設為 '新對話'。"""
    init_db(db_path)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session_title = title.strip() if title and title.strip() else "新對話"

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sessions (title, created_at, updated_at) VALUES (?, ?, ?)",
            (session_title, now, now)
        )
        session_id = cursor.lastrowid
        conn.commit()
        return {
            "id": session_id,
            "title": session_title,
            "created_at": now,
            "updated_at": now
        }


def get_session(session_id: int, *, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """根據 Session ID 查詢會話資訊。"""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def list_sessions(*, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """取得所有對話會話清單，依最新更新時間倒序排列。"""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions ORDER BY updated_at DESC, id DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def update_session_title(session_id: int, title: str, *, db_path: Optional[str] = None) -> bool:
    """更新指定 Session 的標題與更新時間。"""
    init_db(db_path)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?",
            (title.strip(), now, session_id)
        )
        conn.commit()
        return cursor.rowcount > 0


def delete_session(session_id: int, *, db_path: Optional[str] = None) -> bool:
    """刪除指定 Session，因 foreign key ON DELETE CASCADE，其對話訊息將一併被刪除。"""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()
        return cursor.rowcount > 0


def add_chat_message(
    session_id: int,
    role: str,
    content: str,
    mode: str = "chat",
    retrieved_chunks: Optional[List[Dict[str, Any]]] = None,
    *,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """新增一筆對話訊息至特定 Session，並自動觸發更新 Session 的 updated_at。"""
    init_db(db_path)
    if role not in ("user", "assistant"):
        raise ValueError("role 必須為 'user' 或 'assistant'")
    if mode not in ("chat", "rag"):
        raise ValueError("mode 必須為 'chat' 或 'rag'")

    chunks_json = json.dumps(retrieved_chunks, ensure_ascii=False) if retrieved_chunks else None
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM sessions WHERE id = ?", (session_id,))
        if not cursor.fetchone():
            raise ValueError(f"Session {session_id} 不存在")

        cursor.execute('''
            INSERT INTO chat_messages (session_id, role, content, mode, retrieved_chunks, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session_id, role, content, mode, chunks_json, now))
        msg_id = cursor.lastrowid

        cursor.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id))
        conn.commit()

        return {
            "id": msg_id,
            "session_id": session_id,
            "role": role,
            "content": content,
            "mode": mode,
            "retrieved_chunks": retrieved_chunks,
            "created_at": now
        }


def get_chat_messages(
    session_id: int,
    limit: Optional[int] = None,
    *,
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """取得指定 Session 的對話紀錄 (依時間正序排列)。若指定 limit 則取最近的 N 筆訊息。"""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        if limit is not None and limit > 0:
            cursor.execute('''
                SELECT * FROM chat_messages 
                WHERE session_id = ? 
                ORDER BY id DESC 
                LIMIT ?
            ''', (session_id, limit))
            rows = cursor.fetchall()
            messages = [dict(row) for row in reversed(rows)]
        else:
            cursor.execute('''
                SELECT * FROM chat_messages 
                WHERE session_id = ? 
                ORDER BY id ASC
            ''', (session_id,))
            messages = [dict(row) for row in cursor.fetchall()]

        for msg in messages:
            if msg.get("retrieved_chunks"):
                try:
                    msg["retrieved_chunks"] = json.loads(msg["retrieved_chunks"])
                except Exception:
                    pass
        return messages

