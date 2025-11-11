-- Add all test users (discord_id 10000-10082) to every organization
-- This creates OrganizationMember records for each user in each organization

INSERT INTO organizationmember (organization_id, user_id, joined_at, updated_at)
SELECT 
    o.id AS organization_id,
    u.id AS user_id,
    NOW() AS joined_at,
    NOW() AS updated_at
FROM organization o
CROSS JOIN users u
WHERE u.discord_id BETWEEN 10000 AND 10082
  AND u.is_active = 1
  AND o.is_active = 1
  AND NOT EXISTS (
    -- Avoid duplicates: don't insert if membership already exists
    SELECT 1 
    FROM organizationmember om 
    WHERE om.organization_id = o.id 
      AND om.user_id = u.id
  );