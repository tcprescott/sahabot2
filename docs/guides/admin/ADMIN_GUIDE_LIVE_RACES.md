# Async Live Races - Admin Guide

This guide explains how to manage live races for asynchronous tournaments.

## Table of Contents
1. [Overview](#overview)
2. [Creating Live Races](#creating-live-races)
3. [Managing Live Races](#managing-live-races)
4. [Race Room Configuration](#race-room-configuration)
5. [Monitoring & Troubleshooting](#monitoring--troubleshooting)
6. [Best Practices](#best-practices)

---

## Overview

Live races allow tournament participants to compete in real-time on RaceTime.gg. As an admin, you can schedule races, configure race rooms, monitor progress, and manage race lifecycles.

### Key Admin Capabilities
- Schedule live races for specific pools and times
- Configure race room settings (goal, info, start delay, etc.)
- View eligible participants before creating races
- Monitor race status in real-time
- Cancel or delete races as needed
- Track notification delivery to participants

---

## Creating Live Races

### Prerequisites
1. Tournament must have at least one pool with participants
2. RaceTime.gg bot must be configured for your organization
3. Participants should have RaceTime.gg accounts linked

### Step-by-Step: Creating a Race

#### 1. Navigate to Live Races
- Open your tournament admin page
- Click the **"Live Races"** tab
- Click **"Create Live Race"** button

#### 2. Configure Race Settings

**Basic Settings:**
- **Pool**: Select which pool to race (required)
- **Scheduled Time**: Choose date and time for race start (required)
  - Times are displayed and stored in UTC
  - Consider participant timezones when scheduling
  - Recommend scheduling at least 24 hours in advance

**Race Room Configuration:**
- **Goal**: Race goal description (e.g., "Beat the game - Ganon")
- **Info**: Additional race information or rules
- **Start Delay**: Countdown before race starts (15, 30, 45, 60, or 90 seconds)
- **Time Limit**: Maximum race duration (15m to 24h)
- **Streaming Required**: Whether participants must stream
- **Allow Comments**: Allow race room chat
- **Allow Prerace Chat**: Allow chat before race starts
- **Allow Midrace Chat**: Allow chat during race
- **Allow Non-Entrant Chat**: Allow non-participants to chat
- **Auto Start**: Automatically start when all ready
- **Invitational**: Require invitation to join
- **Team Race**: Enable team racing mode

#### 3. Review Eligible Participants
- Click **"View Eligible"** to see who can participate
- Verify participant count matches expectations
- Eligibility is determined by:
  - Active participation in tournament
  - Pool membership
  - Tournament-specific rules

#### 4. Create Race
- Click **"Create Race"**
- Race is scheduled and notifications sent
- Race appears in Live Races table

### Scheduling Tips
- **Lead Time**: Schedule at least 24-48 hours in advance
- **Timezones**: Consider participant timezones (use a timezone converter)
- **Frequency**: Don't over-schedule; give participants time to prepare
- **Pool Size**: Ensure enough participants for meaningful races
- **Communication**: Announce races in Discord/other channels

---

## Managing Live Races

### Viewing Live Races

The **Live Races** table shows all races with:
- **ID**: Unique race identifier
- **Pool**: Which pool the race is for
- **Status**: Current race state
- **Scheduled Time**: When race starts (local timezone)
- **RaceTime.gg URL**: Link to race room (when open)
- **Actions**: Manage race (view, cancel, delete)

### Race Status Flow

```
Scheduled → Room Open → In Progress → Completed
     ↓
  Cancelled
```

**Status Definitions:**
- **Scheduled**: Race created, room not yet opened
- **Room Open**: RaceTime.gg room created and accepting participants (15 min before start)
- **In Progress**: Race has started on RaceTime.gg
- **Completed**: Race finished, all results recorded
- **Cancelled**: Race cancelled by admin

### Filtering Races
Use the status filter dropdown to view:
- All races
- Scheduled races only
- In-progress races only
- Completed races only
- Cancelled races only

### Cancelling a Race

**When to Cancel:**
- Not enough participants
- Schedule conflict
- Technical issues
- Tournament changes

**How to Cancel:**
1. Find race in Live Races table
2. Click **"Cancel"** button
3. Provide cancellation reason
4. Confirm cancellation

**What Happens:**
- Race status changes to "Cancelled"
- Participants receive cancellation notification
- Race room (if open) remains accessible but race won't start
- Race is preserved for historical purposes

### Deleting a Race

**When to Delete:**
- Race was created by mistake
- Duplicate race entries
- Test races

**How to Delete:**
1. Find race in Live Races table
2. Click **"Delete"** button
3. Confirm deletion

**Warning:**
- Deletion is permanent
- Use cancellation instead if you want to preserve race history

---

## Race Room Configuration

### Understanding Race Room Settings

#### Goal
- **Purpose**: Describes what racers need to accomplish
- **Example**: "Beat the game - Ganon", "Complete all dungeons"
- **Best Practice**: Be clear and specific

#### Info
- **Purpose**: Additional race details, rules, or instructions
- **Example**: "No Major Glitches, use provided seed"
- **Best Practice**: Include seed/permalink info, special rules

#### Start Delay
- **Options**: 15s, 30s, 45s, 60s, 90s
- **Purpose**: Countdown timer before race starts
- **Recommendation**: 15s for experienced racers, 30-60s for new racers

#### Time Limit
- **Range**: 15 minutes to 24 hours
- **Purpose**: Maximum time before race auto-finishes
- **Recommendation**: 
  - Standard races: 3-4 hours
  - Long races: 6-8 hours
  - Practice/fun races: 2 hours

#### Streaming Required
- **When to use**: Official tournament races, seeded/high-stakes events
- **Considerations**: Ensures accountability, allows spectators
- **Alternative**: Allow but don't require for casual races

#### Chat Settings
- **Allow Comments**: Enable/disable all chat
- **Allow Prerace Chat**: Chat before race starts
- **Allow Midrace Chat**: Chat during race (consider competitive fairness)
- **Allow Non-Entrant Chat**: Spectator chat
- **Recommendation**: Enable prerace and non-entrant for community engagement

#### Auto Start
- **When to use**: Smaller races where all participants expected
- **Considerations**: Race starts when all mark ready (no manual start needed)
- **Alternative**: Manual start for flexibility

#### Invitational
- **When to use**: Limited participation events, specific matchups
- **Considerations**: Requires manual invitations
- **Alternative**: Open races for general participation

#### Team Race
- **When to use**: Team-based tournaments
- **Considerations**: Requires team assignments
- **Note**: Most async qualifiers use individual races

### Race Room Profiles

For consistent settings across multiple races, create a **Race Room Profile**:
1. Go to **Tournament Settings > Race Room Profiles**
2. Create profile with standard settings
3. Reuse profile when creating races

---

## Monitoring & Troubleshooting

### Real-Time Monitoring

#### Race Status Dashboard
- View all races in Live Races table
- Filter by status to see active races
- Click RaceTime.gg URL to view live race room
- Status updates automatically from RaceTime.gg

#### Notification Tracking
- Check notification logs for delivery status
- View failed deliveries (participants with DMs disabled)
- Resend notifications if needed

### Common Issues & Solutions

#### Issue: Race room didn't open automatically
**Causes:**
- Task scheduler not running
- RaceTime.gg bot credentials expired
- Network connectivity issues

**Solutions:**
1. Check system status in admin panel
2. Verify RaceTime.gg bot configuration
3. Manually open room via "Open Room" button
4. Contact system administrator if issue persists

#### Issue: Participants didn't receive notifications
**Causes:**
- User has DMs disabled
- User hasn't subscribed to notifications
- Discord bot offline

**Solutions:**
1. Check notification delivery logs
2. Ask participants to enable DMs from server members
3. Ask participants to check notification settings
4. Post race info in Discord channel as backup

#### Issue: Wrong participants eligible for race
**Causes:**
- Incorrect pool configuration
- Participant status not updated
- Pool assignments missing

**Solutions:**
1. Review pool configuration in tournament settings
2. Verify participant pool assignments
3. Update participant status if needed
4. Recreate race with correct pool

#### Issue: Race won't start on RaceTime.gg
**Causes:**
- Not enough participants joined room
- Auto-start enabled but not all ready
- RaceTime.gg server issues

**Solutions:**
1. Verify participants joined room
2. Disable auto-start and manually start race
3. Check RaceTime.gg status page
4. Cancel and reschedule if necessary

---

## Best Practices

### Scheduling
✅ **Do:**
- Schedule at least 24-48 hours in advance
- Consider participant timezones
- Communicate schedule via multiple channels
- Create recurring weekly races for consistency
- Build in buffer time before/after races

❌ **Don't:**
- Over-schedule (fatigue participants)
- Schedule during major holidays or events
- Change times last-minute
- Schedule conflicting races for same pool

### Communication
✅ **Do:**
- Announce new races in Discord
- Send reminders 24h and 1h before race
- Provide seed/permalink in race info
- Clearly state rules and requirements
- Respond to participant questions promptly

❌ **Don't:**
- Rely solely on notifications
- Assume everyone checks their DMs
- Change rules during active race
- Leave participants without updates

### Race Configuration
✅ **Do:**
- Use consistent race room settings
- Create reusable race room profiles
- Test settings with practice races
- Set appropriate time limits
- Require streaming for important races

❌ **Don't:**
- Use confusing goal descriptions
- Set unrealistic time limits
- Enable invitational for open tournaments
- Forget to include seed/permalink in info

### Monitoring
✅ **Do:**
- Check in on races as they happen
- Monitor notification delivery logs
- Track participant engagement
- Review race completion rates
- Gather feedback from participants

❌ **Don't:**
- Ignore failed notification deliveries
- Leave cancelled races unexplained
- Overlook patterns of no-shows
- Skip post-race feedback collection

### Emergency Procedures
✅ **Do:**
- Have backup plan for RaceTime.gg outages
- Communicate quickly if cancellation needed
- Reschedule promptly if possible
- Document issues for future prevention

❌ **Don't:**
- Cancel without explanation
- Ignore participant technical issues
- Panic - most issues have solutions
- Delete races unless absolutely necessary

---

## Advanced Features

### Batch Race Creation
For recurring weekly races, consider:
1. Create template race with standard settings
2. Schedule multiple weeks at once
3. Use consistent time slots

### Integration with Tournament Phases
- Schedule live races during specific tournament phases
- Use pools to organize phase participants
- Track progression through completed races

### Custom Race Formats
- Seed races (specific seed/permalink)
- Mystery races (unknown seed until start)
- Beat-the-streamer races (race against recording)
- Team relay races (custom coordination)

---

## Support & Resources

### Getting Help
- **Technical Issues**: Contact system administrators
- **RaceTime.gg Issues**: Check [racetime.gg/support](https://racetime.gg)
- **Feature Requests**: Submit via admin feedback form

### Additional Resources
- [User Guide](USER_GUIDE_LIVE_RACES.md) - Participant instructions
- [API Documentation](API_LIVE_RACES.md) - Programmatic access
- [Architecture Documentation](ASYNC_LIVE_RACES_MIGRATION_PLAN.md) - Technical details

---

## Quick Reference

### Race Creation Checklist
- [ ] Pool selected and has active participants
- [ ] Scheduled time accounts for participant timezones
- [ ] Race room settings configured appropriately
- [ ] Goal and info clearly describe race
- [ ] Eligible participants reviewed
- [ ] Race announced in Discord
- [ ] Notifications enabled for participants
- [ ] Seed/permalink prepared (if applicable)
- [ ] Backup plan ready for technical issues

### Pre-Race Checklist (15 min before)
- [ ] Verify race room opened automatically
- [ ] Check participant join rate
- [ ] Send reminder in Discord
- [ ] Monitor notification delivery logs
- [ ] Be available for participant questions

### Post-Race Checklist
- [ ] Verify results recorded correctly
- [ ] Review race completion rate
- [ ] Check for any issues reported
- [ ] Gather participant feedback
- [ ] Archive race properly
