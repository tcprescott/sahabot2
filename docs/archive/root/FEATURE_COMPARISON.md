# SahasrahBot vs SahaBot2 Feature Comparison

## Executive Summary

This document analyzes the feature set of the original SahasrahBot compared to the current SahaBot2 implementation, identifying functionality that could be ported to enhance SahaBot2.

**Analysis Date**: November 5, 2025  
**Original SahasrahBot Repository**: https://github.com/tcprescott/sahasrahbot

---

## Feature Matrix

| Feature Category | SahasrahBot (Old) | SahaBot2 (Current) | Status | Priority |
|-----------------|-------------------|-------------------|--------|----------|
| **Tournament Management** |
| Live Sync Tournaments | ✅ Full SpeedGaming Integration | ⚠️ Manual Management | 🔴 Missing | High |
| Settings Submission Forms | ✅ Web Forms | ❌ No | 🔴 Missing | High |
| Auto Room Creation | ✅ Yes | ⚠️ Task Scheduler Only | 🟡 Partial | Medium |
| Seed Rolling for Races | ✅ Multiple Randomizers | ⚠️ ALTTPR Only | 🟡 Partial | Medium |
| Tournament Result Tracking | ✅ Full System | ❌ No | 🔴 Missing | High |
| Google Sheets Export | ✅ Yes | ❌ No | 🔴 Missing | Low |
| Scheduling Needs Tracking | ✅ Yes | ❌ No | 🔴 Missing | Medium |
| **Async Tournament Features** |
| Qualifier System | ✅ Yes | ✅ Yes | ✅ Complete | - |
| Par Time Calculation | ✅ Yes | ✅ Yes | ✅ Complete | - |
| Permalink Pools | ✅ Yes | ✅ Yes | ✅ Complete | - |
| Leaderboard | ✅ Yes | ✅ Yes | ✅ Complete | - |
| Re-attempt System | ✅ Yes | ✅ Yes | ✅ Complete | - |
| Whitelist System | ✅ Yes | ⚠️ Basic Permissions | 🟡 Partial | Medium |
| **Randomizer Support** |
| ALTTPR Standard | ✅ Yes | ✅ Yes | ✅ Complete | - |
| ALTTPR Mystery | ✅ Full Weightsets | ❌ No | 🔴 Missing | High |
| ALTTPR Door Randomizer | ✅ Yes | ❌ No | 🔴 Missing | Medium |
| ALTTPR Customizer | ✅ Yes | ⚠️ Limited | 🟡 Partial | Medium |
| SMZ3 | ✅ Yes | ✅ Yes | ✅ Complete | High |
| SM Randomizer (VARIA) | ✅ Yes | ❌ No | 🔴 Missing | Medium |
| SM DASH | ✅ Yes | ❌ No | 🔴 Missing | Medium |
| Z2R (Zelda 2) | ✅ Yes | ❌ No | 🔴 Missing | Low |
| CT Jets | ✅ Yes | ❌ No | 🔴 Missing | Low |
| **Multiworld Features** |
| ALTTPR Door Multiworld | ✅ Full Server | ❌ No | 🔴 Missing | Low |
| SM/SMZ3 Multiworld | ✅ Yes | ❌ No | 🔴 Missing | Low |
| Team Race Support | ✅ Yes | ❌ No | 🔴 Missing | Medium |
| **Preset/Mystery System** |
| Preset Namespaces | ✅ Yes | ✅ Yes | ✅ Complete | - |
| Custom Preset Upload | ✅ Web UI | ✅ Yes | ✅ Complete | - |
| Mystery Weightsets | ✅ 30+ Presets | ❌ No | 🔴 Missing | High |
| Subweights System | ✅ Yes | ❌ No | 🔴 Missing | Medium |
| Customizer Settings | ✅ Full Support | ⚠️ Basic | 🟡 Partial | Medium |
| **Integration Features** |
| SpeedGaming API | ✅ Full Integration | ❌ No | 🔴 Missing | High |
| Challonge Integration | ✅ Yes | ❌ No | 🔴 Missing | Low |
| Google Sheets | ✅ Yes | ❌ No | 🔴 Missing | Low |
| Discord Scheduled Events | ✅ Auto-Create | ⚠️ Manual | 🟡 Partial | Medium |
| **Daily/Weekly Features** |
| Daily Races | ✅ ALTTPR + SMZ3 | ❌ No | 🔴 Missing | Medium |
| Weekly Races | ✅ Yes | ❌ No | 🔴 Missing | Medium |
| Auto-Announcements | ✅ Yes | ❌ No | 🔴 Missing | Medium |
| **RaceTime Bot Features** |
| Auto Seed Generation | ✅ Multiple Games | ⚠️ ALTTPR Only | 🟡 Partial | Medium |
| Gatekeeping | ✅ Yes | ✅ Yes | ✅ Complete | - |
| Team Race Support | ✅ Yes | ❌ No | 🔴 Missing | Medium |
| Multiworld Commands | ✅ Yes | ❌ No | 🔴 Missing | Low |

