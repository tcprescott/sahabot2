# MOTD Banner - Feature Flow Diagram

## User Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Visits Page                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              BasePage._render_motd_banner() called              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              MOTDBanner.render() - Check database               │
│  - Get 'motd_text' from GlobalSettings                          │
│  - Get 'motd_updated_at' timestamp                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
                 No MOTD          MOTD Exists
                    │                 │
                    ▼                 ▼
            ┌─────────────┐   ┌─────────────────────────┐
            │  No Banner  │   │  Render Banner HTML     │
            │  Displayed  │   │  + JavaScript Logic     │
            └─────────────┘   └────────┬────────────────┘
                                       │
                                       ▼
                          ┌────────────────────────────┐
                          │   JavaScript Checks        │
                          │   localStorage for         │
                          │   'motd_dismissed_at'      │
                          └────────┬───────────────────┘
                                   │
                          ┌────────┴─────────┐
                          │                  │
                    Not Dismissed      Was Dismissed
                          │                  │
                          ▼                  ▼
                  ┌──────────────┐   ┌──────────────────────┐
                  │ Show Banner  │   │ Compare Timestamps:   │
                  │              │   │ updated > dismissed?  │
                  └──────────────┘   └────────┬──────────────┘
                                              │
                                      ┌───────┴────────┐
                                      │                │
                                   Yes (show)      No (hide)
                                      │                │
                              ┌───────▼─────┐   ┌─────▼──────┐
                              │ Show Banner │   │ Hide Banner│
                              │ (re-display)│   │            │
                              └─────────────┘   └────────────┘
```

## Admin Flow

```
┌─────────────────────────────────────────────────────────────────┐
│             Admin Opens Settings in Admin Panel                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│            AdminSettingsView renders "Edit MOTD" button         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                Admin clicks "Edit MOTD"                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              MOTDDialog.show() - Load current MOTD              │
│  - Get current 'motd_text' from database                        │
│  - Display in textarea with preview                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Admin edits MOTD text                           │
│  - Type in textarea                                              │
│  - See live preview with formatting                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Admin clicks "Save"                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│             MOTDDialog._save() - Update settings                │
│  1. Save 'motd_text' to GlobalSettings                          │
│  2. Save 'motd_updated_at' with NEW timestamp                   │
│  3. Show success notification                                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              All Users See Banner on Next Page Load             │
│  - Even if they dismissed the old version                       │
│  - New timestamp > old dismissal timestamp                       │
└─────────────────────────────────────────────────────────────────┘
```

## Dismissal Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                   User Sees MOTD Banner                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  User clicks "×" button                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│           JavaScript dismissBtn click handler runs              │
│  1. Get current timestamp: new Date().toISOString()             │
│  2. Store in localStorage: 'motd_dismissed_at'                  │
│  3. Fade out banner (opacity: 0)                                │
│  4. Hide banner (display: none)                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│         Banner Hidden on Current and Future Page Loads          │
│  - Until admin updates MOTD                                     │
│  - Then new timestamp > dismissed timestamp                     │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
┌──────────────────┐
│  GlobalSettings  │
│     Database     │
└────────┬─────────┘
         │
         │ Read/Write
         │
┌────────▼─────────┐
│ SettingsService  │
└────────┬─────────┘
         │
         │ Used by
         │
    ┌────┴─────┐
    │          │
    ▼          ▼
┌─────────┐  ┌──────────┐
│  MOTD   │  │  MOTD    │
│ Banner  │  │ Dialog   │
└────┬────┘  └────┬─────┘
     │            │
     │ Renders    │ Updates
     │            │
     ▼            ▼
┌─────────────────────┐
│    User Browser     │
│  - Sees banner      │
│  - Stores dismissal │
│    in localStorage  │
└─────────────────────┘
```

## Database Schema

```
global_settings table:
┌──────────────────────────────────────────────────────────────┐
│ id │ key              │ value          │ is_public │ updated_at│
├────┼──────────────────┼────────────────┼───────────┼───────────┤
│ 1  │ motd_text        │ "Welcome..."   │ true      │ 2024-...  │
│ 2  │ motd_updated_at  │ "2024-11-06T"  │ true      │ 2024-...  │
└────┴──────────────────┴────────────────┴───────────┴───────────┘
```

## localStorage Schema

```javascript
{
  "motd_dismissed_at": "2024-11-06T22:30:00.000Z"
}
```

## Timestamp Comparison Logic

```javascript
// Example scenario:

// 1. Admin sets MOTD at T1
motd_updated_at = "2024-11-06T10:00:00.000Z"

// 2. User dismisses at T2
localStorage.setItem("motd_dismissed_at", "2024-11-06T10:30:00.000Z")
// Banner hidden

// 3. Admin updates MOTD at T3
motd_updated_at = "2024-11-06T11:00:00.000Z"

// 4. User loads page
dismissed_at = "2024-11-06T10:30:00.000Z"  // From localStorage
updated_at = "2024-11-06T11:00:00.000Z"     // From database

// 5. Comparison
updated_at > dismissed_at  // "2024-11-06T11:00:00.000Z" > "2024-11-06T10:30:00.000Z"
// Result: true → Show banner
```

## Component Integration

```
BasePage (components/base_page.py)
    │
    ├─ _render_header()
    ├─ _render_impersonation_banner()
    ├─ _render_motd_banner()  ← Our MOTD integration
    │      │
    │      └─ MOTDBanner.render() (components/motd_banner.py)
    │              │
    │              ├─ Fetch settings from database
    │              ├─ Render HTML banner
    │              └─ Inject JavaScript for dismissal logic
    │
    └─ _render_sidebar()
```

## Admin UI Integration

```
AdminPage (pages/admin.py)
    │
    └─ Loads AdminSettingsView
            │
            └─ _render_content() (views/admin/admin_settings.py)
                    │
                    ├─ Renders "Message of the Day" card
                    ├─ "Edit MOTD" button
                    │      │
                    │      └─ Opens MOTDDialog
                    │              │
                    │              └─ _save() updates database
                    │
                    └─ Renders "Global Settings" table
```
