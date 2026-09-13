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

from rag_project.activity.service import create_activity, delete_activity  # noqa: E402
from rag_project.schedule.service import (  # noqa: E402
    create_schedule,
    delete_schedule,
    get_schedule,
    list_schedules,
    update_schedule,
)


class ScheduleServiceTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "schedule_test.sqlite")
        self.activity = create_activity(
            name="迎新活動",
            year=2026,
            status="準備中",
            db_path=self.db_path,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def _create_schedule(self):
        return create_schedule(
            activity_id=self.activity["id"],
            meeting_id=8,
            name="報到",
            start_time="2026-09-20T08:00:00+08:00",
            end_time="2026-09-20T09:00:00+08:00",
            location="活動中心",
            owner="小明",
            notes="準備名牌",
            category="活動中",
            db_path=self.db_path,
        )

    def test_create_get_list_update_and_delete_schedule(self):
        created = self._create_schedule()

        self.assertIsInstance(created, dict)
        self.assertEqual(created["activity_id"], self.activity["id"])
        self.assertEqual(created["meeting_id"], 8)
        for field_name in ("created_at", "updated_at"):
            timestamp = created[field_name]
            self.assertEqual(
                timestamp,
                datetime.fromisoformat(timestamp).isoformat(timespec="microseconds"),
            )
        self.assertEqual(created, get_schedule(created["id"], db_path=self.db_path))
        self.assertEqual(
            [created], list_schedules(self.activity["id"], db_path=self.db_path)
        )

        updated = update_schedule(
            created["id"],
            name="開幕",
            end_time=None,
            notes="主持人提前就位",
            db_path=self.db_path,
        )
        self.assertEqual(updated["name"], "開幕")
        self.assertIsNone(updated["end_time"])
        self.assertEqual(updated["notes"], "主持人提前就位")
        self.assertNotEqual(updated["updated_at"], created["updated_at"])

        deleted = delete_schedule(created["id"], db_path=self.db_path)
        self.assertEqual(deleted["id"], created["id"])
        self.assertIsNone(get_schedule(created["id"], db_path=self.db_path))

    def test_rejects_missing_activity_and_invalid_time_range(self):
        with self.assertRaises(ValueError):
            create_schedule(
                activity_id=999,
                name="報到",
                start_time="2026-09-20T08:00:00",
                location="活動中心",
                owner="小明",
                notes="無",
                category="活動中",
                db_path=self.db_path,
            )
        with self.assertRaises(ValueError):
            create_schedule(
                activity_id=self.activity["id"],
                name="報到",
                start_time="2026-09-20T09:00:00",
                end_time="2026-09-20T08:00:00",
                location="活動中心",
                owner="小明",
                notes="無",
                category="活動中",
                db_path=self.db_path,
            )

        created = self._create_schedule()
        with self.assertRaises(ValueError):
            update_schedule(
                created["id"],
                start_time="2026-09-20T10:00:00+08:00",
                db_path=self.db_path,
            )

    def test_activity_with_schedule_cannot_be_deleted(self):
        self._create_schedule()
        with self.assertRaises(sqlite3.IntegrityError):
            delete_activity(self.activity["id"], db_path=self.db_path)

    def test_missing_schedule_returns_none(self):
        self.assertIsNone(get_schedule(999, db_path=self.db_path))
        self.assertIsNone(update_schedule(999, name="新流程", db_path=self.db_path))
        self.assertIsNone(delete_schedule(999, db_path=self.db_path))


if __name__ == "__main__":
    unittest.main()
