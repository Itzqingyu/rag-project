"""資料庫與交接多 Vault 管理模組 (Vault Manager)。

負責處理 ~/.dash/ 規範下所有 Vault 的生命週期管理：
1. 開箱即用建立預設 default Vault。
2. Vault 身分證 (dash_manifest.json) 讀寫與嚴格驗證。
3. 動態切換、新建、重新命名、刪除 Vault。
4. DASH OUT: 將當前 Vault 打包封裝為標準 ZIP。
5. DASH IN: 驗證外部 ZIP 並解壓縮建立為全新獨立 Vault（絕不覆蓋）。
"""

import os
import re
import shutil
import zipfile
import json
import uuid
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

# 核心路徑定義：全面收攏至本機使用者目錄 ~/.dash/
DASH_ROOT = os.path.expanduser(os.path.join("~", ".dash"))
CONFIG_PATH = os.path.join(DASH_ROOT, "config.json")
VAULTS_DIR = os.path.join(DASH_ROOT, "vaults")
TEMP_DIR = os.path.join(DASH_ROOT, "temp")

os.makedirs(VAULTS_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)


# ==========================================
# 1. 全域設定檔管理 (Global Config)
# ==========================================

def load_config() -> Dict[str, Any]:
    """讀取全域設定檔 config.json，若不存在則給予預設值。"""
    if not os.path.exists(CONFIG_PATH):
        default_config = {"active_vault": "default"}
        save_config(default_config)
        return default_config

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not data.get("active_vault"):
                data["active_vault"] = "default"
            return data
    except Exception:
        default_config = {"active_vault": "default"}
        save_config(default_config)
        return default_config


