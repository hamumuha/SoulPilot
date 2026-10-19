import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.security import hash_session_token
from db.session import Base
from models.db_models import (
    ApiConfig,
    ContextMemory,
    Conversation,
    McpServer,
    Message,
    Session,
    Setting,
    User,
)
from models.schemas import ApiConfigResponse
from services.privacy import (
    StreamingRedactor,
    decrypt_secret,
    encrypt_secret,
    migrate_sensitive_data,
    redact_sensitive_data,
)


class PrivacyServiceTests(unittest.TestCase):
    def test_redacts_common_chinese_identifiers_and_email(self):
        value = "手机号13800138000 邮箱alice@example.com 身份证11010519491231002X 卡号6222021234567890"

        self.assertEqual(
            redact_sensitive_data(value),
            "手机号138****8000 邮箱a***@example.com 身份证110105********002X 卡号622202******7890",
        )

    def test_streaming_redactor_masks_identifiers_split_across_chunks(self):
        redactor = StreamingRedactor()
        output = "".join(
            (
                redactor.feed("x" * 260),
                redactor.feed("13800"),
                redactor.feed("138000 alice@exam"),
                redactor.feed("ple.com"),
                redactor.feed("", final=True),
            )
        )

        self.assertEqual(output, "x" * 260 + "138****8000 a***@example.com")

    def test_secret_encryption_round_trips_and_legacy_plaintext_remains_readable(self):
        with patch(
            "services.privacy.DATA_ENCRYPTION_KEY",
            "unit-test-encryption-key-that-is-at-least-thirty-two-characters",
        ):
            encrypted = encrypt_secret("provider-secret")

            self.assertNotIn("provider-secret", encrypted)
            self.assertEqual(decrypt_secret(encrypted), "provider-secret")
            self.assertEqual(encrypt_secret(encrypted), encrypted)
            self.assertEqual(decrypt_secret("legacy-plaintext"), "legacy-plaintext")

    def test_api_config_response_does_not_contain_the_secret(self):
        with patch(
            "services.privacy.DATA_ENCRYPTION_KEY",
            "unit-test-encryption-key-that-is-at-least-thirty-two-characters",
        ):
            config = ApiConfig(
                id="config-id",
                name="test",
                provider="openai",
                api_url="https://example.test",
                api_key=encrypt_secret("provider-secret"),
                selected_model="model",
                enabled=True,
                is_default=False,
            )
            response = ApiConfigResponse.model_validate(config)

        self.assertTrue(response.has_api_key)
        self.assertFalse(hasattr(response, "api_key"))

    def test_sensitive_data_migration_is_idempotent(self):
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        db = sessionmaker(bind=engine)()
        with patch(
            "services.privacy.DATA_ENCRYPTION_KEY",
            "unit-test-encryption-key-that-is-at-least-thirty-two-characters",
        ):
            user = User(id="user-id", username="alice", password_hash="hashed")
            conversation = Conversation(id="conversation-id", user_id="user-id", title="联系13800138000")
            db.add_all(
                [
                    user,
                    conversation,
                    Session(token="legacy-session-token", user_id="user-id"),
                    ApiConfig(
                        id="config-id",
                        name="test",
                        provider="openai",
                        api_url="https://example.test",
                        api_key="legacy-api-key",
                        selected_model="model",
                    ),
                    McpServer(
                        id="server-id",
                        name="test",
                        command="node",
                        args=[],
                        env={"TOKEN": "legacy-mcp-secret"},
                    ),
                    Message(
                        id="message-id",
                        conversation_id="conversation-id",
                        role="user",
                        content="我的手机号13800138000",
                    ),
                    ContextMemory(
                        id="memory-id",
                        kind="preference",
                        title="联系方式",
                        content="alice@example.com",
                        source="manual",
                    ),
                ]
            )
            db.commit()

            migrate_sensitive_data(db)

            message = db.get(Message, "message-id")
            api_config = db.get(ApiConfig, "config-id")
            mcp_server = db.get(McpServer, "server-id")
            session = db.query(Session).one()
            self.assertEqual(message.content, "我的手机号138****8000")
            self.assertEqual(decrypt_secret(api_config.api_key), "legacy-api-key")
            self.assertEqual(decrypt_secret(mcp_server.env["TOKEN"]), "legacy-mcp-secret")
            self.assertNotEqual(session.token, "legacy-session-token")
            self.assertEqual(session.token, hash_session_token("legacy-session-token"))
            self.assertTrue(
                db.query(Setting)
                .filter_by(setting_key="privacy_migration_v1")
                .first()
                .setting_value
            )

            migrate_sensitive_data(db)
            self.assertEqual(db.get(Message, "message-id").content, "我的手机号138****8000")

        db.close()
        Base.metadata.drop_all(engine)
        engine.dispose()

    def test_session_token_hashing_is_idempotent(self):
        token = "opaque-session-token"
        self.assertEqual(hash_session_token(hash_session_token(token)), hash_session_token(token))


if __name__ == "__main__":
    unittest.main()
