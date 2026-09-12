import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

# Define paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DB_PATH = os.path.join(BASE_DIR, "rag_database.sqlite")

def get_connection():
    """建立並回傳 SQLite 資料庫連線"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # 讓查詢結果可以用 dict 方式存取
    return conn

def init_db():
    """初始化資料庫與資料表"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL,
                filename TEXT NOT NULL,
                upload_date DATETIME NOT NULL,
                chunk_count INTEGER NOT NULL
            )
        ''')
        conn.commit()

# 在模塊載入時自動初始化資料表
init_db()

def get_doc_by_path(file_path: str) -> Optional[Dict[str, Any]]:
    """根據路徑查詢檔案紀錄"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM documents WHERE file_path = ?', (file_path,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_doc_by_id(doc_id: int) -> Optional[Dict[str, Any]]:
    """根據 ID 查詢檔案紀錄"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM documents WHERE id = ?', (doc_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_all_docs() -> List[Dict[str, Any]]:
    """取得所有已上傳的檔案清單"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM documents ORDER BY upload_date DESC')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def add_or_update_doc_record(file_path: str, chunk_count: int) -> None:
    """新增或更新檔案紀錄"""
    filename = os.path.basename(file_path)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with get_connection() as conn:
        cursor = conn.cursor()
        # 使用 UPSERT 語法，若 file_path 存在則更新
        cursor.execute('''
            INSERT INTO documents (file_path, filename, upload_date, chunk_count)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(file_path) DO UPDATE SET
                upload_date = excluded.upload_date,
                chunk_count = excluded.chunk_count
        ''', (file_path, filename, now, chunk_count))
        conn.commit()

def delete_doc_record_by_path(file_path: str) -> None:
    """根據路徑刪除檔案紀錄"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM documents WHERE file_path = ?', (file_path,))
        conn.commit()

def delete_doc_record_by_id(doc_id: int) -> None:
    """根據 ID 刪除檔案紀錄"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM documents WHERE id = ?', (doc_id,))
        conn.commit()
