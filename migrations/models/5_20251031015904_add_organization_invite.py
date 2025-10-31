from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `organizationinvite` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `slug` VARCHAR(100) NOT NULL UNIQUE,
    `is_active` BOOL NOT NULL DEFAULT 1,
    `max_uses` INT,
    `uses_count` INT NOT NULL DEFAULT 0,
    `expires_at` DATETIME(6),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `created_by_id` INT NOT NULL,
    `organization_id` INT NOT NULL,
    CONSTRAINT `fk_organiza_users_c9b65652` FOREIGN KEY (`created_by_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_organiza_organiza_db51623b` FOREIGN KEY (`organization_id`) REFERENCES `organization` (`id`) ON DELETE CASCADE,
    KEY `idx_organizatio_slug_882968` (`slug`)
) CHARACTER SET utf8mb4 COMMENT='Invite link for joining an organization.';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `organizationinvite`;"""


MODELS_STATE = (
    "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"
)
