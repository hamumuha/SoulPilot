-- Hamu Pet Web - MySQL Schema
CREATE DATABASE IF NOT EXISTS AIChat DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE AIChat;

CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(128) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS sessions (
    token VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL DEFAULT NULL,
    CONSTRAINT fk_sessions_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    setting_key VARCHAR(100) NOT NULL UNIQUE,
    setting_value JSON NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS api_configs (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    api_url TEXT NOT NULL,
    api_key TEXT NOT NULL,
    selected_model VARCHAR(200) NOT NULL,
    enabled TINYINT(1) DEFAULT 1,
    is_default TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS conversations (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(200) DEFAULT '新对话',
    user_id VARCHAR(36) DEFAULT NULL,
    source VARCHAR(20) DEFAULT 'chat',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_conversation_user (user_id),
    CONSTRAINT fk_conversation_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS messages (
    id VARCHAR(36) PRIMARY KEY,
    conversation_id VARCHAR(36) NOT NULL,
    role ENUM('user', 'assistant', 'system') NOT NULL,
    content MEDIUMTEXT NOT NULL,
    model VARCHAR(200) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_conversation (conversation_id),
    CONSTRAINT fk_messages_conversation FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS custom_templates (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    icon VARCHAR(20) DEFAULT '📝',
    category VARCHAR(50) DEFAULT '自定义',
    prompt TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS mcp_servers (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    command VARCHAR(200) NOT NULL,
    args JSON NOT NULL,
    env JSON DEFAULT NULL,
    enabled TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

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

-- Default settings
INSERT INTO settings (setting_key, setting_value) VALUES
('pet_settings', '{"petSize":"medium","petImageUrl":null,"alwaysOnTop":false,"clickThrough":false,"autoOpenChat":false}'),
('theme_settings', '{"darkMode":false,"chatTheme":"shiba","chatFontSize":"medium"}'),
('general_settings', '{"saveHistory":true,"markdownPath":"./conversations","mcpEnabled":false}'),
('network_proxy', '{"enabled":false,"host":"127.0.0.1","port":7890}'),
('proxy_config', '{"enabled":false,"port":3001,"autoSyncApiConfigs":true}'),
('quick_access_templates', '["summarize","translate","polish","explain"]'),
('active_config_id', 'null')
ON DUPLICATE KEY UPDATE setting_key = setting_key;
