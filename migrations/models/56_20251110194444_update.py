from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `async_qualifiers` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(255) NOT NULL,
    `description` LONGTEXT,
    `is_active` BOOL NOT NULL DEFAULT 1,
    `hide_results` BOOL NOT NULL DEFAULT 0,
    `discord_channel_id` BIGINT UNIQUE,
    `runs_per_pool` SMALLINT NOT NULL DEFAULT 1,
    `max_reattempts` SMALLINT NOT NULL DEFAULT -1,
    `require_racetime_for_async_runs` BOOL NOT NULL DEFAULT 0,
    `discord_warnings` JSON,
    `discord_warnings_checked_at` DATETIME(6),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `organization_id` INT NOT NULL,
    CONSTRAINT `fk_async_qu_organiza_b0d8a129` FOREIGN KEY (`organization_id`) REFERENCES `organization` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='Async Qualifier model.';
        CREATE TABLE IF NOT EXISTS `async_qualifier_audit_logs` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `action` VARCHAR(100) NOT NULL,
    `details` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `tournament_id` INT NOT NULL,
    `user_id` INT,
    CONSTRAINT `fk_async_qu_async_qu_2e5f14d9` FOREIGN KEY (`tournament_id`) REFERENCES `async_qualifiers` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_async_qu_users_7588ea7f` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='Audit log for async qualifier actions.';
        CREATE TABLE IF NOT EXISTS `async_qualifier_pools` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(255) NOT NULL,
    `description` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `tournament_id` INT NOT NULL,
    UNIQUE KEY `uid_async_quali_tournam_471a8b` (`tournament_id`, `name`),
    CONSTRAINT `fk_async_qu_async_qu_e79659f1` FOREIGN KEY (`tournament_id`) REFERENCES `async_qualifiers` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='Pool of permalinks for an async qualifier.';
        CREATE TABLE IF NOT EXISTS `async_qualifier_permalinks` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `url` VARCHAR(500) NOT NULL,
    `notes` LONGTEXT,
    `par_time` DOUBLE,
    `par_updated_at` DATETIME(6),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `pool_id` INT NOT NULL,
    CONSTRAINT `fk_async_qu_async_qu_e0a68310` FOREIGN KEY (`pool_id`) REFERENCES `async_qualifier_pools` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='Permalink/seed for an async qualifier pool.';
        CREATE TABLE IF NOT EXISTS `async_qualifier_live_races` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `episode_id` INT UNIQUE,
    `scheduled_at` DATETIME(6),
    `match_title` VARCHAR(200),
    `racetime_slug` VARCHAR(200) UNIQUE,
    `racetime_goal` VARCHAR(255),
    `room_open_time` DATETIME(6),
    `status` VARCHAR(45) NOT NULL DEFAULT 'scheduled',
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `permalink_id` INT,
    `pool_id` INT NOT NULL,
    `race_room_profile_id` INT,
    `tournament_id` INT NOT NULL,
    CONSTRAINT `fk_async_qu_async_qu_7950a144` FOREIGN KEY (`permalink_id`) REFERENCES `async_qualifier_permalinks` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_async_qu_async_qu_a00f9983` FOREIGN KEY (`pool_id`) REFERENCES `async_qualifier_pools` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_async_qu_race_roo_81eba1bb` FOREIGN KEY (`race_room_profile_id`) REFERENCES `race_room_profiles` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_async_qu_async_qu_9b4a4ff5` FOREIGN KEY (`tournament_id`) REFERENCES `async_qualifiers` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='Live race event for async qualifiers.';
        CREATE TABLE IF NOT EXISTS `async_qualifier_races` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `discord_thread_id` BIGINT,
    `thread_open_time` DATETIME(6),
    `thread_timeout_time` DATETIME(6),
    `start_time` DATETIME(6),
    `end_time` DATETIME(6),
    `status` VARCHAR(50) NOT NULL DEFAULT 'pending',
    `reattempted` BOOL NOT NULL DEFAULT 0,
    `runner_notes` LONGTEXT,
    `runner_vod_url` VARCHAR(500),
    `score` DOUBLE,
    `score_updated_at` DATETIME(6),
    `review_status` VARCHAR(20) NOT NULL DEFAULT 'pending',
    `reviewed_at` DATETIME(6),
    `reviewer_notes` LONGTEXT,
    `review_requested_by_user` BOOL NOT NULL DEFAULT 0,
    `review_request_reason` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `live_race_id` INT,
    `permalink_id` INT NOT NULL,
    `reviewed_by_id` INT,
    `tournament_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    CONSTRAINT `fk_async_qu_async_qu_2f38f320` FOREIGN KEY (`live_race_id`) REFERENCES `async_qualifier_live_races` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_async_qu_async_qu_9bc94b1e` FOREIGN KEY (`permalink_id`) REFERENCES `async_qualifier_permalinks` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_async_qu_users_72efa08a` FOREIGN KEY (`reviewed_by_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_async_qu_async_qu_325e2b4b` FOREIGN KEY (`tournament_id`) REFERENCES `async_qualifiers` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_async_qu_users_515bb920` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='Individual race in an async qualifier.';
        DROP TABLE IF EXISTS `async_tournament_races`;
        DROP TABLE IF EXISTS `async_tournament_audit_logs`;
        DROP TABLE IF EXISTS `async_tournament_live_races`;
        DROP TABLE IF EXISTS `async_tournament_permalinks`;
        DROP TABLE IF EXISTS `async_tournament_pools`;
        DROP TABLE IF EXISTS `async_tournaments`;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `async_qualifier_races`;
        DROP TABLE IF EXISTS `async_qualifier_audit_logs`;
        DROP TABLE IF EXISTS `async_qualifier_live_races`;
        DROP TABLE IF EXISTS `async_qualifiers`;
        DROP TABLE IF EXISTS `async_qualifier_pools`;
        DROP TABLE IF EXISTS `async_qualifier_permalinks`;"""


MODELS_STATE = (
    "eJztfWtz2zjS7l9B6cs458hJ7MTJjM++b5ViKxnv+raSPHuJplgUBUtcU6SGF3s8W/PfTz"
    "fAO0GalCiJlLFVm7FIdBN8AALoB43u/3YW1pQaztveUh9ZD9TsnJL/dkx1QeGPzL0u6ajL"
    "ZXQHL7jqxGCF1aWuuFiMXVYnjmurmgt37lXDoXBpSh3N1peubuFTOr3bC8LKE9VxLE1XXT"
    "olT7o7JyrxHGq/RTVTSwM9ujkrJTE2x+bQtWzqwJW56syJdU/cOfWlHlXDo/+PXVgaqm66"
    "9HfXv6U7xDKNZ+LMrSeTeEvLJJpNVawrq4dn6r95FN5vRkHchtp8/xUu6+aU/k6d4OfyQb"
    "nXqTFNgKhPUQG7rrjPS3btwnS/soL4ihNFswxvYUaFl8/u3DLD0lBTvDqjJrXxneGaa3sI"
    "qekZho9/gDKvaVSEVzEmM6X3qmdgw6B0pl2CizHg/UuaZWKbQm0c9oIzfMrh8dHHzx9//P"
    "Dp449QhNUkvPL5T/560btzQYbA9ajzJ7uvuiovwWCMcGP/zSB3NldtMXRB+RR4UOU0eAFU"
    "MfR8bELwgiIRelEvrgm+hfq7YlBz5s7h59H79wVg/dIbnP3cGxxAqTf4MhZ8Wfyju/ZvHf"
    "N7iGiEIOvaCn4HVXBMSq2E5vb7YgLMTx9LYPnpYy6UeCuJpO4oMJbpj4IO+cWyDKqaOZ9z"
    "XC4F5QQEV8GyTNcM4V0JzQL0vtzcXGKlF47zm8EuXIxSMN5dfelDV2XoQiHdpfHvPcKUja"
    "90qqhuFtRzuOPqCypGNSmZgnXqi74N/tgUxmv2WHiH6Q1MOX5rFWA+urjqD0e9q9sE8Oe9"
    "UR/vHLOrz6mrB59SvTtUQv5xMfqZ4E/y75vrPkPQctyZzZ4YlRv9u4N1Uj3XUkzrSVGnse"
    "82uBoAk2hYQ3VcBebjVZo2LVtD425/aG9JWwavXdiY9PelDupWaMqkpGzIHTckLpCVSmvR"
    "mMTLC9KGjKo1rElxIX//IFySIiJZAL+CwaHPzL/RZ4bjBdRINTXRlO/bU3e+mubh92fQB4"
    "Kr0Wdnq0+hcRPvGvB68FKUz/JnveFZ77zfYSBOVO3hSbWnSgJNvGMdW6krYdnsrcXxIn1F"
    "NdUZe398C6xzYKg6z6b2d081dBCwOyJTNlmiW2jQYlnlt6BwWbMWpUj4CMIUC2xZYTE0YP"
    "md6LFENQzrCS3WZ/zlWkSzFktEnEBN0NRFgbltmZbnGM9dbhFTVZuPTS6E5eCxZEntBWg1"
    "Hxxyb1sLsIdtHWTIElaioMZFy1i3CVrAS9D8lgw1bkvbdGxqqqF5BjO5JypM0GAvk3vd1M"
    "HIxvGb2BRuwkoXK6iCvM0vH6iP0MdnlFni1pKcvJH29Cuwp3cx9idswOOTkxJGIJTKtQLZ"
    "vaTJEq9ZBskR/T2nE6bEWkJQFC1++v8cJdY9AWoHV71/vkmsfS5vrr8FxWMon13efJE29s"
    "Zt7Lk+pQoM4VBjpyKsadEtIiueWRsG7VR3YHacKtpcNU1qCJfWX/RZ7swkll9poZ0eG7Y0"
    "U/10fPzhw+fj9x8+/Xjy8fPnkx/fh1NW9lbR3PXl4hvim2iHLOC2ZzoKLGGUpd/1klgPYW"
    "lj5KKdEd6eRXO0NtAfjj9/CqHFH0VgDq96l5dZ9HByRNrMpYulaCwohi8rvT38DpsBoE1/"
    "83QbhkRYGePKVrm3bIWbCNi5Ko6uJbTJAVc84IKZaEJtBIj/dXhzXTzYxmVT+N6Z8Nbfp7"
    "rmdomhO+6vbVuU4dsXL8rS669ukmVCBelFWRo4mK6o9rAStfuCKkkQ7pgglPsxe7of4y2n"
    "KzZsUlI27E4b1q981K6WPVNN/Q/mpFKN2RdISoY/g2kNTP9NSl3z8CzL+Au6TFXmP0JZ9a"
    "a6qxiWaBH3xZf9+rcBY5SFnJmQze+h1ktr1i6gk1vn+iO3CWoF5hK0DlStoQN0KWDYFkWd"
    "mNxu0JzaAh6195EW9o/t7SSGI8uLO4rxMaj0zqKSHA9L7DFieQLlyb1l8/2/aMOQIBsOYA"
    "n2HEuJ4R7kCJ7/wHYeiQMTHhTQVNMNihDdTEs7XKWmWZ4Jr6mDGf88NlVzSqZ04s1mUAO5"
    "77ebfT/eaFV2/iKJdu79bcSZdkpdVRfNQUX7fqGI3PMT7vlJzmEvTNMs5+Bano1/m241yz"
    "Qj95rs0t266+3gCMRmbfmoL9VgyWcdx5rXB8va8pmPTGzJp7tjDSiW9Hzc2cS3H46Pob3/"
    "orkSZwbKmytJluJlcwWfwnwVCX2ETieyPgTWSikpNFYGdAkTFxTBU3+ONqdTz6BTLvoERg"
    "Zldgw19JkOL4Suia6u6UsVBVghPBDoAExj06Eg6OgL6FKqSZk/Jfo5IkQjXE/MZm/JgPvE"
    "oFckwTlwAXa2Bk94JjbFDS46hVrdmYb+AFpBzRRa168499c8gG6sP+pTeIsuPBsXAYfMpf"
    "IN7jw+hm6dNj0dm4dkGL6R6hJnSTW0xphzpYO3b5bUZD6X8XeMrLr422Lxn2Ge586bsZfy"
    "D1EGL0O42w/BZn3A1pCG2y4MN7rUHfgYq60CkkJtcieqbekUDgErmBVpWbkrveNdaRiQtL"
    "ni6q5RyXk5JdYS8zvlwlyKxjguoDGOszRG6HDkGN6sCqIZwVow3e7B4M0iOrNUgV9iCUQD"
    "wXb20k042tuWtVAsWNkowSBbZRDPSsthfMfDOCyEXU9AnuZ/HZHE9kjoaPrv1PV5fCzzdX"
    "zM/zg+Zr4NyZnuKWcq/bT2omGzvgvBsctqllxa7BWRumnPj4rARRKvdfcAl5YKWwYtbete"
    "NyqSCHnir7QLys2sFQCUGzNb2ZgRH4ZbE8X2OcelkYzNASUwDGba+oGMa27cOFkazNRK5G"
    "VEMxNIDcjifsUAVN5GGluLaN4Eu7pLdWyfp34H4pLOoc3Be4u+odEn/uJua2I0KL/dGoVt"
    "KbfdGj7mHdvOZPumGYdNFvQlu+laQRa3XvuqNo/CyhANyk74/uWUTJ4J7qPqS4MGwWvekt"
    "GcRrFhdIdEUWXGpuqwndh4wBgWunVJTuKRZhzpSLqb/UjPrkRv+8Xb6UJ6Umqn4KRgp+Ak"
    "u1NgWq5oXM53IA0FWrIzsG33URhJcjYIvhqWmkcPxIRSuN6jVNuQPb+5+3LZJ7eD/tnF8M"
    "I/Ax7SX+wmXoqO1g/6vUsBkKvTj1lpud8iD3NLLlluEsiGLb1JIGnutXlFyYWtxoWV4Rd2"
    "fjK5QeSCPIi7M7IFP8aXeRb/k61AsQTHy0uwK1AUuYl4MF0hSyIgV0qLsjjAMcIFiZW5+k"
    "hjjArWuEvwhG0QGXjhOW4UG1glGrVdaKaxaXqLCSiBJ2NsMR77lzLmJuCABGzK99Q2DUP8"
    "V8mxbJZjkUF61/YdlEF65YFdaX5Iu/JVNmxmfSp9V1aYoaXvysZ8V1phazYIZrGjSr2hsC"
    "o4qTQJme2ZneUOU1c/SF3hDPVFeGaYn1nGEEwlTM5yYvGQT8QB0XDL/gfMC8OifuPpYzUy"
    "XbugSjO8KeaVgXkd/tMdm/zMBrdKMdgv3tRNsHEXMpPqDo3KIPIyP2u+cqaChHi7XIG3nK"
    "rAR2rlA2wiebmluuMtVb9REGvLc9dp17QK2bS7P51or9aiSUnZkLvOVmpOV2rGuJxsxN1/"
    "jW04KwyT89QPjlOTy2Epj8MCh8PMKfogYw8VrfiK09MkJGUqmkwqKnhzpbI/Z1pObjIINx"
    "l8mB6tqVLR5zgr2RKIt+B9jEZcNU/ZUEK6ycYgXMNRViQvlxs7Xm7Y9FGnT0r1VUdGsMWL"
    "j+NygZEK4iJlFx+IzkqfSUpUfiGN+EJWWvBkJFsyH299ycPHEkwLSTFApzJ5VsQxd19Yt+"
    "erkYv4IsgxvalTzWMoV4Hs49J3aH9dTKTv0J42bH42smquQ2mxdm0V1he4aodhv1rqdyW0"
    "H2AJUy14VUbwlXZA6fq3JoDbz8HSUtCkv+R2Yn01Ik5VgzGtHqhqu3ltGgzdi4lthAvD2j"
    "tiKw+EprFML4BLxEuL1izb643NBTC7hGtUsqWibLDl8r+ule81SMtD8Jstm+1VLMTOmbog"
    "MvFc6pyOTQL/06en5NbWF6r9TB7oM7+IYqfE74p4GXMOYUcjT3ML3YLRy5dOeQQvpp3Lxf"
    "OGn5Ib9kqqgVWKK4rnSScHLjUx2yx0E5f+7r7hirjSU9Jj/yXY5d+ZLGkT3vVTbZ6Svw5v"
    "rglrSD+pES/u3/dfcIk2MJjJUP7ilvh/BwHH8E15uYh2OiWYKQm+u8UyKBYlSZUezTKn7S"
    "YW5ts4KpuT0xa/ohxn8NyctncmvOD3qa65mMbMcX9t8hQkAhFfupj0TvPb3STjhgrSpHc0"
    "1lTprUmpluwnyMQXkmZeaf8gvkaoxrcIJDdE9jVygpTpgmtkqmSK2xWYgPgHWAN4Nyl1Tf"
    "tsy2IoGJeaZMHGYb6iGBxoYDFAM/ZsTslukXWbePkFE1JskCpp7F6p5vOhax1C7TGlLj/L"
    "7Mz1JZlQ94lSM2FTEv4Ah505ZU/JWsJra+ThmPh1QSwmVsg/WhvXlB9aiavC2yibCasUFo"
    "Dr32NFpA1Zpw3pODA2rbSeTInKBWXDFpRh+1TdO84KvqK1USLtLh+2K4GXkHlN25/JzKWV"
    "k21Z6+XXailoBSvxaHascTl5FSptHp5ll5WJL6zErpJVS+KdOIrB6q+9GMY+t5cRjM0H0j"
    "QUTY8JCIf9Ebm+u7xsgllTxqCpaMpUsGEGzCLADaisVUAOJpY7JxNPN9xDdntKNM9xrcWb"
    "rOmyqiK0WL4EN7h9cqA7Ciurm/8zgsZ9czo2D0kP1lGHPj9KnuZpWwhT9PCbWBjdRHToA9"
    "BPCPQ9HboCweNPuqYaxjNaQBpgSA5My8UfuPSeqA59g7JnqomXJ2A3WVPc6592wRbD1oE/"
    "LJvwbjSFat7DUxXD0h7olFcUxYdQkKiabTlgmBlGopYOvu0Ze3PBu37FJuIve+a/5+Q5+Z"
    "bqdKGjFvEbPuoqubUMXXsewrtSdNmBmmNIHCby1cN358CDwgnvU0KzL82WCGPqZotFL8MN"
    "QsF9Dpe0EmVA3rU2bY5KHTw+Kjh4fJQ9eCwD8m7wUE1sbMhgW3hULCkoD4dlYPWH1MqoRn"
    "ISVLmB+yr4NnkAbC8aNnMALPjsqtKoGblXyqLu3rFh/8jB3e44N5jYKr3nLP7CJb8lGLcq"
    "01uZHRROmSFnsGbM7vyd+PZ02eRpJqRU9HVjvCMInJxpGRSbJEJTbFVHwIOmi3SLaFDWVM"
    "8s0hENu3KlmOVcAwk1cOf8/v091dx33KXfeTegjuXZGnXenVkgmnOuoRatyBjikg29/Xma"
    "c62YP3yb4VNB0ic/WVT0NGvok6HsSWz8dBgFSVnlTsm407u8vPnHuIPc57hz3r/+17iDBf"
    "yjGf5JBtW21Wc8cuCfY+AwQAXp29nbLvk+jp0jPOXD1xgQS1zma+xx51dGpNoBHOknBDfI"
    "EmM/2mbOQ/4P15841/Ff+AUj5p/BM7QQaP8h1uQ/8Na8ecKb0ICGNQP4Diz/WMibHOZUHq"
    "fYLMnJO2UVmjOSaCvRWYrnLKA50yyn/91mQcw/SxETqeEsxe4mt60dpgjHriooJ4QkzmVw"
    "jsbvKkAnpeTpoBJAy60RGW9MspKSbn6VDRuawRkHoZe4FebDVUMetNaSB5mjXzWAgexdK8"
    "HYJJMS6yECEiXZf/L5E9Zf43zXy9zJJUsPnnY7SoVKwOdnCZLyojWwIFPL/MHl52F8NsZ3"
    "jco//BK4paZZJYEnFD/6gj5P4sKSBaiRBZDrpb2YVrPrJbmNu2Ykz9TYUzGgp1j6NW3nyg"
    "MyK4BWsAcuD3ase7Ajs5xYH03Bjlp7wcwZtKRDwbYdCjZp3MQsPoFxk7QH840bZn9WM27O"
    "dRu3A32DIeYigVYK6gPbY/K8xBvmjBsagrMxK2lhR/kNw3pymL2DxQ6dJdX0+9Q+Lu5VWp"
    "7Lj7+gApWpAAVDzVpipDsLk2UHouXO/QcxRtJOTCVMIaGoNIKkESSNIGkESV/WdoAoLclW"
    "xzxrKWgFlqSMf05bF/WswSiu5IMubXFpi796W/wL32cbqc7DzSO1bX1KOwKjXFSsW2Sd+/"
    "t3igsSiuWLlDTT/YcRlCWBLGEPyVrjRYXR6B660OOc8A43v8PYFSgFdvtcdYlqU4ET9Zln"
    "29D3jWdi4Yal4y2Xlg2mPjXhTaEK76a6w//iurqg22Wx+iaU0N9dCv1vOjbxoRba40FFEC"
    "fiUNdlbtVYkzkl957r2TTPjJfeyJs1wVlXFYGX744cE6nHH3njGG4+uLvuKOhg/CjYKXjp"
    "CHskt8Uj7BtzLpQn2CU71JUuha+hYau6FG5yRXeuO+gI9Q2WOMl1geh+4RpuyksqMyxaeo"
    "uFyRCmnqB7oL9lIQhRnNpVKSeIa7oBXUJLsS0XlQSCYCfA0oqv5eaqA+sviqs406SaK1TV"
    "HZsq7siwtRusviYW81azluwr4Wsy0OXrZWfI4uLR9o2fMCh/+yVttzNAcd2Q3m6Ra7qa13"
    "Qh0tm1iD7LBTAutSnCbjNA/nR8/OHD5+P3Hz79ePLx8+eTH9+HiGZvFUH75eIbopsYPrPr"
    "Eg5U1VhlSal2HuTbyNLZ73datRRTSamWHMrZApowarN4jwoLs1jRGskKy6ha7bbzwgG3wZ"
    "jCEgQ+int3BXsgJVqDQdCsk3oNWv8Hr11q31+a7K227KTJvqcNmznPxk3Oyn46abHXtMEv"
    "/XRkzLn27PeHX6p0PBGMW1vOExcLAvSIvgVRpCfBcWJMpDay8N+SzTMKtTVxE66giVj9lR"
    "Rjm3wblkiOTsNCAUvLcYy42nvLZi3xQHGujoXS8hs8bCq/gK8nzn25c9vyZvOUeJYWFvYd"
    "uK6k2cY/yzDXQ21Op55Bp/3HnCBy4oLdMly2E8hwvEqy2iPMYu9EVHOghHAlMbo6woksVB"
    "fKCSLJraUN+e9cSfRhQCrbVNHA5leJ8+y4dIF8dpIqd8Ymd3xYLqlqBz4I4w5D0xl3oBgL"
    "FPWWjOa6w10qoBrQX+H/Diu8AFl4qbEZJjT0bHKFNQ2OY7PsIP5zf3DSNSYX57kHtjMnER"
    "gCwWiVmgDYWe2wjV3V9Rx5SKF2Nj318VTm1cXy9Sz2toTtlgl2jpNjeLMqjHBSqpWM8Mcy"
    "gfI+5gfK+5hNB5IcHSrAmZXc3p5F9M106oL2uAy0x/nQHmeglVzXXlAikuva04bNcF3xpV"
    "TJZVBc5DXRM5Lj2nDSVexXNTAyV4Ge5iFYlpJJGDjyMNDGycHd+Oed2fSpIyA12PVuEYeh"
    "BSVe4ivyIZXHCrZuNIuD5qC10Te9RebrzIQg2q69IcSyc3ZzddW/HvVGN4NTolkLZKRU17"
    "LH5mjQO/tbf4CtAl8HhSsDWJsM+r0rvAgLFhcWUQtOljciKyR8Xrb1SKsm2IuLSU8gaf7t"
    "oZUgzb89bdiM+RcMZpWdHbKCrzQqiTSgZegMGTqjRaEzJM2wIs0QG/K31+uaG80hOwM2iV"
    "vgvVNALoTdNp9dCL8QSS80bTboltqTr75KT8vKQwO7PjQwpxp65enmKsZ0Wlg2546bE2ZD"
    "ezX7OSkpG3LHDXmvm7ozX6klU6KyKXc9xFrmvW4vVqMrU7KyMXfemAtx5L78HIYxkZY4xh"
    "U12CbyF7q6m7djJYY0FGgJoFs4ew6l2AigzCzVqIJlRlBimsFUNx91V+Wpuytu4+XqkAfR"
    "xViz4Zdv060KdUqFRDppIywpnc7UBdREoUvdsaYV0xTlK6hlb6Yd/IjcjN6zPUu5Gb2nDZ"
    "vZjOYeQoo2V02TGhXHPpHsK92SzhzwLIlhRk7us6bwrGHfa70Dyc3Z/sp0lpc3EJPfaA1Y"
    "DpnCs0hf4z7tsmgKh6+q+4nZE27RyebUcr1CVu7cI9bt6bvpZeGTsqCLCbXXRCbw024pEE"
    "tDfV4bA7adfBtpaikWQfx9xfEmQQK+9YCJxnkG0dB/QMswquSiEIdT6Fbti92YdGTBPyV7"
    "19BX1prBXcyf2Ja1qAOTga9w4OvbFiydnuNYmq7yEMrJaBTkQL8nqvnMTIc1u1tVJ5dg8M"
    "nzdYkNTi+4vMQGROn50rT1ebfA84XvrCq2aj5UADAl9UqNRZ61lvKYBsIDhPlbFCLZVu5S"
    "nJQ5XnSSf7roRAZC2E+OSpKPe9qwMhCCPMfRFH5RnkhY8USCPABT9gDMDg8hMPM9zzgLbP"
    "sXLLOAT3g5PuM3eAjB4u8GN1dEx3SLC7Y2Zdke1cBcPTo94nl8WC3eZCMzrqFHGoBbNwA9"
    "u5JrlV+8nflmTkrFQjgpiIVwko2FEK9ZBsh8F8qUWEtsv227UUpbcC9MBmkL7mnDNtMWbM"
    "OcnDFqqqwzXzSAgj2RTZs/O4zyXtH4qW9pnnSdECzPM74V+Ut07rwQc+uQuydN+1CLFs9V"
    "kzbWm65xD/Kc+847FY2QpFRLls4ya3wrjxZIC2QvFqrSAtnThs1YIDK+tMyhtjaeZe2OGs"
    "Ikp2w5WodXaSMXQPV4SlY01mJnBgSWWvJEQb6ZljzGIG20pg1d3cbaaHthV8gtjg1ucUij"
    "rX6jzY+jrlAT37RqmHKBtMT3xcgGzEtftHipGt8gUiRjxKdgB2AUa0lNZaGbnksdZULvYf"
    "FdYWFQpGJ7xs6n97teL8RApb95ug29LuiKmDm0ajfO0yF7cM7A4dd79dA+aQUtWV1sYbXm"
    "j6KiJL0VunSBFtmpU5sYKYxWXHYUqZHrj6RBkkjXfa8brsibtVx6oDxdW0xPqhqsNdOHBi"
    "8vTwncGps8F5Byc335r1Pib35ZpvE8Nq9vrvvQFJbJ32vnSUw5iFPP5oyYv8aosD7JV7C9"
    "1cnRcYOWJ4nIVKuNK2INchQvAHqljNH5GuTiJBMtAL3C2epioWYx/uvw5joH4xz5FMJ3Jr"
    "z696muuV1i6I77ayPxLoAXESimmtKsUje5kYYK0lQTPB26v1IUlKdwJBHKy3EkbeKYU2uh"
    "/5G3Ismza+JSrRwv6j8JvIS+TGEUpQbV2HLAhuWxYDWRP1zka5ADRokBQzq/7IWPhHR+2d"
    "OGlc4vnU0wwqrGNyGUpW3d60bFWMJ54q80SkrI2E6sikE1BZKvFsNgdaj4K5qKQIrFXxGa"
    "0rltg85teZ97DWgGIdu+WM3sm2WxFIxl5bBMzCQ1AYrx724jja0GVTTTlkE2NSLWgmyg8z"
    "ZU2WJoxVNGS7xbGzSqJhmNOgLHRl6r7Y8e6znqjCrM4wp11YTLHWptGSprekHnbY7OPB1L"
    "ZIC9Us3nkYX/lhze/GDW31DfKtDu8KgwewMl5fudfh8b+xedKsmtzIjr5hhaNmuNB/ocg5"
    "ph7A+QYYP5RTLB3t25bXmzeepe0GhRcwlHWriuZID/s6QHfEG4V+GQUsYfXgZ+balbvKR2"
    "94IBlNTunjZsZqUkU9OsNALKeJsyn0/z8vnI8Ju00eE3ry1Xv9c1ZnBeWrOOYMmcLlK4YD"
    "ZjhRXDmpVbMHdAL7HuiQNd653qunSxxBQScWVONv5mGaGxOTZHaHQ76GGauEmg8vojtZ+J"
    "L+zwuJ3eVEfPK6KaUygy8WYz+FUyauf3sMPHFo9Q5nsneBiLg+85/KJvemFf/1Uu/Gte+M"
    "fALY9fUug1TYbxUTvxFS+gs1tV+mCO9GsF0/f0hm6axTDfoSspVYMT12oe+3+590zmUEYm"
    "nm7AuOi8xcf+b2ftGXNrvl3pkVfUkUucnshq2V6Hzrrpd2771+cX19/g3tgc9q9Hp+RobH"
    "7tXVz2z6Gnjs1BfzT4FyvwIT1xFnb7D8efP4U9Hn8UdfbhVe/yUtDjbduy4ct3AnY6iXf+"
    "QfqMYEv8Q7d9lN6mLvREzfJE5km+d0RSapfdd2eDsWQD94I0yrKBaAWs0KoxsRqatFkjT4"
    "NaMHhtSeju/7cp2PqWfOS6fKTk0drDow29SRyCQkItUbZbmllzYmIlKTZsehKXI65FmJX5"
    "Es9WWhLJNizsEE01A4kJxeLOkmpY0pdjvZ8xbNrcshxK5tYTFoPCXCWdgrahtaBcAMralC"
    "xBtWWqBjmgb2dvu36CnTCcAKPvsH+86RILCTomNTbj7p2HT/qUBvKxFLX+6o7oJoHiuUl6"
    "In4vSRTlUB4Jj9tfc7nCKMJVmhXM3kw78cZuSwZxJeNgZQbxZdKgUWxi527YHyi3/cHVxX"
    "B4cXOtgBV6/Q3pgqP378fmzeBb7/ri370R3rrq4yFQpXd+zuiEvPuD/tXNL7zEUaqE6DnH"
    "74/H5ujmbnDdu+pfj5SzQR9WJ3DjAz4gdgPWGwP/xlHiRv/6nF9OKrq7PQ8UfRibV73R2c"
    "/K8Ozn/vkdo0M+onp+ddBPXD8Krp/dXN1e9kf86nF4tXd91r/0y0aa+6PRxfW3oTK8+3J1"
    "MfKFPo7NQe+sn7h49N6/2Lu9HXCkPh4d+dcG/b/2z/xy8MTLi1/gGtMQq+HRSfzO4ObmSr"
    "m57V/ze58SUgFmH48+x69/vbi+GP7Mb/wYvxF/uaOfxia0xj/iFT1+718LW/njMdT94vqX"
    "ixHW/qx/wa6eILr+1d7ZWf92xK/GywZveoLY+lf7/7y9GPCL26eoyjLcL3/jzWS7O+cXw7"
    "ObwblyfsWYwf5V7+KSEYP/6H/5+ebmb4AcTLBXQ2jVrYMvI0HWfxpfElt7YTxLVmRPG7aB"
    "J5jbecBRMksrgCaZpRqYpbyvtwb0Kp6lbe5xuhryRGySpovj/BWWPZ5Nvxqq0O0tr2i3iK"
    "RLvP49l1LuQawkSec/iKAIo7NYHDtomHdT3eF/kQSdFfJq/sME9F0NOpHY6xmG9eSQ4R1Y"
    "9r3zq4trRuvxeEOP1HjmailRp4/Y16ehNHtm/AFOd2wubcaN4LPvLohmeK5L7WxJ4s5Vl2"
    "AISCT2yER10q8qJOkyX6ffEnhUKUvDFZZGzi1+Ae4HsQUl4VY34ZYCegVrPKVh11Z48O3p"
    "U+zs8D729p1xVoql2aT4mZ1/zNm3DYOB7gRfP4E//UqyYQMKkPSH3BTb3K/nCiZcUrJJHg"
    "rYKCZDPWiQJzVqkQOUIfo90Tzbhq4P4zefbOj0zdot0yRDr5Rjg2kJYwPn+8GFArv1f+vc"
    "sL9U5jeP+3UTy3PJ0/xZ1ObvggZev3034TIn+bG9oFEkP7anDZvhx4Kpb/JcjeHJyO2WG+"
    "vEDKanuRXOkLGZs9KSsDbubPf84/5xaTLCWmdNWkg8AmyPn2zed18W4sy4lwB42B+R67vL"
    "yyYQbxfmIzeVCjk3v1S3LN2mR+VfpNm4boLJq5jx+B9LN/mRz4QNmeXSqgjKWC9b548qJ7"
    "JYJ23F9tFLRKE/el8mDD2Uyo1Dz+5Jz4xNsz/Yap5TKTlQXOT1bu06lU+4JYVe5QE3+vtS"
    "BxtsFa4xIdkkrvFVnoaShNVe8BqSsNrThs0QVsFnV5Wwysi9JjJFMlKSkWoPIxV9qttjpB"
    "qMYWbkaqqr14ACdI7beYFyCop1S7t42VyipHfXFWrLODnxs4f4R6AtyzuVlkwewfQvM9Ix"
    "LGvdE5M+pTyyyNNc1+Zk4UHpCR2b8P629UinZPJM1LjT14RCLWjG3QLdMfzuwL3FXKj7BF"
    "Pano5NAv/Tp6fk1tYXqv1MHugzv4htcUp82OFhCY14kxeLwXhK4g0Wv8OL2oEu6JSnhJ1c"
    "RfY1vJypOBfjQX3Cqvi/ycGSmlNogi4J8OiCqv9QDTS9CR74qNMn/3kpzje4xx7qVyEupb"
    "BtdXil5Db7vW0tAlk7/Vqqe0pC14ugfXEb3kc/Vavc4kGJckzl904cWPzamWNcPJZdvIrS"
    "Na52apP9N4NcPrUZlN9edm/xNkjBx11y3zOVybtcKu+iXN4Z1jNe5QzE+V46KbFd++rkjI"
    "vNdMfJi8VWwNXnxV3bYJfu+ON/J7dfk6hau09KH59VqnTktNyue3LBdNjM3pyY+zLAF5M6"
    "aVlJ6zSMr4utpaq3bUJUcuqSU5ffqOTUZcOW5dTTVmemcQuCnWYkd30YqAQbUXIdWXfW3Y"
    "jDqApyWrBZzrYiAmZ7EBfQ8vHe2UYqub6+XJZrFnzPJbKfRv1zeyg3sDeXBzn9PTeV0e+8"
    "QOWX5/BLUff5U7H08nxlVOh2vTyPT07KsEQnJ/k0Ed7bP76zFvt1E1yQdKGVwc2kedeRdv"
    "sratgwr3dmLSheJUYdQHWeTU35zVMNFh1jzYTxPdT290BZMxs9by2e+C5YErowf94agKAe"
    "P2lfU2fmYiRsmDLXBCHh4gPqWtwvWIyypWXomr4uKmjN3qKm5xbjkc0mvzog51zXN1S1B5"
    "CEYfEVHkG/FnCGgdL+Y+uy2ab8D2DuXSjaXDVNnx1YHZwhU3bGdbUYlCgfwpqAtDXhcTpq"
    "T0HCjdXBKUr/0c45OhPosJ65OhV1saXdiJ9LrxGW6GB8SxFZ0MVk7aV+HJErprDFiCypvd"
    "AdZ/2xJY7Kbai0zciASUpdBX86S1Vb9zu6ZequA21b3c1JOGhaT/BUcuB79JPo/aqFx3vB"
    "dgKFim1ZC2VpW/f62obUAPQNQN0t19biboXI2MojtaPsVetDY/8S09dycJA0UybWugvBga"
    "/qi+W29+hY0nAIzSpXdR7WNRwCZSPQ1d71HwypGMm5xrlryDW2rJ9sa/PbX++8sAUerYrK"
    "bYQvovJyO7zG7rLp7XCMQbXSFkpCUO6gyK0x2bCvIu/PLppTJv6RoSF2jedGQ0PINEp07Q"
    "TdyV1fRXUcwK6G7YjsqriF28BrGhclycYr1XweWfjvCp/9eozjptfhBR2YvYtSYEsl38zG"
    "HgcLLBGhbdmsOTD/TGooiXD3P4+w7QSFuUq/oDu3LW82zykjfkbu9wfXlUzT/Fna9owh8Y"
    "L9mcSsnA2arL+0Q5u2nOgW2KGx/l3VQ1sguuO4FeVR3XxQXumuLfPCSDNb8ievsmElf1LX"
    "3C2pgDamsy3hNrOWzba670yT7bXordK2Wtr6zbfXEiZYka2WMew2aq+FZECuuZZ2chHYaQ"
    "I/mHwDTeiDUyXaJVcQc3IpCnCZLYzxJMOqOkTFRMSYDtiGv81pOmGwRebqIwtQqdvoZkNg"
    "AmBJijHWo3Xv63fekr6qzaPHsHiZE8occ1jUS6qznKMqexI8JJ3jZWweTDwXY1SRieXO31"
    "QOe3nHPqRYDaIkseSAvp297bJH433iuwlhvhI/7uRUd5aG+qxwXT970BsO722dmlOeaxNv"
    "5obQDAJsxa5iWFA8Vx5Wh8thDWICHIvIdwn6r8NDdUUOTFwwDlVMQSIIYL4TlA+eoyy9ia"
    "FrLIalnwI2jhg2v+46QZsS1aaESwAIj7qjQw/mqqLFeiweZqQoE0AzWgPmljdUxyXwuWCL"
    "lQ6jGbCjv2LIzPTswi6GLy2DaMqT4zzWRtFAwYaE9HC6O6oiNipVATott+uopQXj6SpYy6"
    "iluU6xYazHsHc3PnZpNEJnYH/phH8kt+sT/mFS9diw4mQmz7UbQAYBkIROVzJ1r6FhG8jU"
    "NfTwRvu9oeoD9q6ERbk9VAs40u06+DQR4No8gPIGie1Tzw0dILZIT2/gEGKKXNzROcROWA"
    "HkbhxKYu+H6Vxgketa6zWH4KTi2uelzKm10P+gNgdxq104DpgekGpkQg3LnDFi9QDlGEk7"
    "M6wJDCH+O697ZnGT52byO+PLtHhZD6Y0Qa6kPqV1uPJ4t61CmyfkGDWNtLkTK8AGKdauOG"
    "DMoIf5FGjXZz+7jF/lo8nYjH8+IGMx45Gz8E86dBjTp9zDB1QkxJnMKRnNaeZd4lQ03mcs"
    "9IRi4vWZrZoYfDZWO5/wVU2Fv05EHjM55Pn5jZA2ZnXXnfQDUQVHQqCC3yijggMoUMFvvK"
    "hCxFxHr8uoaB+FAuo6JVCGu/7eiTo0n1tC8jpDaydKMho7UVaS2DWS2FHPrsg/JQW3SEDl"
    "DHpnwi8x7EqN4p7CoWAFzCPBZmCeHboai7m/lK2OeSTYDMyzY30zMZcc6z5QcZJj3dOGzQ"
    "YpSy3RSi6n0mK7To1Sn63efm61RlgZ9xeYSBlkG0GrJqbBNcm/6tGdGtmFy7J/6Y94fw+p"
    "1tKRt3CAdZNEVjr4loC+EsTnyietxMHBXqaqBtRzUAcBIO/1mWdzyttXwrgorMcIFgMEn0"
    "HwGQLqag09QrIivZHAsEkzFZKMWGk6bKpH3baP98lsLG073gdTme3iIK4KMoDlfuApqe0t"
    "445Odv2px6JBYwhAQ1/oApMxF7mk0PaAO/7YHOAcFg4cnqhgkjbdpoK5pZDAEivYOZFVx0"
    "deI1fFzGL2pVaENym4a0fMpqGK24QA1iIv7kohshlhiW4C3bk+pauCm5GVA4Ko6y5tykwb"
    "bS7iOkt037QC2YUFKC/06XoopxVIlAUom4AIfO3Ie6yOtEiJRDt9oiOocDWEk4JyQJa7iX"
    "u46SR3E/e0YRt4YmMXzSljq2yC4tuu87qhP1LFXj9BTDKD6CVoHWw5T8zaOCdJvJ2kdGsQ"
    "GJvekksmfcnZlMtkhinelhNkpimxL4eCJC6Y2lm7z8YwEezKraIFHb3P6b1uUof4jCXrca"
    "wwdxF3LbijUfieiOqrp1O2r2cTDPaLHnF+jklQd8dkFp7j8mAuKjF08wEEgh3Bt7MZUTXN"
    "8kyXOakvKHXJQjf1hbfwdwtj9Si/acjyiPqDEYtBLPB2lnuIK0yQ3YI9xDjoqQFKn+UCGJ"
    "fa1FJjM0D+dHz84cPn4/cfPv148vHz55Mf34eIZm8VQfvl4huim1gsZq2woB9XQjcm1LJ1"
    "3C7QrboLnhCSW+Exl2+XzixbmNv6r8Ob6zx/77hUCs47E17z+1TX3C5MIo7766bA7fzl3j"
    "NZmDEygaHJ1U3nLT7wfztrr2pECCMcxbvl6Y3xbtJaRAXp3XJ/Bs1bSOeOFhm57Y0ZDdow"
    "Z8sRBdY891SvvLuTFZZsogje6W8rAcvFJKQZ3htsCliUV6e9Izm5lyBJ7/3jRiXpvacNK0"
    "nvutY+kvTeMenNTirUmMQaabe2J7LeJN8rxkfA+eYCmc/7srZcmfy9MKf6oz71/BDNPzg+"
    "tZogcuErcz3BSYwqwkj1juD2g0Oe/HgWfoTsueqQCaVmxO4iMRs7s8N43nwq9jEFFTurJL"
    "nXDXOvsJIP2qu6DRCXlKZV0gwIsFlhuZgSrWG92KxzHg1aHgavXbjw536KSCNUGGOSQttb"
    "Fr7f9ViTosb9CaDi4JIWlaNLPrQrjDACcTnK7HiUwZBcijan2sNKTSoQl03amCZVqG1bgq"
    "P3+cc7RbLyjKdM4bi/xJxkXPe0YTOMa5tj6uxsNR3nR6qBJ5B8TSAW0NRpzmlNmrrl3Gk3"
    "xVUL+s3+hhiqHb0GhxHCOe+L5XZyvJWD292X/JRZsIeJ5VbwUGbhfEAk6VUs9kPOKYsU9N"
    "CFDuWQm57nzo8xiCzLiAaPZS7HQd3QSxjldb+7IX0NL8bzBPohzA8wgWN8V+bQ0awlnb4h"
    "mN3RTwqpOg70XqSxrWS6yTw6W9LWm6WtfZc/QUyXfKfLuMxuE/qFnTuoEkvsGST9/EE1XH"
    "dp/wB/OYs/PvywUna/kzIJ507y882dZNLNaYYO35hw5VGAeVxo10n9gtGC1YlcnK+C62bc"
    "XjlKDoWBTGDqvAhvJNgsiKN6NQLmlsYq63wN0lBihdgEx/IETKzmQLsPMcw6orTI5RDeNu"
    "O1F36bnSinM+/NmICSmvic6dqw1xmzR4WPD9bymgHLwCrjR0ZwewNJZ6jOVVxm/Mzr0Mmi"
    "f8sqQ1jl4iOLH23Tr3y4KOldjka3g5hKXJ8MrzIX/v0hfmmltctGRijuvyJcbfdNb5ExS9"
    "PxAH3hXW7kds4828Z5FdAzeUZ7EtWs9KL8w/HnT+F6HH8ULcWHV73LS1GIO3yssqCOA2Zm"
    "lSE/K7njUb83ner+uM/rBuYifAkLP5ObTdj2C4lVuHnzAd8s4r1ijd3DlIIm7R920F6C9l"
    "ksiXXP0xc5ngYmvXPvGbEPYv32aRCVXn6T0f+q+H7his0v0NH0HsC/V1bj19fwcttzL3bH"
    "5LbnnjZs6I6e4fZf8ut/9UFbco/ncCK+BmRi+xztPVySwIkb9iyjQ03YYCqJrc7w0BiEbV"
    "xhZk/GCth+FRp6ICSvFxVvrKU7XLlNNiWx8VRux60Xfi64ZlJJYlfNtV4OB1RVQSzRbKK6"
    "WNZzKHGWVMM9ZZR3AsJBh3+jEe8dCyKQf07Epz0TJ8zkMZHNHxPZN8IxmkqQd4xq2RTaMd"
    "hzXmEZmBKV60C5wJcNuwW/RpylK80wkcBrcsiTh+8369Xor5BqcGaMeYI1D8WyjnjRR/ay"
    "96KMW5ADYg1xC7ZhiDGTtcD6CkzaEiZXaEiXMLPY4lGQrlBgUOUWjZ2sR16bosFlLakZT3"
    "5IYAVrghmGv3DV6hO5uEv1H0uHFV93bHIjLXhZjLpq2dNYYV9JuNELd+51U3fmXI+GPdow"
    "mCpWJpTnjT3lFZ2zC5rlLQ3KzXSCID2g5X5vw68r1dXmXcJSUMDF07F5SL5Q12XxXuG+od"
    "9T7RmmaG7xs0CtWObWpo/oy4l7bwCAvZyr6HjJZNBLzsFCfdXRQRF8JPYzPhFtUw4swwmL"
    "4MsfhubmgroqGjcALSwM+DaedNvcuhmJDVjFgyIov1t3za9wNeqAKTfNdxqYsYdT6ESHR8"
    "cfPjbI46EZPrKrs4FZL9mUg2xDHGNZDt3qEWBjQjtHGvs2cwGywCwLYW5sz87z5SkYSPIc"
    "eLbtbRK48LCp19+/PsBpvkvgnykA2yW6iSmZ0Sx1uuHc3I1m5ob0+73cf+6wxREb7J9UwQ"
    "KrJPT7QnG8Eu6qcxlzJ+H1fGUNvXMuqxm7iHXTWwu0gqrhGBepBclVl709x7E0nQ1/0fYc"
    "YdUjBzpYXOZz2Zlo//iuZnTXNSmwYX9Eru8uL6uxNqnenYX+xqQjC/4pCfxVoKV1/bos/P"
    "FPukwDrEmFmVNrof9B7VuYDGjOKd9UmW4xJRaUxty4ULwkLXaFqtgmP7Iu2L0jTcTXlGXI"
    "SkkhB8Wrzg/z4mHrw2Cx9q/e1WXyzHBwLDjUA4IuqEZFozl9Zjp8ihMUQEtazB5yluiLQA"
    "5YgEvLTvg0EOsJ1oNvuMuDC9WfeC51Tscmgf/p01Nya+sLFazWB/rML4YaT8l18Cf/4vlr"
    "kQk1LKgUdEsugI89JXgUnjzNrXAxirScL3HAXCgC4o0VsOw3XDp63VMSNTjBr48ccBO6S5"
    "wF/v+PD11iWS78pq729k1UXf70w3vBCbSoDvyLJE86vIsZveX/jSrga4z1j1MiOm2FRN7T"
    "XHXj6qcWdbh40GinYQu7+OXCMh1zWZADFIIOiXFMfdlEJ/AroTvK0psYunZKIn+A8GnQGI"
    "+6o0PPZ+4tBg+J6lcgsltOIxLVF4xZC37jhctdcWHmwQxfWxhBU+jtEqIZJKUKMcVf7LNO"
    "O78UCkHZ7yklQaACditER1QyepxkRWtkRZMgl2aQElI7p5BeHmDY0NIM6qKtJ4GTg7E/mA"
    "SVqwrr0fsyuEKpXGDZvX0+CBxMQU0/DxzMjFnI87NmxWV2lTNLDD+b3aMZnE3yuBbEkOJ8"
    "rl+7FTaSPSuaOzPN8JKTZCS380i3nV8E65+1AZcJdqT3XPc1Usuvr2EzVHLaHClpIaTFdk"
    "wrv2SykwOUY8axH1rMJyu2SJLuS5DNTgHn0QjKOeybNRDPnMe6jmvcm05dliFNf+v7G2dy"
    "/a5dFtM1AlDKo6hbOT441OZ06hl0OlKdh46Ap08W6BaR9E5QVHGhbEmGPtRPUIgwtVlGXl"
    "gKae8BZf3WRBKe33ORvPWDZkJLaR52cLgU1g65dWo/QnWQTw/9M3FZxsh4rHuggAfiFBwz"
    "JAfJgJ2+ljckGqYSJf7n2jIpMvVfMDHzoW6yyvKdA+hA6NcB9QJbc0pZ0irDUqd+vV3Vdr"
    "1ll2CUUN8GhZJI5U1UJzebVYaRFbhPR0fjGNNq0t9dxfZMfw0buyv51pVWQvl8a0vZv/L4"
    "yXh/m5gbtsbm4eDEQRF93i9HK0vI73ol3/8nmI6XfeXy5tspeQ9zRu+M2aPKzW3/Whnc3F"
    "ydkqOxeXbZ713f3Sqjm7vBde+qfz1S7oa9b33ov2OzN/zX9Vn8Fiq4uRspoOL84hoUfygo"
    "dHGt3A5uvg36w+Ep+SgoODy7GfSVs97l2d1lb3Rxc31KToJilxe/9BWsM6vvKfk0Noe3/f"
    "75t94VPFi5uLq9GYxOyefoDW4vofTPN5fn/QG8Qn8AD/0x9tq3N5eX0bvDzZ9A9G44Qhx+"
    "+qmScVNLIDd/Yl6nv2V07LrPwWv2B7/0LnnPGmCDQi+6ue6zPgFYbR3mYNWDoXotcyqOQ5"
    "gzcQtEd0uF7OywqGbDS9PfcdHpCGeegoMNWdGWzD7b8KePbAddtDQqJl+z0k0KG1fLLN8g"
    "vjV47UImna0AuPNLlS3BlNiudgU7f7n3TB7edIIGm246b/Gx/9vZSOtuai+w/QFT6kC3xo"
    "0/FqUyMpGrjFEpUTlA7XiASrEdVZoyJSqbsgnxZ7E9qp/KE4i2clFWv4NaiMxqeUMTki2B"
    "dNssi3Qj2QtvA+lGsqcNm3EjCT67yXM1t4aM3CtlT3YfaqudGBa4gew2XFRzdsm7q0aLEn"
    "/fNUBZ0q+juRBmRq0mhdv6xjbZh9yDvCNwXEgW6BY5LvANeyXujv6y4wLXT0Cr4SeoDU+H"
    "xVzFH+jz4aNqeJQsVd0WnDVcTU35E3/wxym548fjfMV47Z3O0pUC2PbYZJpPiY8V4Q86iJ"
    "7Oays6QfezBw10iPM9Ypk+R4duRf4zCw6+6U5YMd/rAvWRyTMxLfNQnS50s+jwWyBb7vRb"
    "vHSZ428yHFcdK4B8RwjoilXMdb/4ToNxNWnbhH2qVWzzUKAtniTbtsmlW8lmk0buwfGkhu"
    "1JSBZpL8gGySLtacNWTcK0Saspbt4X2E6iYoUWVMLarmZH3Yj8qCMbiLlzW4/UtsFiYbkw"
    "f3epOQ2crMMoKhnDqia95S2tOAanxKcL8Da6j8drEzPMhkKLLIxnsqTJgC9vNmOr7cy6+p"
    "6hr3CBL1Pp7LHRlZ04pNXVvMlXWl17BK40EPZiHSkNhD1t2OJ8o03NSNTANU9jt0m3D2ft"
    "26S7sVejI9ssROswsCwFNmte0W6R3RqdLVd4hNRqtusw3KnzJgudHetggQrUTFhXwZHm8r"
    "Jogw7RwnPI0lCfqX3IZFw82cyj+Ae6WFzMlDh13pJbJsaONY9NLhwJGfpDGBbSgZZnfu9d"
    "onlgVfJ4ehZ7Y6fLApCybbsZPGBsJoJbkgmFx1M/nSoPZjuhM3SdJyOoRayaeOqZ7XjCCz"
    "yB8ejn+QmyDMVTBeG7f1EdDIBvkqE6Vx1bnX+x3B8cErX4N4wJypq3S8C8XSIwCAWWh7LH"
    "PzhjcwGflX4INr6KATttba678KaenXuC+nsUXBjfVjG9xQTDV0rrdLPWaRzsDIDDhWoYuS"
    "imRLd3CPBobThrOUm5TzH4GnuuJhx7K25iJeTkuRoxpivYMmlZac1IM1U27DaC6lkuFcw1"
    "+XRdKCCJujz3iEfVEK0bX/KOCMXkvJJm6vUpN24rH2MSycqOK+y4vi1Xsd/GpKRPjxDQFa"
    "bMpKQ8mrrjo6m7yL61i0VOzQeFojV91aNWAsnXBGIBBZ6TKqsy9102WdbuqIDVs2EJTwXF"
    "u1QN+G093mvt8Am+sWZuGtw5KvumCjYLeJFuyU0CLyz94t7ACFNisdQFPzhxTl7VNOr42c"
    "CohldiN+c6enI9Z3cL1tJW3octle6La/cDBEeKedno92mMiueOdegAFgjz0iwoQHAJBDDa"
    "qqsulnhOaAGTblB9XiTrUadgfePbbuTiPEwDFnvngyk1LXsBa/c//E2AJbXv8Qp8lG8Een"
    "mOsYRmlmKsjKJYz+BqYjiUUJK78RBElo70C1JsxYIrJ8CV4Vpr35JI4ltxRZ4R3g6PVTfE"
    "e0tjtcLboolrzVwQq0Y3Fgq3xVVyC/6mqWmmCrQCUQmsCNhKH35G7rV+9o3M8NLAxUWBWd"
    "64LCI78kR7MVeI+MOtAbpKeUEabJZnRqUmGeWsfwos8aDf5pvfYfa/l21uZrgyFWBO+olB"
    "8DzSue5olj09hGXgHC9pLOsNU5w1tVdRUt7CnnItzJz1NTIdaM76x766JOhv3GI0VI3OLW"
    "MKhdjT3iQ14TVufcb1mcxBL14O/wu10U1M0B0VTlxGgxVemb/a5DksBK8Fr7B0WYU0a7GE"
    "tdpEN3T3OVUZ9RFsqJh2/pvMVWeeLEgXqm5E5dhPAmt2O7T+Q5XMdAIL+YFizu4ewH8c8B"
    "7sIqtUoKh3e8EzRiF+qcrZ9B7Uz1Oq/KsVdbHSGM5bB2F2Cq4XrxK7wdkEN6Q60rrQ4RHv"
    "ss4wgB/IirydzfI7RFqQt3talFMPeTLl8IzrFOEQqisLammFdSDrPumc4T0lI/bni5D6Ej"
    "6NE8lwLA3ridqa6uTKQbdA19ykvH/Rp4IwOT3R1KXuIh2kcidbsbZyTeQ/RQSmr6ds27ys"
    "qY5GSWJ0x7lMbW7BAJuCCoZ3wyE48eDZ2fRAR/R7ngyJur7mpW2Zlmc6odbgAjmw/ETKfk"
    "lnbj0pUfEwCpEV1iAUZe2F7KLPukYj6pLavse2z5VGF4hBH6kRRjvigbTj0Y64OmxMeIiL"
    "ns68TBQgKRruoSPBNI+vy6IkYdnMbBDmcLu3rQUZLimdflMXOF/pi6Vl+1ytg9dn7Dr7KO"
    "LluEv5O9DzFHCqmSkn05bxw8I9/13YtUQXyB4VvsRTwfxCvNjYPIvWPP70eRibK1lkKMs0"
    "njE81PXd5SWCkgQL4UG4AuERQkZNx0O3ecwiDLXzUwnDdPRIActgnL8475KnuQ7zbUyfQx"
    "bYHy03h6WVbuCb5Vyjxhe4leizXAiTcrUEidwSlD8dH3/48Pn4/YdPP558/Pz55Mf3IabZ"
    "W0Xgfrn4hvgmeJCs7Z4eVqvQSiJZyStloE2srVfBN6OgJQ5oSYw/lkD4Yy6+H/PQ5bbFKr"
    "BGkq3Ec6N9llliq4AaCkpMMz01tp6v4oKaJ98ShLceRUJk56+Cd0aBBLwQ8LR1WHWLvEiP"
    "dGHdsQtrjKWqMi2kxGr5gvYgYmuCulsJz7XW23s5zQqpzSrjfq6ClmC87XFfTP6uhLicai"
    "tCvu5cW6hITra7TpsZbFxUcvKJC8mJNoFkZYeppFhLRqPt4RnfxFkB17S4xDeF76pLmBzx"
    "luC77dlUtD+6Atpy8VIJ7nWXLgVq5MJlxwuXVecFOSHkTQiBI0IVNOMyrUTy6H2ZRLZQKh"
    "dJdi91mjju9CHYTS6M2pSWlaEKUt009H3JInthun3TW2T8cJN9NqFge5707zPIdu6G/QHc"
    "GJtXN+f9QW90M8DMymOzd351cc0659gc3t3CLX7h+P37TrlOXl+Qt9CrqGJHTsjJMDGpcB"
    "u6gu+tGPpCdxXokcpCNz1XgHGu30mhjleUqzSd7ynyqKreYVPCcuhNzWsJr74KfTUr+Eo7"
    "qAyNvxdnerPmiIw5uBcNWzV3VnJKZ0SBaMHvy37924AaYQx38eGw3lIfBexO8xo672hYcn"
    "XjPJua8punGiy7lKJ6U1igGJYoUHAlaFDv3wO1PdR6ac0aOW9UwAn3xxSbPur0qVZ88PxL"
    "27GJ+hCitAt4GvuN1fVNtf4rsmFJr6hgz89MPIrqKAt1KrJVK4ASD85zRTG6+wAe0l6Igr"
    "UjQrVmf4lD025QWL9ZWoau6dRRfIjWAwcBuUWNz+2FhR2LrxcWPLLWdlimuk01NwRmi4A0"
    "dQYydPMBxpSZp+NaeC08/HNx31BVixFRl0vbegRM8Gjjeoic+Rra+bHg+ysLNnE6c325Zu"
    "8oiUVTewWP/ckPva6JBIuEehtpaikisbghtcASxVNpPzamhSmZNR6abP3l/XVMXblVfiuA"
    "cbxJ+KQaERrG1LYYqntYs3k2Ve4NdeYo1MTqrrmEiy/7v3L1X0H7NqeoTrQRymLF+u/FQh"
    "z4b1xub7SSyaSbj7ow68iq6F0whS3uXYngiTaFujlunUYl17hVgDphAGL/ffxulU7iWZfl"
    "ycg+6Fygf6cIbuzbDN6QoWhH9dlAF6wROE71tPjT5Dk1mWubs1yfML1l6q4DbVvtUOyLtJ"
    "7gaeTAD2PtYFgdEr3cmxp7VKhVibyD6kXvNuF1tOWhbWarpj+oOZSkXrGuUQ1e0lYeqR0u"
    "p2pgSZClt3+J6Wzx1xksKfhXuiY4A9Wc8mS5vJ/taL4MgkHhOL8MK1IzYK7qPKwJ11Cb06"
    "kHy8UR6GovsRKznIM8qkqUzrk2MzqT0LqlX5wokUYd+IQ5PFqEC/owbCrWag8GaA29qTPR"
    "Vv073aJ4q2pU5qWAq/kwyIBpWw+YBlO92As7/7hATERG74rvG1QB0S/eTgA3ct4CnugKQ3"
    "PnpyGPicgs5Gm3uSALeQVHuPqnlz//Pw2ZWtA="
)