**Legend:**
- ✅ Complete - Feature fully implemented
- ⚠️ Partial - Feature partially implemented or has limitations
- ❌ No - Feature not implemented
- 🔴 Missing - Not implemented at all
- 🟡 Partial - Partially implemented
- Priority: High/Medium/Low

---

## Detailed Feature Analysis

### 1. Live Tournament Management (SpeedGaming Integration)

#### SahasrahBot Implementation
- **Full SpeedGaming API Integration**: Fetches upcoming episodes automatically
- **Submission Forms**: Web-based forms for players to submit settings before matches
- **Auto Room Creation**: Opens race rooms at scheduled times based on SG schedule
- **Result Recording**: Tracks race results and writes them to Google Sheets
- **Scheduling Needs**: Tracks which matches need commentators/trackers
- **Discord Announcements**: Auto-announces matches in designated channels

#### SahaBot2 Current State
- **Manual Management**: Tournament admin must manually create everything
- **Task Scheduler**: Can schedule race room creation but no SG integration
- **No Submission Forms**: Settings must be configured manually

#### Recommendation
**Priority: HIGH**

This is a significant gap. The original system supported fully automated tournament workflows for events like:
- ALTTPR Weekly Tournaments
- ALTTPR League
- ALTTPR French Community
- SMZ3 Tournaments
- SM Randomizer League

**Suggested Approach**:
1. Create SpeedGaming API integration service
2. Add submission form system (similar to old web interface)
3. Implement auto-room creation based on SG schedule
4. Add result tracking and Google Sheets export (optional)
5. Create scheduling needs tracking for restreams

**Files to Reference**:
- `alttprbot/speedgaming.py` - API client
- `alttprbot/tournament/core.py` - Base tournament class
- `alttprbot_discord/cogs/tournament.py` - Tournament scanning loop
- `alttprbot_api/blueprints/tournament.py` - Submission forms

---

### 2. Mystery Weightset System

#### SahasrahBot Implementation
- **30+ Mystery Weightsets**: Pre-configured settings combinations
- **Custom Weightset Upload**: Users can upload their own YAML files
- **Subweights System**: Allows nested/conditional weights
- **Customizer Integration**: Full support for customizer options
- **Mystery Generation Workflow**:
  1. Roll preset (if specified)
  2. Pick subweight (if exists)
  3. Roll entrance shuffle
  4. If no entrance, roll customizer settings
  5. Generate seed with chosen settings

#### SahaBot2 Current State
- **No Mystery Support**: Cannot generate mystery seeds
- **Preset System**: Supports basic presets but no mystery weights

#### Recommendation
**Priority: HIGH**

Mystery races are extremely popular in the ALTTPR community. This is a major missing feature.

**Suggested Approach**:
1. Port mystery generation logic from `alttprbot/alttprgen/randomizer/mysterydoors.py`
2. Create mystery weightset storage system
3. Add web UI for uploading mystery weights
4. Implement subweights support
5. Add Discord commands for mystery generation

