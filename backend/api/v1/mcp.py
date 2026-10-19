import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import update
from sqlalchemy.orm import Session

from api.dependencies import get_current_user
from db.session import get_db
from models.db_models import McpServer, McpToolApproval, McpToolPolicy, User
from models.schemas import McpServerCreate, McpToolApprovalDecision, McpToolPolicyUpdate
from services.mcp_safety import default_tool_mode
from services.mcp_service import mcp_manager, run_mcp
from services.privacy import decrypt_environment, encrypt_environment, redact_sensitive_data

router = APIRouter(prefix="/api/mcp", tags=["mcp"])


class McpServerUpdate(BaseModel):
    name: str | None = None
    command: str | None = None
    args: list[str] | None = None
    env: dict[str, str] | None = None
    enabled: bool | None = None


class McpToolCall(BaseModel):
    server_id: str
    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)


def _server_out(server: McpServer, db: Session, user: User) -> dict:
    status = mcp_manager.status(server.id)
    policies = {
        row.tool_name: row.mode
        for row in db.query(McpToolPolicy)
        .filter(McpToolPolicy.server_id == server.id, McpToolPolicy.user_id == user.id)
        .all()
    }
    tools = []
    if status["connected"]:
        for tool in mcp_manager.tools_of(server.id):
            name = tool.get("name", "")
            description = tool.get("description", "") or name
            tools.append({
                "name": name,
                "description": description,
                "mode": policies.get(name, default_tool_mode(name, description)),
            })
    return {
        "id": server.id,
        "name": server.name,
        "command": server.command,
        "args": server.args,
        "env": {key: "********" for key in (server.env or {})},
        "enabled": server.enabled,
        "connected": status["connected"],
        "toolCount": status["toolCount"],
        "tools": tools,
    }


