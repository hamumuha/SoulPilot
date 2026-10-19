from sqlalchemy import Column, String, Text, Boolean, DateTime, Enum, JSON, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func

from db.session import Base


class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class Session(Base):
    __tablename__ = "sessions"
    token = Column(String(64), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=True)


class Setting(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    setting_key = Column(String(100), unique=True, nullable=False)
    setting_value = Column(JSON, nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ApiConfig(Base):
    __tablename__ = "api_configs"
    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    provider = Column(String(50), nullable=False)
    api_url = Column(Text, nullable=False)
    api_key = Column(Text, nullable=False)
    selected_model = Column(String(200), nullable=False)
    enabled = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    @property
    def has_api_key(self):
        return bool(self.api_key)


class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(String(36), primary_key=True)
    title = Column(String(200), default="新对话")
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    source = Column(String(20), default="chat")  # chat | soul
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Message(Base):
    __tablename__ = "messages"
    id = Column(String(36), primary_key=True)
    conversation_id = Column(String(36), nullable=False)
    role = Column(Enum("user", "assistant", "system"), nullable=False)
    content = Column(Text, nullable=False)
    model = Column(String(200))
    created_at = Column(DateTime, server_default=func.now())


class ContextMemory(Base):
    __tablename__ = "context_memories"
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    conversation_id = Column(String(36), nullable=True, index=True)
    kind = Column(String(32), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(32), nullable=False, default="manual")
    source_message_count = Column(Integer, nullable=False, default=0)
    expires_at = Column(DateTime, nullable=True, index=True)
    last_accessed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class CustomTemplate(Base):
    __tablename__ = "custom_templates"
    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    icon = Column(String(20), default="📝")
    category = Column(String(50), default="自定义")
    prompt = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class McpServer(Base):
    __tablename__ = "mcp_servers"
    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    command = Column(String(200), nullable=False)
    args = Column(JSON, nullable=False)
    env = Column(JSON)
    enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())


class McpToolPolicy(Base):
    __tablename__ = "mcp_tool_policies"
    __table_args__ = (UniqueConstraint("user_id", "server_id", "tool_name", name="uq_mcp_tool_policy"),)
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    server_id = Column(String(36), ForeignKey("mcp_servers.id", ondelete="CASCADE"), nullable=False, index=True)
    tool_name = Column(String(200), nullable=False)
    mode = Column(Enum("read_only", "confirm", "blocked"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class McpToolApproval(Base):
    __tablename__ = "mcp_tool_approvals"
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=True, index=True)
    server_id = Column(String(36), ForeignKey("mcp_servers.id", ondelete="CASCADE"), nullable=False)
    tool_name = Column(String(200), nullable=False)
    arguments = Column(JSON, nullable=False)
    status = Column(Enum("pending", "approved", "rejected", "expired", "executed"), nullable=False, default="pending", index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
    decided_at = Column(DateTime, nullable=True)
