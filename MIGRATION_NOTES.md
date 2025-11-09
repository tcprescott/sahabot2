# Database Migration Notes

## Pending Migration: Add RacetimeRoom Table

### Overview
This migration creates a new `racetime_rooms` table to track active RaceTime race rooms separately from the `matches` table. This decouples room state from match data and provides better room lifecycle management.

### Migration Steps

1. **Create the `racetime_rooms` table:**
```sql
CREATE TABLE IF NOT EXISTS `racetime_rooms` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `slug` VARCHAR(255) NOT NULL UNIQUE COMMENT 'Full room slug (e.g., alttpr/cool-doge-1234)',
    `category` VARCHAR(50) NOT NULL COMMENT 'RaceTime category (e.g., alttpr)',
    `room_name` VARCHAR(255) NOT NULL COMMENT 'Room name only (e.g., cool-doge-1234)',
    `status` VARCHAR(50) NULL COMMENT 'Current race status (open, pending, in_progress, finished, cancelled)',
    `match_id` INT NULL UNIQUE COMMENT 'Associated tournament match (if any)',
    `bot_id` INT NULL COMMENT 'Bot managing this room',
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT 'When room was created or joined',
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT 'Last status update',
    CONSTRAINT `fk_racetime_rooms_match` FOREIGN KEY (`match_id`) REFERENCES `matches` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_racetime_rooms_bot` FOREIGN KEY (`bot_id`) REFERENCES `racetime_bots` (`id`) ON DELETE SET NULL,
    INDEX `idx_racetime_rooms_slug` (`slug`),
    INDEX `idx_racetime_rooms_category` (`category`),
    INDEX `idx_racetime_rooms_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

2. **Migrate existing data from `matches.racetime_room_slug` to `racetime_rooms`:**
```sql
-- Create RacetimeRoom records for all matches with active race rooms
INSERT INTO `racetime_rooms` (`slug`, `category`, `room_name`, `match_id`, `status`, `created_at`, `updated_at`)
SELECT 
    m.racetime_room_slug as slug,
    SUBSTRING_INDEX(m.racetime_room_slug, '/', 1) as category,
    SUBSTRING_INDEX(m.racetime_room_slug, '/', -1) as room_name,
    m.id as match_id,
    CASE 
        WHEN m.finished_at IS NOT NULL THEN 'finished'
        WHEN m.started_at IS NOT NULL THEN 'in_progress'
        WHEN m.checked_in_at IS NOT NULL THEN 'pending'
        ELSE 'open'
    END as status,
    m.created_at,
    m.updated_at
FROM `matches` m
WHERE m.racetime_room_slug IS NOT NULL
    AND m.finished_at IS NULL;  -- Only migrate unfinished matches
```

3. **Verify the migration:**
```sql
-- Count records
SELECT COUNT(*) FROM racetime_rooms;

-- Check that all unfinished matches with rooms have corresponding RacetimeRoom records
SELECT COUNT(*) 
FROM matches m
WHERE m.racetime_room_slug IS NOT NULL 
    AND m.finished_at IS NULL
    AND NOT EXISTS (SELECT 1 FROM racetime_rooms r WHERE r.match_id = m.id);
-- Should return 0
```

4. **After verification, the `matches.racetime_room_slug` field can be dropped in a future migration:**
```sql
-- DO NOT RUN THIS YET - wait until code is fully migrated
-- ALTER TABLE `matches` DROP COLUMN `racetime_room_slug`;
```

### Code Changes Required

Update all code that references `match.racetime_room_slug` to use `match.racetime_room.slug` instead:

1. **Services** (tournament_service.py, etc.)
   - Change: `if match.racetime_room_slug:`
   - To: `if await match.racetime_room.exists():`
   - Or: `room = await match.racetime_room.get_or_none()`

2. **Views** (event_schedule.py, etc.)
   - Prefetch: `await Match.filter(...).prefetch_related('racetime_room').all()`
   - Access: `match.racetime_room.slug if match.racetime_room else None`

3. **Bot Code** (racetime/client.py)
   - Update room creation to create RacetimeRoom records
   - Update room joining to query RacetimeRoom table
   - Update room cleanup to delete RacetimeRoom records

### Rollback Plan

If issues arise, the migration can be rolled back:

```sql
-- Drop the new table
DROP TABLE IF EXISTS `racetime_rooms`;

-- The matches.racetime_room_slug field remains unchanged
```

### Notes

- The `racetime_room_slug` field is marked as DEPRECATED in the Match model but kept for backward compatibility
- Once all code is migrated and tested, a follow-up migration will remove the deprecated field
- The RacetimeRoom table uses OneToOne relationship with Match (one room per match maximum)
- Finished matches don't need RacetimeRoom records (they're historical data)