**Files to Reference**:
- `alttprbot/alttprgen/randomizer/mysterydoors.py` - Mystery generation
- `alttprbot/alttprgen/generator.py` - ALTTPRMystery class
- `presets/alttprmystery/` - Example weightsets
- `docs/mysteryyaml.md` - Documentation

**Use Cases**:
- Ladder Seasons (different mystery weights each season)
- PogChampionship (winner picks mystery weights)
- Tournament mystery races
- Daily mystery races

---

### 3. Multi-Randomizer Support

#### SahasrahBot Support
- **SMZ3** (Super Metroid + ALTTPR Combo Randomizer)
- **SM VARIA** (Super Metroid Randomizer)
- **SM DASH** (Super Metroid DASH Randomizer)
- **Z2R** (Zelda 2 Randomizer)
- **CT Jets** (Chrono Trigger Jets of Time)

#### SahaBot2 Current State
- **ALTTPR Only**: Only supports A Link to the Past Randomizer

#### Recommendation
**Priority: HIGH (SMZ3), MEDIUM (SM), LOW (Others)**

**SMZ3 is particularly important** because:
- Large active community
- Weekly races
- Tournament support needed
- Already have integration code in old bot

**Suggested Approach**:
1. **SMZ3 (Priority 1)**:
   - Port SMZ3Discord generator class
   - Add preset support for SMZ3
   - Implement multiworld support
   - Add RaceTime.gg handler for SMZ3 category

2. **SM Randomizers (Priority 2)**:
   - Port VARIA integration
   - Port DASH integration
   - Add preset support
   - Add RaceTime.gg handlers

3. **Others (Priority 3)**:
   - Z2R and CT Jets if community demand exists

**Files to Reference**:
- `alttprbot_discord/util/smz3_discord.py` - SMZ3 generator
- `alttprbot_discord/util/sm_discord.py` - SM generators
- `alttprbot_racetime/handlers/smz3.py` - SMZ3 RaceTime bot
- `alttprbot_racetime/handlers/smr.py` - SM RaceTime bot
- `alttprbot/tournament/smz3coop.py` - SMZ3 tournament support
- `alttprbot/tournament/smrl.py` - SM League support

---

### 4. Multiworld System

#### SahasrahBot Implementation
- **Door Randomizer Multiworld**: Full server implementation
  - Host multiworld games
  - Password protection
  - Player management (kick, forfeit)
  - Item sending between players
  - Message system
- **SM/SMZ3 Multiworld**: Team race support
  - Generate multiworld seeds for teams
  - Support for 2+ player teams
  - Seed distribution per team

#### SahaBot2 Current State
- **No Multiworld Support**: Not implemented

#### Recommendation
**Priority: LOW to MEDIUM**

While multiworld is cool, it's a complex feature with limited use cases. The Door Randomizer multiworld requires a separate server (`alttpr-multiworld`) which adds infrastructure complexity.

**Suggested Approach (if implemented)**:
1. Start with SM/SMZ3 multiworld (simpler - just seed generation)
2. Add team race support to async tournaments
3. Door multiworld requires separate server deployment (lower priority)

**Files to Reference**:
- `alttprbot_discord/cogs/smmulti.py` - SM/SMZ3 multiworld Discord UI
- `alttprbot_discord/cogs/doorsmw.py` - Door multiworld Discord commands
- `alttprbot/alttprgen/smz3multi.py` - Multiworld seed generation

---

### 5. Settings Submission Forms

#### SahasrahBot Implementation
- **Web Forms**: Players submit settings before tournament matches
- **Validation**: Ensures valid settings combinations
- **Audit Trail**: Logs who submitted what settings
- **Discord Notifications**: Sends confirmation to audit channel
- **Game Number Support**: Different settings per game in a match series

#### SahaBot2 Current State
- **No Submission Forms**: Settings must be configured manually by admins

#### Recommendation
**Priority: HIGH**

Essential for tournament automation. Without this, admins must manually configure each race.

**Suggested Approach**:
1. Create submission form models (store settings per episode)
2. Build web UI for submission forms
3. Add validation logic
4. Implement Discord notifications
5. Link to tournament race creation

