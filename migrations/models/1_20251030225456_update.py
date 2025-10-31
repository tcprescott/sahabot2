from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `streamchannel` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(255) NOT NULL UNIQUE,
    `stream_url` VARCHAR(255),
    `is_active` BOOL NOT NULL DEFAULT 1,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `organization` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(255) NOT NULL UNIQUE,
    `description` LONGTEXT,
    `is_active` BOOL NOT NULL DEFAULT 1,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `tournament` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(255) NOT NULL,
    `description` LONGTEXT,
    `is_active` BOOL NOT NULL DEFAULT 1,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `organization_id` INT NOT NULL,
    CONSTRAINT `fk_tourname_organiza_30378f42` FOREIGN KEY (`organization_id`) REFERENCES `organization` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `match` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `scheduled_at` DATETIME(6),
    `checked_in_at` DATETIME(6),
    `started_at` DATETIME(6),
    `finished_at` DATETIME(6),
    `confirmed_at` DATETIME(6),
    `comment` LONGTEXT,
    `title` VARCHAR(255),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `stream_channel_id` INT,
    `tournament_id` INT NOT NULL,
    CONSTRAINT `fk_match_streamch_b0bb94e3` FOREIGN KEY (`stream_channel_id`) REFERENCES `streamchannel` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_match_tourname_afaca194` FOREIGN KEY (`tournament_id`) REFERENCES `tournament` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `crew` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `role` VARCHAR(100) NOT NULL,
    `approved` BOOL NOT NULL DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `approved_by_id` INT,
    `match_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    CONSTRAINT `fk_crew_users_ecc3b650` FOREIGN KEY (`approved_by_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_crew_match_10fe8cca` FOREIGN KEY (`match_id`) REFERENCES `match` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_crew_users_489b8481` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `matchplayers` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `finish_rank` INT,
    `assigned_station` VARCHAR(50),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `match_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    CONSTRAINT `fk_matchpla_match_185e9428` FOREIGN KEY (`match_id`) REFERENCES `match` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_matchpla_users_151c9d6c` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `tournamentplayers` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `tournament_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    CONSTRAINT `fk_tourname_tourname_ceef4cf1` FOREIGN KEY (`tournament_id`) REFERENCES `tournament` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_tourname_users_652d04ed` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `organizationmember` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `joined_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `organization_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    CONSTRAINT `fk_organiza_organiza_9c703c8c` FOREIGN KEY (`organization_id`) REFERENCES `organization` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_organiza_users_a1db5f86` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `organizationpermission` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `permission_name` VARCHAR(100) NOT NULL,
    `description` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `organization_id` INT NOT NULL,
    CONSTRAINT `fk_organiza_organiza_3eb8393c` FOREIGN KEY (`organization_id`) REFERENCES `organization` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        ALTER TABLE `audit_logs` ADD `organization_id` INT;
        CREATE TABLE `organizationmember_organizationpermission` (
    `organizationmember_id` INT NOT NULL REFERENCES `organizationmember` (`id`) ON DELETE CASCADE,
    `organizationpermission_id` INT NOT NULL REFERENCES `organizationpermission` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        ALTER TABLE `audit_logs` ADD CONSTRAINT `fk_audit_lo_organiza_5427d43d` FOREIGN KEY (`organization_id`) REFERENCES `organization` (`id`) ON DELETE CASCADE;
        ALTER TABLE `audit_logs` ADD INDEX `idx_audit_logs_organiz_53230c` (`organization_id`);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `audit_logs` DROP INDEX `idx_audit_logs_organiz_53230c`;
        ALTER TABLE `audit_logs` DROP FOREIGN KEY `fk_audit_lo_organiza_5427d43d`;
        ALTER TABLE `audit_logs` DROP COLUMN `organization_id`;
        DROP TABLE IF EXISTS `tournament`;
        DROP TABLE IF EXISTS `match`;
        DROP TABLE IF EXISTS `crew`;
        DROP TABLE IF EXISTS `organizationmember_organizationpermission`;
        DROP TABLE IF EXISTS `organizationpermission`;
        DROP TABLE IF EXISTS `organizationmember`;
        DROP TABLE IF EXISTS `tournamentplayers`;
        DROP TABLE IF EXISTS `organization`;
        DROP TABLE IF EXISTS `matchplayers`;
        DROP TABLE IF EXISTS `streamchannel`;"""


MODELS_STATE = (
    "eJztXVtT48YS/isqnkiVs2G9Bvb4PJnLJiQYU2CSVHa3VGNrsOcgjRRpBPik+O+ZGV1HNy"
    "Qh25KZPGzwaLqt+Xou/XW35H/2DFODuvPhzoH23lD5Zw8DA9I/hPaesgcsK2plDQTMdN7R"
    "pT14C5g5xAZzQhvvge5A2qRBZ24jiyATs65MmcJVKDa0bOhATBBeKGfImZu29iNwyZI1zQ"
    "GBmsIVf2CaNXNOVdOedZV8w9/wiFAVM5dAZ/gNK/Q/pA2VaxsZwF4pD3DlNWqeFpVd9DVy"
    "HcrFmbLvYvS3C38Qe7KrDDSxP2sR+7H/029DGBDTjjoLzcq+xobk3fpsFXait01v0SLKPe"
    "0zNw0LEDRDOiKrxM2AR0BATLv3WVkCZyl2hAZAetSPf1SAplE8Ha+nBW0DOQ413VDhmEcN"
    "ig4foe6j6KjU5uiRjv+PJaTQ2wr9x8MMzOemiwnto3h9PJG5DdkAVUCGysjvwtuYaoIM6B"
    "BgWF5f19LCvpfAIX5D1I3ND88uKjEX/AboLPn6nTYjrMFn6AQfrQf1HkFdE6Y50pgC3q6S"
    "lcXbLjD5wjuyqTdT56buGjjqbK3I0sRhb4QJa11ADG12q7SN2C6b/djVdX+VBAvCu9Ooi3"
    "eLMRkN3gNXZ2uISaeWUNAYWxB+09zEbPnRu3H4ABfsW37sfxwcDz5/Ohp8pl34nYQtxy/e"
    "8KKxe4Icgavp3gu/TqeP14PDGOEWrZM0fidokQuhKPc6lAFwLcDyP/3+p0/H/YNPR58PB8"
    "fHh58PQlDTl4rQPbn4mQFMO5h0v/R20QDxNMLBbpLG+XQJ7GKU47IJrOkA62AdNERgR3t9"
    "Q2gb4FnVIV6QJZuuh4cFSP4+ujn9ZXSzT3v9IOJ55V/qe9eyoRX23jr4phTUAtmfrlvDeF"
    "AC4UEuvoM8dL2zpw6skWQn8VzrnOUndR1QQ0GJaYBp5NFkOgHn2DU4phf0xgCewxS2ooJm"
    "TrMyyB5k+Na35zf0wjc8npyd34ymE/rpkH4cnY0vrobKxwP69+3dNb3kNfQPDpKudeHp96"
    "l/fBSed+xD0Ql3Ox5dXqaPtNBXzPAZTFOHAOf4XXG5BMozKrgumEM/otYELvIAJpNLdtOG"
    "4/ytey5Bwh+4uhufnN/sf+TTmXZCJMdNABZS2bhVnZ5DRKUzUqXnEaU5FfzaQh21ZvUWto"
    "tGHN4I14ikpIE8o1cYAclGU5RMwKf5oh+CP1rqhNExaBOsr3xbFkA3vRif305H42thQp+N"
    "pufsSp+3rhKt+0eJbTpUovxxMf1FYR+VvyZX5xxB0yELm39j1G/61x67J0r2TRWbTyqlrt"
    "G0C1oDYATDRoyyqmFFSWnYrRqW3zyj9fcPMYLKGmZg/vAEqMcjXIntmK5GNzndXDgZx5Av"
    "++W3G6jzgESGqf3Q2IjpuTQXrdwOX4LJG7RG9hbPDmI+QPxWJCw0ZWraOeVLQmHZ5iNd3H"
    "T3fnobGqe+hm7OCTZ+1YDGDNrOEllvnBklsWjrrDAAmS9VSwcrP8ZdH4kxU3UdaeooIsR0"
    "eUQJk2ZgmYb6uo+NaS8ARv/nI34jLJOYqjFfjB3DhR3EZt/MO5rTl4y+kWwBGCz4XbPvZt"
    "+UPHgz8lXxQzk/ZyW6AK8nrrhWhfbnCRjW+YGlnPwkB7d3OlFVRqh8YoqJDZUvpg3RArNm"
    "hZheXuZpabLcDP0SA2o8+eJp9+Tik3KoTPiQgM5uKa4oPt+UfQIxYDkZExP4TPwUk6eUZW"
    "y8PA2dsD/FslyQAKQ7Q+XX28mVwg2pPCGy9MWC6/4ALdVPNQ2Vi+sg7aSY92HqKJ0omgYJ"
    "n6Cbp1imf7aS/onALxuGjCRkIiIK6nqrIo0jW0U54dxIJAHkHaYD/KqhOekpOnLI9zY7oV"
    "kgskELXDPAbn88+jMJ6+nl5CRJIpmCk2TMMdxrqsxWUaqTEfNBmfk6yJ+ug9RslSGxnYic"
    "pENicR8hM6OfeyRmSK4pXtzKAzIWVaROSzXoYhLvKMSeitiJEKbx8z3e3+AqlYrLpk5BxV"
    "rr4MvjSrTZBk+hcxqfGHR0dEzQy/2cjm5PR2fne7lLtwHwJgl1bVu2ZTHM2JeyscwPGK+V"
    "wQYB0ywGGwumFjBYIXRbgsFeXyi8vwIcx5wjXmHoETROuDLo62sSjLveEjrDHNrCKgwDZu"
    "ZJPQLdhf/lDZbOTEWppH8JUa5HD1LFWZpPWHEtyg+D+r8PktBthdBVrTB7U1XZtl3jjwcH"
    "JXxj2ivXOebXRA+AT22VrYMqOIpSzVDjtc9FAcyjMuVjR/n1Y0epAjJZJtJ8mYjkbjvK3X"
    "TgEFbnW8e0SdkGjNuqgFKbbBkMu9CY8NlCVF0NU4qS0pBbNuTmwwHb2FV3KR7QouRpr2pA"
    "YDskltd2ZBDYoOYjn7wGNTav0tZ8KCVF3DhFtKnrXYXaBP27me9bC0cMqswqEpu42AZ5Td"
    "U1KYmNJDayTlsaNl2nnVlpO1tV85DTgu8ob5auSq2EXVzkPdELyclqgCY5WcNJWr76GoBt"
    "HOjpLm7xjeh14GJbvqwMyDoB2xQP8GZnRkAgnLb5EYFwhciQQNtOg15BSMCZL6Hm6rW89K"
    "SsjFlvOWZN7TF/oOZAuA6ZTgpLc27ZnPQ0tOvxZ1FSGnLLhrxHGDnLWpZMiEpTbnuLNfE9"
    "Yo9p1dlhE7LSmFs3psGeW03bcQqfc1zHmEhHCueKDHb+51SwVepxndBel5Orn4PuyWd4El"
    "V0iFTLMoUCHQF0A0+VyZTITkTOZUpkRw2bSonQUUJgqPMlwBjq1WLUmbLvNDESezlFJQxT"
    "cjLan8CzgejrVFDWPizLBmFTk+X1MLa4RhvA8pYrPI30tW5pl0Uzc/uqGtXOfntRGud39O"
    "ai9/7OorUnOgJY8vIdMdheSXvETCWzH207HXsF2Q8vuqbaAD9UADAh9U5dNeA49MSjjIQe"
    "dZVfJZMh20n2f1imxPQwv8L0MFVgKqn/TjBESf131LA5b5iUtXyylm89oBWwe1mVVrMqTR"
    "ZBtvvBNDE6kkHQUuGTfIbmxSdikRtJ0dq2xfUKKNpGX2uyefTWn0v043OuXek3h0SpTnKz"
    "taAp32wiHwCUzGhPUt53ZNj6P9TCvXLYRA6jlefNVnIXsSxshmMs5mjzvWIxMSxdYukSt2"
    "jj3MRr26M7SyGZX/2ZEOuIW7zpClDpI0sfWbpSma6U9JF31LCFPyW1nTfy716+Y7uvSm9x"
    "GL+Bl6VvibS1CNTmq++6/tN4m6GxBXV4mQCWIbWyIq+j3Fb6uTvhDkk/d0cNW/RzsvKJHV"
    "kIJR9zag0pqPGYk6yLanddlMBYM/zlJKPNd5WTVFp6yW3b7oq8ZFkUJfM/Mv8j8z+SF3eM"
    "PklevKOGrV8jBVwNEVU3F28MNo+Ynktz0eYjqDjmHhGWxuLu7Zz1pdBo5B0IcUIw5go7jI"
    "gFbQM5DlXdICrXodKOIbMpnulPm1fYZjS5ynFOI+ovmWeTB+qamef/TIRreSuCoHRWpBcq"
    "DSurkNqbbJAZmhqgydKtNZZuyTxNq/I0JWnJGODV1GT/1pjZb+Mm63Y1C2zEx6IW0AVxZD"
    "ZjbNSHyKK+ps3N8QBXydUS4e7PgNB2GZ09lX5HsrRNd7HM6ZP9HblTjLarKdO8lKZXMSRe"
    "oVgiZuVolnj/kmq17cTsFVCt2Pyumu/LEO3mw19r+Q1fmfxbY/JPJqp2gknKEMGOGlaGCJ"
    "o6uyXb3cqDSo3xttwE25s4W/0sW5v5WjSqJFdLst98viZQsCKuliJ2a+VrYTItl66NoI2y"
    "fxfVv9IromMg6iPpV8u28F4B/Xqke0Pm9p1Pu2Ii3aRba6m1ZEujAoh+924CuBa+Sr+RZD"
    "7a8Ovt5CqHS0UiCSDvMB3gVw3NSU/RkUO+txPWAhTZqItpa5KhJnxmpuAky4HbZFH/y79v"
    "tnsV"
)
