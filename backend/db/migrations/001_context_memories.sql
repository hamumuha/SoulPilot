CREATE TABLE IF NOT EXISTS context_memories (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) DEFAULT NULL,
    conversation_id VARCHAR(36) DEFAULT NULL,
    kind VARCHAR(32) NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    source VARCHAR(32) NOT NULL DEFAULT 'manual',
    source_message_count INT NOT NULL DEFAULT 0,
    expires_at DATETIME DEFAULT NULL,
    last_accessed_at DATETIME DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_context_user_kind (user_id, kind),
    INDEX idx_context_kind_user (kind, user_id),
    INDEX idx_context_conversation (conversation_id),
    INDEX idx_context_expiry (expires_at),
    CONSTRAINT fk_context_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;
