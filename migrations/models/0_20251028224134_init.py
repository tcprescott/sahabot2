from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `users` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `discord_id` BIGINT NOT NULL UNIQUE,
    `discord_username` VARCHAR(255) NOT NULL,
    `discord_discriminator` VARCHAR(4),
    `discord_avatar` VARCHAR(255),
    `discord_email` VARCHAR(255),
    `permission` SMALLINT NOT NULL COMMENT 'USER: 0\nMODERATOR: 50\nADMIN: 100\nSUPERADMIN: 200' DEFAULT 0,
    `is_active` BOOL NOT NULL DEFAULT 1,
    `api_rate_limit_per_minute` INT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    KEY `idx_users_discord_2431d5` (`discord_id`)
) CHARACTER SET utf8mb4 COMMENT='User model representing Discord-authenticated users.';
CREATE TABLE IF NOT EXISTS `audit_logs` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `action` VARCHAR(255) NOT NULL,
    `details` JSON,
    `ip_address` VARCHAR(45),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` INT,
    CONSTRAINT `fk_audit_lo_users_4188f9a7` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='Audit log for tracking user actions.';
CREATE TABLE IF NOT EXISTS `api_tokens` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(100),
    `token_hash` VARCHAR(64) NOT NULL UNIQUE,
    `is_active` BOOL NOT NULL DEFAULT 1,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `last_used_at` DATETIME(6),
    `expires_at` DATETIME(6),
    `user_id` INT NOT NULL,
    CONSTRAINT `fk_api_toke_users_82cd9ef8` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    KEY `idx_api_tokens_token_h_783e9a` (`token_hash`)
) CHARACTER SET utf8mb4 COMMENT='API token associated with a user.';
CREATE TABLE IF NOT EXISTS `aerich` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `version` VARCHAR(255) NOT NULL,
    `app` VARCHAR(100) NOT NULL,
    `content` JSON NOT NULL
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
    "LH+RHA=="
)