def save_config(config: Dict[str, Any]) -> None:
    """寫入全域設定檔 config.json。"""
    os.makedirs(DASH_ROOT, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_active_vault_name() -> str:
    """取得當前使用中之 Vault 名稱。"""
    cfg = load_config()
    return cfg.get("active_vault", "default")


def get_active_vault_dir() -> str:
    """取得當前使用中之 Vault 實體目錄絕對路徑。"""
    active_name = get_active_vault_name()
    vault_dir = os.path.join(VAULTS_DIR, active_name)
    if not os.path.exists(vault_dir):
        ensure_default_vault()
        vault_dir = os.path.join(VAULTS_DIR, "default")
    return os.path.abspath(vault_dir)


# ==========================================
# 2. 動態路徑解析器 (Dynamic Path Resolvers)
# ==========================================

def get_vault_dir(vault_name: Optional[str] = None) -> str:
    """取得指定或當前 Vault 的根目錄。"""
    if vault_name:
        return os.path.abspath(os.path.join(VAULTS_DIR, vault_name))
    return get_active_vault_dir()


def get_db_path(vault_name: Optional[str] = None) -> str:
    """取得指定或當前 Vault 之 SQLite 資料庫路徑。"""
    return os.path.join(get_vault_dir(vault_name), "dash_database.sqlite")


def get_chroma_dir(vault_name: Optional[str] = None) -> str:
    """取得指定或當前 Vault 之 ChromaDB 向量庫目錄。"""
    return os.path.join(get_vault_dir(vault_name), "chroma_db")


def get_markdown_dir(vault_name: Optional[str] = None) -> str:
    """取得指定或當前 Vault 之託管 Markdown 文件目錄。"""
    return os.path.join(get_vault_dir(vault_name), "markdown")


def get_manifest_path(vault_name: Optional[str] = None) -> str:
    """取得指定或當前 Vault 之 dash_manifest.json 身分證路徑。"""
    return os.path.join(get_vault_dir(vault_name), "dash_manifest.json")


def sanitize_vault_name(name: str) -> str:
    """過濾非法資料夾字元，確保 Vault 命名安全合規。"""
    cleaned = re.sub(r'[\\/*?:"<>|]', "", name.strip())
    return cleaned or "vault"


# ==========================================
# 3. 身分證 (Manifest) 管理
# ==========================================

def read_manifest(vault_dir: str) -> Optional[Dict[str, Any]]:
    """讀取指定 Vault 目錄中的 dash_manifest.json 身分證。"""
    manifest_file = os.path.join(vault_dir, "dash_manifest.json")
    if not os.path.exists(manifest_file):
        return None
    try:
        with open(manifest_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if data.get("app") == "DASH":
                return data
    except Exception:
        pass
    return None


def write_manifest(vault_dir: str, manifest_data: Dict[str, Any]) -> None:
    """寫入或更新 dash_manifest.json 身分證。"""
    manifest_file = os.path.join(vault_dir, "dash_manifest.json")
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, ensure_ascii=False, indent=2)


# ==========================================
# 4. Vault 生命週期管理 (Create / Init / List / Switch / Rename / Delete)
# ==========================================

def init_vault(vault_name: str, description: str = "") -> Dict[str, Any]:
    """初始化並建立一個全新的空白 Vault 目錄與資料庫結構。"""
    clean_name = sanitize_vault_name(vault_name)
    target_dir = os.path.join(VAULTS_DIR, clean_name)
    if os.path.exists(target_dir):
        raise ValueError(f"Vault 名稱「{clean_name}」已存在，無法重複建立。")

    os.makedirs(target_dir, exist_ok=True)
    os.makedirs(os.path.join(target_dir, "markdown"), exist_ok=True)
    os.makedirs(os.path.join(target_dir, "chroma_db"), exist_ok=True)

    # 建立專屬身分證
    now = datetime.now().isoformat()
    manifest_data = {
        "app": "DASH",
        "version": "1.1.0",
        "vault_id": f"v-{uuid.uuid4().hex[:12]}",
        "name": clean_name,
        "created_at": now,
        "updated_at": now,
        "description": description or f"本機 Vault: {clean_name}"
    }
    write_manifest(target_dir, manifest_data)

    # 初始化 SQLite 資料表結構
    from dash_backend import database
    database.init_db(get_db_path(clean_name))

    return {
        "name": clean_name,
        "path": target_dir,
        "manifest": manifest_data
    }


def ensure_default_vault() -> None:
    """開箱即用檢查：若 default Vault 不存在或無 manifest，自動初始化。"""
    default_dir = os.path.join(VAULTS_DIR, "default")
    manifest = read_manifest(default_dir)
    if not manifest:
        os.makedirs(default_dir, exist_ok=True)
        os.makedirs(os.path.join(default_dir, "markdown"), exist_ok=True)
        os.makedirs(os.path.join(default_dir, "chroma_db"), exist_ok=True)
        now = datetime.now().isoformat()
        manifest_data = {
            "app": "DASH",
            "version": "1.1.0",
            "vault_id": f"v-{uuid.uuid4().hex[:12]}",
            "name": "default",
            "created_at": now,
            "updated_at": now,
            "description": "開箱預設知識庫"
        }
        write_manifest(default_dir, manifest_data)
        from dash_backend import database
        database.init_db(os.path.join(default_dir, "dash_database.sqlite"))

    # 確保 config 存在且指向有效 vault
    cfg = load_config()
    current_active = cfg.get("active_vault", "default")
    if not os.path.exists(os.path.join(VAULTS_DIR, current_active)):
        cfg["active_vault"] = "default"
        save_config(cfg)


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


def get_vault_stats(vault_name: Optional[str] = None) -> Dict[str, Any]:
    """取得指定或當前 Vault 的資料庫統計概況。"""
    target_dir = get_vault_dir(vault_name)
    db_file = os.path.join(target_dir, "dash_database.sqlite")
    chroma_dir = os.path.join(target_dir, "chroma_db")
    markdown_dir = os.path.join(target_dir, "markdown")

    stats = {
        "vault_name": os.path.basename(target_dir),
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

    if os.path.exists(db_file):
        try:
            stats["db_size_bytes"] = os.path.getsize(db_file)
            conn = sqlite3.connect(db_file)
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

    stats["chroma_size_bytes"] = get_dir_size(chroma_dir)
    stats["markdown_size_bytes"] = get_dir_size(markdown_dir)
    stats["data_size_bytes"] = get_dir_size(target_dir)

    return stats


def list_vaults() -> List[Dict[str, Any]]:
    """列出 ~/.dash/vaults/ 底下所有合法的 Vault。"""
    ensure_default_vault()
    active_name = get_active_vault_name()
    vault_list = []

    if not os.path.exists(VAULTS_DIR):
        return vault_list

    for entry in os.listdir(VAULTS_DIR):
        entry_dir = os.path.join(VAULTS_DIR, entry)
        if not os.path.isdir(entry_dir):
            continue

        manifest = read_manifest(entry_dir)
        if not manifest:
            # 依嚴格防呆原則，缺少身分證者不列入合法 Vault
            continue

        is_active = (entry == active_name)
        stats = get_vault_stats(entry)
        vault_list.append({
            "name": entry,
            "display_name": manifest.get("name", entry),
            "vault_id": manifest.get("vault_id", ""),
            "path": entry_dir,
            "created_at": manifest.get("created_at"),
            "updated_at": manifest.get("updated_at"),
            "description": manifest.get("description", ""),
            "is_active": is_active,
            "stats": stats,
        })

    # 將目前使用中的 Vault 排序置頂，其餘按字母順序排列
    vault_list.sort(key=lambda x: (not x["is_active"], x["name"].lower()))
    return vault_list


def switch_vault(vault_name: str) -> Dict[str, Any]:
    """動態熱切換使用中的 Vault。"""
    clean_name = sanitize_vault_name(vault_name)
    target_dir = os.path.join(VAULTS_DIR, clean_name)
    if not os.path.exists(target_dir):
        raise FileNotFoundError(f"找不到指定的 Vault: {clean_name}")

    manifest = read_manifest(target_dir)
    if not manifest:
        raise ValueError(f"該目錄缺少合法 dash_manifest.json 身分證: {clean_name}")

    # 1. 寫入全域設定
    cfg = load_config()
    cfg["active_vault"] = clean_name
    save_config(cfg)

    # 2. 清空後端連線快取與向量庫實例
    from dash_backend import database
    database.reset_db_state()

    # 3. 確保目標資料庫 Schema 健全
    database.init_db(get_db_path(clean_name))

    return {
        "status": "success",
        "message": f"已成功切換至 Vault「{clean_name}」",
        "active_vault": clean_name,
        "manifest": manifest,
        "stats": get_vault_stats(clean_name)
    }


def rename_vault(old_name: str, new_name: str) -> Dict[str, Any]:
    """重新命名指定的 Vault。"""
    clean_old = sanitize_vault_name(old_name)
    clean_new = sanitize_vault_name(new_name)

    if not clean_new:
        raise ValueError("新 Vault 名稱不能為空。")

    old_dir = os.path.join(VAULTS_DIR, clean_old)
    new_dir = os.path.join(VAULTS_DIR, clean_new)

    if not os.path.exists(old_dir):
        raise FileNotFoundError(f"找不到欲更名的 Vault: {clean_old}")

    if clean_old == clean_new:
        return {"status": "success", "message": "名稱未變更", "name": clean_new}

    if os.path.exists(new_dir):
        raise ValueError(f"已存在同名的 Vault「{clean_new}」，無法更名。")

    # 若更名的是當前使用中的 Vault，先釋放連線
    active_name = get_active_vault_name()
    is_active = (clean_old == active_name)
    if is_active:
        from dash_backend import database
        database.reset_db_state()

    # 執行資料夾重新命名
    os.rename(old_dir, new_dir)

    # 更新 manifest 中的名稱
    manifest = read_manifest(new_dir) or {}
    manifest["name"] = clean_new
    manifest["updated_at"] = datetime.now().isoformat()
    write_manifest(new_dir, manifest)

    # 若為使用中的 Vault，同步更新全域設定檔
    if is_active:
        cfg = load_config()
        cfg["active_vault"] = clean_new
        save_config(cfg)

    return {
        "status": "success",
        "message": f"已成功將 Vault「{clean_old}」重新命名為「{clean_new}」",
        "old_name": clean_old,
        "new_name": clean_new,
        "manifest": manifest
    }


def delete_vault(vault_name: str) -> Dict[str, Any]:
    """刪除指定的非當前使用中 Vault。"""
    clean_name = sanitize_vault_name(vault_name)
    target_dir = os.path.join(VAULTS_DIR, clean_name)

    if not os.path.exists(target_dir):
        raise FileNotFoundError(f"找不到欲刪除的 Vault: {clean_name}")

    active_name = get_active_vault_name()
    if clean_name == active_name:
        raise ValueError("無法刪除當前使用中的 Vault！請先切換至其他 Vault 後再進行刪除。")

    shutil.rmtree(target_dir, ignore_errors=True)

    return {
        "status": "success",
        "message": f"已成功刪除 Vault「{clean_name}」",
        "deleted_vault": clean_name
    }


# ==========================================
# 5. DASH OUT (打包導出 ZIP)
# ==========================================

def export_vault_to_zip(vault_name: Optional[str] = None, output_zip_path: Optional[str] = None) -> str:
    """DASH OUT: 將指定或當前使用中的 Vault 打包為符合規範的 ZIP 檔案。"""
    target_name = sanitize_vault_name(vault_name) if vault_name else get_active_vault_name()
    target_dir = get_vault_dir(target_name)

    if not os.path.exists(target_dir):
        raise FileNotFoundError(f"找不到欲導出的 Vault 目錄: {target_name}")

    manifest = read_manifest(target_dir)
    if not manifest:
        raise ValueError(f"該 Vault 缺少合法 dash_manifest.json 身分證，無法導出: {target_name}")

    if not output_zip_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = os.path.join(TEMP_DIR, "exports")
        os.makedirs(export_dir, exist_ok=True)
        output_zip_path = os.path.join(export_dir, f"dash_{target_name}_{timestamp}.zip")

    stats = get_vault_stats(target_name)
    manifest_data = dict(manifest)
    manifest_data["exported_at"] = datetime.now().isoformat()
    manifest_data["stats"] = stats

    db_path = os.path.join(target_dir, "dash_database.sqlite")
    chroma_dir = os.path.join(target_dir, "chroma_db")
    markdown_dir = os.path.join(target_dir, "markdown")

    with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. 寫入包含統計資訊的最新簽名身分證
        zf.writestr("dash_manifest.json", json.dumps(manifest_data, ensure_ascii=False, indent=2))

        # 2. 寫入 SQLite 資料庫 (若存在)
        if os.path.exists(db_path):
            zf.write(db_path, arcname="dash_database.sqlite")

        # 3. 寫入 Chroma 向量庫
        if os.path.exists(chroma_dir):
            for root, _, files in os.walk(chroma_dir):
                for f in files:
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, target_dir)
                    zf.write(full_p, arcname=rel_p.replace("\\", "/"))

        # 4. 寫入 Markdown 託管檔案
        if os.path.exists(markdown_dir):
            for root, _, files in os.walk(markdown_dir):
                for f in files:
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, target_dir)
                    zf.write(full_p, arcname=rel_p.replace("\\", "/"))

    return output_zip_path


