import json
import re
from typing import AsyncGenerator, Optional

import httpx

from config.constants import PROVIDER_TEMPLATES


def format_friendly_error(error: str) -> str:
    err = error.lower()
    if "api key" in err or "401" in err:
        return "🔑 API 密钥好像不对呢~ 请检查一下配置~"
    if "quota" in err or "balance" in err:
        return "💰 配额用完啦！需要充值或等待重置哦~"
    if "rate limit" in err or "429" in err:
        return "🚦 请求太频繁啦，休息一下再试吧~"
    if "timeout" in err or "timed out" in err:
        return "⏱️ 等待时间太长了，网络可能有点慢呢~"
    if "network" in err or "enotfound" in err or "econnrefused" in err:
        return "🌐 网络连接似乎有点问题，检查一下网络吧~"
    if "403" in err:
        return "🚫 没有访问权限哦~"
    if "404" in err:
        return "🔍 找不到这个地址呢，确认 API URL 是否正确~"
    if any(code in err for code in ("500", "502", "503")):
        return "💥 服务器那边出了点问题，过会儿再试试吧~"
    return f"遇到了一点小问题：{error}"


def normalize_openai_url(api_url: str) -> str:
    """把各种风格的 OpenAI 兼容 API URL 统一成 /v1/chat/completions 完整路径。

    支持的输入:
      https://api.deepseek.com                     -> https://api.deepseek.com/v1/chat/completions
      https://api.deepseek.com/                    -> https://api.deepseek.com/v1/chat/completions
      https://api.deepseek.com/v1                  -> https://api.deepseek.com/v1/chat/completions
      https://api.deepseek.com/v1/                 -> https://api.deepseek.com/v1/chat/completions
      https://api.deepseek.com/v1/chat/completions -> 原样返回
      https://api.deepseek.com/chat/completions    -> https://api.deepseek.com/v1/chat/completions
    """
    trimmed = api_url.rstrip("/")
    if trimmed.endswith("/chat/completions"):
        return trimmed
    if trimmed.endswith("/v1"):
        return trimmed + "/chat/completions"
    return trimmed + "/v1/chat/completions"


def check_vision_support(provider: str, model_id: str) -> bool:
    template = PROVIDER_TEMPLATES.get(provider)
    if not template:
        return False
    for model in template["models"]:
        if model["id"] == model_id:
            return model.get("supportsVision", False)
    return False


