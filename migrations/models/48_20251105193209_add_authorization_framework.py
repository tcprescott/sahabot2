from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `organization_roles` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL,
    `description` LONGTEXT,
    `is_builtin` BOOL NOT NULL DEFAULT 0,
    `is_locked` BOOL NOT NULL DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `created_by_id` INT,
    `organization_id` INT NOT NULL,
    UNIQUE KEY `uid_organizatio_organiz_782dbf` (`organization_id`, `name`),
    CONSTRAINT `fk_organiza_users_c6ecf1e0` FOREIGN KEY (`created_by_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_organiza_organiza_4702e2ce` FOREIGN KEY (`organization_id`) REFERENCES `organization` (`id`) ON DELETE CASCADE,
    KEY `idx_organizatio_organiz_2f3853` (`organization_id`, `is_builtin`),
    KEY `idx_organizatio_organiz_ae9185` (`organization_id`, `is_locked`)
) CHARACTER SET utf8mb4 COMMENT='Roles within an organization (both built-in and custom).';
        CREATE TABLE IF NOT EXISTS `organization_member_roles` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `assigned_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `assigned_by_id` INT,
    `member_id` INT NOT NULL,
    `role_id` INT NOT NULL,
    UNIQUE KEY `uid_organizatio_member__c7cc33` (`member_id`, `role_id`),
    CONSTRAINT `fk_organiza_users_7c191360` FOREIGN KEY (`assigned_by_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_organiza_organiza_810e4066` FOREIGN KEY (`member_id`) REFERENCES `organizationmember` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_organiza_organiza_9dfef70b` FOREIGN KEY (`role_id`) REFERENCES `organization_roles` (`id`) ON DELETE CASCADE,
    KEY `idx_organizatio_member__dc6789` (`member_id`),
    KEY `idx_organizatio_role_id_c024cb` (`role_id`)
) CHARACTER SET utf8mb4 COMMENT='Many-to-many relationship between organization members and roles.';
        CREATE TABLE IF NOT EXISTS `policy_statements` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `effect` VARCHAR(10) NOT NULL,
    `actions` JSON NOT NULL,
    `resources` JSON NOT NULL,
    `conditions` JSON,
    `description` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4 COMMENT='Individual policy statement with Effect/Actions/Resources/Conditions.';
        CREATE TABLE IF NOT EXISTS `role_policies` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `created_by_id` INT,
    `policy_statement_id` INT NOT NULL,
    `role_id` INT NOT NULL,
    UNIQUE KEY `uid_role_polici_role_id_e95ca1` (`role_id`, `policy_statement_id`),
    CONSTRAINT `fk_role_pol_users_9751390d` FOREIGN KEY (`created_by_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_role_pol_policy_s_33f0754d` FOREIGN KEY (`policy_statement_id`) REFERENCES `policy_statements` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_role_pol_organiza_1672f3fe` FOREIGN KEY (`role_id`) REFERENCES `organization_roles` (`id`) ON DELETE CASCADE,
    KEY `idx_role_polici_role_id_8964d2` (`role_id`),
    KEY `idx_role_polici_policy__f771e6` (`policy_statement_id`)
) CHARACTER SET utf8mb4 COMMENT='Links PolicyStatement to OrganizationRole.';
        CREATE TABLE IF NOT EXISTS `user_policies` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `created_by_id` INT,
    `organization_id` INT NOT NULL,
    `policy_statement_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    UNIQUE KEY `uid_user_polici_user_id_27b941` (`user_id`, `organization_id`, `policy_statement_id`),
    CONSTRAINT `fk_user_pol_users_3d19eb05` FOREIGN KEY (`created_by_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_user_pol_organiza_a55f22ce` FOREIGN KEY (`organization_id`) REFERENCES `organization` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_user_pol_policy_s_3b2c95c8` FOREIGN KEY (`policy_statement_id`) REFERENCES `policy_statements` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_user_pol_users_d5803e00` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    KEY `idx_user_polici_user_id_690f27` (`user_id`, `organization_id`)
) CHARACTER SET utf8mb4 COMMENT='Direct policy assignments to users (bypassing roles).';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `policy_statements`;
        DROP TABLE IF EXISTS `role_policies`;
        DROP TABLE IF EXISTS `organization_roles`;
        DROP TABLE IF EXISTS `organization_member_roles`;
        DROP TABLE IF EXISTS `user_policies`;"""


MODELS_STATE = (
    "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"
)
