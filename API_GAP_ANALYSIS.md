# API Gap Analysis: Current State vs. Required for JS Frontend

## Executive Summary

This document analyzes the existing API coverage and identifies gaps that need to be filled to support a pure JavaScript frontend.

**Current State**: ~70 API endpoints across 22 route files  
**Estimated Need**: ~120-150 total endpoints  
**Gap**: ~50-80 new endpoints required  

---

## Existing API Coverage

### ✅ Well-Covered Areas (70-90% complete)

These areas have comprehensive API coverage and need minimal additions:

#### 1. User Management (`api/routes/users.py`)
- ✅ Get current user (`/users/me`)
- ✅ List all users (`/users/`)
- ✅ Search users (`/users/search`)
- ✅ Update user permission
- ✅ Update user settings
- ⚠️ **Missing**: Bulk user operations, user statistics

#### 2. Health Checks (`api/routes/health.py`)
- ✅ Basic health check
- ✅ Database health check
- ✅ Complete - no gaps

#### 3. Tokens (`api/routes/tokens.py`)
- ✅ List user tokens
- ✅ Create token
- ✅ Delete token
- ✅ Complete - no gaps

#### 4. Organizations (`api/routes/organizations.py`)
- ✅ List organizations
- ✅ Get organization details
- ✅ Create organization
- ✅ Update organization
- ✅ Get organization members
- ⚠️ **Missing**: Remove member, update member role

#### 5. Invites (`api/routes/invites.py`)
- ✅ List invites
- ✅ Create invite
- ✅ Update invite
- ✅ Delete invite
- ✅ Accept invite
- ✅ Complete - no gaps

#### 6. Presets (`api/routes/presets.py`)
- ✅ List presets
- ✅ Create preset
- ✅ Get preset details
- ✅ Update preset
- ✅ Delete preset
- ⚠️ **Missing**: Search/filter presets by game type, download preset file

#### 7. Tournaments (`api/routes/tournaments.py`)
- ✅ List tournaments
- ✅ Create tournament
- ✅ Update tournament
- ✅ Delete tournament
- ✅ Get tournament details
- ⚠️ **Missing**: Tournament participants, seeding, bracket generation

#### 8. Async Qualifiers (`api/routes/async_qualifiers.py`)
- ✅ List async qualifiers
- ✅ Create async qualifier
- ✅ Get async qualifier details
- ✅ Update async qualifier
- ✅ Delete async qualifier
- ⚠️ **Missing**: Participant registration, race submission

#### 9. Async Live Races (`api/routes/async_live_races.py`)
- ✅ List races
- ✅ Get race details
- ✅ Create race
- ✅ Update race status
- ⚠️ **Missing**: Submit race result, review race, reattempt race

#### 10. Scheduled Tasks (`api/routes/scheduled_tasks.py`)
- ✅ List tasks
- ✅ Create task
- ✅ Get task details
- ✅ Update task
- ✅ Delete task
- ✅ Complete - no gaps

#### 11. RaceTime Bots (`api/routes/racetime_bots.py`)
- ✅ List bots
- ✅ Get bot details
- ✅ Create bot
- ✅ Update bot
- ✅ Delete bot
- ✅ Complete - no gaps

#### 12. Race Room Profiles (`api/routes/race_room_profiles.py`)
- ✅ List profiles
- ✅ Get profile details
- ✅ Create profile
- ✅ Update profile
- ✅ Delete profile
- ✅ Complete - no gaps

#### 13. Tournament Match Settings (`api/routes/tournament_match_settings.py`)
- ✅ List settings
- ✅ Get settings details
- ✅ Create settings
- ✅ Delete settings
- ✅ Bulk create settings
- ✅ Complete - no gaps

#### 14. Stream Channels (`api/routes/stream_channels.py`)
- ✅ List channels
- ✅ Create channel
- ✅ Get channel details
- ✅ Update channel
- ✅ Delete channel
- ✅ Complete - no gaps

#### 15. Settings (`api/routes/settings.py`)
- ✅ List organization settings
- ✅ Create setting
- ✅ Get setting details
- ✅ Update setting
- ✅ Delete setting
- ✅ Complete - no gaps

#### 16. Audit Logs (`api/routes/audit_logs.py`)
- ✅ List audit logs
- ✅ Get audit log details
- ✅ Search audit logs
- ✅ Complete - no gaps

#### 17. Discord Guilds (`api/routes/discord_guilds.py`)
- ✅ List guilds
- ✅ Get guild details
- ✅ Remove guild
- ✅ Complete - no gaps

#### 18. Discord Scheduled Events (`api/routes/discord_scheduled_events.py`)
- ✅ List events
- ✅ Get event details
- ✅ Create event
- ✅ Delete event
- ✅ Complete - no gaps