**Files to Reference**:
- `alttprbot/models/tournament_games.py` - Settings storage model
- `alttprbot_api/blueprints/tournament.py` - Submission endpoints
- `alttprbot_api/templates/submission*.html` - Form templates
- `alttprbot/tournament/core.py` - `process_submission_form()` method

**Tournament Types Supported**:
- ALTTPR League (multiple preset options)
- ALTTPR FR (custom settings builder)
- ALTTPR ES (preset selection)
- SMZ3 Coop (preset selection)
- SM Randomizer League (preset + game selection)

---

### 6. Daily/Weekly Race System

#### SahasrahBot Implementation
- **Daily ALTTPR**: Automatic daily race generation
- **SMZ3 Weekly**: Weekly SMZ3 races on schedule
- **Auto-Announcements**: Announces races in Discord
- **Auto-Room Creation**: Opens race rooms at scheduled times
- **Broadcast Channel Integration**: Shows which channel streams the race

#### SahaBot2 Current State
- **No Daily System**: Must manually create races

#### Recommendation
**Priority: MEDIUM**

Daily races are popular but can be implemented gradually.

**Suggested Approach**:
1. Use existing task scheduler as base
2. Create daily race configuration system
3. Add announcement system
4. Link to RaceTime.gg room creation

**Files to Reference**:
- `alttprbot/tournament/dailies/alttprdaily.py` - ALTTPR daily
- `alttprbot/tournament/dailies/smz3.py` - SMZ3 weekly
- `alttprbot/tournament/dailies/core.py` - Base daily race class

---

### 7. Result Tracking & Export

#### SahasrahBot Implementation
- **Tournament Results Table**: Tracks all race results
- **Google Sheets Export**: Writes results to spreadsheets
- **Unrecorded Race Tracking**: Finds races missing results
- **Episode Linking**: Links results to SpeedGaming episodes
- **Seed/Settings Storage**: Stores permalink and settings used

#### SahaBot2 Current State
- **No Result Tracking**: Results not automatically tracked

#### Recommendation
**Priority: MEDIUM to LOW**

Useful for tournament admins but not critical for basic functionality.

**Suggested Approach**:
1. Add result tracking to match model
2. Implement Google Sheets API integration (optional)
3. Add result viewing UI
4. Export functionality

**Files to Reference**:
- `alttprbot/database/tournament_results.py` - Result tracking
- `alttprbot/tournaments.py` - Google Sheets export task

---

### 8. Enhanced RaceTime.gg Bot Features

#### SahasrahBot vs SahaBot2

| Feature | SahasrahBot | SahaBot2 | Notes |
|---------|-------------|----------|-------|
| Multi-game support | ✅ ALTTPR, SMZ3, SM, Z2R | ⚠️ ALTTPR only | Need more randomizers |
| Preset rolling | ✅ Yes | ✅ Yes | ✅ Complete |
| Mystery rolling | ✅ Yes | ❌ No | 🔴 Missing |
| Team race multiworld | ✅ Yes | ❌ No | 🔴 Missing |
| Tournament integration | ✅ Yes | ⚠️ Manual | 🟡 Partial |
| Gatekeeping | ✅ Yes | ✅ Yes | ✅ Complete |
| Spoiler log handling | ✅ Yes | ⚠️ Basic | 🟡 Partial |

#### Recommendation
**Priority: MEDIUM**

RaceTime.gg bot features can be added incrementally as other features are ported.

---

### 9. Discord Scheduled Events Integration

#### SahasrahBot Implementation
- **Auto-Create Events**: Automatically creates Discord scheduled events for tournament matches
- **Sync with Schedule**: Updates based on SpeedGaming schedule
- **Countdown Display**: Shows time until event
- **Broadcast Channels**: Includes restream channel info

#### SahaBot2 Current State
- **Manual Creation**: Events must be created manually
- **Model Support**: Has `DiscordScheduledEvent` model but limited automation

#### Recommendation
**Priority: MEDIUM**

Nice quality-of-life feature for tournament organization.

