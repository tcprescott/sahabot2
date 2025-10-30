# BasePage Component

The `BasePage` class provides a consistent header and layout template for all pages in the SahaBot2 application.

## Features

- **Header Bar**: Consistent header with logo, app name, and navigation menu
- **Sidebar Flyout**: Slide-in navigation sidebar with hamburger menu
- **User Menu**: Dynamic menu with login/logout, dark mode toggle, and admin panel access
- **Authentication**: Built-in support for public, authenticated, and admin pages
- **Mobile Responsive**: Header and sidebar adapt to mobile and desktop viewports

## Usage

### Simple Page (No Authentication Required)

```python
from nicegui import ui
from components import BasePage

@ui.page('/mypage')
async def my_page():
    """Simple public page."""
    base = BasePage.simple_page(title="My Page")
    
    # Optional: Define sidebar items
    sidebar_items = [
        {
            'label': 'Home',
            'icon': 'home',
            'action': lambda: ui.navigate.to('/')
        },
        {
            'label': 'About',
            'icon': 'info',
            'action': lambda: ui.navigate.to('/about')
        },
    ]
    
    async def content(page: BasePage):
        """Render page content."""
        with ui.element('div').classes('card'):
            ui.label('Public content here')
            if page.user:
                ui.label(f'Hello, {page.user.discord_username}!')
    
    await base.render(content, sidebar_items=sidebar_items)
```

### Authenticated Page (Login Required)

```python
from nicegui import ui
from components import BasePage

@ui.page('/protected')
async def protected_page():
    """Page requiring authentication."""
    base = BasePage.authenticated_page(title="Protected Page")
    
    async def content(page: BasePage):
        """Render page content - user is guaranteed to exist."""
        with ui.element('div').classes('card'):
            ui.label(f'Welcome, {page.user.discord_username}!')
    
    await base.render(content)
```

### Admin Page (Admin Permission Required)

```python
from nicegui import ui
from components import BasePage

@ui.page('/admin')
async def admin_page():
    """Page requiring admin permission."""
    base = BasePage.admin_page(title="Admin Panel")
    
    async def content(page: BasePage):
        """Render page content - user is guaranteed to be admin."""
        with ui.element('div').classes('card'):
            ui.label(f'Admin: {page.user.discord_username}')
    
    await base.render(content)
```

## Header Features

### Left Side
- **Hamburger Menu**: Opens sidebar flyout navigation
- **Logo**: Icon representing the application
- **App Name**: "SahaBot2" branding

### Right Side (Not Logged In)
- **Menu Button**: Opens dropdown menu
  - Toggle Dark Mode
  - Login with Discord

### Right Side (Logged In)
- **Username**: Displays Discord username
- **Menu Button**: Opens dropdown menu
  - Toggle Dark Mode
  - Admin Panel (if admin)
  - Logout

## Sidebar Navigation

The sidebar provides navigation between pages with responsive behavior:
- **Desktop (≥769px)**: Always visible, permanent side navigation
- **Mobile (<769px)**: Flyout overlay, toggled with hamburger menu

### Sidebar Features
- **Responsive Behavior**: Always-on for desktop, flyout for mobile
- **Slide Animation**: Smooth slide-in/out transition (mobile)
- **Backdrop Overlay**: Dark overlay behind sidebar (mobile only)
- **Close Button**: X button in sidebar header (mobile only)
- **Navigation Items**: Custom items with icons and labels
- **Auto-close**: Sidebar closes when an item is clicked (mobile only)

### Sidebar Items Structure

Each sidebar item should have:
- `label`: Display text
- `icon`: Material icon name
- `action`: Callback function (typically navigation)

```python
sidebar_items = [
    {
        'label': 'Dashboard',
        'icon': 'dashboard',
        'action': lambda: ui.navigate.to('/dashboard')
    },
    {
        'label': 'Settings',
        'icon': 'settings',
        'action': lambda: ui.navigate.to('/settings')
    },
]
```

## Styling

All styles are defined in `/static/css/main.css` with the following classes:

### Header Classes
- `.header-bar`: Main header container
- `.header-container`: Flex container for left/right sections
- `.header-left`: Left side content (hamburger + logo + brand)
- `.header-right`: Right side content (user + menu)
- `.header-hamburger`: Hamburger menu button
- `.header-logo`: Logo icon styling
- `.header-brand`: App name styling
- `.header-username`: Username display styling
- `.header-menu-button`: User menu button styling

### Sidebar Classes
- `.sidebar-flyout`: Main sidebar container
- `.sidebar-open`: Sidebar visible state
- `.sidebar-closed`: Sidebar hidden state
- `.sidebar-header`: Sidebar header with title and close button
- `.sidebar-items`: Container for navigation items
- `.sidebar-item`: Individual navigation item
- `.sidebar-item-icon`: Item icon styling
- `.sidebar-item-label`: Item text styling
- `.sidebar-backdrop`: Dark overlay for mobile

### Responsive Design

**Header:**
- **Desktop (≥769px)**: 
  - Full layout with username visible
  - Hamburger menu hidden (sidebar always visible)
- **Mobile (<769px)**: 
  - Compact layout with username hidden
  - Hamburger menu visible for sidebar toggle

**Sidebar:**
- **Desktop (≥769px)**: 
  - Always visible (280px width)
  - No backdrop overlay
  - Close button hidden
  - Page content shifts right to accommodate sidebar
- **Mobile (<769px)**: 
  - Flyout overlay (85vw width, max 320px)
  - Dark backdrop overlay when open
  - Close button visible
  - Smooth slide animation
  - Closes on item click or backdrop tap

## Content Function

The `content` function passed to `render()` receives the `BasePage` instance as a parameter:

```python
async def content(page: BasePage):
    """
    Render page content.
    
    Args:
        page: BasePage instance with user property
    """
    # Access current user
    if page.user:
        ui.label(f'User: {page.user.discord_username}')
        ui.label(f'Permission: {page.user.permission.name}')
```

## Examples

See `/pages/example.py` for complete working examples of:
- Simple public page
- Authenticated page
- Admin page

Visit the following URLs to see the examples:
- `/example` - Public page
- `/example/protected` - Requires login
- `/example/admin` - Requires admin permission

## Architecture Notes

Following SahaBot2 architectural principles:

1. **No Inline CSS**: All styles in `main.css`
2. **Separation of Concerns**: BasePage handles presentation only
3. **Authentication/Authorization**: Uses `DiscordAuthService` from middleware
4. **Async/Await**: All methods are async
5. **Type Hints**: Full type annotations
6. **Docstrings**: Complete documentation

## Future Enhancements

Potential improvements:
- Custom logo image support
- Breadcrumb navigation
- Page-specific header actions
- Notification indicators in header
- User avatar display
