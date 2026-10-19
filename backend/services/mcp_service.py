import asyncio
import json
import os
import re
import shutil
import threading
from typing import Any, Optional

# MCP stdio 协议（JSON-RPC 2.0，换行分隔）客户端 + 连接管理器
PROTOCOL_VERSION = "2024-11-05"


class _McpLoopThread:
    """专用的 Proactor 事件循环线程。

    uvicorn 在 Windows 上默认使用 SelectorEventLoop，它不支持子进程；
    MCP 需要创建子进程，因此所有 MCP 协程都调度到本线程执行，
    会话（子进程/管道）生命周期固定在该循环中，跨请求保持连接。
    """

    def __init__(self) -> None:
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._ready = threading.Event()
        threading.Thread(target=self._run, name="mcp-proactor", daemon=True).start()
        self._ready.wait()

    def _run(self) -> None:
        if os.name == "nt":
            loop: asyncio.AbstractEventLoop = asyncio.ProactorEventLoop()
        else:
            loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop
        self._ready.set()
        loop.run_forever()

    async def run(self, coro):
        return await asyncio.wrap_future(asyncio.run_coroutine_threadsafe(coro, self._loop))


_mcp_loop = _McpLoopThread()


async def run_mcp(coro):
    """把 MCP 协程调度到专用 Proactor 循环线程执行。"""
    return await _mcp_loop.run(coro)


class McpStdioClient:
    """一个 MCP stdio 服务器的客户端会话。"""

    def __init__(self, name: str, command: str, args: list[str], env: Optional[dict] = None):
        self.name = name
        self.command = command
        self.args = args
        self.env = env or {}
        self.process: Optional[asyncio.subprocess.Process] = None
        self.tools: list[dict] = []
        self.connected = False
        self.server_info: dict = {}
        self._request_id = 0
        self._stderr_task: Optional[asyncio.Task] = None
        self._stderr_tail: list[str] = []

    async def connect(self) -> list[dict]:
        """启动子进程并完成 MCP 初始化握手，返回工具列表。"""
        await self.disconnect()
        launch = self._resolve_command()
        merged_env = {**os.environ, **self.env}
        try:
            self.process = await asyncio.create_subprocess_exec(
                *launch,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=merged_env,
                cwd=os.getcwd(),
            )
        except FileNotFoundError:
            raise RuntimeError(f"找不到命令 {self.command}，请确认已安装并加入 PATH")

        # 后台收集 stderr 尾部，便于连接失败时给出原因
        self._stderr_task = asyncio.create_task(self._drain_stderr())

        try:
            result = await self._request(
                "initialize",
                {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "hamu-pet", "version": "3.0.0"},
                },
                # 首次运行 npx/uvx 需下载依赖，可能较慢
                timeout=150,
            )
            self.server_info = result.get("serverInfo", {})
            await self._notify("notifications/initialized", {})
            tools_result = await self._request("tools/list", {}, timeout=60)
        except RuntimeError:
            await self.disconnect()
            raise
        except Exception as e:
            await self.disconnect()
            detail = " | ".join(self._stderr_tail[-3:]) or str(e)
            if not detail:
                detail = "启动超时（首次运行 npx/uvx 需要下载依赖，可能较慢，请重试）"
            raise RuntimeError(f"MCP 初始化失败：{detail[:300]}")

        self.tools = tools_result.get("tools", [])
        self.connected = True
        return self.tools

    def _resolve_command(self) -> list[str]:
        """Windows 下 npx/uvx 等是 .cmd 脚本，需经 cmd.exe 启动。"""
        cmd = self.command
        resolved = shutil.which(cmd)
        if os.name == "nt" and resolved and resolved.lower().endswith((".cmd", ".bat")):
            return ["cmd.exe", "/c", resolved, *self.args]
        return [resolved or cmd, *self.args]

    async def _drain_stderr(self) -> None:
        assert self.process and self.process.stderr
        try:
            while True:
                line = await self.process.stderr.readline()
                if not line:
                    break
                self._stderr_tail.append(line.decode("utf-8", "ignore").strip())
                self._stderr_tail = self._stderr_tail[-20:]
        except Exception:
            pass

    async def _request(self, method: str, params: dict, timeout: float = 30) -> dict:
        if not self.process or not self.process.stdin:
            raise RuntimeError("MCP 进程未启动")
        self._request_id += 1
        request_id = self._request_id
        payload = json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        self.process.stdin.write((payload + "\n").encode())
        await self.process.stdin.drain()

        loop = asyncio.get_event_loop()
        deadline = loop.time() + timeout
        while True:
            remaining = deadline - loop.time()
            if remaining <= 0:
                raise TimeoutError(f"MCP 响应超时（{method}）")
            line = await asyncio.wait_for(self.process.stdout.readline(), timeout=remaining)
            if not line:
                raise RuntimeError("MCP 进程已退出：" + (" | ".join(self._stderr_tail[-3:]) or "无输出"))
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            if msg.get("id") != request_id:
                continue  # 通知或其他请求的响应
            if "error" in msg:
                raise RuntimeError(str(msg["error"].get("message", msg["error"]))[:300])
            return msg.get("result", {})

    async def _notify(self, method: str, params: dict) -> None:
        if not self.process or not self.process.stdin:
            return
        payload = json.dumps({"jsonrpc": "2.0", "method": method, "params": params})
        self.process.stdin.write((payload + "\n").encode())
        await self.process.stdin.drain()

    async def call_tool(self, name: str, arguments: dict, timeout: float = 90) -> dict:
        return await self._request("tools/call", {"name": name, "arguments": arguments}, timeout=timeout)

    async def disconnect(self) -> None:
        self.connected = False
        if self._stderr_task:
            self._stderr_task.cancel()
            self._stderr_task = None
        if self.process:
            try:
                if self.process.stdin:
                    self.process.stdin.close()
                self.process.terminate()
            except ProcessLookupError:
                pass
            except Exception:
                pass
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
            self.process = None