# ==========================================
# 6. DASH IN (匯入 ZIP 建立全新 Vault)
# ==========================================

def verify_vault_zip(zip_path: str) -> Dict[str, Any]:
    """檢驗傳入之 ZIP 是否為合法的 DASH 專屬資料包。"""
    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"找不到檔案: {zip_path}")

    if not zipfile.is_zipfile(zip_path):
        raise ValueError("上傳的檔案非有效的 ZIP 壓縮檔。")

    with zipfile.ZipFile(zip_path, "r") as zf:
        namelist = zf.namelist()

        if "dash_manifest.json" not in namelist:
            raise ValueError("非本系統 (DASH) 導出之資料包：找不到 dash_manifest.json 簽名檔。")

        try:
            manifest_bytes = zf.read("dash_manifest.json")
            manifest = json.loads(manifest_bytes.decode("utf-8"))
        except Exception as e:
            raise ValueError(f"dash_manifest.json 簽名解析失敗: {str(e)}")

        if manifest.get("app") != "DASH":
            raise ValueError("簽名內容無效：非 DASH 專屬資料包。")

        if "dash_database.sqlite" not in namelist:
            raise ValueError("資料包結構不完整：缺少 dash_database.sqlite 資料庫。")

        return manifest


def import_vault_from_zip(zip_path: str, target_name: Optional[str] = None) -> Dict[str, Any]:
    """DASH IN: 嚴格校驗資料包並將其解壓縮建立為一個『全新獨立的 Vault』並自動切換載入。"""
    manifest = verify_vault_zip(zip_path)

    # 決定新 Vault 的名稱（優先採用指定名稱，若無則依據 manifest 的原始名稱）
    raw_name = target_name or manifest.get("name") or "imported_vault"
    clean_name = sanitize_vault_name(raw_name)

    # 重名防呆：若已存在同名 Vault，自動後綴 _1, _2 等序號
    final_name = clean_name
    counter = 1
    while os.path.exists(os.path.join(VAULTS_DIR, final_name)):
        final_name = f"{clean_name}_{counter}"
        counter += 1

    new_vault_dir = os.path.join(VAULTS_DIR, final_name)
    os.makedirs(new_vault_dir, exist_ok=True)
    os.makedirs(os.path.join(new_vault_dir, "markdown"), exist_ok=True)
    os.makedirs(os.path.join(new_vault_dir, "chroma_db"), exist_ok=True)

    # 解壓縮檔案至全新 Vault 目錄
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            # 安全防範路徑穿越
            target_path = os.path.abspath(os.path.join(new_vault_dir, member.filename))
            if not target_path.startswith(os.path.abspath(new_vault_dir)):
                raise ValueError(f"不安全的壓縮包路徑: {member.filename}")
            zf.extract(member, new_vault_dir)

    # 更新 manifest 中的名稱與更新時間
    manifest["name"] = final_name
    manifest["updated_at"] = datetime.now().isoformat()
    write_manifest(new_vault_dir, manifest)

    # 切換至此全新 Vault
    switch_result = switch_vault(final_name)

    return {
        "status": "success",
        "message": f"已成功將資料包匯入為全新 Vault「{final_name}」並已自動切換載入！",
        "vault_name": final_name,
        "manifest": manifest,
        "stats": switch_result.get("stats", {})
    }