#### 19. RaceTime OAuth (`api/routes/racetime.py`)
- ✅ Get RaceTime user info
- ✅ Link RaceTime account
- ✅ Get category details
- ✅ Get category leaderboard
- ✅ Submit async race
- ✅ Complete - no gaps

#### 20. Twitch OAuth (`api/routes/twitch.py`)
- ✅ Get Twitch user info
- ✅ Link Twitch account
- ✅ Get Twitch channel info
- ✅ Get Twitch stream info
- ✅ Search Twitch channels
- ✅ Complete - no gaps

#### 21. UI Authorization (`api/routes/ui_authorization.py`)
- ✅ Check organization permissions
- ✅ Get user organizations
- ✅ Check if user is member
- ✅ Check if user can manage tournaments
- ✅ Check if user can review races
- ✅ Complete - no gaps

---

## ⚠️ Partially Covered Areas (30-70% complete)

These areas need significant API additions:

### 1. Tournament Management (50% complete)

**Existing**:
- CRUD operations for tournaments

**Missing** (~15 endpoints):
- `GET /tournaments/{id}/participants` - List tournament participants
- `POST /tournaments/{id}/participants` - Register participant
- `DELETE /tournaments/{id}/participants/{participant_id}` - Remove participant
- `GET /tournaments/{id}/matches` - List tournament matches
- `POST /tournaments/{id}/matches` - Create match
- `PATCH /tournaments/{id}/matches/{match_id}` - Update match result
- `DELETE /tournaments/{id}/matches/{match_id}` - Delete match
- `POST /tournaments/{id}/seed` - Generate tournament seeding
- `POST /tournaments/{id}/bracket` - Generate bracket
- `GET /tournaments/{id}/standings` - Get tournament standings
- `GET /tournaments/{id}/schedule` - Get tournament schedule
- `POST /tournaments/{id}/schedule` - Update tournament schedule
- `GET /tournaments/{id}/export` - Export tournament data
- `POST /tournaments/{id}/clone` - Clone tournament
- `POST /tournaments/{id}/start` - Start tournament

### 2. Async Qualifier Race Management (40% complete)

**Existing**:
- CRUD for async qualifiers
- Basic race operations

**Missing** (~10 endpoints):
- `POST /async-qualifiers/{id}/register` - Register for qualifier
- `POST /async-qualifiers/{id}/submit-race` - Submit race result
- `GET /async-qualifiers/{id}/leaderboard` - Get leaderboard
- `GET /async-qualifiers/{id}/my-races` - Get user's race submissions
- `POST /async-qualifiers/{id}/races/{race_id}/review` - Review race submission
- `POST /async-qualifiers/{id}/races/{race_id}/approve` - Approve race
- `POST /async-qualifiers/{id}/races/{race_id}/reject` - Reject race
- `POST /async-qualifiers/{id}/races/{race_id}/reattempt` - Request reattempt
- `GET /async-qualifiers/{id}/participants` - List participants
- `GET /async-qualifiers/{id}/export` - Export qualifier data

### 3. Organization Member Management (60% complete)

**Existing**:
- Get organization members

**Missing** (~5 endpoints):
- `POST /organizations/{id}/members` - Add member to organization
- `DELETE /organizations/{id}/members/{user_id}` - Remove member
- `PATCH /organizations/{id}/members/{user_id}` - Update member role
- `GET /organizations/{id}/roles` - List available roles
- `POST /organizations/{id}/invite` - Send organization invite

### 4. Preset Management (70% complete)

**Existing**:
- CRUD for presets

**Missing** (~3 endpoints):
- `GET /presets/search` - Search presets with filters
- `GET /presets/{id}/download` - Download preset file
- `POST /presets/upload` - Upload preset file

---

## ❌ Missing Areas (0-30% complete)

These areas have little to no API coverage and need to be built from scratch:

### 1. Dashboard & Statistics (0% complete)

**Missing** (~10 endpoints):
- `GET /dashboard/overview` - Dashboard overview statistics
- `GET /dashboard/recent-activity` - Recent activity feed
- `GET /dashboard/my-tournaments` - User's tournaments
- `GET /dashboard/my-races` - User's races
- `GET /dashboard/notifications` - User notifications
- `POST /dashboard/notifications/{id}/read` - Mark notification as read
- `GET /statistics/tournaments` - Tournament statistics
- `GET /statistics/users` - User statistics
- `GET /statistics/races` - Race statistics
- `GET /statistics/organizations` - Organization statistics

### 2. File Upload & Media (0% complete)

**Missing** (~5 endpoints):
- `POST /upload/preset` - Upload preset file with validation
- `POST /upload/avatar` - Upload user avatar
- `POST /upload/logo` - Upload organization logo
- `GET /media/{filename}` - Serve uploaded media
- `DELETE /media/{filename}` - Delete uploaded media

