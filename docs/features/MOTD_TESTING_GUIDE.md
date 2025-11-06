# MOTD Banner - Manual Testing Guide

## Prerequisites
- Admin user account with `Permission.ADMIN`
- Access to Admin Panel
- Browser with localStorage enabled
- Modern browser (Chrome, Firefox, Safari, Edge)

## Test Plan

### Test 1: Initial Setup (Admin)
**Objective**: Verify MOTD can be created and saved

**Steps**:
1. Log in as admin user
2. Navigate to Admin Panel (top-right menu → Admin Panel)
3. Click "Settings" in the sidebar
4. Locate "Message of the Day" card at the top
5. Click "Edit MOTD" button
6. Enter test message: `Welcome to SahaBot2! This is a test announcement.`
7. Verify preview shows the message with purple gradient background
8. Click "Save"

**Expected Result**:
- ✅ Success notification appears
- ✅ Dialog closes
- ✅ Settings page refreshes

### Test 2: Banner Display
**Objective**: Verify banner appears on pages

**Steps**:
1. Navigate to home page (/)
2. Observe top of page (below header, above content)

**Expected Result**:
- ✅ Purple gradient banner visible
- ✅ Banner contains message from Test 1
- ✅ Campaign icon (📢) on left
- ✅ Close button (×) on right
- ✅ White text on purple background

### Test 3: Banner Dismissal
**Objective**: Verify users can dismiss banner

**Steps**:
1. On home page with banner visible
2. Click the × close button
3. Observe banner behavior
4. Navigate to different pages (Admin Panel, Profile, etc.)

**Expected Result**:
- ✅ Banner fades out smoothly
- ✅ Banner hidden after fade completes
- ✅ Banner remains hidden on all pages
- ✅ No banner on page refreshes

### Test 4: Persistence of Dismissal
**Objective**: Verify dismissal persists across sessions

**Steps**:
1. After Test 3 (banner dismissed)
2. Close browser completely
3. Reopen browser
4. Log in again
5. Visit any page

**Expected Result**:
- ✅ Banner still hidden (dismissal remembered)
- ✅ localStorage contains `motd_dismissed_at` timestamp

### Test 5: MOTD Update Triggers Re-display
**Objective**: Verify banner reappears when admin updates it

**Steps**:
1. After Test 4 (banner dismissed)
2. As admin, go to Admin Panel → Settings
3. Click "Edit MOTD"
4. Change message to: `<strong>Updated:</strong> New information available!`
5. Click "Save"
6. Navigate to any page

**Expected Result**:
- ✅ Banner reappears (even though previously dismissed)
- ✅ New message shown with bold formatting
- ✅ Banner visible on all pages again

### Test 6: HTML Formatting
**Objective**: Verify HTML formatting works correctly

**Steps**:
1. As admin, edit MOTD
2. Enter HTML content:
   ```html
   🎉 <strong>Important:</strong> Check out our <a href="/presets">new presets</a> and <em>tournament features</em>!
   ```
3. Verify preview shows formatted content
4. Save and view on page

**Expected Result**:
- ✅ Bold text renders correctly
- ✅ Italic text renders correctly
- ✅ Link is clickable and styled
- ✅ Emoji displays
- ✅ Preview matches actual banner

### Test 7: Empty MOTD (Disable Banner)
**Objective**: Verify banner can be disabled

**Steps**:
1. As admin, edit MOTD
2. Clear all text (empty textarea)
3. Click "Save"
4. Navigate to any page

**Expected Result**:
- ✅ No banner appears anywhere
- ✅ No error messages
- ✅ Page renders normally without banner

### Test 8: Mobile Responsiveness
**Objective**: Verify banner works on mobile devices

**Steps**:
1. Set MOTD with test message
2. Open browser DevTools
3. Toggle device toolbar (mobile view)
4. Select various device sizes (iPhone, iPad, etc.)
5. View banner on home page

**Expected Result**:
- ✅ Banner spans full width
- ✅ Text wraps appropriately
- ✅ Close button remains accessible
- ✅ Icon and text properly aligned
- ✅ Touch-friendly close button

### Test 9: Multiple Users
**Objective**: Verify independent dismissal per user

**Steps**:
1. User A: View and dismiss banner
2. User B: Log in (different browser/incognito)
3. User B: View pages

