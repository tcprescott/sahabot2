# Async Qualifier End-User Features

This document describes the end-user functionality implemented for async qualifiers in SahaBot2.

## Overview

Async tournaments allow players to complete races asynchronously at their own pace. Players race permalinks from various pools, and scores are calculated based on finish time relative to a par time (average of top 5 finishers on each permalink).

## Features Implemented

### 1. Dashboard View (`views/tournaments/async_dashboard.py`)

The dashboard is the main view for players to see their tournament progress and race history.

**Features:**
- **Tournament Header**
  - Tournament name, description, and status (Active/Closed)
  - Direct link to Discord channel for starting new races
  
- **Player Statistics Card**
  - Completed races count
  - Forfeited races count
  - Active races count (pending/in progress)
  - Total score across all races
  - Personal best time with pool indication
  - Reattempt status indicator

- **Pool Progress Card**
  - Visual progress bars for each pool
  - Shows completed vs. total runs required per pool
  - Indicates remaining runs needed

- **My Races Table**
  - Filtering by status (All, Finished, In Progress, Pending, Forfeit)
  - Sorting options (Newest First, Oldest First, Best Score, Worst Score)
  - Desktop: Full data table with all race details
  - Mobile: Responsive card layout optimized for small screens
  - Each race shows:
    - Date/time
    - Pool name
    - Status badge
    - Elapsed time
    - Score
    - Links to seed, VOD, and Discord thread

### 2. Leaderboard View (`views/tournaments/async_leaderboard.py`)

Shows tournament standings with player rankings.

**Features:**
- **Header with Stats**
  - Total participant count
  - Runs per pool configuration
  
- **Filtering Options**
  - Search by player name
  - Filter by minimum completed races
  
- **Desktop Leaderboard Table**
  - Rank with medal emojis (🥇🥈🥉) for top 3
  - Player name (highlights current user)
  - Total score
  - Completed/Forfeit/Remaining race counts
  - Link to view player's detailed race history

- **Mobile Leaderboard Cards**
  - Compact card format for each player
  - Prominent score display
  - Stats grid (Completed/Forfeit/Remaining)
  - Button to view race history

### 3. Player History View (`views/tournaments/async_player_history.py`)

Shows detailed race history for a specific player in the tournament.

**Features:**
- Player's complete race history
- All race details (date, pool, status, time, score, VOD, thread links)
- Reattempt indicator
- Links to seed and Discord thread for each race

### 4. Pools View (`views/tournaments/async_pools.py`)

Lists all tournament pools (likely already implemented).

### 5. Permalink View (`views/tournaments/async_permalink.py`)

Shows details about a specific permalink and all races completed on it (likely already implemented).

## User Workflows

### Starting a New Race

1. User navigates to tournament dashboard
2. Clicks "Go to Discord Channel" button
3. In Discord, clicks "Start New Async Run" button
4. Bot shows available pools
5. User selects pool and confirms
6. Bot creates private thread with seed link
7. User clicks "Ready" to start countdown
8. Bot counts down and starts timer
9. User completes race
10. User clicks "Finish" or "Forfeit"
11. If finished, user submits VOD and notes via Discord modal

### Viewing Progress

1. User navigates to tournament dashboard
2. Views personal stats (completed, forfeited, active, total score)
3. Checks pool progress to see which pools still need runs
4. Filters race history by status or sorts by various criteria
5. Clicks on seed/VOD/thread links as needed

### Checking Standings

1. User navigates to leaderboard view
2. Searches for specific players if desired
3. Filters by minimum completed races
4. Views own ranking (highlighted row/card)
5. Clicks "View History" to see detailed race history for any player

### Viewing Race Details

1. From leaderboard, clicks "View History" for a player
2. Sees complete race history for that player
3. Can view seeds, VODs, and thread links
4. Can see reattempt status for each race

## Technical Implementation

### Architecture

- **Views Layer**: NiceGUI components for presentation
  - `AsyncDashboardView`: Player dashboard
  - `AsyncLeaderboardView`: Tournament standings
  - `AsyncPlayerHistoryView`: Player race history
  
- **Services Layer**: Business logic (already implemented)
  - `AsyncTournamentService`: Handles all tournament operations
  - Methods: `get_user_races()`, `get_leaderboard()`, etc.

- **Discord Bot Layer**: Race initiation and management
  - `discordbot/async_qualifier_views.py`: Discord UI components
  - `discordbot/commands/async_qualifier.py`: Admin commands
  - Persistent views for buttons in Discord channels
  - Modal forms for VOD submission

