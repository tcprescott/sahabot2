# Components Directory - Base Page Template

## Summary
Created a `components/` directory with a reusable `BasePage` template that provides consistent layout, navigation, and authentication across all pages.

## Changes Made

### 1. Created Components Directory
```
components/
├── __init__.py          # Package exports
└── base_page.py         # Base page template class
```

### 2. BasePage Template Features

The `BasePage` class provides:
- ✅ **Automatic CSS loading** - No need to manually add CSS in each page
- ✅ **Consistent navbar** - Same navigation across all pages
- ✅ **Built-in authentication** - Handles auth checks automatically
- ✅ **User access** - `page.user` available in content functions
- ✅ **Logout handling** - Centralized logout functionality
- ✅ **Active nav highlighting** - Shows which page is currently active

### 3. Helper Methods

**Three convenient factory methods:**

1. **`BasePage.simple_page()`** - For public pages
   - No authentication required
   - Navbar shown by default
   - User info available if logged in

2. **`BasePage.authenticated_page()`** - For protected pages
   - Requires user login
   - Redirects to login if not authenticated
   - User guaranteed to be available

3. **`BasePage.admin_page()`** - For admin pages
   - Requires admin permissions
   - Redirects to home if unauthorized
   - User guaranteed to be admin

### 4. Updated Pages

All pages now use the base template:

#### **home.py** - Uses `BasePage.simple_page()`
```python
base = BasePage.simple_page(title="SahaBot2", active_nav="home")

async def content(page: BasePage):
    # Access page.user for current user
    if page.user:
        ui.label(f'Hello, {page.user.discord_username}!')
```

#### **admin.py** - Uses `BasePage.admin_page()`
```python
base = BasePage.admin_page(title="SahaBot2 - Admin", active_nav="admin")

async def content(page: BasePage):
    # page.user is guaranteed to be admin here
    ui.label(f'Welcome, {page.user.discord_username}')
```

#### **auth.py** - Uses `BasePage.simple_page()` without navbar
```python
base = BasePage.simple_page(title="SahaBot2", show_navbar=False)

async def content(page: BasePage):
    # Authentication callback content
    pass
```

### 5. Updated Documentation

- ✅ **README.md** - Added components directory to project structure
- ✅ **.github/copilot-instructions.md** - Updated with:
  - Components section in Core Files
  - New "Page Structure (Using BasePage Template)" section
  - Examples showing all helper methods
  - Instructions for creating new UI components

## Benefits

### Before (Manual Setup)
Each page had to:
- Manually add CSS link
- Create navbar with all links
- Check authentication/authorization
- Handle logout button
- Maintain active nav state
- Wrap content in page-container/content-wrapper

### After (Using BasePage)
Pages now:
- ✅ Use one line: `base = BasePage.simple_page()`
- ✅ Focus only on content rendering
- ✅ Get consistent layout automatically
- ✅ Have auth handled transparently
- ✅ Access current user via `page.user`

## Usage Examples

### Public Page
```python
@ui.page('/')
async def home_page():
    base = BasePage.simple_page(title="Home", active_nav="home")
    
    async def content(page: BasePage):
        with ui.element('div').classes('card'):
            if page.user:
                ui.label(f'Welcome back, {page.user.discord_username}!')
            else:
                ui.label('Please log in.')
    
    await base.render(content)()
```

### Protected Page
```python
@ui.page('/profile')
async def profile_page():
    base = BasePage.authenticated_page(title="Profile", active_nav="profile")
    
    async def content(page: BasePage):
        # page.user is guaranteed to exist
        with ui.element('div').classes('card'):
            ui.label(f'User ID: {page.user.id}')
            ui.label(f'Email: {page.user.discord_email}')
    
    await base.render(content)()
```

### Admin Page
```python
@ui.page('/admin')
async def admin_page():
    base = BasePage.admin_page(title="Admin Panel", active_nav="admin")
    
    async def content(page: BasePage):
        # page.user is guaranteed to be admin
        user_service = UserService()
        users = await user_service.get_all_users()
        # ... render admin content
    
    await base.render(content)()
```

### Custom Permission Page
```python
@ui.page('/moderate')
async def moderate_page():
    base = BasePage(
        title="Moderation",
        active_nav="moderate",
        require_permission=Permission.MODERATOR
    )
    
    async def content(page: BasePage):
        # page.user is guaranteed to be moderator or higher
        pass
    
    await base.render(content)()
```

## Architecture Improvement

This change reinforces the core principles:
1. ✅ **DRY (Don't Repeat Yourself)** - Navbar and layout code in one place
2. ✅ **Separation of Concerns** - Template handles layout, pages handle content
3. ✅ **Consistency** - All pages look and behave the same
4. ✅ **Maintainability** - Update navbar once, affects all pages
5. ✅ **Clean Code** - Pages are now much shorter and focused

## Breaking Changes

**None!** The old approach still works, but new pages should use the `BasePage` template for consistency.

## Next Steps

Future enhancements could include:
- Additional template variations (full-width, no container, etc.)
- Breadcrumb navigation support
- Page footer component
- Loading states and error boundaries
- Custom navbar items per page
