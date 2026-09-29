"""資料庫與交接全量管理模組 (Vault Manager)。

負責處理本機資料 (SQLite 資料庫、Chroma 向量庫、託管 Markdown 文件) 之全量導出、
安全驗證導入、覆蓋前自動快照備份與歷史備份還原。
"""

import os
import shutil
import zipfile
import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

# 路徑定義
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(BACKEND_DIR)
PYTHON_DIR = os.path.dirname(SRC_DIR)

DATA_DIR = os.path.join(PYTHON_DIR, "data")
BACKUPS_DIR = os.path.join(PYTHON_DIR, "data_backups")
DB_PATH = os.path.join(DATA_DIR, "dash_database.sqlite")
CHROMA_DIR = os.path.join(DATA_DIR, "chroma_db")
MARKDOWN_DIR = os.path.join(DATA_DIR, "markdown")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(BACKUPS_DIR, exist_ok=True)


def get_dir_size(dir_path: str) -> int:
    """計算目錄總容量大小 (bytes)。"""
    if not os.path.exists(dir_path):
        return 0
    total = 0
    for root, _, files in os.walk(dir_path):
        for f in files:
            fp = os.path.join(root, f)
            try:
                total += os.path.getsize(fp)
            except OSError:
                pass
    return total


def get_vault_stats() -> Dict[str, Any]:
    """取得當前資料庫與檔案儲存庫之統計概況。"""
    stats = {
        "activities_count": 0,
        "meetings_count": 0,
        "tasks_count": 0,
        "decisions_count": 0,
        "schedules_count": 0,
        "incidents_count": 0,
        "documents_count": 0,
        "chat_sessions_count": 0,
        "data_size_bytes": 0,
        "db_size_bytes": 0,
        "chroma_size_bytes": 0,
        "markdown_size_bytes": 0,
        "last_updated": datetime.now().isoformat(),
    }

    if os.path.exists(DB_PATH):
        try:
            stats["db_size_bytes"] = os.path.getsize(DB_PATH)
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            table_mappings = [
                ("activities", "activities_count"),
                ("meetings", "meetings_count"),
                ("tasks", "tasks_count"),
                ("decisions", "decisions_count"),
                ("schedules", "schedules_count"),
                ("incidents", "incidents_count"),
                ("documents", "documents_count"),
                ("sessions", "chat_sessions_count"),
            ]

            for table, stat_key in table_mappings:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[stat_key] = cursor.fetchone()[0]
                except sqlite3.OperationalError:
                    pass

            conn.close()
        except Exception:
            pass

    stats["chroma_size_bytes"] = get_dir_size(CHROMA_DIR)
    stats["markdown_size_bytes"] = get_dir_size(MARKDOWN_DIR)
    stats["data_size_bytes"] = get_dir_size(DATA_DIR)

    return stats


def export_vault_to_zip(output_zip_path: Optional[str] = None) -> str:
    """將當前 data/ 目錄打包封裝為包含 dash_manifest.json 的標準 ZIP 檔案。"""
    if not output_zip_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_dir = os.path.join(BACKUPS_DIR, "temp_export")
        os.makedirs(temp_dir, exist_ok=True)
        output_zip_path = os.path.join(temp_dir, f"dash_export_{timestamp}.zip")

    stats = get_vault_stats()
    manifest_data = {
        "app": "DASH",
        "version": "1.1.0",
        "manifest_version": 1,
        "exported_at": datetime.now().isoformat(),
        "stats": stats,
    }

    with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. 寫入簽名描述檔
        zf.writestr("dash_manifest.json", json.dumps(manifest_data, ensure_ascii=False, indent=2))

        # 2. 寫入 SQLite 資料庫 (若存在)
        if os.path.exists(DB_PATH):
            zf.write(DB_PATH, arcname="dash_database.sqlite")

        # 3. 寫入 Chroma 向量庫
        if os.path.exists(CHROMA_DIR):
            for root, _, files in os.walk(CHROMA_DIR):
                for f in files:
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, DATA_DIR)
                    zf.write(full_p, arcname=rel_p.replace("\\", "/"))

        # 4. 寫入 Markdown 託管檔案
        if os.path.exists(MARKDOWN_DIR):
            for root, _, files in os.walk(MARKDOWN_DIR):
                for f in files:
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, DATA_DIR)
                    zf.write(full_p, arcname=rel_p.replace("\\", "/"))

    return output_zip_path


