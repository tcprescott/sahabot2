from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `randomizer_presets` DROP INDEX `uid_randomizer__randomi_358748`;
        CREATE TABLE IF NOT EXISTS `preset_namespaces` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL UNIQUE COMMENT 'Unique namespace identifier (slug)',
    `display_name` VARCHAR(200) NOT NULL COMMENT 'Human-friendly display name',
    `description` LONGTEXT COMMENT 'Optional namespace description',
    `is_public` BOOL NOT NULL COMMENT 'Whether namespace is publicly visible' DEFAULT 1,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `organization_id` INT COMMENT 'Organization owner (for org namespaces)',
    `user_id` INT COMMENT 'User owner (for personal namespaces)',
    CONSTRAINT `fk_preset_n_organiza_ab6965e5` FOREIGN KEY (`organization_id`) REFERENCES `organization` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_preset_n_users_bb870883` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    KEY `idx_preset_name_user_id_32bd41` (`user_id`),
    KEY `idx_preset_name_organiz_ec5bb3` (`organization_id`),
    KEY `idx_preset_name_is_publ_0e7064` (`is_public`)
) CHARACTER SET utf8mb4 COMMENT='Model for preset namespaces.';
        ALTER TABLE `randomizer_presets` ADD `namespace_id` INT NOT NULL COMMENT 'Namespace this preset belongs to';
        ALTER TABLE `randomizer_presets` MODIFY COLUMN `user_id` INT NOT NULL COMMENT 'User who created the preset';
        ALTER TABLE `randomizer_presets` ADD CONSTRAINT `fk_randomiz_preset_n_1ad6ac04` FOREIGN KEY (`namespace_id`) REFERENCES `preset_namespaces` (`id`) ON DELETE CASCADE;
        ALTER TABLE `randomizer_presets` ADD UNIQUE INDEX `uid_randomizer__namespa_9c21cf` (`namespace_id`, `randomizer`, `name`);
        ALTER TABLE `randomizer_presets` ADD INDEX `idx_randomizer__namespa_0f69e7` (`namespace_id`, `randomizer`);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `randomizer_presets` DROP INDEX `idx_randomizer__namespa_0f69e7`;
        ALTER TABLE `randomizer_presets` DROP INDEX `uid_randomizer__namespa_9c21cf`;
        ALTER TABLE `randomizer_presets` DROP FOREIGN KEY `fk_randomiz_preset_n_1ad6ac04`;
        ALTER TABLE `randomizer_presets` DROP COLUMN `namespace_id`;
        ALTER TABLE `randomizer_presets` MODIFY COLUMN `user_id` INT NOT NULL;
        DROP TABLE IF EXISTS `preset_namespaces`;
        ALTER TABLE `randomizer_presets` ADD UNIQUE INDEX `uid_randomizer__randomi_358748` (`randomizer`, `name`);"""


MODELS_STATE = (
    "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"
    "uItCpZre4ako0mo+Usym3GBP/6f6SR0Nk="
)
