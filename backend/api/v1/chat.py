import json
import logging
import asyncio
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.dependencies import get_current_user
from db.session import SessionLocal, get_db
from models.db_models import (
    ApiConfig,
    ContextMemory,
    Conversation,
    McpServer,
    McpToolApproval,
    McpToolPolicy,
    Message,
    User,
)
from models.schemas import ChatStreamRequest, VisionRequest
from services.ai_service import ai_service
from services.context_service import (
    SUMMARY_INTERVAL_MESSAGES,
    build_system_context,
    create_memory,
    retrieve_context,
    select_recent_messages,
    upsert_session_summary,
)
from services.privacy import StreamingRedactor, decrypt_secret, redact_json_strings, redact_sensitive_data
from services.mcp_service import mcp_manager, run_mcp
from services.mcp_safety import default_tool_mode
from services.setting_service import get_active_config, get_setting

router = APIRouter(prefix="/api", tags=["chat"])
logger = logging.getLogger(__name__)

# 单次回复最多执行的工具调用轮数，防止死循环
MAX_TOOL_ROUNDS = 5


def _collect_mcp_tools(db: Session, user_id: str) -> tuple[list[dict], dict[str, tuple[str, str]]]:
    """设置开启 MCP 且服务器「已连接 + 已启用」时，聚合可用工具。"""
    general = get_setting(db, "general_settings", {}) or {}
    if not (isinstance(general, dict) and general.get("mcpEnabled")):
        return [], {}
    enabled_servers = db.query(McpServer).filter(McpServer.enabled == True).all()
    if not enabled_servers:
        return [], {}
    tools, tool_index = mcp_manager.build_tools([s.id for s in enabled_servers])
    policies = {
        (policy.server_id, policy.tool_name): policy.mode
        for policy in db.query(McpToolPolicy).filter(McpToolPolicy.user_id == user_id).all()
    }
    safe_tools = []
    safe_index = {}
    for tool in tools:
        name = tool["function"]["name"]
        server_id, raw_name = tool_index[name]
        source = next(
            (item for item in mcp_manager.tools_of(server_id) if item.get("name") == raw_name),
            {},
        )
        mode = policies.get(
            (server_id, raw_name),
            default_tool_mode(raw_name, source.get("description", "")),
        )
        if mode == "blocked":
            continue
        safe_tools.append(tool)
        safe_index[name] = (server_id, raw_name)
    return safe_tools, safe_index


async def _wait_for_tool_approval(approval_id: str) -> str:
    deadline = asyncio.get_running_loop().time() + 180
    while asyncio.get_running_loop().time() < deadline:
        approval_db = SessionLocal()
        try:
            approval = approval_db.query(McpToolApproval).filter(McpToolApproval.id == approval_id).first()
            if not approval:
                return "expired"
            if approval.status != "pending":
                return approval.status
            if approval.expires_at <= datetime.utcnow():
                approval.status = "expired"
                approval_db.commit()
                return "expired"
        finally:
            approval_db.close()
        await asyncio.sleep(0.5)

    approval_db = SessionLocal()
    try:
        approval = (
            approval_db.query(McpToolApproval)
            .filter(McpToolApproval.id == approval_id, McpToolApproval.status == "pending")
            .first()
        )
        if approval:
            approval.status = "expired"
            approval_db.commit()
    finally:
        approval_db.close()
    return "expired"


def _current_tool_access(
    user_id: str,
    server_id: str,
    tool_name: str,
    description: str,
) -> tuple[str | None, str | None]:
    access_db = SessionLocal()
    try:
        server = (
            access_db.query(McpServer)
            .filter(McpServer.id == server_id, McpServer.enabled == True)
            .first()
        )
        if not server:
            return None, None
        policy = (
            access_db.query(McpToolPolicy)
            .filter(
                McpToolPolicy.user_id == user_id,
                McpToolPolicy.server_id == server_id,
                McpToolPolicy.tool_name == tool_name,
            )
            .first()
        )
        mode = policy.mode if policy else default_tool_mode(tool_name, description)
        return mode, server.name
    finally:
        access_db.close()


