"""對話會話 (Session)、上下文記憶與模式切換單元測試。

驗證：
1. Session 資料表與訊息表 CRUD (含 CASCADE 刪除)。
2. Clean Context Isolation 乾淨隔離機制：驗證多輪對話歷史只保留純文字，當輪 RAG 檢索資料不污染後續上下文。
3. 普通聊天模式 (chat) 與 RAG 知識庫模式 (rag) 自由切換。
4. FastAPI REST API 端點 (/sessions, /sessions/{id}/messages)。
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# 將 src 目錄加入 sys.path
PYTHON_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PYTHON_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from rag_project.database import (
    init_db,
    create_session,
    get_session,
    list_sessions,
    update_session_title,
    delete_session,
    add_chat_message,
    get_chat_messages,
)
from rag_project.document_processing.llm_service import chat_with_context
from fastapi.testclient import TestClient
from rag_project.main import app


class TestChatSession(unittest.TestCase):
    def setUp(self):
        """為每個測試案例建立臨時 SQLite 資料庫以維持測試隔離性。"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = os.path.join(self.temp_dir, "test_chat.sqlite")
        init_db(self.temp_db)

    def tearDown(self):
        """清理臨時檔案。"""
        if os.path.exists(self.temp_db):
            os.remove(self.temp_db)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_session_crud_and_cascade_delete(self):
        """測試 Session 的建立、查詢、修改標題、新增訊息與 CASCADE 串聯刪除。"""
        # 1. 建立 Session
        s1 = create_session(title="第一次討論", db_path=self.temp_db)
        self.assertIsNotNone(s1["id"])
        self.assertEqual(s1["title"], "第一次討論")

        # 2. 查詢 Session
        retrieved = get_session(s1["id"], db_path=self.temp_db)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["title"], "第一次討論")

        # 3. 更新標題
        updated = update_session_title(s1["id"], "第二次討論修訂版", db_path=self.temp_db)
        self.assertTrue(updated)
        retrieved_again = get_session(s1["id"], db_path=self.temp_db)
        self.assertEqual(retrieved_again["title"], "第二次討論修訂版")

        # 4. 新增訊息
        msg1 = add_chat_message(
            session_id=s1["id"],
            role="user",
            content="你好，請問專案進度如何？",
            mode="chat",
            db_path=self.temp_db
        )
        msg2 = add_chat_message(
            session_id=s1["id"],
            role="assistant",
            content="目前進度良好！",
            mode="chat",
            db_path=self.temp_db
        )
        self.assertEqual(msg1["role"], "user")
        self.assertEqual(msg2["role"], "assistant")

        # 5. 查詢訊息
        messages = get_chat_messages(s1["id"], db_path=self.temp_db)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["content"], "你好，請問專案進度如何？")
        self.assertEqual(messages[1]["content"], "目前進度良好！")

        # 6. 刪除 Session 測試 CASCADE
        del_success = delete_session(s1["id"], db_path=self.temp_db)
        self.assertTrue(del_success)
        self.assertIsNone(get_session(s1["id"], db_path=self.temp_db))
        
        # 關聯的 chat_messages 應已被串聯刪除
        remaining_messages = get_chat_messages(s1["id"], db_path=self.temp_db)
        self.assertEqual(len(remaining_messages), 0)

    def test_chat_message_metadata_and_limit(self):
        """測試 RAG 模式下 chunks JSON metadata 的儲存與反序列化，以及 limit 功能。"""
        s = create_session(title="測試檢索記錄", db_path=self.temp_db)
        chunks = [
            {"content": "這是第一份會議紀錄片段", "metadata": {"source": "doc1.md"}},
            {"content": "這是第二份會議紀錄片段", "metadata": {"source": "doc2.md"}}
        ]
        
        add_chat_message(
            session_id=s["id"],
            role="assistant",
            content="根據文件，結論如下...",
            mode="rag",
            retrieved_chunks=chunks,
            db_path=self.temp_db
        )

        msgs = get_chat_messages(s["id"], db_path=self.temp_db)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]["mode"], "rag")
        self.assertIsInstance(msgs[0]["retrieved_chunks"], list)
        self.assertEqual(len(msgs[0]["retrieved_chunks"]), 2)
        self.assertEqual(msgs[0]["retrieved_chunks"][0]["metadata"]["source"], "doc1.md")

    @patch("rag_project.document_processing.llm_service.completion")
    def test_clean_context_isolation(self, mock_completion):
        """驗證 Clean Context Isolation 防記憶污染機制：
        歷史上下文不應被前次 RAG 注入的大段【參考資料】污染。
        """
        # Mock LLM response
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock(message=MagicMock(content="這是 AI 模擬回答"))]
        mock_completion.return_value = mock_resp

        # 模擬過去的對話歷史 (純淨對話)
        history = [
            {"role": "user", "content": "上次會議由誰主持？"},
            {"role": "assistant", "content": "上次會議由王經理主持。"}
        ]

        # 第 2 次發起 RAG 模式
        new_query = "這次預算通過了嗎？"
        chunks = ["預算審核結果：已通過新台幣 50 萬元。"]

        chat_with_context(
            user_query=new_query,
            history_messages=history,
            mode="rag",
            retrieved_chunks=chunks,
            max_history_turns=5
        )

        # 檢驗 mock_completion 所接收到的 messages
        call_args = mock_completion.call_args[1]
        sent_messages = call_args["messages"]

        # 驗證：
        # 1. 第一個是 System Prompt
        self.assertEqual(sent_messages[0]["role"], "system")
        # 2. 第二個是第 1 輪歷史 user query (純問題，無舊檢索污染)
        self.assertEqual(sent_messages[1]["role"], "user")
        self.assertEqual(sent_messages[1]["content"], "上次會議由誰主持？")
        # 3. 第三個是第 1 輪歷史 assistant 回答
        self.assertEqual(sent_messages[2]["role"], "assistant")
        self.assertEqual(sent_messages[2]["content"], "上次會議由王經理主持。")
        # 4. 第四個是當前輪次，才包含了當次的參考資料
        self.assertEqual(sent_messages[3]["role"], "user")
        self.assertIn("【參考資料】", sent_messages[3]["content"])
        self.assertIn("預算審核結果：已通過新台幣 50 萬元。", sent_messages[3]["content"])
        self.assertIn("【使用者問題】\n這次預算通過了嗎？", sent_messages[3]["content"])

    @patch("rag_project.document_processing.llm_service.completion")
    def test_mode_switching_to_chat(self, mock_completion):
        """測試同 Session 中切換為普通聊天模式 (chat mode)，不注入任何參考資料。"""
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock(message=MagicMock(content="沒問題，我來協助您！"))]
        mock_completion.return_value = mock_resp

        history = [
            {"role": "user", "content": "我的名字是小李。"},
            {"role": "assistant", "content": "你好小李，很高興認識你！"}
        ]

        chat_with_context(
            user_query="你還記得我叫什麼名字嗎？",
            history_messages=history,
            mode="chat",
            retrieved_chunks=None,
            max_history_turns=5
        )

        call_args = mock_completion.call_args[1]
        sent_messages = call_args["messages"]

        # 驗證最後一個 user message 只是純問題，沒有【參考資料】標記
        current_msg = sent_messages[-1]
        self.assertEqual(current_msg["role"], "user")
        self.assertEqual(current_msg["content"], "你還記得我叫什麼名字嗎？")
        self.assertNotIn("【參考資料】", current_msg["content"])

    @patch("rag_project.main.chat_with_context")
    @patch("rag_project.main.search")
    def test_api_session_and_messages_endpoints(self, mock_search, mock_chat_context):
        """測試 FastAPI 的 /sessions 與 /sessions/{id}/messages RESTful 端點。"""
        mock_chat_context.return_value = "這是 API 測試回傳之回答。"
        
        # 模擬 RAG search 回傳
        mock_doc = MagicMock()
        mock_doc.page_content = "這是測試檢索段落"
        mock_doc.metadata = {"source": "test.md"}
        mock_search.return_value = [mock_doc]

        client = TestClient(app)

        # 1. 建立 Session
        res = client.post("/sessions", json={"title": "API 測試會話"})
        self.assertEqual(res.status_code, 200)
        session_data = res.json()["session"]
        session_id = session_data["id"]
        self.assertEqual(session_data["title"], "API 測試會話")

        # 2. 發送普通模式聊天訊息
        msg_res1 = client.post(f"/sessions/{session_id}/messages", json={
            "content": "請跟我問好",
            "mode": "chat"
        })
        self.assertEqual(msg_res1.status_code, 200)
        body1 = msg_res1.json()
        self.assertEqual(body1["mode"], "chat")
        self.assertEqual(body1["assistant_message"]["content"], "這是 API 測試回傳之回答。")
        self.assertEqual(len(body1["retrieved_chunks"]), 0)

        # 3. 發送 RAG 模式訊息
        msg_res2 = client.post(f"/sessions/{session_id}/messages", json={
            "content": "查詢檢索文件內容",
            "mode": "rag",
            "top_k": 3
        })
        self.assertEqual(msg_res2.status_code, 200)
        body2 = msg_res2.json()
        self.assertEqual(body2["mode"], "rag")
        self.assertEqual(len(body2["retrieved_chunks"]), 1)
        self.assertEqual(body2["retrieved_chunks"][0]["content"], "這是測試檢索段落")

        # 4. 查詢 Session Detail
        detail_res = client.get(f"/sessions/{session_id}")
        self.assertEqual(detail_res.status_code, 200)
        detail_data = detail_res.json()
        self.assertEqual(len(detail_data["messages"]), 4)  # 2 user + 2 assistant

        # 5. 清理刪除 Session
        del_res = client.delete(f"/sessions/{session_id}")
        self.assertEqual(del_res.status_code, 200)

    @patch("rag_project.document_processing.llm_service.completion")
    def test_llm_failure_does_not_pollute_context_or_db(self, mock_completion):
        """驗證當 LLM API 呼叫失敗時：
        1. chat_with_context 應拋出 RuntimeError，而非回傳錯誤字串假裝成功。
        2. 歷史中若曾有 [錯誤] 訊息，會被自動過濾，不送入上下文。
        3. API 遇到錯誤時回傳 502，且 SQLite 不寫入任何殘留訊息（避免污染歷史）。
        """
        # 1. 測試 completion 拋出例外時，chat_with_context 是否拋出 RuntimeError
        mock_completion.side_effect = Exception("OpenAI API 500 Internal Error")
        with self.assertRaises(RuntimeError) as ctx:
            chat_with_context(
                user_query="測試問題",
                history_messages=[],
                mode="chat"
            )
        self.assertIn("LLM 呼叫失敗", str(ctx.exception))

        # 2. 測試防禦性過濾：歷史中帶有 [錯誤] 的錯誤訊息不應被送入上下文
        mock_completion.side_effect = None
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock(message=MagicMock(content="正常回答"))]
        mock_completion.return_value = mock_resp

        dirty_history = [
            {"role": "user", "content": "上次問題"},
            {"role": "assistant", "content": "[錯誤] LLM 呼叫失敗: Connection timed out"},
            {"role": "user", "content": "正常問題"},
            {"role": "assistant", "content": "正常過去回答"}
        ]
        chat_with_context(
            user_query="新問題",
            history_messages=dirty_history,
            mode="chat"
        )
        call_args = mock_completion.call_args[1]
        sent_messages = call_args["messages"]
        for msg in sent_messages:
            self.assertFalse(msg["content"].startswith("[錯誤]"), "錯誤訊息不應出現在傳給 LLM 的上下文！")

        # 3. 測試 API 層面：當 LLM 失敗時，SQLite 完全不留任何半拉子訊息
        client = TestClient(app)
        s = client.post("/sessions", json={"title": "失敗測試會話"}).json()["session"]
        s_id = s["id"]

        # mock chat_with_context 在 API 中拋出例外
        with patch("rag_project.main.chat_with_context", side_effect=RuntimeError("連線中斷")):
            fail_res = client.post(f"/sessions/{s_id}/messages", json={
                "content": "這是一條會失敗的訊息",
                "mode": "chat"
            })
            self.assertEqual(fail_res.status_code, 502)

        # 驗證資料庫：完全沒有留下該條 user 或 assistant 訊息
        detail = client.get(f"/sessions/{s_id}").json()
        self.assertEqual(len(detail["messages"]), 0, "失敗時資料庫應保持乾淨，不可有任何殘留！")


if __name__ == "__main__":
    unittest.main()