@router.get("/servers")
def list_mcp_servers(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(McpServer).order_by(McpServer.created_at.desc()).all()
    return [_server_out(r, db, user) for r in rows]


@router.post("/servers")
def create_mcp_server(
    body: McpServerCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    values = body.model_dump()
    values["env"] = encrypt_environment(values["env"])
    server = McpServer(id=str(uuid.uuid4()), **values)
    db.add(server)
    db.commit()
    return _server_out(server, db, user)


@router.put("/servers/{server_id}")
async def update_mcp_server(
    server_id: str,
    body: McpServerUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    server = db.query(McpServer).filter(McpServer.id == server_id).first()
    if not server:
        raise HTTPException(404, "MCP 服务器不存在")
    for field, value in body.model_dump(exclude_unset=True).items():
        if field == "env":
            value = encrypt_environment(value)
        setattr(server, field, value)
    db.commit()
    # 配置变更后旧连接作废，需重新连接
    await run_mcp(mcp_manager.disconnect(server_id))
    return _server_out(server, db, user)


@router.delete("/servers/{server_id}")
async def delete_mcp_server(
    server_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    server = db.query(McpServer).filter(McpServer.id == server_id).first()
    if not server:
        raise HTTPException(404, "MCP 服务器不存在")
    await run_mcp(mcp_manager.disconnect(server_id))
    db.delete(server)
    db.commit()
    return {"success": True}


@router.post("/servers/{server_id}/connect")
async def connect_mcp_server(
    server_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    server = db.query(McpServer).filter(McpServer.id == server_id).first()
    if not server:
        raise HTTPException(404, "MCP 服务器不存在")
    try:
        tools = await run_mcp(
            mcp_manager.connect(
                server.id, server.name, server.command, server.args, decrypt_environment(server.env)
            )
        )
    except Exception as e:
        raise HTTPException(400, redact_sensitive_data(str(e)))
    return {
        "success": True,
        "toolCount": len(tools),
        "tools": [{"name": t.get("name"), "description": t.get("description", "")} for t in tools],
        "serverInfo": getattr(mcp_manager.clients.get(server_id), "server_info", {}),
    }


@router.post("/servers/{server_id}/disconnect")
async def disconnect_mcp_server(server_id: str, user: User = Depends(get_current_user)):
    await run_mcp(mcp_manager.disconnect(server_id))
    return {"success": True}


@router.put("/servers/{server_id}/tool-policy")
def update_tool_policy(
    server_id: str,
    body: McpToolPolicyUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    server = db.query(McpServer).filter(McpServer.id == server_id).first()
    if not server:
        raise HTTPException(404, "MCP 服务器不存在")
    known_tools = {tool.get("name") for tool in mcp_manager.tools_of(server_id)}
    if body.tool_name not in known_tools:
        raise HTTPException(404, "工具不存在或服务器尚未连接")
    policy = (
        db.query(McpToolPolicy)
        .filter(
            McpToolPolicy.user_id == user.id,
            McpToolPolicy.server_id == server_id,
            McpToolPolicy.tool_name == body.tool_name,
        )
        .first()
    )
    if policy:
        policy.mode = body.mode
    else:
        db.add(McpToolPolicy(
            id=str(uuid.uuid4()),
            user_id=user.id,
            server_id=server_id,
            tool_name=body.tool_name,
            mode=body.mode,
        ))
    db.commit()
    return {"tool_name": body.tool_name, "mode": body.mode}


@router.post("/approvals/{approval_id}/decision")
def decide_tool_approval(
    approval_id: str,
    body: McpToolApprovalDecision,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    now = datetime.utcnow()
    approval = (
        db.query(McpToolApproval)
        .filter(
            McpToolApproval.id == approval_id,
            McpToolApproval.user_id == user.id,
        )
        .first()
    )
    if not approval:
        raise HTTPException(404, "工具确认请求不存在")
    if approval.status != "pending":
        raise HTTPException(409, "工具确认请求已处理或已失效")
    if approval.expires_at <= now:
        approval.status = "expired"
        db.commit()
        raise HTTPException(410, "工具确认已超时，请重新发起")
    next_status = "approved" if body.approve else "rejected"
    result = db.execute(
        update(McpToolApproval)
        .where(
            McpToolApproval.id == approval_id,
            McpToolApproval.user_id == user.id,
            McpToolApproval.status == "pending",
            McpToolApproval.expires_at > now,
        )
        .values(status=next_status, decided_at=now)
    )
    db.commit()
    if result.rowcount != 1:
        raise HTTPException(409, "工具确认请求已处理或已失效")
    return {"success": True, "status": next_status}


@router.post("/call")
async def call_mcp_tool(
    body: McpToolCall,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """手动调用已连接 MCP 服务器的工具（调试用）。"""
    server = (
        db.query(McpServer)
        .filter(McpServer.id == body.server_id, McpServer.enabled == True)
        .first()
    )
    if not server:
        raise HTTPException(404, "MCP 服务器不存在或已禁用")
    policy = (
        db.query(McpToolPolicy)
        .filter(
            McpToolPolicy.user_id == user.id,
            McpToolPolicy.server_id == body.server_id,
            McpToolPolicy.tool_name == body.tool,
        )
        .first()
    )
    tool = next((t for t in mcp_manager.tools_of(body.server_id) if t.get("name") == body.tool), None)
    if not tool:
        raise HTTPException(404, "工具不存在或服务器尚未连接")
    mode = policy.mode if policy else default_tool_mode(body.tool, tool.get("description", ""))
    if mode == "blocked":
        raise HTTPException(403, "该工具已被权限策略禁止")
    if mode == "confirm":
        raise HTTPException(409, "该工具需要用户确认，请通过聊天中的确认流程调用")
    try:
        result = await run_mcp(mcp_manager.call_tool(body.server_id, body.tool, body.arguments))
    except Exception as e:
        raise HTTPException(400, str(e))
    return {"success": True, "content": redact_sensitive_data(mcp_manager.extract_tool_text(result))}
