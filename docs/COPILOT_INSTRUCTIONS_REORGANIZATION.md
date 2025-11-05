# Copilot Instructions Reorganization Plan

## Current State
- **File**: `.github/copilot-instructions.md`
- **Size**: 1,182 lines
- **Issue**: Too large, contains detailed examples and step-by-step guides that could be referenced

## Proposed Structure

### 1. Core Instructions (`.github/copilot-instructions.md`) - ~400-500 lines
**Purpose**: Essential patterns, rules, and quick reference that Copilot needs for most coding tasks

**Contents**:
- **Project Overview** (brief - 3-4 paragraphs)
  - What is SahaBot2
  - Tech stack (NiceGUI, FastAPI, Tortoise ORM, Discord)
  - Multi-tenant architecture note
- **Core Principles** (keep all - these are critical)
  - Responsive Design
  - Separation of Concerns
  - Logging Standards
  - DateTime Standards
  - Event System (high-level)
  - External CSS/JS Only
  - External Links Pattern
  - Discord OAuth2
  - Authorization
  - Code Quality Standards
  - Discord Bot Architecture
  - Porting from Original Bot
- **Quick Architecture Reference** (1-2 paragraphs)
  - Layer structure (UI → Services → Repositories → Models)
  - Key directories and their purposes
  - Reference to `docs/ARCHITECTURE.md` for details
- **Critical Patterns** (brief examples only)
  - Using BasePage for pages
  - Using services (not ORM in UI)
  - Event emission
  - Authorization checks
  - Reference to `docs/PATTERNS.md` for full examples
- **Common Pitfalls** (keep all - these prevent mistakes)
- **Where to Learn More** (new section)
  - Link to all detailed documentation

### 2. Architecture Guide (`docs/ARCHITECTURE.md`) - New
**Purpose**: Detailed system architecture and component descriptions

**Contents**:
- **Core Files** (detailed descriptions)
  - main.py, frontend.py, config.py, database.py
  - Full responsibility descriptions
- **Application Layer**
  - Services (with examples)
  - Repositories (with examples)
  - Events system (detailed)
  - Utils
- **Authentication & Authorization**
  - DiscordAuthService details
  - AuthorizationService patterns
  - Multi-tenancy implementation
- **UI Layer**
  - Pages structure
  - Views organization (by subdirectory)
  - Components structure
  - Dialogs organization (by subdirectory)
  - Static assets
- **Discord Bot Layer**
  - Bot lifecycle management
  - Command organization
  - Integration patterns
- **Database**
  - Tortoise ORM configuration
  - Migration workflow
  - Model organization

### 3. Patterns & Conventions (`docs/PATTERNS.md`) - New
**Purpose**: Detailed code patterns with full examples

**Contents**:
- **Async/Await Patterns**
- **Page Structure**
  - Full BasePage examples
  - Simple, authenticated, admin pages
  - Dynamic content with views
  - Query parameter notifications
- **Service Usage**
  - Service initialization
  - Calling async methods
  - Error handling patterns
- **Authorization Patterns**
  - Checking permissions in services
  - Enforcing in pages
  - Multi-tenant authorization
- **API Routes**
  - Standard route pattern
  - Authorization at service layer
  - Rate limiting
  - Response formatting
- **CSS Classes Reference**
  - Complete class listing with examples
  - Responsive patterns
  - Dark mode patterns
- **Discord Bot Command Patterns**
  - Full command examples
  - Service delegation
  - Error handling

### 4. Adding Features Guide (`docs/ADDING_FEATURES.md`) - New
**Purpose**: Step-by-step guides for common development tasks

**Contents**:
- **New Page** (full walkthrough)
- **New UI Component** (full walkthrough)
- **New Dialog** (full walkthrough)
- **New View** (full walkthrough)
- **New Business Logic** (service + repository)
- **New Authorization Check**
- **New Model** (with migrations)
- **New Discord Bot Command**
- **New API Endpoint**
- **Testing Guide**

