CREATE TABLE IF NOT EXISTS mcp_tool_policies (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    server_id VARCHAR(36) NOT NULL,
    tool_name VARCHAR(200) NOT NULL,
    mode ENUM('read_only', 'confirm', 'blocked') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_mcp_tool_policy (user_id, server_id, tool_name),
    INDEX idx_mcp_policy_server (server_id),
    CONSTRAINT fk_mcp_policy_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_mcp_policy_server FOREIGN KEY (server_id) REFERENCES mcp_servers(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS mcp_tool_approvals (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    conversation_id VARCHAR(36) DEFAULT NULL,
    server_id VARCHAR(36) NOT NULL,
    tool_name VARCHAR(200) NOT NULL,
    arguments JSON NOT NULL,
    status ENUM('pending', 'approved', 'rejected', 'expired', 'executed') NOT NULL DEFAULT 'pending',
    expires_at DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    decided_at DATETIME DEFAULT NULL,
    INDEX idx_mcp_approval_user_status (user_id, status),
    INDEX idx_mcp_approval_expiry (expires_at),
    CONSTRAINT fk_mcp_approval_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_mcp_approval_conversation FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    CONSTRAINT fk_mcp_approval_server FOREIGN KEY (server_id) REFERENCES mcp_servers(id) ON DELETE CASCADE
) ENGINE=InnoDB;