### 3. Notifications System (0% complete)

**Missing** (~8 endpoints):
- `GET /notifications` - List user notifications
- `GET /notifications/unread` - Count unread notifications
- `POST /notifications/{id}/read` - Mark notification as read
- `POST /notifications/read-all` - Mark all as read
- `DELETE /notifications/{id}` - Delete notification
- `GET /notifications/settings` - Get notification preferences
- `PATCH /notifications/settings` - Update notification preferences
- `POST /notifications/test` - Send test notification

### 4. WebSocket Events (0% complete)

**Missing** (1 WebSocket endpoint):
- `WS /ws/events` - WebSocket connection for real-time updates
  - Race status updates
  - Tournament bracket updates
  - Notification delivery
  - Live leaderboard updates
  - Discord scheduled event updates

### 5. Admin Panel Data (20% complete)

**Existing**:
- User management
- Audit logs

**Missing** (~10 endpoints):
- `GET /admin/system-info` - System information
- `GET /admin/logs` - Application logs
- `GET /admin/metrics` - System metrics
- `POST /admin/cache/clear` - Clear application cache
- `POST /admin/tasks/run` - Manually run scheduled task
- `GET /admin/jobs` - List background jobs
- `GET /admin/errors` - Recent error logs
- `GET /admin/performance` - Performance metrics
- `POST /admin/maintenance` - Enable/disable maintenance mode
- `GET /admin/config` - Application configuration

### 6. Search & Filtering (10% complete)

**Existing**:
- User search
- Some basic list filtering

**Missing** (~8 endpoints):
- `GET /search/global` - Global search across entities
- `GET /search/tournaments` - Advanced tournament search
- `GET /search/users` - Advanced user search
- `GET /search/organizations` - Advanced organization search
- `GET /search/races` - Advanced race search
- `GET /search/presets` - Advanced preset search
- `GET /search/suggestions` - Search suggestions/autocomplete
- `GET /search/recent` - Recent searches

### 7. Export & Reporting (0% complete)

**Missing** (~6 endpoints):
- `GET /export/tournament/{id}` - Export tournament as CSV/JSON
- `GET /export/leaderboard/{id}` - Export leaderboard
- `GET /export/races/{qualifier_id}` - Export race results
- `GET /export/audit-logs` - Export audit logs
- `GET /reports/tournament-summary/{id}` - Generate tournament report
- `GET /reports/organization-activity/{id}` - Organization activity report

---

## API Endpoint Count Summary

| Category | Current | Needed | Gap | Priority |
|----------|---------|--------|-----|----------|
| Well-Covered (Complete) | ~45 | ~45 | 0 | - |
| Well-Covered (Minor gaps) | ~20 | ~25 | 5 | Medium |
| Partially Covered | ~15 | ~45 | 30 | High |
| Missing Areas | ~0 | ~50 | 50 | Medium-High |
| **Total** | **~80** | **~165** | **~85** | - |

---

## Priority Ranking for New Endpoints

### Priority 1: Critical for MVP (Weeks 1-2)
1. **Dashboard/Overview** (10 endpoints) - Users need landing page
2. **Tournament Participants** (5 endpoints) - Core tournament functionality
3. **WebSocket Events** (1 endpoint) - Real-time updates
4. **Notifications System** (8 endpoints) - User engagement

**Subtotal**: ~24 endpoints

### Priority 2: High Value Features (Weeks 3-4)
1. **Tournament Matches** (10 endpoints) - Tournament management
2. **Async Qualifier Registration/Submission** (10 endpoints) - Core async feature
3. **Organization Member Management** (5 endpoints) - Admin functionality
4. **File Upload** (5 endpoints) - Preset management

**Subtotal**: ~30 endpoints

### Priority 3: Nice to Have (Weeks 5-6)
1. **Search & Filtering** (8 endpoints) - Improved UX
2. **Admin Panel Data** (10 endpoints) - System monitoring
3. **Export & Reporting** (6 endpoints) - Data analysis
4. **Preset Search/Download** (3 endpoints) - Better preset browsing

**Subtotal**: ~27 endpoints

### Priority 4: Future Enhancements (Post-MVP)
1. **Advanced Statistics** (remaining dashboard endpoints)
2. **Additional Reports**
3. **Bulk Operations**

**Subtotal**: ~4 endpoints

---

## API Development Effort Estimate

### By Priority

| Priority | Endpoints | Complexity | Effort (days) |
|----------|-----------|------------|---------------|
| P1 (Critical) | 24 | Medium | 8-10 |
| P2 (High Value) | 30 | Medium-High | 12-15 |
| P3 (Nice to Have) | 27 | Low-Medium | 8-10 |
| P4 (Future) | 4 | Low | 1-2 |
| **Total** | **85** | - | **29-37 days** |

