# Async Live Races - API Documentation

This document describes the REST API endpoints for managing live races in asynchronous tournaments.

## Table of Contents
1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Endpoints](#endpoints)
4. [Schemas](#schemas)
5. [Error Handling](#error-handling)
6. [Examples](#examples)

---

## Overview

The Live Races API provides programmatic access to schedule, manage, and monitor live racing events for asynchronous tournaments.

### Base URL
```
/api/v1/tournaments/{tournament_id}/live-races
```

### API Features
- List all live races for a tournament
- Get individual live race details
- Create new live races
- Open race rooms (admin)
- Update race status
- Cancel races
- Delete races
- Get eligible participants
- Track race lifecycle events

---

## Authentication

All endpoints require authentication via session cookies (Discord OAuth2).

### Required Permissions
- **List/View**: No special permissions (tournament participants can view)
- **Create**: Organization ADMIN or MODERATOR permission
- **Update/Cancel/Delete**: Organization ADMIN or MODERATOR permission
- **Open Room**: Organization ADMIN or MODERATOR permission

### Rate Limiting
- **General**: 100 requests per minute per user
- **Create/Update/Delete**: 10 requests per minute per user

---

## Endpoints

### 1. List Live Races

Get all live races for a tournament with optional filtering.

**Endpoint:**
```http
GET /api/v1/tournaments/{tournament_id}/live-races
```

**Query Parameters:**
- `status` (optional): Filter by status (`scheduled`, `room_open`, `in_progress`, `completed`, `cancelled`)
- `pool_id` (optional): Filter by pool ID
- `include_cancelled` (optional, boolean): Include cancelled races (default: false)

**Response:**
```json
{
  "items": [
    {
      "id": 123,
      "tournament_id": 1,
      "pool_id": 5,
      "pool_name": "Beginners",
      "scheduled_time": "2024-01-15T20:00:00Z",
      "status": "scheduled",
      "racetime_url": null,
      "created_at": "2024-01-10T12:00:00Z"
    }
  ],
  "count": 1
}
```

**Status Codes:**
- `200 OK`: Success
- `403 Forbidden`: Not authorized to view tournament
- `404 Not Found`: Tournament not found

---

### 2. Get Live Race Details

Get detailed information about a specific live race.

**Endpoint:**
```http
GET /api/v1/tournaments/{tournament_id}/live-races/{race_id}
```

**Response:**
```json
{
  "id": 123,
  "tournament_id": 1,
  "pool_id": 5,
  "pool_name": "Beginners",
  "scheduled_time": "2024-01-15T20:00:00Z",
  "status": "scheduled",
  "racetime_url": null,
  "room_opened_at": null,
  "race_started_at": null,
  "race_finished_at": null,
  "cancelled_at": null,
  "cancellation_reason": null,
  "race_room_config": {
    "goal": "Beat the game",
    "info": "Standard ruleset",
    "start_delay": 15,
    "time_limit": 10800,
    "streaming_required": true,
    "allow_comments": true,
    "allow_prerace_chat": true,
    "allow_midrace_chat": false,
    "allow_non_entrant_chat": true,
    "auto_start": false,
    "invitational": false,
    "team_race": false
  },
  "created_at": "2024-01-10T12:00:00Z",
  "updated_at": "2024-01-10T12:00:00Z"
}
```

**Status Codes:**
- `200 OK`: Success
- `403 Forbidden`: Not authorized to view tournament
- `404 Not Found`: Tournament or race not found

---

### 3. Create Live Race

Schedule a new live race for a tournament pool.

**Endpoint:**
```http
POST /api/v1/tournaments/{tournament_id}/live-races
```

**Request Body:**
```json
{
  "pool_id": 5,
  "scheduled_time": "2024-01-15T20:00:00Z",
  "race_room_config": {
    "goal": "Beat the game",
    "info": "Standard ruleset - Seed: https://example.com/seed/123",
    "start_delay": 15,
    "time_limit": 10800,
    "streaming_required": true,
    "allow_comments": true,
    "allow_prerace_chat": true,
    "allow_midrace_chat": false,
    "allow_non_entrant_chat": true,
    "auto_start": false,
    "invitational": false,
    "team_race": false
  }
}
```

**Response:**
```json
{
  "id": 123,
  "tournament_id": 1,
  "pool_id": 5,
  "pool_name": "Beginners",
  "scheduled_time": "2024-01-15T20:00:00Z",
  "status": "scheduled",
  "created_at": "2024-01-10T12:00:00Z"
}
```

**Status Codes:**
- `201 Created`: Live race created successfully
- `400 Bad Request`: Invalid request data
- `403 Forbidden`: Not authorized to create races
- `404 Not Found`: Tournament or pool not found

**Validation Rules:**
- `scheduled_time` must be in the future
- `pool_id` must exist and belong to tournament
- `start_delay` must be 15, 30, 45, 60, or 90 seconds
- `time_limit` must be between 900 (15min) and 86400 (24h) seconds

---

### 4. Get Eligible Participants

Get list of participants eligible for a specific live race.

**Endpoint:**
```http
GET /api/v1/tournaments/{tournament_id}/live-races/{race_id}/eligible
```

**Response:**
```json
{
  "items": [
    {
      "user": {
        "id": 1,
        "discord_username": "Player1",
        "discord_discriminator": "1234",
        "discord_id": "123456789"
      },
      "is_eligible": true,
      "reason": null
    },
    {
      "user": {
        "id": 2,
        "discord_username": "Player2",
        "discord_discriminator": "5678",
        "discord_id": "987654321"
      },
      "is_eligible": false,
      "reason": "Not in pool"
    }
  ],
  "count": 2,
  "eligible_count": 1
}
```

**Status Codes:**
- `200 OK`: Success
- `403 Forbidden`: Not authorized to view tournament
- `404 Not Found`: Tournament or race not found

---

### 5. Open Race Room (Admin Only)

Manually open a RaceTime.gg race room for a scheduled race.

**Endpoint:**
```http
POST /api/v1/tournaments/{tournament_id}/live-races/{race_id}/open
```

**Request Body:**
```json
{}
```

**Response:**
```json
{
  "id": 123,
  "status": "room_open",
  "racetime_url": "https://racetime.gg/alttpr/amazing-rando-1234",
  "room_opened_at": "2024-01-15T19:45:00Z"
}
```

**Status Codes:**
- `200 OK`: Room opened successfully
- `400 Bad Request`: Race already opened or invalid state
- `403 Forbidden`: Not authorized
- `404 Not Found`: Tournament or race not found
- `500 Internal Server Error`: RaceTime.gg API error

**Notes:**
- Race room automatically opens 15 minutes before scheduled time
- Manual opening only needed if automatic opening fails
- Can only open races in "scheduled" status

---

### 6. Update Race Status

Update the status of a live race (typically called by automated tasks).

**Endpoint:**
```http
PATCH /api/v1/tournaments/{tournament_id}/live-races/{race_id}
```

**Request Body:**
```json
{
  "status": "in_progress",
  "racetime_data": {
    "participant_count": 5,
    "status": "in_progress",
    "started_at": "2024-01-15T20:00:00Z"
  }
}
```

**Response:**
```json
{
  "id": 123,
  "status": "in_progress",
  "race_started_at": "2024-01-15T20:00:00Z",
  "updated_at": "2024-01-15T20:00:05Z"
}
```

**Status Codes:**
- `200 OK`: Status updated successfully
- `400 Bad Request`: Invalid status transition
- `403 Forbidden`: Not authorized
- `404 Not Found`: Tournament or race not found

**Valid Status Transitions:**
- `scheduled` → `room_open`
- `room_open` → `in_progress`
- `in_progress` → `completed`
- Any status → `cancelled`

---

### 7. Cancel Live Race

Cancel a scheduled or in-progress live race.

**Endpoint:**
```http
POST /api/v1/tournaments/{tournament_id}/live-races/{race_id}/cancel
```

**Request Body:**
```json
{
  "reason": "Not enough participants registered"
}
```

**Response:**
```json
{
  "id": 123,
  "status": "cancelled",
  "cancelled_at": "2024-01-15T18:00:00Z",
  "cancellation_reason": "Not enough participants registered"
}
```

**Status Codes:**
- `200 OK`: Race cancelled successfully
- `400 Bad Request`: Race already cancelled or completed
- `403 Forbidden`: Not authorized
- `404 Not Found`: Tournament or race not found

**Notes:**
- Participants receive cancellation notifications
- Race is preserved for historical purposes
- Cannot cancel completed races

---

### 8. Delete Live Race

Permanently delete a live race.

**Endpoint:**
```http
DELETE /api/v1/tournaments/{tournament_id}/live-races/{race_id}
```

**Response:**
```json
{
  "message": "Live race deleted successfully"
}
```

**Status Codes:**
- `200 OK`: Race deleted successfully
- `403 Forbidden`: Not authorized
- `404 Not Found`: Tournament or race not found

**Warning:**
- Deletion is permanent and cannot be undone
- Use cancellation instead to preserve race history
- Only delete test races or mistakes

---

## Schemas

### LiveRaceStatus Enum
```python
class LiveRaceStatus(str, Enum):
    SCHEDULED = "scheduled"        # Race created, room not open
    ROOM_OPEN = "room_open"        # RaceTime.gg room open
    IN_PROGRESS = "in_progress"    # Race started
    COMPLETED = "completed"        # Race finished
    CANCELLED = "cancelled"        # Race cancelled
```

### RaceRoomConfig Schema
```json
{
  "goal": "string (required)",              // Race goal description
  "info": "string (optional)",              // Additional race info
  "start_delay": "integer (15-90)",         // Countdown in seconds
  "time_limit": "integer (900-86400)",      // Max duration in seconds
  "streaming_required": "boolean",          // Require streaming
  "allow_comments": "boolean",              // Enable chat
  "allow_prerace_chat": "boolean",          // Chat before start
  "allow_midrace_chat": "boolean",          // Chat during race
  "allow_non_entrant_chat": "boolean",      // Spectator chat
  "auto_start": "boolean",                  // Auto-start when ready
  "invitational": "boolean",                // Require invitation
  "team_race": "boolean"                    // Team racing mode
}
```

### LiveRace Schema
```json
{
  "id": "integer",
  "tournament_id": "integer",
  "pool_id": "integer",
  "pool_name": "string",
  "scheduled_time": "datetime (ISO 8601)",
  "status": "LiveRaceStatus",
  "racetime_url": "string (nullable)",
  "room_opened_at": "datetime (nullable)",
  "race_started_at": "datetime (nullable)",
  "race_finished_at": "datetime (nullable)",
  "cancelled_at": "datetime (nullable)",
  "cancellation_reason": "string (nullable)",
  "race_room_config": "RaceRoomConfig",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### LiveRaceEligibility Schema
```json
{
  "user": {
    "id": "integer",
    "discord_username": "string",
    "discord_discriminator": "string",
    "discord_id": "string"
  },
  "is_eligible": "boolean",
  "reason": "string (nullable)"    // Reason if not eligible
}
```

---

## Error Handling

### Error Response Format
```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Error Codes

**400 Bad Request**
- Invalid request parameters
- Invalid date/time format
- Invalid status transition
- Missing required fields
- Validation errors

**403 Forbidden**
- Insufficient permissions
- Not authorized for organization
- Not authorized for tournament

**404 Not Found**
- Tournament not found
- Race not found
- Pool not found

**409 Conflict**
- Race already exists for time slot
- Cannot cancel completed race
- Invalid state transition

**500 Internal Server Error**
- RaceTime.gg API error
- Database error
- Unexpected server error

---

## Examples

### Example 1: Create a Weekly Race Series

Create 4 races for every Saturday at 8 PM UTC:

```python
import requests
from datetime import datetime, timedelta

BASE_URL = "https://sahabot.example.com/api/v1"
tournament_id = 1
pool_id = 5

# Standard race configuration
race_config = {
    "race_room_config": {
        "goal": "Beat the game",
        "info": "Weekly race - Standard ruleset",
        "start_delay": 15,
        "time_limit": 10800,
        "streaming_required": False,
        "allow_comments": True,
        "allow_prerace_chat": True,
        "allow_midrace_chat": False,
        "allow_non_entrant_chat": True,
        "auto_start": False,
        "invitational": False,
        "team_race": False
    }
}

# Create races for next 4 Saturdays
start_date = datetime(2024, 1, 13, 20, 0, 0)  # First Saturday at 8 PM UTC
for week in range(4):
    scheduled_time = start_date + timedelta(weeks=week)
    
    response = requests.post(
        f"{BASE_URL}/tournaments/{tournament_id}/live-races",
        json={
            "pool_id": pool_id,
            "scheduled_time": scheduled_time.isoformat() + "Z",
            **race_config
        }
    )
    
    if response.status_code == 201:
        race = response.json()
        print(f"Created race {race['id']} for {scheduled_time}")
    else:
        print(f"Error: {response.json()}")
```

### Example 2: Monitor Race Progress

Poll race status until completion:

```python
import time

race_id = 123

while True:
    response = requests.get(
        f"{BASE_URL}/tournaments/{tournament_id}/live-races/{race_id}"
    )
    
    if response.status_code == 200:
        race = response.json()
        print(f"Race {race_id} status: {race['status']}")
        
        if race['status'] in ['completed', 'cancelled']:
            print(f"Race finished: {race}")
            break
    
    time.sleep(30)  # Check every 30 seconds
```

### Example 3: Get Participants Before Creating Race

Check eligible participants before scheduling:

```python
# Create the race first
response = requests.post(
    f"{BASE_URL}/tournaments/{tournament_id}/live-races",
    json={
        "pool_id": pool_id,
        "scheduled_time": "2024-01-15T20:00:00Z",
        "race_room_config": {...}
    }
)

race = response.json()
race_id = race['id']

# Get eligible participants
response = requests.get(
    f"{BASE_URL}/tournaments/{tournament_id}/live-races/{race_id}/eligible"
)

eligibility = response.json()
print(f"Eligible participants: {eligibility['eligible_count']}/{eligibility['count']}")

# Cancel if not enough participants
if eligibility['eligible_count'] < 3:
    requests.post(
        f"{BASE_URL}/tournaments/{tournament_id}/live-races/{race_id}/cancel",
        json={"reason": "Not enough eligible participants"}
    )
```

### Example 4: Filter Races by Status

Get all in-progress races:

```python
response = requests.get(
    f"{BASE_URL}/tournaments/{tournament_id}/live-races",
    params={"status": "in_progress"}
)

races = response.json()
print(f"Found {races['count']} in-progress races")

for race in races['items']:
    print(f"Race {race['id']}: {race['racetime_url']}")
```

---

## Best Practices

### API Usage Guidelines

1. **Rate Limiting**: Respect rate limits (100 req/min general, 10 req/min for mutations)
2. **Polling**: When polling race status, use 30-60 second intervals
3. **Error Handling**: Always check response status codes and handle errors gracefully
4. **Timezone Awareness**: All timestamps are UTC - convert to local timezone for display
5. **Validation**: Validate input before sending to API
6. **Idempotency**: Use unique identifiers to prevent duplicate race creation

### Security Best Practices

1. **Authentication**: Always include session cookies
2. **HTTPS**: Use HTTPS for all API requests
3. **Credentials**: Never log or expose authentication tokens
4. **Input Validation**: Validate and sanitize all user input
5. **Authorization**: Check permissions before allowing actions

### Performance Optimization

1. **Batch Operations**: Create multiple races in separate requests (no batch endpoint yet)
2. **Caching**: Cache tournament/pool data to reduce API calls
3. **Pagination**: Use pagination for large result sets (if implemented)
4. **Selective Fetching**: Only request data you need

---

## Support

For API support or to report issues:
- Contact system administrators
- Submit issues via feedback form
- Check [Architecture Documentation](ASYNC_LIVE_RACES_MIGRATION_PLAN.md) for technical details