### 5. Existing Documentation (Keep/Enhance)
These are already well-organized and should be referenced:
- `docs/BASEPAGE_GUIDE.md` - ✅ Good
- `docs/DIALOG_ACTION_ROW_PATTERN.md` - ✅ Good
- `docs/COMPONENTS_GUIDE.md` - ✅ Good
- `docs/JAVASCRIPT_GUIDELINES.md` - ✅ Good
- `docs/EVENT_SYSTEM.md` - ✅ Good
- `docs/NOTIFICATION_SYSTEM.md` - ✅ Good
- Many other specialized guides - ✅ Good

## Benefits of Reorganization

### 1. **Smaller Core Instructions**
- Faster to load and parse
- Easier for Copilot to process
- Focus on "must know" rules

### 2. **Better Organization**
- Related content grouped logically
- Easy to find specific information
- Clear separation of rules vs examples vs guides

### 3. **Easier Maintenance**
- Update examples in one place
- Add new patterns without bloating core file
- Clear ownership of documentation sections

### 4. **Better Discoverability**
- New developers can find step-by-step guides
- Copilot can reference detailed docs when needed
- Table of contents in each file

## Migration Strategy

### Phase 1: Create New Documents
1. Create `docs/ARCHITECTURE.md` with detailed architecture content
2. Create `docs/PATTERNS.md` with full pattern examples
3. Create `docs/ADDING_FEATURES.md` with step-by-step guides

### Phase 2: Streamline Core Instructions
1. Reduce `.github/copilot-instructions.md` to essentials
2. Add "See docs/X.md for details" references
3. Keep only critical examples inline

### Phase 3: Cross-Reference
1. Add table of contents to each new doc
2. Link between related docs
3. Update main README to reference documentation structure

## Example: Before and After

### Before (copilot-instructions.md)
```markdown
### Page Structure (Using BasePage Template)
All pages should use the `BasePage` component for consistent layout:

```python
from components.base_page import BasePage

def register():
    """Register page routes."""

    @ui.page('/path')
    async def page_name():
        """Page docstring."""
        # Create base page (simple, authenticated, or admin)
        base = BasePage.simple_page(title="Page Title", active_nav="home")
        # ... 50 more lines of examples ...
```

**BasePage Helper Methods:**
- `BasePage.simple_page()` - No auth required
- ... 20 more lines ...

**Benefits:**
- Automatic CSS loading
- ... 10 more lines ...
```

### After (copilot-instructions.md)
```markdown
### Page Structure
All pages must use `BasePage` for consistent layout and authentication:

```python
from components.base_page import BasePage

@ui.page('/path')
async def page_name():
    base = BasePage.authenticated_page(title="Page", active_nav="home")
    async def content(page: BasePage):
        ui.label(f'Hello {page.user.discord_username}!')
    await base.render(content)()
```

**See `docs/BASEPAGE_GUIDE.md` for complete examples and patterns.**
```

### After (docs/BASEPAGE_GUIDE.md)
```markdown
# BasePage Usage Guide

## Overview
All pages should use the `BasePage` component...

## Helper Methods
... full detailed list ...

## Examples
### Simple Page
... full example ...

### Authenticated Page
... full example ...

... etc ...
```

## Implementation Checklist

- [ ] Create `docs/ARCHITECTURE.md`
- [ ] Create `docs/PATTERNS.md`
- [ ] Create `docs/ADDING_FEATURES.md`
- [ ] Streamline `.github/copilot-instructions.md`
- [ ] Add cross-references between docs
- [ ] Update main README with documentation guide
- [ ] Test with Copilot to ensure context is still effective

## Estimated Sizes

| File | Current | Target | Reduction |
|------|---------|--------|-----------|
| `.github/copilot-instructions.md` | 1,182 lines | ~450 lines | 62% |
| `docs/ARCHITECTURE.md` | N/A | ~300 lines | New |
| `docs/PATTERNS.md` | N/A | ~400 lines | New |
| `docs/ADDING_FEATURES.md` | N/A | ~350 lines | New |

**Total Documentation**: ~1,500 lines (organized across 4 focused files instead of 1 monolithic file)