### Breakdown by Complexity

| Complexity | Count | Time Each | Total |
|------------|-------|-----------|-------|
| Simple (CRUD) | 40 | 2-3 hours | 10-12 days |
| Medium (Logic) | 30 | 4-6 hours | 12-18 days |
| Complex (Integration) | 15 | 1-2 days | 15-30 days |

**Realistic Estimate**: **6-8 weeks** (with testing, documentation)

---

## API Design Considerations

### 1. Pagination
All list endpoints should support:
```
GET /endpoint?page=1&per_page=20&sort_by=created_at&order=desc
```

**Response format**:
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "per_page": 20,
  "pages": 8
}
```

### 2. Filtering
Support common filters:
```
GET /tournaments?status=active&organization_id=5&game=alttpr
```

### 3. Searching
Full-text search where applicable:
```
GET /search?q=tournament&type=tournament&organization_id=5
```

### 4. Error Handling
Consistent error responses:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid tournament ID",
    "details": {...}
  }
}
```

### 5. Rate Limiting
Headers in every response:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1699999999
```

### 6. Caching
Support ETags and conditional requests:
```
ETag: "abc123"
Cache-Control: max-age=300
```

### 7. Versioning
API versioning strategy:
```
GET /api/v1/tournaments
Accept: application/vnd.sahabot.v1+json
```

---

## Authentication & Security

### JWT Token Structure
```json
{
  "user_id": 123,
  "discord_id": "1234567890",
  "permissions": ["user", "admin"],
  "organizations": [1, 2, 3],
  "exp": 1699999999,
  "iat": 1699999000
}
```

### Token Refresh Flow
1. Access token expires after 15 minutes
2. Refresh token valid for 30 days
3. Client automatically refreshes using:
   ```
   POST /api/auth/refresh
   Content-Type: application/json
   
   {
     "refresh_token": "..."
   }
   ```

### Multi-Tenant Security
Every request must:
1. Validate user is authenticated
2. Validate user is member of organization (if org-scoped)
3. Validate user has required permission
4. Filter results by organization

**Never trust client-provided `organization_id`**

---

## WebSocket Protocol

### Connection
```
WS /ws/events?token=<access_token>
```

### Event Format
```json
{
  "type": "RACE_UPDATED",
  "organization_id": 5,
  "data": {
    "race_id": 123,
    "status": "completed"
  },
  "timestamp": "2024-11-14T20:00:00Z"
}
```

### Event Types
- `RACE_UPDATED` - Race status changed
- `TOURNAMENT_UPDATED` - Tournament info changed
- `MATCH_UPDATED` - Match result updated
- `NOTIFICATION` - New notification for user
- `LEADERBOARD_UPDATED` - Leaderboard changed
- `SCHEDULED_EVENT_UPDATED` - Discord event updated

### Heartbeat
Client sends ping every 30 seconds:
```json
{"type": "PING"}
```

Server responds:
```json
{"type": "PONG"}
```

---

## Documentation Requirements

Each endpoint needs:
1. **OpenAPI/Swagger specification** - Auto-generated from FastAPI
2. **Examples** - Request/response examples
3. **Error cases** - Document all error codes
4. **Permissions** - Required permission level
5. **Rate limits** - Endpoint-specific limits if different from default

---

## Testing Strategy

### API Testing
1. **Unit tests** - Test each endpoint in isolation
2. **Integration tests** - Test endpoint chains (create → read → update → delete)
3. **Authentication tests** - Test with various permission levels
4. **Rate limit tests** - Verify rate limiting works
5. **Multi-tenant tests** - Verify organization isolation

### Test Coverage Goal
- **90%+ coverage** for API routes
- **100% coverage** for authorization logic

---

## Conclusion

**Current API Coverage**: ~48% (80 of 165 endpoints)  
**Required New Endpoints**: ~85 endpoints  
**Estimated Effort**: **6-8 weeks** for API completion  

The good news is that the existing API infrastructure is solid and follows FastAPI best practices. The service layer already contains all the business logic, so most new endpoints will be straightforward CRUD operations with service method calls.

**Key Recommendations**:
1. Start with Priority 1 endpoints (dashboard, tournaments, WebSocket)
2. Implement comprehensive OpenAPI documentation as you go
3. Add integration tests for each new endpoint
4. Use API-first development (design endpoint before implementing)
5. Consider API versioning from the start

---

**Document Version**: 1.0  
**Date**: November 14, 2024  
**Author**: GitHub Copilot Coding Agent  
**Status**: Draft for Review