@router.post("/chat/stream")
async def chat_stream(
    body: ChatStreamRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    config = None
    if body.config_id:
        config = db.query(ApiConfig).filter(ApiConfig.id == body.config_id).first()
    if not config:
        config = get_active_config(db)
    if not config:
        async def no_config():
            yield f"data: {json.dumps({'error': '请先在设置中添加并选择 API 配置~'}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(no_config(), media_type="text/event-stream")

    messages = [
        {"role": m.role, "content": redact_sensitive_data(m.content)}
        for m in body.messages
        if m.role in {"user", "assistant"}
    ]
    conversation = None
    if body.conversation_id:
        conversation = (
            db.query(Conversation)
            .filter(Conversation.id == body.conversation_id)
            .first()
        )
        if not conversation:
            raise HTTPException(404, "对话不存在")
        if conversation.user_id != user.id:
            raise HTTPException(403, "无权访问该对话")
    latest_user_message = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
    last_user_msg = {"role": "user", "content": latest_user_message} if latest_user_message else None
    context = retrieve_context(
        db,
        user_id=user.id,
        conversation_id=body.conversation_id,
        query=latest_user_message[:4000],
    )
    messages = [
        {"role": "system", "content": build_system_context(context)},
        *select_recent_messages(messages),
    ]
    mcp_tools, tool_index = _collect_mcp_tools(db, user.id)

    # 请求级 session 在流式响应期间会失效，这里先取出后续需要的字段，
    # 避免在 event_generator 内访问 ORM 属性触发 DetachedInstanceError 而中断流。
    cfg_provider = config.provider
    cfg_api_url = config.api_url
    cfg_api_key = decrypt_secret(config.api_key)
    cfg_model = config.selected_model
    cfg_name = config.name
    user_id = user.id

    async def event_generator():
        display_content = ""   # 流式展示给用户的内容（含工具状态行）
        db_content = ""        # 入库的纯模型输出
        history = [dict(m) for m in messages]
        tools = mcp_tools or None
        error_occurred = False
        tool_memory_entries: list[tuple[str, str]] = []

        for _ in range(MAX_TOOL_ROUNDS):
            round_content = ""
            pending_calls = None
            output_redactor = StreamingRedactor()
            reasoning_redactor = StreamingRedactor()
            async for chunk in ai_service.stream_chat(
                cfg_provider, cfg_api_url, cfg_api_key, cfg_model, history, cfg_name, tools
            ):
                try:
                    data = json.loads(chunk)
                except json.JSONDecodeError:
                    continue
                if "error" in data:
                    if isinstance(data["error"], str):
                        data["error"] = redact_sensitive_data(data["error"])
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                    error_occurred = True
                    break
                if "reasoning" in data:
                    safe_reasoning = reasoning_redactor.feed(data["reasoning"])
                    if safe_reasoning:
                        yield f"data: {json.dumps({'reasoning': safe_reasoning}, ensure_ascii=False)}\n\n"
                    continue
                if "tool_calls" in data:
                    pending_calls = data["tool_calls"]
                    continue
                if "content" in data:
                    round_content += data["content"]
                    db_content += data["content"]
                    safe_content = output_redactor.feed(data["content"])
                    if safe_content:
                        display_content += safe_content
                        yield f"data: {json.dumps({'content': safe_content}, ensure_ascii=False)}\n\n"
            redacted_tail = output_redactor.feed("", final=True)
            if redacted_tail:
                display_content += redacted_tail
                yield f"data: {json.dumps({'content': redacted_tail}, ensure_ascii=False)}\n\n"
            reasoning_tail = reasoning_redactor.feed("", final=True)
            if reasoning_tail:
                yield f"data: {json.dumps({'reasoning': reasoning_tail}, ensure_ascii=False)}\n\n"
            if error_occurred or not pending_calls:
                break

            # 模型请求调用 MCP 工具：回填 assistant tool_calls，执行后携带结果继续对话
            history.append({
                "role": "assistant",
                "content": redact_sensitive_data(round_content) or None,
                "tool_calls": [
                    {"id": tc["id"], "type": "function",
                     "function": {"name": tc["name"], "arguments": redact_sensitive_data(tc["arguments"])}}
                    for tc in pending_calls
                ],
            })
            for tc in pending_calls:
                try:
                    args = json.loads(tc["arguments"]) if isinstance(tc["arguments"], str) else tc["arguments"]
                    if not isinstance(args, dict):
                        raise ValueError("工具参数必须是 JSON 对象")
                except (json.JSONDecodeError, TypeError, ValueError) as e:
                    history.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": f"工具调用未执行：参数格式无效（{e}）",
                    })
                    continue
                server_info = tool_index.get(tc["name"])
                if not server_info:
                    history.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": "工具调用未执行：该工具不在当前用户允许的工具列表中。",
                    })
                    continue
                server_id, raw_name = server_info
                original_tool = next(
                    (item for item in mcp_manager.tools_of(server_id) if item.get("name") == raw_name),
                    {},
                )
                approval_id = None
                approved = False
                rejected = False
                while True:
                    mode, server_name = _current_tool_access(
                        user_id,
                        server_id,
                        raw_name,
                        original_tool.get("description", ""),
                    )
                    if mode is None or not mcp_manager.status(server_id)["connected"]:
                        history.append({
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": "工具调用未执行：MCP 服务器已禁用或断开连接。",
                        })
                        break
                    if mode == "blocked":
                        history.append({
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": "工具调用未执行：此工具已被权限策略禁止。",
                        })
                        break
                    if mode != "confirm" or approved:
                        break

                    approval_id = str(uuid.uuid4())
                    approval_db = SessionLocal()
                    try:
                        approval_db.add(McpToolApproval(
                            id=approval_id,
                            user_id=user_id,
                            conversation_id=body.conversation_id,
                            server_id=server_id,
                            tool_name=raw_name,
                            arguments=redact_json_strings(args),
                            status="pending",
                            expires_at=datetime.utcnow() + timedelta(minutes=3),
                        ))
                        approval_db.commit()
                    finally:
                        approval_db.close()
                    confirmation_event = {
                        'confirmation_required': {
                            'approval_id': approval_id,
                            'server_name': server_name or server_id,
                            'tool_name': raw_name,
                            'description': original_tool.get('description', ''),
                            'arguments': redact_json_strings(args),
                            'expires_in_seconds': 180,
                        }
                    }
                    yield f"data: {json.dumps(confirmation_event, ensure_ascii=False)}\n\n"
                    decision = await _wait_for_tool_approval(approval_id)
                    if decision != "approved":
                        reason = "用户拒绝了此次调用" if decision == "rejected" else "用户未在 3 分钟内确认"
                        history.append({
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": f"工具未执行：{reason}。",
                        })
                        rejected = True
                        break
                    approved = True

                if rejected:
                    continue
                if mode is None or mode == "blocked" or not mcp_manager.status(server_id)["connected"]:
                    if approval_id and approved:
                        approval_db = SessionLocal()
                        try:
                            approval_db.query(McpToolApproval).filter(
                                McpToolApproval.id == approval_id,
                                McpToolApproval.status == "approved",
                            ).update(
                                {McpToolApproval.status: "rejected"},
                                synchronize_session=False,
                            )
                            approval_db.commit()
                        finally:
                            approval_db.close()
                    continue

                status = f"\n🛠 正在调用工具「{tc['name']}」…\n"
                try:
                    result = await run_mcp(mcp_manager.call_tool(server_id, raw_name, args))
                    result_text = mcp_manager.extract_tool_text(result)
                except Exception as e:
                    result_text = f"工具调用失败：{e}"
                result_text = redact_sensitive_data(result_text)
                display_content += status
                yield f"data: {json.dumps({'content': status}, ensure_ascii=False)}\n\n"
                if approval_id and approved:
                    approval_db = SessionLocal()
                    try:
                        approval_db.query(McpToolApproval).filter(
                            McpToolApproval.id == approval_id,
                            McpToolApproval.user_id == user_id,
                            McpToolApproval.status == "approved",
                        ).update(
                            {McpToolApproval.status: "executed"},
                            synchronize_session=False,
                        )
                        approval_db.commit()
                    finally:
                        approval_db.close()
                history.append({"role": "tool", "tool_call_id": tc["id"], "content": result_text[:8000]})
                tool_memory_entries.append((
                    tc["name"],
                    f"参数: {json.dumps(redact_json_strings(args), ensure_ascii=False, default=str)[:800]}\n结果: {result_text[:2400]}",
                ))

        if body.conversation_id and (db_content or last_user_msg):
            save_db = SessionLocal()
            try:
                # 对话可能已被用户删除，校验存在性，避免写入孤儿消息
                conv_exists = (
                    save_db.query(Conversation.id)
                    .filter(Conversation.id == body.conversation_id)
                    .first()
                )
                if conv_exists:
                    conversation_row = (
                        save_db.query(Conversation)
                        .filter(Conversation.id == body.conversation_id)
                        .first()
                    )
                    update_values = {Conversation.updated_at: datetime.utcnow()}
                    if (
                        last_user_msg
                        and conversation_row
                        and (conversation_row.title or "") == "新对话"
                    ):
                        update_values[Conversation.title] = last_user_msg["content"].strip()[:60] or "新对话"
                    save_db.query(Conversation).filter(
                        Conversation.id == body.conversation_id
                    ).update(update_values, synchronize_session=False)
                    if last_user_msg:
                        save_db.add(Message(
                            id=str(uuid.uuid4()),
                            conversation_id=body.conversation_id,
                            role="user",
                            content=redact_sensitive_data(last_user_msg["content"]),
                        ))
                    if db_content:
                        save_db.add(Message(
                            id=str(uuid.uuid4()),
                            conversation_id=body.conversation_id,
                            role="assistant",
                            content=redact_sensitive_data(db_content),
                            model=f"{config.name} ({config.selected_model})",
                        ))
                    for title, content in tool_memory_entries:
                        create_memory(
                            save_db,
                            user_id=user.id,
                            kind="tool_result",
                            title=f"工具结果 · {title}",
                            content=content,
                            source="mcp",
                            conversation_id=body.conversation_id,
                        )
                    save_db.commit()
                    if db_content:
                        await _maybe_summarize_conversation(
                            save_db,
                            user_id=user.id,
                            conversation_id=body.conversation_id,
                            config=config,
                        )
            finally:
                save_db.close()

        if not db_content and not error_occurred:
            yield f"data: {json.dumps({'error': '模型已结束生成，但没有返回可显示的回答。请重试，或在设置中更换模型。'}, ensure_ascii=False)}\n\n"
            return

        yield f"data: {json.dumps({'done': True, 'model': f'{config.name} ({config.selected_model})'}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