class McpManager:
    """管理所有已连接的 MCP 服务器会话。"""

    def __init__(self) -> None:
        self.clients: dict[str, McpStdioClient] = {}

    async def connect(self, server_id: str, name: str, command: str, args: list[str], env: Optional[dict]) -> list[dict]:
        old = self.clients.pop(server_id, None)
        if old:
            await old.disconnect()
        client = McpStdioClient(name, command, args, env)
        tools = await client.connect()
        self.clients[server_id] = client
        return tools

    async def disconnect(self, server_id: str) -> None:
        client = self.clients.pop(server_id, None)
        if client:
            await client.disconnect()

    async def call_tool(self, server_id: str, name: str, arguments: dict) -> dict:
        client = self.clients.get(server_id)
        if not client or not client.connected:
            raise RuntimeError("该 MCP 服务器尚未连接")
        return await client.call_tool(name, arguments)

    def status(self, server_id: str) -> dict:
        client = self.clients.get(server_id)
        return {"connected": bool(client and client.connected), "toolCount": len(client.tools) if client else 0}

    def tools_of(self, server_id: str) -> list[dict]:
        client = self.clients.get(server_id)
        return client.tools if client else []

    def build_tools(self, server_ids: list[str]) -> tuple[list[dict], dict[str, tuple[str, str]]]:
        """把已连接服务器的 MCP 工具转换为 OpenAI function 格式。

        返回 (tools, index)：index 把（可能加前缀的）工具名映射回 (server_id, 原始工具名)。
        """
        tools: list[dict] = []
        index: dict[str, tuple[str, str]] = {}
        seen: set[str] = set()
        for sid in server_ids:
            client = self.clients.get(sid)
            if not client or not client.connected:
                continue
            for t in client.tools:
                raw_name = t.get("name", "")
                if not raw_name:
                    continue
                name = re.sub(r"[^a-zA-Z0-9_-]", "_", raw_name)
                if name in seen:
                    name = re.sub(r"[^a-zA-Z0-9_-]", "_", f"{client.name}_{raw_name}")[:64]
                if name in seen:
                    continue
                seen.add(name)
                tools.append({
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": t.get("description", "") or name,
                        "parameters": t.get("inputSchema") or {"type": "object", "properties": {}},
                    },
                })
                index[name] = (sid, raw_name)
        return tools, index

    @staticmethod
    def extract_tool_text(result: dict) -> str:
        """把 MCP tools/call 的结果抽取为纯文本。"""
        parts: list[str] = []
        for item in result.get("content", []) or []:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
        if not parts:
            return json.dumps(result, ensure_ascii=False)[:2000]
        return "\n".join(parts)


mcp_manager = McpManager()
