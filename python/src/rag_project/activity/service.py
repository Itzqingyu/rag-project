"""Activity 的 SQLite CRUD 邏輯。"""

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from rag_project.database.sqlite_db import get_connection, init_db


ACTIVITY_FIELDS = {
    "name",
    "year",
    "status",
    "start_date",
    "end_date",
    "venue",
    "activity_type",
    "coordinator",
    "expected_attendees",
    "budget",
}


def _utc_now(after: Optional[str] = None) -> str:
    """回傳固定微秒精度的 UTC ISO 8601 時間，並可保證晚於指定時間。"""
    now = datetime.now(timezone.utc)
    if after is not None:
        previous = datetime.fromisoformat(after.replace("Z", "+00:00"))
        if previous.tzinfo is None:
            previous = previous.replace(tzinfo=timezone.utc)
        if now <= previous:
            now = previous + timedelta(microseconds=1)
    return now.isoformat(timespec="microseconds")


def _validate_activity_id(activity_id: int) -> None:
    if isinstance(activity_id, bool) or not isinstance(activity_id, int) or activity_id <= 0:
        raise ValueError("activity_id 必須是正整數")


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} 不可為空")
    return value.strip()


def _optional_text(value: Any, field_name: str) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} 必須是字串或 None")
    normalized = value.strip()
    return normalized or None


def _positive_year(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError("year 必須是正整數")
    return value


def _optional_non_negative_int(value: Any, field_name: str) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field_name} 必須是非負整數或 None")
    return value


def _optional_date(value: Any, field_name: str) -> Optional[str]:
    """驗證並標準化 YYYY-MM-DD 日期；尚未確定時可傳入 None。"""
    normalized = _optional_text(value, field_name)
    if normalized is None:
        return None
    try:
        return date.fromisoformat(normalized).isoformat()
    except ValueError as exc:
        raise ValueError(f"{field_name} 必須使用 YYYY-MM-DD 格式") from exc


def _normalize_fields(values: Dict[str, Any]) -> Dict[str, Any]:
    """集中驗證欄位，讓 create 與 update 使用相同資料規格。"""
    normalized: Dict[str, Any] = {}

    for field_name, value in values.items():
        if field_name not in ACTIVITY_FIELDS:
            raise ValueError(f"不支援的 Activity 欄位: {field_name}")

        if field_name in {"name", "status"}:
            normalized[field_name] = _required_text(value, field_name)
        elif field_name == "year":
            normalized[field_name] = _positive_year(value)
        elif field_name in {"start_date", "end_date"}:
            normalized[field_name] = _optional_date(value, field_name)
        elif field_name in {"expected_attendees", "budget"}:
            normalized[field_name] = _optional_non_negative_int(value, field_name)
        else:
            normalized[field_name] = _optional_text(value, field_name)

    return normalized


def _validate_date_range(start_date: Optional[str], end_date: Optional[str]) -> None:
    if start_date is not None and end_date is not None and end_date < start_date:
        raise ValueError("end_date 不可早於 start_date")


def create_activity(
    name: str,
    year: int,
    status: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    venue: Optional[str] = None,
    activity_type: Optional[str] = None,
    coordinator: Optional[str] = None,
    expected_attendees: Optional[int] = None,
    budget: Optional[int] = None,
    *,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """建立活動並回傳完整資料；回傳的 id 即為其他模組使用的 activity_id。"""
    values = _normalize_fields(
        {
            "name": name,
            "year": year,
            "status": status,
            "start_date": start_date,
            "end_date": end_date,
            "venue": venue,
            "activity_type": activity_type,
            "coordinator": coordinator,
            "expected_attendees": expected_attendees,
            "budget": budget,
        }
    )
    _validate_date_range(values["start_date"], values["end_date"])
    init_db(db_path)

    now = _utc_now()
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO activities (
                name, year, status, start_date, end_date, venue,
                activity_type, coordinator, expected_attendees, budget,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                values["name"],
                values["year"],
                values["status"],
                values["start_date"],
                values["end_date"],
                values["venue"],
                values["activity_type"],
                values["coordinator"],
                values["expected_attendees"],
                values["budget"],
                now,
                now,
            ),
        )
        activity_id = cursor.lastrowid
        conn.commit()

        # 在同一連線讀回完整紀錄，確保呼叫端立即拿到 activity_id。
        row = conn.execute(
            "SELECT * FROM activities WHERE id = ?", (activity_id,)
        ).fetchone()

    return dict(row)


def get_activity(activity_id: int, *, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """依 activity_id 取得單一活動；不存在時回傳 None。"""
    _validate_activity_id(activity_id)
    init_db(db_path)

    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM activities WHERE id = ?", (activity_id,)
        ).fetchone()
    return dict(row) if row else None


def list_activities(*, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """列出所有活動，依年份與流水號由新到舊排序。"""
    init_db(db_path)

    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM activities ORDER BY year DESC, id DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def update_activity(
    activity_id: int,
    *,
    db_path: Optional[str] = None,
    **changes: Any,
) -> Optional[Dict[str, Any]]:
    """局部更新活動並回傳更新後資料；不存在時回傳 None。"""
    _validate_activity_id(activity_id)
    if not changes:
        raise ValueError("至少需要提供一個要更新的欄位")

    normalized = _normalize_fields(changes)
    init_db(db_path)

    with get_connection(db_path) as conn:
        current_row = conn.execute(
            "SELECT * FROM activities WHERE id = ?", (activity_id,)
        ).fetchone()
        if current_row is None:
            return None

        current = dict(current_row)
        next_start_date = normalized.get("start_date", current["start_date"])
        next_end_date = normalized.get("end_date", current["end_date"])
        _validate_date_range(next_start_date, next_end_date)

        assignments = [f"{field_name} = ?" for field_name in normalized]
        values = list(normalized.values())
        assignments.append("updated_at = ?")
        values.append(_utc_now(after=current["updated_at"]))
        values.append(activity_id)

        conn.execute(
            f"UPDATE activities SET {', '.join(assignments)} WHERE id = ?",
            values,
        )
        conn.commit()
        updated_row = conn.execute(
            "SELECT * FROM activities WHERE id = ?", (activity_id,)
        ).fetchone()

    return dict(updated_row)


def delete_activity(
    activity_id: int, *, db_path: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """刪除活動並回傳被刪除的資料；不存在時回傳 None。"""
    _validate_activity_id(activity_id)
    init_db(db_path)

    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM activities WHERE id = ?", (activity_id,)
        ).fetchone()
        if row is None:
            return None

        deleted = dict(row)
        # 未來子表使用 ON DELETE RESTRICT 時，SQLite 會在這裡阻止誤刪。
        conn.execute("DELETE FROM activities WHERE id = ?", (activity_id,))
        conn.commit()

    return deleted
