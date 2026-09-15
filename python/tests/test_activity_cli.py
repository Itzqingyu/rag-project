import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from rag_project import database
from rag_project.activity_services.activity import create_activity
from rag_project.activity_services.decision import (
    create_decision,
    get_decision,
    list_decisions,
)
from rag_project.activity_services.incident import (
    create_incident,
    get_incident,
    list_incidents,
)
from rag_project.activity_services.meeting_task import (
    add_meeting,
    add_task,
    get_meetings,
    get_task_by_id,
    get_tasks,
)
from rag_project.activity_services.schedule import (
    create_schedule,
    get_schedule,
    list_schedules,
)
from rag_project.database import add_or_update_doc_record, get_connection
from tests import test_main as cli


class ActivityCliSmokeTest(unittest.TestCase):
    """以臨時 SQLite 驗證 Activity-first CLI，不碰正式資料庫或付費 LLM。"""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "activity_cli.sqlite")
        self.db_path_patch = patch.object(database, "DB_PATH", self.db_path)
        self.db_path_patch.start()
        self.activity_a = create_activity(
            name="CLI 活動 A", year=2026, status="籌備中"
        )
        self.activity_b = create_activity(
            name="CLI 活動 B", year=2026, status="籌備中"
        )

    def tearDown(self):
        self.db_path_patch.stop()
        self.temp_dir.cleanup()

    def test_child_lists_and_relation_choices_are_scoped_to_activity(self):
        meeting_a = add_meeting(
            activity_id=self.activity_a["id"], name="A 的會議"
        )
        add_meeting(activity_id=self.activity_b["id"], name="B 的會議")

        output = io.StringIO()
        with patch("builtins.input", side_effect=["2"]), redirect_stdout(output):
            cli.handle_meeting_menu(self.activity_a["id"])
        self.assertIn("A 的會議", output.getvalue())
        self.assertNotIn("B 的會議", output.getvalue())

        task_inputs = [
            "1",              # 新增 Task
            "確認交通",       # content
            "測試負責人",     # assignee
            "2026-09-20",    # due_date
            "1",              # priority: 高
            "1",              # status: pending
            "1",              # 目前 Activity 的 Meeting 清單第一筆
        ]
        with patch("builtins.input", side_effect=task_inputs), redirect_stdout(
            io.StringIO()
        ):
            cli.handle_task_menu(self.activity_a["id"])

        tasks = get_tasks(activity_id=self.activity_a["id"])
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["meeting_id"], meeting_a["id"])
        self.assertEqual(tasks[0]["priority"], "高")
        self.assertEqual(tasks[0]["status"], "pending")

    def test_ai_cli_records_current_document_on_created_meeting(self):
        file_path = os.path.join(self.temp_dir.name, "source.md")
        add_or_update_doc_record(
            file_path,
            1,
            markdown_content="# CLI AI 會議",
        )
        with get_connection() as conn:
            document_id = conn.execute(
                "SELECT id FROM documents WHERE file_path = ?", (file_path,)
            ).fetchone()["id"]

        extracted = {
            "meeting": {"name": "AI 解析會議", "content": "測試內容"},
            "decisions": [],
            "tasks": [],
        }
        with patch.object(
            cli, "extract_structured_meeting_data", return_value=extracted
        ), patch(
            # Activity 清單依 id DESC；第二個選項是先建立的 activity_a。
            "builtins.input", side_effect=[str(document_id), "y", "2"]
        ), redirect_stdout(io.StringIO()):
            cli.handle_ai_extract_and_commit()

        meetings = get_meetings(activity_id=self.activity_a["id"])
        self.assertEqual(len(meetings), 1)
        self.assertEqual(meetings[0]["source_document_id"], document_id)

    def test_decision_schedule_and_incident_cli_use_current_activity(self):
        meeting_a = add_meeting(
            activity_id=self.activity_a["id"], name="A 關聯會議"
        )
        add_meeting(activity_id=self.activity_b["id"], name="B 關聯會議")

        decision_inputs = [
            "2", "交通方式", "甲案,乙案", "乙案", "預算較低", "",
            "2",  # confirmation_status: confirmed
            "1",  # 只能選到 A 的 Meeting
        ]
        with patch("builtins.input", side_effect=decision_inputs), redirect_stdout(
            io.StringIO()
        ):
            cli.handle_decision_menu(self.activity_a["id"])

        schedule_inputs = [
            "2", "集合", "2026-09-15 08:00", "", "校門", "組長",
            "確認名單", "活動前", "1",
        ]
        with patch("builtins.input", side_effect=schedule_inputs), redirect_stdout(
            io.StringIO()
        ):
            cli.handle_schedule_menu(self.activity_a["id"])

        incident_inputs = [
            "2", "車輛晚到", "2026-09-15 08:10", "道路壅塞",
            "提早發車", "1",
        ]
        with patch("builtins.input", side_effect=incident_inputs), redirect_stdout(
            io.StringIO()
        ):
            cli.handle_incident_menu(self.activity_a["id"])

        decisions = list_decisions(activity_id=self.activity_a["id"])
        schedules = list_schedules(activity_id=self.activity_a["id"])
        incidents = list_incidents(activity_id=self.activity_a["id"])
        self.assertEqual(decisions[0]["meeting_id"], meeting_a["id"])
        self.assertEqual(decisions[0]["confirmation_status"], "confirmed")
        self.assertEqual(schedules[0]["meeting_id"], meeting_a["id"])
        self.assertEqual(incidents[0]["schedule_id"], schedules[0]["id"])
        self.assertEqual(list_decisions(activity_id=self.activity_b["id"]), [])
        self.assertEqual(list_schedules(activity_id=self.activity_b["id"]), [])
        self.assertEqual(list_incidents(activity_id=self.activity_b["id"]), [])

    def test_updates_keep_values_and_can_clear_optional_relations(self):
        """Enter 保留一般欄位，/clear 主動解除三種可選外鍵。"""
        meeting = add_meeting(
            activity_id=self.activity_a["id"], name="可解除關聯會議"
        )
        task = add_task(
            activity_id=self.activity_a["id"],
            meeting_id=meeting["id"],
            content="保留內容",
        )
        decision = create_decision(
            activity_id=self.activity_a["id"],
            meeting_id=meeting["id"],
            problem="保留問題",
            options='["甲", "乙"]',
            final_decision="甲",
            reason="測試",
            source="CLI",
        )
        schedule = create_schedule(
            activity_id=self.activity_a["id"],
            meeting_id=meeting["id"],
            name="保留流程",
            start_time="2026-09-15 09:00",
            location="測試地點",
            owner="測試負責人",
            notes="測試",
            category="活動中",
        )
        incident = create_incident(
            activity_id=self.activity_a["id"],
            schedule_id=schedule["id"],
            content="保留事件",
            occurred_at="2026-09-15 09:10",
        )

        task_inputs = ["3", "1", "", "", "", "", "", "/clear"]
        with patch("builtins.input", side_effect=task_inputs), redirect_stdout(
            io.StringIO()
        ):
            cli.handle_task_menu(self.activity_a["id"])

        decision_inputs = ["3", "1", "", "", "", "", "", "", "/clear"]
        with patch("builtins.input", side_effect=decision_inputs), redirect_stdout(
            io.StringIO()
        ):
            cli.handle_decision_menu(self.activity_a["id"])

        schedule_inputs = [
            "3", "1", "", "", "", "", "", "", "", "/clear"
        ]
        with patch("builtins.input", side_effect=schedule_inputs), redirect_stdout(
            io.StringIO()
        ):
            cli.handle_schedule_menu(self.activity_a["id"])

        incident_inputs = ["3", "1", "", "", "", "", "/clear"]
        with patch("builtins.input", side_effect=incident_inputs), redirect_stdout(
            io.StringIO()
        ):
            cli.handle_incident_menu(self.activity_a["id"])

        self.assertEqual(get_task_by_id(task["id"])["content"], "保留內容")
        self.assertIsNone(get_task_by_id(task["id"])["meeting_id"])
        self.assertEqual(get_decision(decision["id"])["problem"], "保留問題")
        self.assertIsNone(get_decision(decision["id"])["meeting_id"])
        self.assertEqual(get_schedule(schedule["id"])["name"], "保留流程")
        self.assertIsNone(get_schedule(schedule["id"])["meeting_id"])
        self.assertEqual(get_incident(incident["id"])["content"], "保留事件")
        self.assertIsNone(get_incident(incident["id"])["schedule_id"])

    def test_zero_returns_through_child_menus_without_losing_activity(self):
        """五個子選單的 0 回工作區，工作區的 0 才回主選單。"""
        inputs = [
            "1", "0",  # Meeting -> 工作區
            "2", "0",  # Task -> 工作區
            "3", "0",  # Decision -> 工作區
            "4", "0",  # Schedule -> 工作區
            "5", "0",  # Incident -> 工作區
            "0",        # Activity 工作區 -> 主選單
        ]
        output = io.StringIO()
        with patch("builtins.input", side_effect=inputs), redirect_stdout(output):
            cli.handle_activity_workspace(self.activity_a["id"])

        rendered = output.getvalue()
        self.assertGreaterEqual(rendered.count("CLI 活動 A"), 6)
        self.assertNotIn("CLI 活動 B", rendered)
        self.assertIn("0. 回上一層", rendered)
        self.assertIn("0. 回主選單", rendered)

    def test_other_management_submenus_can_return_without_exiting(self):
        """Activity 管理與額外模組入口的 0 都只返回主選單。"""
        with patch("builtins.input", side_effect=["0"]), redirect_stdout(
            io.StringIO()
        ):
            cli.handle_activity_menu()
        with patch("builtins.input", side_effect=["0"]), redirect_stdout(
            io.StringIO()
        ):
            cli.handle_extra_menu(self.activity_a["id"])

    def test_main_menu_can_start_and_exit(self):
        with patch("builtins.input", side_effect=["0"]), redirect_stdout(
            io.StringIO()
        ), self.assertRaises(SystemExit) as exit_context:
            cli.main()
        self.assertEqual(exit_context.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
