from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatStreamRequest(BaseModel):
    messages: list[ChatMessage]
    config_id: Optional[str] = None
    conversation_id: Optional[str] = None


class ApiConfigCreate(BaseModel):
    name: str
    provider: str
    api_url: str
    api_key: str = Field(min_length=1)
    selected_model: str
    enabled: bool = True
    is_default: bool = False


class ApiConfigUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    api_url: Optional[str] = None
    api_key: Optional[str] = Field(default=None, min_length=1)
    selected_model: Optional[str] = None
    enabled: Optional[bool] = None
    is_default: Optional[bool] = None


class ApiConfigResponse(BaseModel):
    id: str
    name: str
    provider: str
    api_url: str
    has_api_key: bool
    selected_model: str
    enabled: bool
    is_default: bool

    class Config:
        from_attributes = True


class SettingUpdate(BaseModel):
    value: Any


class TemplateCreate(BaseModel):
    name: str
    icon: str = "📝"
    category: str = "自定义"
    prompt: str


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    category: Optional[str] = None
    prompt: Optional[str] = None


class ConversationSave(BaseModel):
    title: Optional[str] = None
    messages: list[ChatMessage]


class TestApiRequest(BaseModel):
    provider: str
    api_url: str
    api_key: str
    selected_model: str


class VisionRequest(BaseModel):
    image_base64: str
    prompt: Optional[str] = None
    config_id: Optional[str] = None


class McpServerCreate(BaseModel):
    name: str
    command: str
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    enabled: bool = False


# ---------- 认证 ----------
class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class UserPublic(BaseModel):
    id: str
    username: str


class AuthResponse(BaseModel):
    token: str
    user: UserPublic


# ---------- 心灵之旅：情绪分析 ----------
class SoulAnalyzeRequest(BaseModel):
    emotion: str
    user_input: str
    conversation_id: Optional[str] = None


class SoulAnalyzeResponse(BaseModel):
    analysis: str
    advice: str
    keywords: list[str]
    conversation_id: str


# ---------- 对话历史读取 ----------
class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    model: Optional[str] = None
    created_at: Optional[str] = None


class ConversationOut(BaseModel):
    id: str
    title: str
    source: str
    created_at: Optional[str] = None


class ContextMemoryCreate(BaseModel):
    kind: Literal["preference", "global_knowledge"]
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=5000)


class ContextMemoryUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    content: Optional[str] = Field(default=None, min_length=1, max_length=5000)


class ContextRetentionUpdate(BaseModel):
    ttl_days: dict[str, Optional[int]]


class McpToolPolicyUpdate(BaseModel):
    tool_name: str = Field(min_length=1, max_length=200)
    mode: Literal["read_only", "confirm", "blocked"]


class McpToolApprovalDecision(BaseModel):
    approve: bool
