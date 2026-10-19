import base64
import hashlib
import re
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from config.settings import DATA_ENCRYPTION_KEY

_ENCRYPTED_PREFIX = "enc:v1:"
_EMAIL = re.compile(
    r"(?<![A-Za-z0-9_.+-])[A-Za-z0-9_.+-]{1,64}@[A-Za-z0-9.-]{1,189}\.[A-Za-z]{2,63}"
    r"(?![A-Za-z0-9_.-])"
)
_CHINA_ID_18 = re.compile(r"(?<!\d)(\d{6})\d{8}(\d{3}[\dXx])(?!\d)")
_CHINA_ID_15 = re.compile(r"(?<!\d)(\d{6})\d{5}(\d{4})(?!\d)")
_MOBILE = re.compile(r"(?<!\d)(?:\+?86[- ]?)?(1[3-9]\d)\d{4}(\d{4})(?!\d)")
_BANK_CARD = re.compile(r"(?<!\d)(\d{6})\d{6,9}(\d{4})(?!\d)")
_MAX_MATCH_LENGTH = 320


def redact_sensitive_data(value: str) -> str:
    value = _EMAIL.sub(lambda match: _mask_email(match.group()), value)
    value = _CHINA_ID_18.sub(r"\1********\2", value)
    value = _CHINA_ID_15.sub(r"\1*****\2", value)
    value = _MOBILE.sub(r"\1****\2", value)
    return _BANK_CARD.sub(r"\1******\2", value)


def _mask_email(address: str) -> str:
    name, domain = address.split("@", 1)
    return f"{name[:1]}***@{domain}"


class StreamingRedactor:
    def __init__(self) -> None:
        self._buffer = ""

    def feed(self, text: str, *, final: bool = False) -> str:
        self._buffer += text
        if final:
            result = redact_sensitive_data(self._buffer)
            self._buffer = ""
            return result

        safe_end = max(0, len(self._buffer) - _MAX_MATCH_LENGTH)
        for pattern in (_EMAIL, _CHINA_ID_18, _CHINA_ID_15, _MOBILE, _BANK_CARD):
            for match in pattern.finditer(self._buffer):
                if match.start() < safe_end < match.end():
                    safe_end = match.start()
        safe_text = self._buffer[:safe_end]
        self._buffer = self._buffer[safe_end:]
        return redact_sensitive_data(safe_text)


def encrypt_secret(value: str) -> str:
    if value.startswith(_ENCRYPTED_PREFIX):
        try:
            decrypt_secret(value)
            return value
        except ValueError:
            pass
    return _ENCRYPTED_PREFIX + _fernet().encrypt(value.encode("utf-8")).decode("ascii")


def decrypt_secret(value: str) -> str:
    if not value.startswith(_ENCRYPTED_PREFIX):
        return value
    token = value[len(_ENCRYPTED_PREFIX):]
    try:
        return _fernet().decrypt(token.encode("ascii")).decode("utf-8")
    except (InvalidToken, UnicodeDecodeError) as error:
        raise ValueError("敏感配置无法解密，请确认 DATA_ENCRYPTION_KEY 与部署时一致") from error


def _fernet() -> Fernet:
    if (
        len(DATA_ENCRYPTION_KEY) < 32
        or DATA_ENCRYPTION_KEY.startswith("__")
    ):
        raise RuntimeError("DATA_ENCRYPTION_KEY 必须设置为至少 32 个字符的随机密钥")
    key = base64.urlsafe_b64encode(hashlib.sha256(DATA_ENCRYPTION_KEY.encode("utf-8")).digest())
    return Fernet(key)


def encrypt_environment(env: dict[str, str] | None) -> dict[str, str]:
    return {key: encrypt_secret(value) for key, value in (env or {}).items()}


def decrypt_environment(env: dict[str, str] | None) -> dict[str, str]:
    return {key: decrypt_secret(value) for key, value in (env or {}).items()}


def redact_json_strings(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: redact_sensitive_data(nested) if isinstance(nested, str) else redact_json_strings(nested)
            for key, nested in value.items()
        }
    if isinstance(value, list):
        return [
            redact_sensitive_data(nested) if isinstance(nested, str) else redact_json_strings(nested)
            for nested in value
        ]
    return value


def migrate_sensitive_data(db: Any) -> None:
    from core.security import hash_session_token
    from models.db_models import (
        ApiConfig,
        ContextMemory,
        Conversation,
        McpServer,
        McpToolApproval,
        Message,
        Session,
        Setting,
    )

    _fernet()
    marker = db.query(Setting).filter(Setting.setting_key == "privacy_migration_v1").first()
    if marker and marker.setting_value is True:
        for row in db.query(ApiConfig).all():
            decrypt_secret(row.api_key)
        for row in db.query(McpServer).all():
            decrypt_environment(row.env)
        return

    for row in db.query(Session).all():
        row.token = hash_session_token(row.token)
    for row in db.query(ApiConfig).all():
        row.api_key = encrypt_secret(row.api_key)
    for row in db.query(McpServer).all():
        row.env = encrypt_environment(row.env)
    for row in db.query(McpToolApproval).all():
        row.arguments = redact_json_strings(row.arguments)

    for model, columns in (
        (Conversation, ("title",)),
        (Message, ("content",)),
        (ContextMemory, ("title", "content")),
    ):
        primary_key = model.id
        last_id = ""
        while True:
            query = db.query(model).filter(primary_key > last_id).order_by(primary_key).limit(500)
            rows = query.all()
            if not rows:
                break
            for row in rows:
                for column in columns:
                    value = getattr(row, column)
                    if value:
                        setattr(row, column, redact_sensitive_data(value))
            last_id = getattr(rows[-1], model.__mapper__.primary_key[0].key)
            db.commit()
    if marker:
        marker.setting_value = True
    else:
        db.add(Setting(setting_key="privacy_migration_v1", setting_value=True))
    db.commit()
