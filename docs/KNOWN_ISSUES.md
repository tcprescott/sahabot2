# Known Issues

## Tab Switching Failures with Sidebar (RESOLVED)

**Status**: ✅ RESOLVED  
**Date Reported**: October 29, 2025  
**Date Resolved**: October 29, 2025  
**Root Cause**: Inline module imports causing class identity issues  
**Severity**: High - Core functionality affected

### Resolution Summary

The tab switching failures were caused by **inline imports** of the `Sidebar` component inside the `page_renderer()` function in `base_page.py`. Moving the import to module level (top of file) resolved the issue completely.

**The Fix:**
```python
# At top of base_page.py (CORRECT):
from components.sidebar import Sidebar

# Inside function (BROKEN - DO NOT DO THIS):
def page_renderer():
    from components.sidebar import Sidebar  # ❌ BAD
```

### Why Inline Imports Failed

1. **Module Identity**: Each page render could get a different module instance
2. **Class Identity**: The `Sidebar` class object itself could be different on each import
3. **State Persistence**: Module-level imports ensure the same class is used throughout
4. **NiceGUI Bindings**: NiceGUI tracks component types by class identity; inline imports broke this

### Lessons Learned

- **Always import at module level** - Never use inline imports for components, services, or models
- **Python's import system** - Inline imports can create subtle bugs with class/module identity
- **NiceGUI specifics** - Framework relies on consistent class identity for component tracking
- **Updated Copilot Instructions** - Added explicit guidance to avoid inline imports

---

## Symptoms (Historical)
- Tab switching eventually stops working after multiple interactions
- Sidebar buttons stop responding or select wrong tabs
- Issue occurs after toggling sidebar open/closed several times
- Not a memory leak (verified via Chrome DevTools)

### Investigation History

#### Initial Diagnosis: Lambda Closure Bug
Initially identified a classic Python lambda-in-loop closure bug in `components/sidebar.py`:

```python
# BROKEN CODE (old):
for tab in self.tabs:
    ui.button(
        tab['label'],
        on_click=lambda lbl=tab['label']: self._on_select_tab(lbl)
    )
```

**Problem**: All lambdas captured reference to `tab` variable, not the value. After loop completed, all lambdas referenced the LAST tab.

**Fix Applied**: Replaced with proper closure factory pattern:

```python
# FIXED CODE:
def make_click_handler(label: str):
    """Create a click handler for a specific tab label."""
    def handler():
        self._on_select_tab(label)
    return handler

for tab in self.tabs:
    click_handler = make_click_handler(tab['label'])
    ui.button(tab['label'], on_click=click_handler)
```

#### Current Issue: Still Failing After Fix
Despite fixing the lambda closure bug, tab switching still fails intermittently.

### Architecture Overview

**File**: `components/base_page.py`
- Creates `Sidebar` instance with `panels=None`
- Calls `sidebar.render()` which creates button handlers
- Renders tabs via `render_tabbed_page()` which creates `ui.tabs` panels
- Sets `sidebar.panels = self._panels` after tabs are rendered

**File**: `components/sidebar.py`
- Stores reference to `ui.tabs` panels in `self.panels`
- Button handlers call `self._on_select_tab(label)`
- `_on_select_tab()` sets `self.panels.value = label` to switch tabs
- When sidebar toggles, clears and re-renders buttons

### Current Hypothesis

The issue may be related to **lifecycle timing** of the `panels` reference:

1. Sidebar created with `panels=None`
2. Sidebar renders buttons (handlers created)
3. Tabs rendered, creating `panels` object
4. `sidebar.panels = panels` assignment happens
5. Button click → handler accesses `self.panels` → should work (instance variable)
6. Sidebar toggle → clears/re-renders buttons → new handlers created
7. New handlers should still access `self.panels` → **but something breaks**

**Potential causes**:
- NiceGUI `ui.tabs` reference becoming stale after certain operations
- Sidebar toggle causing DOM updates that break tab panel bindings
- Race condition between sidebar re-render and panels state
- Context manager scope issues with NiceGUI elements

### Debugging Steps Added

Added comprehensive logging to track panel lifecycle:

**In `components/sidebar.py`**:
```python
def _on_select_tab(self, label: str) -> None:
    logger.info("_on_select_tab called with label='%s', panels=%s", label, self.panels)
    if self.panels is not None:
        logger.info("Setting panels.value to '%s'", label)
        self.panels.value = label
        logger.info("Successfully set panels.value to '%s'", label)
    else:
        logger.warning("Cannot select tab '%s' - panels is None!", label)
```

**In `components/base_page.py`**:
```python
logger.info("Setting sidebar.panels to %s (from self._panels)", self._panels)
self._sidebar.panels = self._panels
logger.info("Sidebar.panels is now %s", self._sidebar.panels)
```

### Next Steps for Investigation

1. **Review Logs**: Check terminal output for patterns:
   - Does `panels` become `None` after certain operations?
   - Are there exceptions when setting `panels.value`?
   - Does the panels object ID change unexpectedly?

2. **Test Scenario**: Systematically test:
   - Load page → click tab (should log success)
   - Toggle sidebar → click same tab (does it work?)
   - Toggle sidebar again → click different tab (does it work?)
   - After N toggles, does it fail consistently?

3. **Compare with SGLMan**: Review working implementation in `sglman/theme/base.py`:
   - How do they handle sidebar + tabs?
   - Do they avoid the panels reference pattern?
   - Different lifecycle management?

4. **Potential Solutions to Try**:
   - **Option A**: Don't pass panels reference, use JavaScript bridge to switch tabs
   - **Option B**: Recreate sidebar instance on each toggle instead of re-rendering
   - **Option C**: Use NiceGUI's built-in drawer component instead of custom sidebar
   - **Option D**: Abandon responsive sidebar, use fixed sidebar or top tabs only

### Files Involved

- `components/base_page.py` (lines 280-305): Sidebar + tab rendering
- `components/sidebar.py` (entire file): Sidebar component
- `pages/home.py`: Uses `BasePage.authenticated_page()` with tabbed interface

### Related Documentation

- `MEMORY_LEAK_DEBUGGING.md`: Guide created during investigation (not a memory leak)
- `COMPONENTS_GUIDE.md`: Component architecture documentation
- Copilot Instructions: Architecture patterns and conventions

### Workarounds

**For Development**: Use non-sidebar layout by removing `use_sidebar=True`:
```python
# In pages/home.py:
base = BasePage.authenticated_page(
    title="Home",
    active_nav="home",
    tabs=tabs,
    # use_sidebar=True,  # Comment this out to use top tabs instead
)
```

Top tabs work reliably - this is purely a sidebar integration issue.

---

**Last Updated**: October 29, 2025  
**Assigned To**: TBD  
**Priority**: High - Blocks responsive sidebar feature