### Mobile Responsiveness

All views are designed mobile-first with responsive layouts:
- Desktop: Full data tables with all columns
- Mobile: Card-based layouts with essential information
- CSS utility classes for `hidden md:block` and `block md:hidden`
- Flexbox and grid layouts that adapt to screen size

### CSS Additions

Added to `static/css/main.css`:
- `.pool-progress-card`: Pool progress container styling
- `.progress-bar-container`: Progress bar wrapper
- `.progress-bar`: Animated gradient progress indicator
- `.filter-select`: Filter dropdown styling
- Text color utilities: `.text-danger`, `.text-info`, `.text-success`, `.text-warning`
- `.icon-large`: Large icon sizing
- Grid utilities: `.grid`, `.grid-cols-*`, `.md:grid-cols-*`
- Responsive utilities: `.hidden`, `.md:hidden`, `.block`, `.md:block`

## Discord Bot Integration

The Discord bot provides the primary interface for starting and managing races:

### Persistent Views (Always Active)

1. **AsyncTournamentMainView**
   - "Start New Async Run" button
   - Shown in tournament Discord channels
   - Checks user membership and eligibility
   - Shows pool selection modal

2. **RaceReadyView**
   - "Ready (start countdown)" button
   - Shown in race thread after creation
   - Starts 10-second countdown

3. **RaceInProgressView**
   - "Finish" and "Forfeit" buttons
   - Shown after race starts
   - Records completion time

4. **RacePostView**
   - "Submit Run Information" button
   - Shown after race finishes
   - Opens modal for VOD URL and notes

### Admin Commands

- Background tasks for race timeout management
- Score calculation tasks

### Admin UI Actions

- **Post Embed to Discord**: Admins can post the tournament embed with action buttons directly from the web interface
  - Available in Organization Admin > Async Qualifiers
  - "Post Embed" button appears for tournaments with a configured Discord channel
  - Posts an embed with tournament info and the "Start New Async Run" button
  - Previously required using the `/async_post_embed` Discord command

## Future Enhancements (Not Yet Implemented)

These features from the original SahasrahBot could be added:

1. **VOD Submission via Web**
   - Dialog for submitting VOD and notes from web UI
   - Currently only available via Discord

2. **Reattempt Functionality via Web**
   - Allow users to request reattempts from web
   - Currently only available via Discord admin

3. **Race Review Queue (Admin)**
   - Queue for reviewing completed races
   - Approve/reject races
   - Add reviewer notes

4. **Advanced Filtering**
   - Filter leaderboard by pool
   - Show per-pool leaderboards
   - Filter by date range

5. **Statistics and Analytics**
   - Average finish times per pool
   - Personal improvement graphs
   - Head-to-head comparisons

6. **Export Functionality**
   - Export leaderboard to CSV
   - Export race history
   - Generate tournament report

## Testing Checklist

- [ ] Dashboard displays correctly on desktop
- [ ] Dashboard displays correctly on mobile
- [ ] Pool progress bars show accurate completion
- [ ] Personal stats calculate correctly
- [ ] Race filtering works (status, sorting)
- [ ] Leaderboard displays correctly on desktop
- [ ] Leaderboard displays correctly on mobile
- [ ] Leaderboard filtering works (search, min races)
- [ ] Current user is highlighted in leaderboard
- [ ] Player history view shows all races
- [ ] Links to seeds, VODs, threads work correctly
- [ ] Discord bot integration works (start race)
- [ ] Race countdown and timing works
- [ ] VOD submission via Discord works
- [ ] Score calculation updates correctly
- [ ] Reattempt indicator shows correctly

## Related Documentation

- [ASYNC_TOURNAMENT_PERMISSIONS_ANALYSIS.md](ASYNC_TOURNAMENT_PERMISSIONS_ANALYSIS.md) - Permission system details
- [DISCORD_CHANNEL_PERMISSIONS.md](DISCORD_CHANNEL_PERMISSIONS.md) - Discord integration details
- [BASEPAGE_GUIDE.md](BASEPAGE_GUIDE.md) - Page structure and patterns
- Original SahasrahBot: https://github.com/tcprescott/sahasrahbot

## Summary

The async qualifier end-user functionality provides a comprehensive web interface for players to:
- View their tournament progress and statistics
- Track races across multiple pools
- View leaderboards and standings
- Explore race history for themselves and others
- Access seeds, VODs, and Discord threads

The implementation follows SahaBot2 architecture principles with proper separation of concerns, mobile-first responsive design, and integration with the Discord bot for race management.