async def _maybe_summarize_conversation(db: Session, *, user_id: str, conversation_id: str, config: ApiConfig) -> None:
    message_count = (
        db.query(func.count(Message.id))
        .filter(Message.conversation_id == conversation_id)
        .scalar()
        or 0
    )
    summary = (
        db.query(ContextMemory)
        .filter(
            ContextMemory.user_id == user_id,
            ContextMemory.conversation_id == conversation_id,
            ContextMemory.kind == "session_summary",
        )
        .first()
    )
    summarized_count = summary.source_message_count if summary else 0
    if message_count - summarized_count < SUMMARY_INTERVAL_MESSAGES:
        return

    recent_messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc(), Message.id.desc())
        .limit(24)
        .all()
    )
    transcript = "\n".join(
        f"{'用户' if item.role == 'user' else '助手'}: {item.content[:1200]}"
        for item in reversed(recent_messages)
    )
    old_summary = summary.content if summary else "（尚无历史摘要）"
    summary_messages = [
        {
            "role": "system",
            "content": (
                "你负责维护一份对话会话摘要，供后续 AI 对话理解历史。请只保留对后续交流有用的事实、"
                "已确定的目标、未完成事项、关键决定和上下文；区分用户明确表达与推测，不补造信息。"
                "用简洁中文输出，最多 1200 字，不要写建议或开场白。"
            ),
        },
        {
            "role": "user",
            "content": f"已有摘要：\n{old_summary}\n\n最近对话：\n{transcript}\n\n请合并更新摘要。",
        },
    ]
    try:
        content, error = await ai_service.chat_completion(
            config.provider,
            config.api_url,
            decrypt_secret(config.api_key),
            config.selected_model,
            summary_messages,
            config.name,
        )
        if error:
            logger.warning("会话摘要生成失败 conversation_id=%s: %s", conversation_id, error)
            return
        if not content.strip():
            logger.warning("会话摘要为空 conversation_id=%s", conversation_id)
            return
        upsert_session_summary(
            db,
            user_id=user_id,
            conversation_id=conversation_id,
            content=content.strip()[:5000],
            source_message_count=message_count,
        )
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("会话摘要生成异常 conversation_id=%s", conversation_id)


@router.post("/chat/vision/stream")
async def vision_stream(
    body: VisionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    config = None
    if body.config_id:
        config = db.query(ApiConfig).filter(ApiConfig.id == body.config_id).first()
    if not config:
        config = get_active_config(db)
    if not config:
        async def no_config():
            yield f"data: {json.dumps({'error': '请先在设置中添加 API 配置~'}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(no_config(), media_type="text/event-stream")

    async def event_generator():
        async for chunk in ai_service.analyze_vision(
            config.provider, config.api_url, decrypt_secret(config.api_key), config.selected_model,
            body.image_base64, redact_sensitive_data(body.prompt or ""),
        ):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