**Suggested Approach**:
1. Add auto-creation when tournament rooms are scheduled
2. Sync with task scheduler
3. Update event status when race starts/ends

**Files to Reference**:
- `alttprbot/discord_scheduled_event.py` - Event creation logic
- `alttprbot_discord/cogs/tournament.py` - `update_scheduled_event()` method

---

### 10. Preset Namespace Features

#### Feature Parity Check

| Feature | SahasrahBot | SahaBot2 | Status |
|---------|-------------|----------|--------|
| User namespaces | ✅ Yes | ✅ Yes | ✅ Complete |
| Preset upload | ✅ Yes | ✅ Yes | ✅ Complete |
| Preset download | ✅ Yes | ⚠️ API only | 🟡 Partial |
| Public namespace listing | ✅ Yes | ⚠️ Basic | 🟡 Partial |
| Namespace permissions | ✅ Delegated access | ⚠️ Owner only | 🟡 Partial |
| Multi-randomizer support | ✅ Yes | ✅ Yes | ✅ Complete |

#### Recommendation
**Priority: LOW**

Core functionality exists. Minor enhancements possible:
1. Add preset download UI
2. Improve namespace browsing
3. Add delegated access permissions

---

## Implementation Roadmap

### Phase 1: High Priority Tournament Features (8-10 weeks)
1. **Mystery Weightset System** (3 weeks)
   - Port mystery generation logic
   - Create storage system
   - Add web UI
   - Implement Discord commands

2. **Settings Submission Forms** (2 weeks)
   - Create form models
   - Build web UI
   - Add validation
   - Discord notifications

3. **SpeedGaming Integration** (3-4 weeks)
   - API client
   - Episode fetching
   - Auto-room creation
   - Announcement system

### Phase 2: Randomizer Expansion (6-8 weeks)
1. **SMZ3 Support** (3-4 weeks)
   - Generator integration
   - Preset system
   - RaceTime.gg handler
   - Tournament support

2. **SM Randomizers** (3-4 weeks)
   - VARIA integration
   - DASH integration
   - RaceTime.gg handlers

### Phase 3: Enhanced Features (4-6 weeks)
1. **Daily/Weekly Races** (2 weeks)
   - Configuration system
   - Auto-scheduling
   - Announcements

2. **Result Tracking** (2 weeks)
   - Result storage
   - Viewing UI
   - Export functionality

3. **Discord Scheduled Events** (1 week)
   - Auto-creation
   - Status sync

### Phase 4: Advanced Features (Optional)
1. **Multiworld Support** (4-6 weeks)
   - SM/SMZ3 multiworld seed generation
   - Team race support
   - Door multiworld (if needed)

2. **Google Sheets Integration** (1 week)
   - Export functionality
   - Auto-sync

---

## Technical Considerations

### Architecture Compatibility
- **SahasrahBot**: Flask-based web app with separate Discord bot
- **SahaBot2**: FastAPI + NiceGUI with integrated bot

**Key Differences**:
1. SahaBot2 has cleaner separation of concerns (services/repositories)
2. SahaBot2 uses async/await throughout
3. SahaBot2 has better multi-tenant support
4. SahasrahBot has more mature tournament automation

**Porting Strategy**:
- Extract business logic from old bot
- Adapt to SahaBot2's service layer pattern
- Maintain multi-tenant isolation
- Use existing event system for notifications

### Database Schema Additions Needed

1. **Tournament Games Table** (for submission forms)
   ```python
   class TournamentGame(Model):
       episode_id = CharField(unique=True)
       event = CharField()
       settings = JSONField()
       submitted = BooleanField(default=False)
       created_at = DatetimeField(auto_now_add=True)
   ```

2. **Tournament Results Table** (for result tracking)
   ```python
   class TournamentResult(Model):
       srl_id = CharField(unique=True)  # RaceTime.gg race ID
       episode_id = CharField()
       event = CharField()
       permalink = TextField()
       status = CharField()
       results_json = JSONField()
       written_to_gsheet = DatetimeField(null=True)
   ```

