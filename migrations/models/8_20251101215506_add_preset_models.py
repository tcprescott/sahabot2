from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `preset_namespaces` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(255) NOT NULL UNIQUE,
    `owner_discord_id` BIGINT,
    `is_public` BOOL NOT NULL DEFAULT 1,
    `description` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    KEY `idx_preset_nam_name_a27cba` (`name`),
    KEY `idx_preset_nam_owner_d_89eca4` (`owner_discord_id`)
) CHARACTER SET utf8mb4 COMMENT='A namespace for organizing presets';
        CREATE TABLE IF NOT EXISTS `presets` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `preset_name` VARCHAR(255) NOT NULL,
    `randomizer` VARCHAR(50) NOT NULL,
    `content` LONGTEXT NOT NULL,
    `description` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `namespace_id` INT NOT NULL,
    UNIQUE KEY `uid_presets_preset__3e4d31` (`preset_name`, `randomizer`, `namespace_id`),
    KEY `idx_presets_preset__b5aff6` (`preset_name`),
    KEY `idx_presets_randomi_06c4ae` (`randomizer`),
    KEY `idx_presets_preset__e7e1dc` (`preset_name`, `randomizer`, `namespace_id`),
    KEY `idx_presets_randomi_3a50e0` (`randomizer`, `namespace_id`),
    CONSTRAINT `fk_presets_preset_n_d17cbc8a` FOREIGN KEY (`namespace_id`) REFERENCES `preset_namespaces` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='A preset configuration for a randomizer';
        CREATE TABLE IF NOT EXISTS `preset_namespace_collaborators` (
    `presetnamesp_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    FOREIGN KEY (`presetnamesp_id`) REFERENCES `preset_namespaces` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `preset_namespace_collaborators`;
        DROP TABLE IF EXISTS `presets`;
        DROP TABLE IF EXISTS `preset_namespaces`;"""


MODELS_STATE = "updated_with_presets"
