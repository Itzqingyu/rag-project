import json
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
from rag_project.decision import (  # noqa: E402
    create_decision,
    delete_decision,
    get_decision,
    list_decisions,
    update_decision,
)
from rag_project.meeting_task import add_meeting  # noqa: E402


class DecisionServiceTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "decision_test.sqlite")
        self.activity = create_activity(
            name="迎新活動",
            year=2026,
            status="準備中",
            db_path=self.db_path,
        )
        self.meeting = add_meeting(
            activity_id=self.activity["id"],
            name="決策來源會議",
            db_path=self.db_path,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def _create_decision(self):
        return create_decision(
            activity_id=self.activity["id"],
            meeting_id=self.meeting["id"],
            problem="雨天場地如何安排？",
            options='["延期", "改室內"]',
            final_decision="改室內",
            reason="避免影響出席率",
            source="三籌會議紀錄",
            db_path=self.db_path,
        )

    def test_create_get_list_update_and_delete_decision(self):
        created = self._create_decision()

        self.assertIsInstance(created, dict)
        self.assertEqual(created["activity_id"], self.activity["id"])
        self.assertEqual(created["meeting_id"], self.meeting["id"])
        self.assertEqual(json.loads(created["options"]), ["延期", "改室內"])
        self.assertEqual(created["confirmation_status"], "pending")
        for field_name in ("created_at", "updated_at"):
            timestamp = created[field_name]
            self.assertEqual(
                timestamp,
                datetime.fromisoformat(timestamp).isoformat(timespec="microseconds"),
            )
        self.assertEqual(created, get_decision(created["id"], db_path=self.db_path))
        self.assertEqual(
            [created], list_decisions(self.activity["id"], db_path=self.db_path)
        )

        updated = update_decision(
            created["id"],
            final_decision="延期",
            confirmation_status="confirmed",
            meeting_id=None,
            db_path=self.db_path,
        )
        self.assertEqual(updated["final_decision"], "延期")
        self.assertEqual(updated["confirmation_status"], "confirmed")
        self.assertIsNone(updated["meeting_id"])
        self.assertNotEqual(updated["updated_at"], created["updated_at"])

        deleted = delete_decision(created["id"], db_path=self.db_path)
        self.assertEqual(deleted["id"], created["id"])
        self.assertIsNone(get_decision(created["id"], db_path=self.db_path))

    def test_rejects_missing_activity_and_invalid_values(self):
        with self.assertRaises(ValueError):
            create_decision(
                activity_id=999,
                problem="問題",
                options='["A"]',
                final_decision="A",
                reason="原因",
                source="人工輸入",
                db_path=self.db_path,
            )
        with self.assertRaises(ValueError):
            create_decision(
                activity_id=self.activity["id"],
                problem="問題",
                options='["A"]',
                final_decision="A",
                reason="原因",
                source="人工輸入",
                confirmation_status="approved",
                db_path=self.db_path,
            )
        with self.assertRaises(ValueError):
            create_decision(
                activity_id=self.activity["id"],
                problem=" ",
                options='["A"]',
                final_decision="A",
                reason="原因",
                source="人工輸入",
                db_path=self.db_path,
            )
        with self.assertRaises(ValueError):
            create_decision(
                activity_id=self.activity["id"],
                problem="問題",
                options="不是 JSON",
                final_decision="A",
                reason="原因",
                source="人工輸入",
                db_path=self.db_path,
            )

    def test_activity_with_decision_cannot_be_deleted(self):
        self._create_decision()
        with self.assertRaises(sqlite3.IntegrityError):
            delete_activity(self.activity["id"], db_path=self.db_path)

    def test_rejects_cross_activity_meeting_on_create_and_update(self):
        other_activity = create_activity(
            name="另一場活動",
            year=2026,
            status="準備中",
            db_path=self.db_path,
        )
        with self.assertRaises(ValueError):
            create_decision(
                activity_id=self.activity["id"],
                meeting_id=999,
                problem="不存在會議",
                options='["A"]',
                final_decision="A",
                reason="原因",
                source="會議紀錄",
                db_path=self.db_path,
            )
        with self.assertRaises(ValueError):
            create_decision(
                activity_id=other_activity["id"],
                meeting_id=self.meeting["id"],
                problem="跨活動問題",
                options='["A"]',
                final_decision="A",
                reason="原因",
                source="會議紀錄",
                db_path=self.db_path,
            )

        decision = self._create_decision()
        with self.assertRaises(ValueError):
            update_decision(
                decision["id"],
                activity_id=other_activity["id"],
                db_path=self.db_path,
            )

    def test_missing_decision_returns_none(self):
        self.assertIsNone(get_decision(999, db_path=self.db_path))
        self.assertIsNone(
            update_decision(999, problem="新問題", db_path=self.db_path)
        )
        self.assertIsNone(delete_decision(999, db_path=self.db_path))


if __name__ == "__main__":
    unittest.main()
