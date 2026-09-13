import os
import sys
import tempfile
import unittest

PYTHON_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PYTHON_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from rag_project.activity.service import create_activity, get_activity
from rag_project.meeting_task import (
    add_meeting,
    get_meetings,
    get_meeting_by_id,
    update_meeting,
    delete_meeting,
    add_task,
    get_tasks,
    get_task_by_id,
    update_task,
    delete_task,
)

class MeetingTaskServiceTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "meeting_task_test.sqlite")
        # Create default activity
        self.activity = create_activity(
            name="2026 年終成果展",
            year=2026,
            status="籌備中",
            db_path=self.db_path,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_meeting_crud(self):
        act_id = self.activity["id"]
        m = add_meeting(
            activity_id=act_id,
            name="籌備第一次會前會",
            start_time="2026-10-01 10:00",
            end_time="2026-10-01 12:00",
            location="301 會議室",
            participants="Alice, Bob",
            content="討論活動時程與分工",
            db_path=self.db_path,
        )

        self.assertIsNotNone(m)
        self.assertEqual(m["activity_id"], act_id)
        self.assertEqual(m["name"], "籌備第一次會前會")

        # Fetch meeting
        fetched = get_meeting_by_id(m["id"], db_path=self.db_path)
        self.assertEqual(fetched, m)

        # List meetings
        m_list = get_meetings(activity_id=act_id, db_path=self.db_path)
        self.assertEqual(len(m_list), 1)

        # Update meeting
        ok = update_meeting(m["id"], location="401 大型會議室", db_path=self.db_path)
        self.assertTrue(ok)
        updated = get_meeting_by_id(m["id"], db_path=self.db_path)
        self.assertEqual(updated["location"], "401 大型會議室")

        # Delete meeting
        deleted = delete_meeting(m["id"], db_path=self.db_path)
        self.assertTrue(deleted)
        self.assertIsNone(get_meeting_by_id(m["id"], db_path=self.db_path))

    def test_task_crud(self):
        act_id = self.activity["id"]
        m = add_meeting(
            activity_id=act_id,
            name="任務對齊會",
            db_path=self.db_path,
        )

        t = add_task(
            activity_id=act_id,
            content="訂購活動場地便當",
            assignee="Carol",
            due_date="2026-10-05",
            priority="高",
            meeting_id=m["id"],
            db_path=self.db_path,
        )

        self.assertIsNotNone(t)
        self.assertEqual(t["activity_id"], act_id)
        self.assertEqual(t["meeting_id"], m["id"])
        self.assertEqual(t["priority"], "高")
        self.assertEqual(t["status"], "pending")

        # List tasks
        tasks = get_tasks(activity_id=act_id, meeting_id=m["id"], db_path=self.db_path)
        self.assertEqual(len(tasks), 1)

        # Update task status
        ok = update_task(t["id"], status="completed", db_path=self.db_path)
        self.assertTrue(ok)
        updated_t = get_task_by_id(t["id"], db_path=self.db_path)
        self.assertEqual(updated_t["status"], "completed")

        # Delete task
        deleted = delete_task(t["id"], db_path=self.db_path)
        self.assertTrue(deleted)
        self.assertIsNone(get_task_by_id(t["id"], db_path=self.db_path))

    def test_foreign_key_cascade_deletion(self):
        act_id = self.activity["id"]
        m = add_meeting(
            activity_id=act_id,
            name="即將隨活動刪除的會議",
            db_path=self.db_path,
        )
        t = add_task(
            activity_id=act_id,
            content="即將隨活動刪除的待辦",
            meeting_id=m["id"],
            db_path=self.db_path,
        )

        # Verify items exist before deletion
        self.assertIsNotNone(get_meeting_by_id(m["id"], db_path=self.db_path))
        self.assertIsNotNone(get_task_by_id(t["id"], db_path=self.db_path))

        # Delete activity via direct SQL delete to trigger FK cascade
        from rag_project.database.sqlite_db import get_connection
        with get_connection(self.db_path) as conn:
            conn.execute("DELETE FROM activities WHERE id = ?", (act_id,))
            conn.commit()

        # Associated meetings and tasks should be deleted automatically via CASCADE
        self.assertEqual(get_meetings(activity_id=act_id, db_path=self.db_path), [])
        self.assertEqual(get_tasks(activity_id=act_id, db_path=self.db_path), [])

if __name__ == "__main__":
    unittest.main()
