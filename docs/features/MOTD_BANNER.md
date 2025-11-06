# MOTD (Message of the Day) Banner

## Overview

The MOTD banner is a dismissible notification banner that appears at the top of all pages. It's designed to communicate important information to users, such as announcements, maintenance notifications, or upcoming events.

## Key Features

1. **Dismissible**: Users can dismiss the banner by clicking the close button
2. **Smart Re-display**: Banner automatically reappears if an admin updates the MOTD text
3. **HTML Support**: Admins can use HTML formatting for rich content
4. **Global**: Appears on all pages for all users
5. **Persistent**: Dismissal state stored in browser localStorage

## How It Works

### For Users

1. **Viewing the Banner**: When an MOTD is active, a purple gradient banner appears at the top of every page
2. **Dismissing**: Click the "×" button on the right side of the banner to hide it
3. **Re-appearance**: If an admin updates the MOTD, the banner will reappear even if you previously dismissed it

### For Admins

1. **Accessing MOTD Settings**:
   - Navigate to Admin Panel → Settings
   - Look for the "Message of the Day" card
   - Click "Edit MOTD" button

2. **Editing MOTD**:
   - Enter your message in the text area
   - HTML formatting is supported (e.g., `<strong>`, `<em>`, `<a>`)
   - Preview shows how the banner will appear
   - Click "Save" to activate

3. **Disabling MOTD**:
   - Open the MOTD dialog
   - Clear the text field (leave it empty)
   - Click "Save"
   - Banner will no longer appear for any users

## Technical Details

### Storage

- **MOTD Text**: Stored in `global_settings` table with key `motd_text`
- **Update Timestamp**: Stored with key `motd_updated_at` (ISO 8601 format)
- **Dismissal State**: Stored in browser localStorage as `motd_dismissed_at`

### Dismissal Logic

```javascript
// User dismissed banner at timestamp T1
localStorage.setItem('motd_dismissed_at', T1)

// Admin updates MOTD at timestamp T2
// Banner checks: T2 > T1 ? show : hide
if (motd_updated_at > motd_dismissed_at) {
    // Show banner (admin updated after user dismissed)
} else {
    // Keep hidden (user dismissed current version)
}
```

### Architecture

**Components**:
- `components/motd_banner.py` - Banner rendering and visibility logic
- `components/dialogs/admin/motd_dialog.py` - Admin editing interface
- `components/base_page.py` - Integration point (renders banner on all pages)

**Services**:
- Uses `SettingsService` to read/write MOTD settings
- No additional service layer needed

**Storage**:
- Uses existing `GlobalSetting` model
- No database migration required

## HTML Formatting Examples

### Simple Text
```html
Welcome to SahaBot2! Please check out our new features.
```

### Bold/Emphasis
```html
<strong>Important:</strong> System maintenance scheduled for <em>tomorrow at 3pm UTC</em>.
```

### Links
```html
New tournament starting! <a href="/org/1/tournaments">Sign up here</a>
```

### Complex Formatting
```html
🎉 <strong>Big News:</strong> We've added <a href="/presets">new randomizer presets</a>! 
Check them out in the <em>Presets</em> tab.
```

## Examples

### Maintenance Notification
```html
⚠️ <strong>Scheduled Maintenance:</strong> The site will be down for maintenance 
on Saturday, Nov 9th from 2-4 PM UTC. Thank you for your patience!
```

### New Feature Announcement
```html
🎉 <strong>New Feature:</strong> You can now link your Twitch account! 
Visit your <a href="/profile">profile page</a> to connect.
```

### Tournament Announcement
```html
🏆 <strong>Tournament Alert:</strong> ALTTPR Season 5 signups are now open! 
<a href="/org/2/tournaments">Register here</a> before November 15th.
```

## Best Practices

1. **Keep it concise**: Banner should be readable at a glance
2. **Use HTML sparingly**: Too much formatting can be overwhelming
3. **Update, don't create new**: Editing the MOTD is better than creating multiple announcements
4. **Clear when done**: Remove MOTD when the announcement is no longer relevant
5. **Test formatting**: Use the preview to ensure your HTML renders correctly

## Troubleshooting

### Banner not appearing
- Check if MOTD text is set (Admin Panel → Settings)
- Verify `motd_text` global setting exists and is not empty
- Check browser console for JavaScript errors

### Banner reappears after dismissal
- This is expected if admin updated the MOTD
- Each MOTD update creates a new timestamp
- Users must re-dismiss after each update

### Formatting not working
- Ensure HTML tags are properly closed
- Check preview in MOTD dialog before saving
- Some HTML tags may be sanitized by browser for security

## Security Considerations

### HTML Content Security

- **Admin-only editing**: Only users with `Permission.ADMIN` can edit MOTD content
- **Trusted content**: Admins are trusted users with full system access
- **HTML rendering**: `ui.html()` is used to support formatting, but only for admin-provided content
- **Browser protection**: Modern browsers block dangerous tags (script, iframe) automatically
- **CSP protection**: Content-Security-Policy headers prevent inline script execution
- **XSS mitigation**: All JavaScript variables are properly escaped before injection

### Important Notes

1. **Current implementation is secure** because:
   - Only admins can edit MOTD (permission-checked)
   - Content is stored in database, not from untrusted sources
   - Admins already have full system access

2. **If permissions change** (e.g., allowing moderators to edit MOTD):
   - Implement server-side HTML sanitization (e.g., using `bleach` library)
   - Whitelist allowed HTML tags (strong, em, a, br, etc.)
   - Strip potentially dangerous attributes and tags

3. **Data flow**:
   - Admin → MOTDDialog → GlobalSettings → MOTDBanner → Browser
   - No user-provided content in the chain

### Timestamp Security

- Update timestamps are server-generated (not user input)
- JavaScript variables are escaped to prevent injection
- ISO 8601 format prevents parsing vulnerabilities

### Public Setting Rationale

MOTD is marked as `is_public=True` in GlobalSettings because:
- Designed to be visible to all users (authenticated and guests)
- Contains no sensitive information (announcements, events)
- No privacy concerns with public visibility

## Future Enhancements

Potential improvements for future iterations:

1. **Organization-specific MOTD**: Different messages per organization
2. **Scheduled MOTD**: Auto-activate/deactivate at specific times
3. **Banner styles**: Different colors for different message types (info, warning, success)
4. **Rich editor**: WYSIWYG editor for easier formatting
5. **Analytics**: Track how many users dismiss vs. click links in MOTD

## Code References

- Banner component: `components/motd_banner.py`
- Admin dialog: `components/dialogs/admin/motd_dialog.py`
- Settings view: `views/admin/admin_settings.py`
- Base page integration: `components/base_page.py` (line ~240)
- Tests: `tests/test_motd.py`
