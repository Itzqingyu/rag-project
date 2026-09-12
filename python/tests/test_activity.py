import os
import sys
import tempfile
import unittest
from datetime import datetime


# 讓測試直接載入尚未安裝的 src package，不依賴 RAG 或 LLM 模組。
PYTHON_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PYTHON_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from rag_project.activity.service import (  # noqa: E402
    create_activity,
    delete_activity,
    get_activity,
    list_activities,
    update_activity,
)
from rag_project.database.sqlite_db import get_connection, init_db  # noqa: E402


class ActivityServiceTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "activity_test.sqlite")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_connection_enables_foreign_keys(self):
        with get_connection(self.db_path) as conn:
            enabled = conn.execute("PRAGMA foreign_keys").fetchone()[0]

        self.assertEqual(enabled, 1)

    def test_activities_table_contains_shared_schema(self):
        init_db(self.db_path)
        with get_connection(self.db_path) as conn:
            columns = {
                row["name"] for row in conn.execute("PRAGMA table_info(activities)")
            }

        self.assertEqual(
            columns,
            {
                "id",
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
                "created_at",
                "updated_at",
            },
        )

    def test_create_get_list_update_and_delete_activity(self):
        created = create_activity(
            name="2026 迎新宿營",
            year=2026,
            status="準備中",
            start_date="2026-09-20",
            end_date="2026-09-22",
            venue="高雄",
            activity_type="宿營",
            coordinator="小明",
            expected_attendees=120,
            budget=300000,
            db_path=self.db_path,
        )

        self.assertIsInstance(created, dict)
        self.assertIsInstance(created["id"], int)
        self.assertGreater(created["id"], 0)
        for timestamp_field in ("created_at", "updated_at"):
            timestamp = created[timestamp_field]
            parsed_timestamp = datetime.fromisoformat(timestamp)
            self.assertEqual(
                timestamp,
                parsed_timestamp.isoformat(timespec="microseconds"),
            )
        self.assertEqual(created, get_activity(created["id"], db_path=self.db_path))
        self.assertEqual([created], list_activities(db_path=self.db_path))

        updated = update_activity(
            created["id"],
            status="進行中",
            venue="台南",
            budget=320000,
            db_path=self.db_path,
        )
        self.assertEqual(updated["id"], created["id"])
        self.assertEqual(updated["status"], "進行中")
        self.assertEqual(updated["venue"], "台南")
        self.assertEqual(updated["budget"], 320000)
        self.assertNotEqual(updated["updated_at"], created["updated_at"])
        self.assertEqual(
            updated["updated_at"],
            datetime.fromisoformat(updated["updated_at"]).isoformat(
                timespec="microseconds"
            ),
        )

        deleted = delete_activity(created["id"], db_path=self.db_path)
        self.assertEqual(deleted["id"], created["id"])
        self.assertIsNone(get_activity(created["id"], db_path=self.db_path))
        self.assertEqual([], list_activities(db_path=self.db_path))

    def test_rejects_invalid_values_and_date_range(self):
        with self.assertRaises(ValueError):
            create_activity(name=" ", year=2026, status="準備中", db_path=self.db_path)

        with self.assertRaises(ValueError):
            create_activity(
                name="錯誤日期活動",
                year=2026,
                status="準備中",
                start_date="2026-09-22",
                end_date="2026-09-20",
                db_path=self.db_path,
            )

        with self.assertRaises(ValueError):
            create_activity(
                name="錯誤預算活動",
                year=2026,
                status="準備中",
                budget=-1,
                db_path=self.db_path,
            )

    def test_missing_activity_returns_none(self):
        self.assertIsNone(get_activity(999, db_path=self.db_path))
        self.assertIsNone(
            update_activity(999, status="完成", db_path=self.db_path)
        )
        self.assertIsNone(delete_activity(999, db_path=self.db_path))


if __name__ == "__main__":
    unittest.main()
