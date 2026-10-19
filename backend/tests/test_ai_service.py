import json
import unittest
from unittest.mock import patch

from services.ai_service import AIService


class MockStreamResponse:
    status_code = 200

    def __init__(self, lines):
        self.lines = lines

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return None

    async def aiter_lines(self):
        for line in self.lines:
            yield line


class MockAsyncClient:
    def __init__(self, lines):
        self.lines = lines
        self.request_body = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return None

    def stream(self, method, url, *, json, headers):
        self.request_body = json
        return MockStreamResponse(self.lines)


class AIServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_reasoner_gets_a_larger_output_budget_and_empty_result_is_an_error(self):
        lines = [
            "data: " + json.dumps({
                "choices": [{
                    "delta": {"reasoning_content": "reasoning only"},
                    "finish_reason": "length",
                }]
            }),
            "data: [DONE]",
        ]
        client = MockAsyncClient(lines)

        with patch("services.ai_service.httpx.AsyncClient", return_value=client):
            chunks = [
                json.loads(chunk)
                async for chunk in AIService()._stream_openai_compatible(
                    "https://example.test/v1/chat/completions",
                    "test-key",
                    "deepseek-reasoner",
                    [{"role": "user", "content": "hello"}],
                )
            ]

        self.assertEqual(client.request_body["max_tokens"], 8192)
        self.assertNotIn("temperature", client.request_body)
        self.assertEqual(len(chunks), 1)
        self.assertIn("思考阶段耗尽", chunks[0]["error"])

    async def test_chat_model_keeps_existing_request_parameters(self):
        lines = [
            "data: " + json.dumps({
                "choices": [{"delta": {"content": "hello"}, "finish_reason": None}]
            }),
            "data: [DONE]",
        ]
        client = MockAsyncClient(lines)

        with patch("services.ai_service.httpx.AsyncClient", return_value=client):
            chunks = [
                json.loads(chunk)
                async for chunk in AIService()._stream_openai_compatible(
                    "https://example.test/v1/chat/completions",
                    "test-key",
                    "deepseek-chat",
                    [{"role": "user", "content": "hello"}],
                )
            ]

        self.assertEqual(client.request_body["max_tokens"], 2000)
        self.assertEqual(client.request_body["temperature"], 0.7)
        self.assertEqual(chunks, [{"content": "hello"}])
