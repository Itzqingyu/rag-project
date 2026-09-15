"""Schedule 的 SQLite CRUD 邏輯。"""

from typing import Any, Dict, List, Optional

from rag_project.activity_services.activity_common import (
    ensure_activity_exists,
    ensure_meeting_matches_activity,
    iso_datetime,
    optional_positive_id,
    positive_id,
    required_text,
    utc_now,
    validate_time_range,
)
from rag_project.database import get_connection, init_db


SCHEDULE_FIELDS = {
    "activity_id",
    "meeting_id",
    "name",
    "start_time",
    "end_time",
    "location",
    "owner",
    "notes",
    "category",
}


def _normalize_fields(values: Dict[str, Any]) -> Dict[str, Any]:
    normalized: Dict[str, Any] = {}
    for field_name, value in values.items():
        if field_name not in SCHEDULE_FIELDS:
            raise ValueError(f"不支援的 Schedule 欄位: {field_name}")
        if field_name == "activity_id":
            normalized[field_name] = positive_id(value, field_name)
        elif field_name == "meeting_id":
            normalized[field_name] = optional_positive_id(value, field_name)
        elif field_name == "start_time":
            normalized[field_name] = iso_datetime(value, field_name)
        elif field_name == "end_time":
            normalized[field_name] = iso_datetime(
                value, field_name, optional=True
            )
        else:
            normalized[field_name] = required_text(value, field_name)
    return normalized


def create_schedule(
    activity_id: int,
    name: str,
    start_time: str,
    location: str,
    owner: str,
    notes: str,
    category: str,
    end_time: Optional[str] = None,
    meeting_id: Optional[int] = None,
    *,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """建立活動流程，並驗證可選 Meeting 與 Activity 的一致性。"""
    values = _normalize_fields(
        {
            "activity_id": activity_id,
            "meeting_id": meeting_id,
            "name": name,
            "start_time": start_time,
            "end_time": end_time,
            "location": location,
            "owner": owner,
            "notes": notes,
            "category": category,
        }
    )
    validate_time_range(values["start_time"], values["end_time"])
    init_db(db_path)
    now = utc_now()

    with get_connection(db_path) as conn:
        ensure_activity_exists(conn, values["activity_id"])
        ensure_meeting_matches_activity(
            conn, values["meeting_id"], values["activity_id"]
        )
        cursor = conn.execute(
            """
            INSERT INTO schedules (
                activity_id, meeting_id, name, start_time, end_time, location,
                owner, notes, category, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                values["activity_id"],
                values["meeting_id"],
                values["name"],
                values["start_time"],
                values["end_time"],
                values["location"],
                values["owner"],
                values["notes"],
                values["category"],
                now,
                now,
            ),
        )
        schedule_id = cursor.lastrowid
        conn.commit()
        row = conn.execute(
            "SELECT * FROM schedules WHERE id = ?", (schedule_id,)
        ).fetchone()
    return dict(row)


def get_schedule(
    schedule_id: int, *, db_path: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    positive_id(schedule_id, "schedule_id")
    init_db(db_path)
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM schedules WHERE id = ?", (schedule_id,)
        ).fetchone()
    return dict(row) if row else None


def list_schedules(
    activity_id: Optional[int] = None, *, db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        if activity_id is None:
            rows = conn.execute(
                "SELECT * FROM schedules ORDER BY start_time, id"
            ).fetchall()
        else:
            normalized_id = ensure_activity_exists(conn, activity_id)
            rows = conn.execute(
                """
                SELECT * FROM schedules
                WHERE activity_id = ?
                ORDER BY start_time, id
                """,
                (normalized_id,),
            ).fetchall()
    return [dict(row) for row in rows]


def update_schedule(
    schedule_id: int,
    *,
    db_path: Optional[str] = None,
    **changes: Any,
) -> Optional[Dict[str, Any]]:
    positive_id(schedule_id, "schedule_id")
    if not changes:
        raise ValueError("至少需要提供一個要更新的欄位")
    normalized = _normalize_fields(changes)
    init_db(db_path)

    with get_connection(db_path) as conn:
        current_row = conn.execute(
            "SELECT * FROM schedules WHERE id = ?", (schedule_id,)
        ).fetchone()
        if current_row is None:
            return None
        current = dict(current_row)

        next_activity_id = normalized.get("activity_id", current["activity_id"])
        next_meeting_id = normalized.get("meeting_id", current["meeting_id"])
        next_start_time = normalized.get("start_time", current["start_time"])
        next_end_time = normalized.get("end_time", current["end_time"])
        ensure_activity_exists(conn, next_activity_id)
        ensure_meeting_matches_activity(conn, next_meeting_id, next_activity_id)
        validate_time_range(next_start_time, next_end_time)

        conflicting_incident = conn.execute(
            """
            SELECT 1 FROM incidents
            WHERE schedule_id = ? AND activity_id != ?
            LIMIT 1
            """,
            (schedule_id, next_activity_id),
        ).fetchone()
        if conflicting_incident is not None:
            raise ValueError("Schedule 已被其他 Activity 的 Incident 使用，無法變更 activity_id")

        assignments = [f"{field_name} = ?" for field_name in normalized]
        values = list(normalized.values())
        assignments.append("updated_at = ?")
        values.append(utc_now(after=current["updated_at"]))
        values.append(schedule_id)
        conn.execute(
            f"UPDATE schedules SET {', '.join(assignments)} WHERE id = ?", values
        )
        conn.commit()
        updated_row = conn.execute(
            "SELECT * FROM schedules WHERE id = ?", (schedule_id,)
        ).fetchone()
    return dict(updated_row)


def delete_schedule(
    schedule_id: int, *, db_path: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    positive_id(schedule_id, "schedule_id")
    init_db(db_path)
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM schedules WHERE id = ?", (schedule_id,)
        ).fetchone()
        if row is None:
            return None
        deleted = dict(row)
        conn.execute("DELETE FROM schedules WHERE id = ?", (schedule_id,))
        conn.commit()
    return deleted