def verify_vault_zip(zip_path: str) -> Dict[str, Any]:
    """檢驗傳入之 ZIP 是否為合法的 DASH 備份資料包。"""
    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"找不到檔案: {zip_path}")

    if not zipfile.is_zipfile(zip_path):
        raise ValueError("上傳的檔案非有效的 ZIP 壓縮檔。")

    with zipfile.ZipFile(zip_path, "r") as zf:
        namelist = zf.namelist()

        # 檢查是否具備專屬簽名描述檔
        if "dash_manifest.json" not in namelist:
            raise ValueError("非本系統 (DASH) 導出之資料包：找不到 dash_manifest.json 簽名檔。")

        try:
            manifest_bytes = zf.read("dash_manifest.json")
            manifest = json.loads(manifest_bytes.decode("utf-8"))
        except Exception as e:
            raise ValueError(f"dash_manifest.json 簽名解析失敗: {str(e)}")

        if manifest.get("app") != "DASH":
            raise ValueError("簽名內容無效：非 DASH 專屬資料包。")

        # 檢查核心資料結構 (至少應包含 SQLite 資料庫)
        if "dash_database.sqlite" not in namelist:
            raise ValueError("資料包結構不完整：缺少 dash_database.sqlite 資料庫。")

        return manifest


def create_auto_backup() -> Optional[str]:
    """覆蓋前自動對現有本地 data/ 進行快照備份。"""
    if not os.path.exists(DB_PATH) and not os.path.exists(MARKDOWN_DIR):
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"backup_{timestamp}.zip"
    backup_path = os.path.join(BACKUPS_DIR, backup_filename)

    export_vault_to_zip(backup_path)
    return backup_filename


def import_vault_from_zip(zip_path: str) -> Dict[str, Any]:
    """校驗、建立安全快照並全量解壓替換本機 data/ 資料庫。"""
    manifest = verify_vault_zip(zip_path)

    # 1. 建立當前資料的自動安全快照
    auto_backup_file = create_auto_backup()

    # 2. 清理記憶體快取與連線
    from dash_backend import database
    database._vectorstore = None

    # 3. 清理舊的 Chroma 與 Markdown 實體目錄 (保留安全機制)
    if os.path.exists(CHROMA_DIR):
        shutil.rmtree(CHROMA_DIR, ignore_errors=True)
    if os.path.exists(MARKDOWN_DIR):
        shutil.rmtree(MARKDOWN_DIR, ignore_errors=True)

    os.makedirs(DATA_DIR, exist_ok=True)

    # 4. 解壓縮新資料覆蓋至 DATA_DIR
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            # 跳過 manifest 本身不覆蓋至 data/ 根目錄
            if member.filename == "dash_manifest.json":
                continue
            # 安全防範路徑穿越
            target_path = os.path.abspath(os.path.join(DATA_DIR, member.filename))
            if not target_path.startswith(os.path.abspath(DATA_DIR)):
                raise ValueError(f"不安全的壓縮包路徑: {member.filename}")
            zf.extract(member, DATA_DIR)

    # 5. 重新初始化資料庫 Schema 確保健全
    database.init_db()

    return {
        "status": "success",
        "message": "資料包已成功驗證並全量導入！",
        "backup_created": auto_backup_file,
        "manifest": manifest,
        "stats": get_vault_stats(),
    }


def list_backups() -> List[Dict[str, Any]]:
    """列出本機所有的安全快照備份清單。"""
    backups = []
    if not os.path.exists(BACKUPS_DIR):
        return backups

    for filename in os.listdir(BACKUPS_DIR):
        if filename.endswith(".zip") and not filename.startswith("dash_export_"):
            full_path = os.path.join(BACKUPS_DIR, filename)
            try:
                stat = os.stat(full_path)
                backups.append({
                    "filename": filename,
                    "size_bytes": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
            except OSError:
                pass

    backups.sort(key=lambda x: x["created_at"], reverse=True)
    return backups


def restore_backup(backup_filename: str) -> Dict[str, Any]:
    """依指定快照檔名還原資料。"""
    # 安全路徑防護
    safe_name = os.path.basename(backup_filename)
    backup_path = os.path.join(BACKUPS_DIR, safe_name)

    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"找不到備份檔案: {safe_name}")

    return import_vault_from_zip(backup_path)
