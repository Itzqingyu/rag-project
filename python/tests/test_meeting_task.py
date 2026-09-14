import os
import sqlite3
import sys
import tempfile
import unittest

PYTHON_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PYTHON_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from rag_project.activity_services.activity import create_activity, delete_activity, get_activity
from rag_project.activity_services.decision import create_decision, get_decision
from rag_project.activity_services.meeting_task import (
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
from rag_project.activity_services.schedule import create_schedule, get_schedule

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

    def test_activity_with_meeting_or_task_cannot_be_deleted(self):
        act_id = self.activity["id"]
        add_meeting(
            activity_id=act_id,
            name="保留歷史的會議",
            db_path=self.db_path,
        )
        with self.assertRaises(sqlite3.IntegrityError):
            delete_activity(act_id, db_path=self.db_path)

        task_activity = create_activity(
            name="只有待辦的活動",
            year=2026,
            status="籌備中",
            db_path=self.db_path,
        )
        add_task(
            activity_id=task_activity["id"],
            content="保留歷史的待辦",
            db_path=self.db_path,
        )
        with self.assertRaises(sqlite3.IntegrityError):
            delete_activity(task_activity["id"], db_path=self.db_path)

    def test_task_rejects_cross_activity_meeting(self):
        other_activity = create_activity(
            name="另一場活動",
            year=2026,
            status="籌備中",
            db_path=self.db_path,
        )
        meeting = add_meeting(
            activity_id=self.activity["id"],
            name="本活動會議",
            db_path=self.db_path,
        )

        with self.assertRaises(ValueError):
            add_task(
                activity_id=self.activity["id"],
                meeting_id=999,
                content="不存在會議的待辦",
                db_path=self.db_path,
            )

        with self.assertRaises(ValueError):
            add_task(
                activity_id=other_activity["id"],
                meeting_id=meeting["id"],
                content="錯誤跨活動待辦",
                db_path=self.db_path,
            )

        task = add_task(
            activity_id=self.activity["id"],
            meeting_id=meeting["id"],
            content="正確待辦",
            db_path=self.db_path,
        )
        with self.assertRaises(ValueError):
            update_task(
                task["id"],
                activity_id=other_activity["id"],
                db_path=self.db_path,
            )

    def test_meeting_and_task_store_content_without_reading_file_paths(self):
        content = os.path.join(
            os.path.dirname(__file__), "test_data", "sample.md"
        )
        meeting = add_meeting(
            activity_id=self.activity["id"],
            name="只儲存文字的會議",
            content=content,
            db_path=self.db_path,
        )
        task = add_task(
            activity_id=self.activity["id"],
            content=content,
            db_path=self.db_path,
        )

        self.assertEqual(meeting["content"], content)
        self.assertEqual(task["content"], content)

    def test_task_can_clear_meeting_id(self):
        meeting = add_meeting(
            activity_id=self.activity["id"],
            name="待解除的會議",
            db_path=self.db_path,
        )
        task = add_task(
            activity_id=self.activity["id"],
            meeting_id=meeting["id"],
            content="可解除會議關聯的待辦",
            db_path=self.db_path,
        )

        self.assertTrue(
            update_task(task["id"], meeting_id=None, db_path=self.db_path)
        )
        self.assertIsNone(
            get_task_by_id(task["id"], db_path=self.db_path)["meeting_id"]
        )

    def test_update_meeting_rejects_cross_activity_and_blank_time_is_safe(self):
        other_activity = create_activity(
            name="另一場活動",
            year=2026,
            status="籌備中",
            db_path=self.db_path,
        )
        meeting = add_meeting(
            activity_id=self.activity["id"],
            name="不可任意移動的會議",
            start_time="2026-10-01 10:00",
            db_path=self.db_path,
        )
        add_task(
            activity_id=self.activity["id"],
            meeting_id=meeting["id"],
            content="綁定會議的待辦",
            db_path=self.db_path,
        )

        with self.assertRaises(ValueError):
            update_meeting(
                meeting["id"],
                activity_id=other_activity["id"],
                db_path=self.db_path,
            )

        self.assertTrue(
            update_meeting(meeting["id"], start_time="", db_path=self.db_path)
        )
        updated = get_meeting_by_id(meeting["id"], db_path=self.db_path)
        self.assertEqual(updated["start_time"], "")
        self.assertEqual(updated["date"], "")

    def test_deleting_meeting_nulls_all_child_meeting_ids(self):
        meeting = add_meeting(
            activity_id=self.activity["id"],
            name="刪除後保留子資料的會議",
            db_path=self.db_path,
        )
        task = add_task(
            activity_id=self.activity["id"],
            meeting_id=meeting["id"],
            content="待辦",
            db_path=self.db_path,
        )
        decision = create_decision(
            activity_id=self.activity["id"],
            meeting_id=meeting["id"],
            problem="場地問題",
            options='["A館", "B館"]',
            final_decision="A館",
            reason="容量足夠",
            source="會議紀錄",
            db_path=self.db_path,
        )
        schedule = create_schedule(
            activity_id=self.activity["id"],
            meeting_id=meeting["id"],
            name="報到",
            start_time="2026-10-01T09:00:00+08:00",
            location="大廳",
            owner="小明",
            notes="準備名牌",
            category="活動中",
            db_path=self.db_path,
        )

        self.assertTrue(delete_meeting(meeting["id"], db_path=self.db_path))
        self.assertIsNone(get_task_by_id(task["id"], db_path=self.db_path)["meeting_id"])
        self.assertIsNone(
            get_decision(decision["id"], db_path=self.db_path)["meeting_id"]
        )
        self.assertIsNone(
            get_schedule(schedule["id"], db_path=self.db_path)["meeting_id"]
        )

if __name__ == "__main__":
    unittest.main()