**Expected Result**:
- ✅ User B sees banner (not affected by User A's dismissal)
- ✅ User B can independently dismiss
- ✅ Each user's dismissal tracked separately

### Test 10: Long Message Handling
**Objective**: Verify banner handles long content

**Steps**:
1. As admin, edit MOTD
2. Enter long message (100+ words)
3. Save and view

**Expected Result**:
- ✅ Banner expands vertically to fit content
- ✅ Text wraps correctly
- ✅ Close button remains visible
- ✅ No text overflow or truncation
- ✅ Scrolling not required (content visible)

### Test 11: Special Characters
**Objective**: Verify special characters handled correctly

**Steps**:
1. Edit MOTD with special characters:
   ```
   Testing: "quotes" 'apostrophes' <brackets> & ampersands é accents 日本語
   ```
2. Save and view

**Expected Result**:
- ✅ All characters display correctly
- ✅ No encoding issues
- ✅ No JavaScript errors

### Test 12: Browser LocalStorage Check
**Objective**: Verify localStorage usage

**Steps**:
1. View banner and dismiss it
2. Open browser DevTools → Application/Storage tab
3. Navigate to Local Storage → your domain
4. Look for `motd_dismissed_at` key

**Expected Result**:
- ✅ Key exists in localStorage
- ✅ Value is ISO 8601 timestamp
- ✅ Format: `2024-11-06T22:30:00.000Z`

### Test 13: Admin Panel Integration
**Objective**: Verify admin UI is user-friendly

**Steps**:
1. As admin, go to Settings
2. Observe "Message of the Day" card
3. Test "Edit MOTD" button
4. Test dialog interface

**Expected Result**:
- ✅ Card clearly labeled and positioned
- ✅ Button prominent and accessible
- ✅ Dialog opens smoothly
- ✅ Textarea is large enough
- ✅ Preview updates in real-time
- ✅ Save/Cancel buttons work

### Test 14: Permission Enforcement
**Objective**: Verify only admins can edit MOTD

**Steps**:
1. Log in as non-admin user
2. Navigate to home page
3. Check if admin panel accessible
4. If somehow access Settings page, verify MOTD edit unavailable

**Expected Result**:
- ✅ Non-admin cannot access Admin Panel
- ✅ MOTD banner still visible to all users
- ✅ Editing restricted to admins only

### Test 15: Timestamp Comparison Logic
**Objective**: Verify re-display logic works correctly

**Steps**:
1. View banner, note time T1
2. Dismiss banner at T2
3. Admin updates MOTD at T3 (after T2)
4. Refresh page

**Expected Result**:
- ✅ Banner reappears (T3 > T2)
- ✅ localStorage has T2 dismissal
- ✅ Database has T3 update
- ✅ JavaScript correctly compares timestamps

## Browser Compatibility Checklist

Test on:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Safari (iOS)
- [ ] Chrome Mobile (Android)

## Accessibility Checklist

- [ ] Banner has sufficient color contrast (white on purple)
- [ ] Close button is keyboard accessible (Tab + Enter)
- [ ] Screen reader announces banner content
- [ ] Banner doesn't interfere with page navigation
- [ ] Banner doesn't create scroll trap

## Performance Checklist

- [ ] Page load time not noticeably affected
- [ ] No visible flash/flicker when banner hides
- [ ] Smooth fade-out animation
- [ ] No JavaScript console errors
- [ ] No memory leaks (test with DevTools memory profiler)

## Edge Cases

### Edge Case 1: JavaScript Disabled
**Test**: Disable JavaScript in browser, view page
**Expected**: Banner shows but cannot be dismissed (graceful degradation)

### Edge Case 2: LocalStorage Disabled
**Test**: Disable localStorage (private/incognito mode with restrictions)
**Expected**: Banner always visible, cannot be dismissed

### Edge Case 3: Rapid MOTD Updates
**Test**: Admin updates MOTD 3 times in quick succession
**Expected**: Latest version shown, timestamp always current

### Edge Case 4: Concurrent Browser Tabs
**Test**: Open multiple tabs, dismiss banner in one tab
**Expected**: Other tabs still show banner until refreshed

### Edge Case 5: Clock Skew
**Test**: Change system time, test timestamp comparison
**Expected**: ISO 8601 string comparison still works correctly

## Regression Testing

After any changes to:
- [ ] BasePage component
- [ ] Admin settings
- [ ] GlobalSettings service
- [ ] CSS styling

Re-run tests 1-7 to ensure MOTD still works.

## Automated Testing

Run unit tests:
```bash
poetry run pytest tests/test_motd.py -v
```

Expected: All tests pass

## Issue Reporting Template

If issues found, report with:
- Test number and name
- Steps to reproduce
- Expected vs actual result
- Browser and version
- Screenshots (if visual issue)
- Console errors (if any)
- localStorage contents (if relevant)

## Success Criteria

Feature is ready for production if:
- ✅ All 15 tests pass
- ✅ No JavaScript errors in console
- ✅ Works on all major browsers
- ✅ Mobile responsive
- ✅ Accessible (keyboard + screen reader)
- ✅ Unit tests pass
- ✅ Code review approved
- ✅ Documentation complete
