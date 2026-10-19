import unittest
import uuid
from datetime import datetime, timedelta
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.session import Base
from models.db_models import ContextMemory, User
from services.context_service import (
    MAX_TASK_CONTEXT_CHARS,
    build_system_context,
    relevance_score,
    retrieve_context,
    select_recent_messages,
)
from services.mcp_safety import default_tool_mode


class ContextServiceTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()
        self.user_id = str(uuid.uuid4())
        self.session.add(User(id=self.user_id, username="context-test", password_hash="unused"))
        self.session.commit()

    def tearDown(self):
        self.session.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_relevance_score_matches_chinese_bigrams(self):
        relevant = relevance_score("我喜欢柴犬和简洁回答", "沟通偏好", "用户喜欢柴犬，偏好简洁回答。")
        unrelated = relevance_score("我喜欢柴犬和简洁回答", "天气知识", "明天会下雨，气温较低。")

        self.assertGreater(relevant, unrelated)
        self.assertGreater(relevant, 0)
        self.assertEqual(unrelated, 0)

    def test_relevance_score_matches_english_terms_case_insensitively(self):
        self.assertGreater(
            relevance_score("Use Python for this task", "Language preference", "The user prefers python."),
            0,
        )

    def test_mcp_tool_defaults_require_confirmation_for_unknown_or_mutating_tools(self):
        self.assertEqual(default_tool_mode("list_files", "List files in a directory"), "read_only")
        self.assertEqual(default_tool_mode("get_status", "Get server status"), "read_only")
        self.assertEqual(default_tool_mode("search_files", "Search files and list matches"), "confirm")
        self.assertEqual(default_tool_mode("delete_file", "Delete a file"), "confirm")
        self.assertEqual(default_tool_mode("read_file", "Read file contents"), "confirm")
        self.assertEqual(default_tool_mode("get_secret", "Get a secret value"), "confirm")
        self.assertEqual(default_tool_mode("process", "Perform an operation"), "confirm")

    def test_recent_task_context_is_bounded_and_keeps_newest_message(self):
        messages = [
            {"role": "user", "content": "old " * 5000},
            {"role": "assistant", "content": "middle " * 5000},
            {"role": "user", "content": "current request"},
        ]

        selected = select_recent_messages(messages)

        self.assertLessEqual(sum(len(message["content"]) for message in selected), MAX_TASK_CONTEXT_CHARS)
        self.assertEqual(selected[-1]["content"], "current request")

    def test_context_prompt_keeps_memory_layers_explicit(self):
        summary = SimpleNamespace(content="正在实现一套分层上下文系统。")
        preference = SimpleNamespace(title="回答风格", content="使用简洁中文。")
        tool_result = SimpleNamespace(title="工具结果 · 文件搜索", content="找到 context_service.py。")
        knowledge = SimpleNamespace(title="项目约定", content="API 使用 FastAPI。")

        prompt = build_system_context({
            "summary": summary,
            "preferences": [preference],
            "tool_results": [tool_result],
            "global_knowledge": [knowledge],
        })

        for layer in ("任务上下文", "会话摘要", "用户长期偏好", "相关工具结果", "全局知识"):
            self.assertIn(layer, prompt)

    def test_retrieval_respects_user_and_conversation_scopes_and_expiry(self):
        conversation_id = str(uuid.uuid4())
        other_user_id = str(uuid.uuid4())
        self.session.add(User(id=other_user_id, username="other-context-test", password_hash="unused"))
        rows = [
            ContextMemory(
                id=str(uuid.uuid4()), user_id=self.user_id, kind="preference",
                title="回复语言", content="用户偏好使用简洁中文。", source="manual",
            ),
            ContextMemory(
                id=str(uuid.uuid4()), user_id=self.user_id, kind="tool_result",
                conversation_id=conversation_id, title="工具结果 · 文件搜索",
                content="参数: 搜索文件\n结果: 找到 context_service.py", source="mcp",
            ),
            ContextMemory(
                id=str(uuid.uuid4()), user_id=self.user_id, kind="tool_result",
                conversation_id=str(uuid.uuid4()), title="工具结果 · 文件搜索",
                content="参数: 搜索文件\n结果: 不应进入此会话", source="mcp",
            ),
            ContextMemory(
                id=str(uuid.uuid4()), user_id=self.user_id, kind="tool_result",
                conversation_id=conversation_id, title="天气查询",
                content="结果: 明天会下雨，气温较低。", source="mcp",
            ),
            ContextMemory(
                id=str(uuid.uuid4()), user_id=None, kind="global_knowledge",
                title="项目语言", content="项目后端使用 Python。", source="manual",
            ),
            ContextMemory(
                id=str(uuid.uuid4()), user_id=None, kind="global_knowledge",
                title="天气知识", content="明天会下雨，气温较低。", source="manual",
            ),
            ContextMemory(
                id=str(uuid.uuid4()), user_id=other_user_id, kind="preference",
                title="回复语言", content="用户偏好使用简洁中文。", source="manual",
            ),
            ContextMemory(
                id=str(uuid.uuid4()), user_id=self.user_id, kind="preference",
                title="过期偏好", content="用户偏好长篇回答。",
                source="manual", expires_at=datetime.utcnow() - timedelta(days=1),
            ),
        ]
        self.session.add_all(rows)
        self.session.commit()

        context = retrieve_context(
            self.session,
            user_id=self.user_id,
            conversation_id=conversation_id,
            query="请用简洁中文查找项目文件",
        )

        self.assertEqual(len(context["preferences"]), 1)
        self.assertEqual(len(context["tool_results"]), 1)
        self.assertEqual(context["tool_results"][0].conversation_id, conversation_id)
        self.assertEqual(len(context["global_knowledge"]), 1)
        self.assertEqual(
            self.session.query(ContextMemory).filter(ContextMemory.title == "过期偏好").count(),
            0,
        )


if __name__ == "__main__":
    unittest.main()