class AIService:
    async def test_connection(self, provider: str, api_url: str, api_key: str, model: str) -> dict:
        try:
            if provider == "gemini":
                return await self._test_gemini(api_url, api_key, model)
            if provider == "claude":
                return await self._test_claude(api_url, api_key, model)
            return await self._test_openai_compatible(api_url, api_key, model)
        except Exception as e:
            return {"success": False, "error": format_friendly_error(str(e))}

    async def _test_openai_compatible(self, api_url: str, api_key: str, model: str) -> dict:
        url = normalize_openai_url(api_url)
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                url,
                json={"model": model, "messages": [{"role": "user", "content": "你好"}], "max_tokens": 10},
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            )
            if resp.status_code >= 400:
                data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                msg = data.get("error", {}).get("message", resp.text)
                return {"success": False, "error": format_friendly_error(msg)}
            return {"success": True, "message": "✅ 连接成功啦~ 可以开始对话了！"}

    async def _test_gemini(self, api_url: str, api_key: str, model: str) -> dict:
        url = f"{api_url.rstrip('/')}/{model}:generateContent?key={api_key}"
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                url,
                json={"contents": [{"role": "user", "parts": [{"text": "你好"}]}]},
                headers={"Content-Type": "application/json"},
            )
            if resp.status_code >= 400:
                data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                msg = data.get("error", {}).get("message", resp.text)
                return {"success": False, "error": format_friendly_error(msg)}
            return {"success": True, "message": "✅ 连接成功啦~ 可以开始对话了！"}

    async def _test_claude(self, api_url: str, api_key: str, model: str) -> dict:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                api_url,
                json={"model": model, "max_tokens": 10, "messages": [{"role": "user", "content": "你好"}]},
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
            )
            if resp.status_code >= 400:
                data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                msg = data.get("error", {}).get("message", resp.text)
                return {"success": False, "error": format_friendly_error(msg)}
            return {"success": True, "message": "✅ 连接成功啦~ 可以开始对话了！"}

    async def stream_chat(
        self,
        provider: str,
        api_url: str,
        api_key: str,
        model: str,
        messages: list[dict],
        config_name: str = "",
        tools: Optional[list] = None,
    ) -> AsyncGenerator[str, None]:
        try:
            if provider == "gemini":
                async for chunk in self._stream_gemini(api_url, api_key, model, messages):
                    yield chunk
            elif provider == "claude":
                async for chunk in self._stream_claude(api_url, api_key, model, messages):
                    yield chunk
            else:
                async for chunk in self._stream_openai_compatible(api_url, api_key, model, messages, tools):
                    yield chunk
        except Exception as e:
            yield json.dumps({"error": format_friendly_error(str(e))}, ensure_ascii=False)

    async def chat_completion(
        self,
        provider: str,
        api_url: str,
        api_key: str,
        model: str,
        messages: list[dict],
        config_name: str = "",
    ) -> tuple[str, Optional[str]]:
        """非流式调用：收集完整内容。返回 (content, error)。"""
        full = ""
        error: Optional[str] = None
        async for chunk in self.stream_chat(provider, api_url, api_key, model, messages, config_name):
            try:
                data = json.loads(chunk)
            except json.JSONDecodeError:
                continue
            if "error" in data:
                error = data["error"]
                break
            if "content" in data:
                full += data["content"]
        return full, error

    async def _stream_openai_compatible(
        self, api_url: str, api_key: str, model: str, messages: list[dict], tools: Optional[list] = None
    ) -> AsyncGenerator[str, None]:
        url = normalize_openai_url(api_url)
        is_reasoning_model = model.lower().endswith("-reasoner")
        body: dict = {
            "model": model,
            "messages": messages,
            "max_tokens": 8192 if is_reasoning_model else 2000,
            "stream": True,
        }
        if not is_reasoning_model:
            body["temperature"] = 0.7
        if tools:
            body["tools"] = tools
            body["tool_choice"] = "auto"
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                url,
                json=body,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            ) as resp:
                if resp.status_code >= 400:
                    body_bytes = await resp.aread()
                    try:
                        data = json.loads(body_bytes)
                        msg = data.get("error", {}).get("message", body_bytes.decode())
                    except Exception:
                        msg = body_bytes.decode()
                    yield json.dumps({"error": format_friendly_error(msg)}, ensure_ascii=False)
                    return
                # 工具调用参数以增量方式流式返回，需按 index 聚合后一次性抛出
                tool_calls_acc: dict[int, dict] = {}
                has_content = False
                finish_reason = None
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    payload = line[6:].strip()
                    if payload == "[DONE]":
                        break
                    try:
                        data = json.loads(payload)
                        choice = data.get("choices", [{}])[0]
                        if choice.get("finish_reason"):
                            finish_reason = choice["finish_reason"]
                        delta = choice.get("delta", {})
                        # 推理模型（如 deepseek-reasoner）先流式输出思考内容，需单独下发，
                        # 否则用户在思考阶段看不到任何反馈，会误以为没有回复
                        reasoning = delta.get("reasoning_content")
                        if reasoning:
                            yield json.dumps({"reasoning": reasoning}, ensure_ascii=False)
                        content = delta.get("content", "")
                        if content:
                            has_content = True
                            yield json.dumps({"content": content}, ensure_ascii=False)
                        for tc in delta.get("tool_calls") or []:
                            idx = tc.get("index", 0)
                            acc = tool_calls_acc.setdefault(idx, {"id": "", "name": "", "arguments": ""})
                            if tc.get("id"):
                                acc["id"] = tc["id"]
                            fn = tc.get("function") or {}
                            if fn.get("name"):
                                acc["name"] += fn["name"]
                            if fn.get("arguments"):
                                acc["arguments"] += fn["arguments"]
                    except json.JSONDecodeError:
                        continue
                if tool_calls_acc:
                    calls = [
                        {
                            "id": acc["id"] or f"call_{idx}",
                            "name": acc["name"],
                            "arguments": acc["arguments"] or "{}",
                        }
                        for idx, acc in sorted(tool_calls_acc.items())
                    ]
                    yield json.dumps({"tool_calls": calls}, ensure_ascii=False)
                elif not has_content:
                    if is_reasoning_model and finish_reason == "length":
                        error = "推理模型在思考阶段耗尽了输出额度，没有生成最终回答。请重试，或改用普通对话模型。"
                    else:
                        error = "模型没有返回可显示的回答，请检查模型配置后重试。"
                    yield json.dumps({"error": error}, ensure_ascii=False)

    async def _stream_gemini(
        self, api_url: str, api_key: str, model: str, messages: list[dict]
    ) -> AsyncGenerator[str, None]:
        contents = []
        system_instruction = None
        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
                continue
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        request_body: dict = {"contents": contents}
        if system_instruction:
            request_body["systemInstruction"] = {"parts": [{"text": system_instruction}]}
        url = f"{api_url.rstrip('/')}/{model}:streamGenerateContent?alt=sse&key={api_key}"
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                url,
                json=request_body,
                headers={"Content-Type": "application/json"},
            ) as resp:
                if resp.status_code >= 400:
                    body = await resp.aread()
                    try:
                        data = json.loads(body)
                        msg = data.get("error", {}).get("message", body.decode())
                    except Exception:
                        msg = body.decode()
                    yield json.dumps({"error": format_friendly_error(msg)}, ensure_ascii=False)
                    return
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    try:
                        data = json.loads(line[6:])
                        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                        for part in parts:
                            text = part.get("text", "")
                            if text:
                                yield json.dumps({"content": text}, ensure_ascii=False)
                    except json.JSONDecodeError:
                        continue

    async def _stream_claude(
        self, api_url: str, api_key: str, model: str, messages: list[dict]
    ) -> AsyncGenerator[str, None]:
        system_msg = None
        claude_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                claude_messages.append({"role": msg["role"], "content": msg["content"]})
        body: dict = {"model": model, "max_tokens": 4096, "messages": claude_messages, "stream": True}
        if system_msg:
            body["system"] = system_msg
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                api_url,
                json=body,
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
            ) as resp:
                if resp.status_code >= 400:
                    body_bytes = await resp.aread()
                    try:
                        data = json.loads(body_bytes)
                        msg = data.get("error", {}).get("message", body_bytes.decode())
                    except Exception:
                        msg = body_bytes.decode()
                    yield json.dumps({"error": format_friendly_error(msg)}, ensure_ascii=False)
                    return
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    try:
                        data = json.loads(line[6:])
                        if data.get("type") == "content_block_delta":
                            text = data.get("delta", {}).get("text", "")
                            if text:
                                yield json.dumps({"content": text}, ensure_ascii=False)
                    except json.JSONDecodeError:
                        continue

    async def analyze_vision(
        self,
        provider: str,
        api_url: str,
        api_key: str,
        model: str,
        image_base64: str,
        prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        if not check_vision_support(provider, model):
            yield json.dumps({"error": "当前模型不支持视觉分析，请更换支持视觉的模型~"}, ensure_ascii=False)
            return
        text = prompt or "请详细描述这张图片的内容，包括主要元素、文字信息和整体场景。"
        clean_b64 = re.sub(r"^data:image/[^;]+;base64,", "", image_base64)

        if provider == "gemini":
            url = f"{api_url.rstrip('/')}/{model}:streamGenerateContent?alt=sse&key={api_key}"
            body = {
                "contents": [{
                    "role": "user",
                    "parts": [
                        {"text": text},
                        {"inline_data": {"mime_type": "image/png", "data": clean_b64}},
                    ],
                }]
            }
            async with httpx.AsyncClient(timeout=120) as client:
                async with client.stream("POST", url, json=body) as resp:
                    if resp.status_code >= 400:
                        body_bytes = await resp.aread()
                        yield json.dumps({"error": format_friendly_error(body_bytes.decode())}, ensure_ascii=False)
                        return
                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            try:
                                data = json.loads(line[6:])
                                for part in data.get("candidates", [{}])[0].get("content", {}).get("parts", []):
                                    t = part.get("text", "")
                                    if t:
                                        yield json.dumps({"content": t}, ensure_ascii=False)
                            except json.JSONDecodeError:
                                continue
        elif provider == "claude":
            body = {
                "model": model,
                "max_tokens": 4096,
                "stream": True,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": clean_b64}},
                        {"type": "text", "text": text},
                    ],
                }],
            }
            async with httpx.AsyncClient(timeout=120) as client:
                async with client.stream(
                    "POST", api_url, json=body,
                    headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
                ) as resp:
                    if resp.status_code >= 400:
                        body_bytes = await resp.aread()
                        yield json.dumps({"error": format_friendly_error(body_bytes.decode())}, ensure_ascii=False)
                        return
                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            try:
                                data = json.loads(line[6:])
                                if data.get("type") == "content_block_delta":
                                    t = data.get("delta", {}).get("text", "")
                                    if t:
                                        yield json.dumps({"content": t}, ensure_ascii=False)
                            except json.JSONDecodeError:
                                continue
        else:
            url = normalize_openai_url(api_url)
            body = {
                "model": model,
                "stream": True,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": text},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{clean_b64}"}},
                    ],
                }],
            }
            async with httpx.AsyncClient(timeout=120) as client:
                async with client.stream(
                    "POST", url, json=body,
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                ) as resp:
                    if resp.status_code >= 400:
                        body_bytes = await resp.aread()
                        yield json.dumps({"error": format_friendly_error(body_bytes.decode())}, ensure_ascii=False)
                        return
                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            payload = line[6:].strip()
                            if payload == "[DONE]":
                                break
                            try:
                                data = json.loads(payload)
                                content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                if content:
                                    yield json.dumps({"content": content}, ensure_ascii=False)
                            except json.JSONDecodeError:
                                continue


ai_service = AIService()
