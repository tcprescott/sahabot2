# Discord Scheduled Events API Reference

This document provides a quick reference for the Discord Scheduled Events REST API endpoints.

## Authentication

All endpoints require Bearer token authentication. Include your API token in the Authorization header:

```
Authorization: Bearer YOUR_API_TOKEN
```

## Permissions

All Discord scheduled event endpoints require **MODERATOR** or **ADMIN** permission in the organization.

## Endpoints

### 1. List Discord Scheduled Events

Get all Discord scheduled events for an organization, optionally filtered by tournament.

**Endpoint:** `GET /api/discord-events/organizations/{organization_id}`

**Query Parameters:**
- `tournament_id` (optional): Filter events by tournament ID

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": 123,
      "organization_id": 1,
      "match_id": 456,
      "scheduled_event_id": 1234567890,
      "event_slug": "tournament-match-1",
      "created_at": "2025-11-04T12:00:00Z",
      "updated_at": "2025-11-04T12:30:00Z"
    }
  ],
  "count": 1
}
```

**Example:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.example.com/api/discord-events/organizations/1?tournament_id=5"
```

---

### 2. Get Events for Match

Get all Discord scheduled events for a specific match.

**Endpoint:** `GET /api/discord-events/organizations/{organization_id}/matches/{match_id}`

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": 123,
      "organization_id": 1,
      "match_id": 456,
      "scheduled_event_id": 1234567890,
      "event_slug": "tournament-match-1",
      "created_at": "2025-11-04T12:00:00Z",
      "updated_at": "2025-11-04T12:30:00Z"
    }
  ],
  "count": 1
}
```

**Example:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.example.com/api/discord-events/organizations/1/matches/456"
```

---

### 3. Sync Discord Events

Synchronize Discord scheduled events for a tournament. This operation:
- Creates events for newly scheduled matches
- Updates events for matches with changed details
- Deletes events for completed or deleted matches

**Endpoint:** `POST /api/discord-events/organizations/{organization_id}/sync`

**Request Body:**
```json
{
  "tournament_id": 5
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "stats": {
    "created": 3,
    "updated": 2,
    "deleted": 1,
    "skipped": 0,
    "errors": 0
  },
  "message": "Sync successful: Created 3 event(s), Updated 2 event(s), Deleted 1 event(s)"
}
```

**Example:**
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tournament_id": 5}' \
  "https://api.example.com/api/discord-events/organizations/1/sync"
```

---

### 4. Delete Events for Match

Delete all Discord scheduled events for a match from all configured Discord servers.

**Endpoint:** `DELETE /api/discord-events/organizations/{organization_id}/matches/{match_id}`

**Response:** `204 No Content`

**Example:**
```bash
curl -X DELETE \
  -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.example.com/api/discord-events/organizations/1/matches/456"
```

---

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Invalid or expired token"
}
```

### 403 Forbidden
```json
{
  "detail": "Insufficient permissions to manage Discord events"
}
```

### 404 Not Found
```json
{
  "detail": "Match not found or events already deleted"
}
```

### 429 Too Many Requests
```json
{
  "detail": "Rate limit exceeded"
}
```

---

## Use Cases

### Monitor Events for a Tournament
```bash
# List all events for tournament 5
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.example.com/api/discord-events/organizations/1?tournament_id=5"
```

### Bulk Sync Events
```bash
# Sync all events for a tournament
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tournament_id": 5}' \
  "https://api.example.com/api/discord-events/organizations/1/sync"
```

### Manual Event Cleanup
```bash
# Delete events for a specific match
curl -X DELETE \
  -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.example.com/api/discord-events/organizations/1/matches/456"
```

---

## Rate Limits

All endpoints are subject to rate limiting. If you exceed the rate limit, you'll receive a `429 Too Many Requests` response.

## Notes

- All timestamps are in UTC and follow ISO 8601 format
- The `scheduled_event_id` is Discord's internal ID for the event
- Events are automatically managed via the UI and event listeners; these endpoints are for manual intervention or external integrations
- Deleting a match via the API or UI will automatically delete its Discord events
