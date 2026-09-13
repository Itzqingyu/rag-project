import os
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime


PYTHON_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PYTHON_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from rag_project.activity import create_activity, delete_activity  # noqa: E402
from rag_project.incident import (  # noqa: E402
    create_incident,
    delete_incident,
    get_incident,
    list_incidents,
    update_incident,
)
from rag_project.schedule import create_schedule, delete_schedule  # noqa: E402
from rag_project.database import get_connection, init_db  # noqa: E402


class IncidentServiceTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "incident_test.sqlite")
        self.activity = self._create_activity("迎新活動")
        self.other_activity = self._create_activity("送舊活動")
        self.schedule = self._create_schedule(self.activity["id"])

    def tearDown(self):
        self.temp_dir.cleanup()

    def _create_activity(self, name):
        return create_activity(
            name=name,
            year=2026,
            status="準備中",
            db_path=self.db_path,
        )

    def _create_schedule(self, activity_id):
        return create_schedule(
            activity_id=activity_id,
            name="團康",
            start_time="2026-09-20T14:00:00+08:00",
            end_time="2026-09-20T15:00:00+08:00",
            location="操場",
            owner="小華",
            notes="準備音響",
            category="活動中",
            db_path=self.db_path,
        )

    def _create_incident(self, **overrides):
        values = {
            "activity_id": self.activity["id"],
            "schedule_id": self.schedule["id"],
            "content": "音響臨時無法啟動",
            "occurred_at": "2026-09-20T14:10:00+08:00",
            "cause": None,
            "suggestion": None,
        }
        values.update(overrides)
        return create_incident(db_path=self.db_path, **values)

    def test_create_get_list_update_and_delete_incident(self):
        created = self._create_incident()

        self.assertIsInstance(created, dict)
        self.assertEqual(created["activity_id"], self.activity["id"])
        self.assertEqual(created["schedule_id"], self.schedule["id"])
        self.assertIsNone(created["cause"])
        for field_name in ("created_at", "updated_at"):
            timestamp = created[field_name]
            self.assertEqual(
                timestamp,
                datetime.fromisoformat(timestamp).isoformat(timespec="microseconds"),
            )
        self.assertEqual(created, get_incident(created["id"], db_path=self.db_path))
        self.assertEqual(
            [created], list_incidents(self.activity["id"], db_path=self.db_path)
        )

        updated = update_incident(
            created["id"],
            cause="電源線鬆脫",
            suggestion="活動前增加設備檢查表",
            schedule_id=None,
            db_path=self.db_path,
        )
        self.assertEqual(updated["cause"], "電源線鬆脫")
        self.assertEqual(updated["suggestion"], "活動前增加設備檢查表")
        self.assertIsNone(updated["schedule_id"])
        self.assertNotEqual(updated["updated_at"], created["updated_at"])

        deleted = delete_incident(created["id"], db_path=self.db_path)
        self.assertEqual(deleted["id"], created["id"])
        self.assertIsNone(get_incident(created["id"], db_path=self.db_path))

    def test_rejects_missing_activity_and_cross_activity_schedule(self):
        with self.assertRaises(ValueError):
            self._create_incident(activity_id=999, schedule_id=None)
        with self.assertRaises(ValueError):
            self._create_incident(activity_id=self.other_activity["id"])
        with self.assertRaises(ValueError):
            self._create_incident(schedule_id=999)

        created = self._create_incident()
        with self.assertRaises(ValueError):
            update_incident(
                created["id"],
                activity_id=self.other_activity["id"],
                db_path=self.db_path,
            )

    def test_deleting_schedule_keeps_incident_and_nulls_schedule_id(self):
        created = self._create_incident()

        delete_schedule(self.schedule["id"], db_path=self.db_path)

        remaining = get_incident(created["id"], db_path=self.db_path)
        self.assertIsNotNone(remaining)
        self.assertIsNone(remaining["schedule_id"])

    def test_activity_with_incident_cannot_be_deleted(self):
        incident_only_activity = self._create_activity("只有臨時紀錄的活動")
        create_incident(
            activity_id=incident_only_activity["id"],
            content="下雨",
            occurred_at="2026-09-20T16:00:00+08:00",
            db_path=self.db_path,
        )
        with self.assertRaises(sqlite3.IntegrityError):
            delete_activity(incident_only_activity["id"], db_path=self.db_path)

    def test_schema_uses_required_foreign_key_actions(self):
        init_db(self.db_path)
        with get_connection(self.db_path) as conn:
            meeting_fks = {
                (row["from"], row["table"], row["to"], row["on_delete"])
                for row in conn.execute("PRAGMA foreign_key_list(meetings)")
            }
            task_fks = {
                (row["from"], row["table"], row["to"], row["on_delete"])
                for row in conn.execute("PRAGMA foreign_key_list(tasks)")
            }
            decision_fks = {
                (row["from"], row["table"], row["to"], row["on_delete"])
                for row in conn.execute("PRAGMA foreign_key_list(decisions)")
            }
            schedule_fks = {
                (row["from"], row["table"], row["to"], row["on_delete"])
                for row in conn.execute("PRAGMA foreign_key_list(schedules)")
            }
            incident_fks = {
                (row["from"], row["table"], row["to"], row["on_delete"])
                for row in conn.execute("PRAGMA foreign_key_list(incidents)")
            }

        self.assertEqual(
            meeting_fks,
            {("activity_id", "activities", "id", "RESTRICT")},
        )
        self.assertEqual(
            task_fks,
            {
                ("activity_id", "activities", "id", "RESTRICT"),
                ("meeting_id", "meetings", "id", "SET NULL"),
            },
        )
        self.assertEqual(
            decision_fks,
            {
                ("activity_id", "activities", "id", "RESTRICT"),
                ("meeting_id", "meetings", "id", "SET NULL"),
            },
        )
        self.assertEqual(
            schedule_fks,
            {
                ("activity_id", "activities", "id", "RESTRICT"),
                ("meeting_id", "meetings", "id", "SET NULL"),
            },
        )
        self.assertEqual(
            incident_fks,
            {
                ("activity_id", "activities", "id", "RESTRICT"),
                ("schedule_id", "schedules", "id", "SET NULL"),
            },
        )

    def test_missing_incident_returns_none(self):
        self.assertIsNone(get_incident(999, db_path=self.db_path))
        self.assertIsNone(
            update_incident(999, content="更新", db_path=self.db_path)
        )
        self.assertIsNone(delete_incident(999, db_path=self.db_path))


if __name__ == "__main__":
    unittest.main()