3. **Mystery Weightsets Table** (extends existing Presets)
   - Already have `Presets` table
   - May need additional fields for subweights support

4. **Daily Race Config Table**
   ```python
   class DailyRaceConfig(Model):
       randomizer = CharField()  # alttpr, smz3, etc.
       enabled = BooleanField(default=True)
       schedule_time = TimeField()
       preset = CharField()
       announcement_channel_id = BigIntField()
   ```

### API Integrations Needed

1. **SpeedGaming API**
   - Endpoint: `https://speedgaming.org/api`
   - Get episodes
   - Get schedule
   - Get commentators/trackers

2. **Google Sheets API** (Optional)
   - OAuth2 setup
   - Service account credentials
   - gspread-asyncio library

3. **Additional Randomizer APIs**
   - SMZ3: `https://samus.link/api`
   - SM VARIA: `https://sm.samus.link/api`
   - SM DASH: `https://dashrando.net/api`

### Dependencies to Add

```toml
# For mystery/randomizer support
pyz3r = "^7.0.0"  # ALTTPR library

# For SMZ3 support
smz3-discord = "^1.0.0"  # May need to create/adapt

# For Google Sheets (optional)
gspread-asyncio = "^1.0.0"
google-auth = "^2.0.0"

# For SpeedGaming integration
aiohttp = "^3.8.0"  # Already have

# For mystery weightsets
pyyaml = "^6.0.0"  # Already have
```

---

## Backward Compatibility

### Data Migration from SahasrahBot

If migrating from old bot:

1. **User Data**: Discord OAuth already handles this
2. **Presets**: Export from old DB, import to new namespace system
3. **Async Tournament Data**: May need to preserve history
4. **Tournament Results**: Historical data can be imported

**Migration Script Needed**: Yes, for preset namespaces and historical data

---

## Community Impact Analysis

### Most Requested Features (Based on Usage)

1. **Mystery Races** - Used in:
   - ALTTPR Ladder (weekly)
   - PogChampionship (monthly)
   - Various community tournaments
   - **Estimated Usage**: 100+ races/month

2. **Tournament Automation** - Used in:
   - ALTTPR Weekly Tournaments
   - ALTTPR League
   - French/Spanish/German Communities
   - **Estimated Usage**: 20-30 tournaments/year

3. **SMZ3 Support** - Used in:
   - Weekly SMZ3 races
   - SMZ3 tournaments
   - Community events
   - **Estimated Usage**: 50+ races/month

4. **Daily Races** - Used in:
   - ALTTPR Daily Challenge
   - SMZ3 Weekly races
   - **Estimated Usage**: 365+ races/year

### Features with Lower Demand

1. **Multiworld** - Niche use case
2. **Z2R/CT Jets** - Small communities
3. **Google Sheets Export** - Admin convenience, not player-facing

---

## Conclusion

### Critical Missing Features (Implement First)
1. ✅ **Mystery Weightset System** - High community demand
2. ✅ **Settings Submission Forms** - Essential for tournaments
3. ✅ **SpeedGaming Integration** - Core tournament automation

### Important Missing Features (Implement Second)
4. ✅ **SMZ3 Support** - Large active community
5. ✅ **SM Randomizer Support** - Established tournaments
6. ✅ **Daily/Weekly Race System** - Regular community events

### Nice-to-Have Features (Implement Later)
7. ⚠️ **Result Tracking & Export** - Admin convenience
8. ⚠️ **Enhanced Discord Events** - Quality of life
9. ⚠️ **Multiworld Support** - Niche but cool

### Low Priority Features
10. ❌ **Z2R/CT Jets Support** - Small communities
11. ❌ **Google Sheets Integration** - Optional admin tool

---

## Next Steps

1. **Prioritize features based on community needs**
2. **Create detailed implementation specs for Phase 1 features**
3. **Set up development timeline**
4. **Allocate resources for porting efforts**
5. **Establish testing strategy for ported features**
6. **Plan incremental rollout to minimize disruption**

---

**Document Version**: 1.0  
**Last Updated**: November 5, 2025  
**Author**: AI Analysis based on repository comparison
