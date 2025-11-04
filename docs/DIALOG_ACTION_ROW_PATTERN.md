# Dialog Action Row Pattern

## Overview
All dialogs extending `BaseDialog` must follow a specific pattern for action button placement to ensure consistent layout with buttons at opposite ends of the dialog.

## The Pattern

### ✅ Correct Pattern
Action rows must be placed **directly in the dialog body**, NOT nested inside wrapper containers:

```python
def _render_body(self) -> None:
    """Render dialog content."""
    # Content sections (info, forms, etc.) at root level
    self.create_section_title('Section Title')
    self.create_info_row('Label', 'Value')
    
    ui.separator()
    
    # Form fields
    with self.create_form_grid(columns=2):
        with ui.element('div'):
            ui.input(label='Field 1').classes('w-full')
        with ui.element('div'):
            ui.input(label='Field 2').classes('w-full')
    
    ui.separator()
    
    # Actions row at root level (NOT inside a wrapper!)
    with self.create_actions_row():
        ui.button('Cancel', on_click=self.close).classes('btn')
        ui.button('Save', on_click=self._save).classes('btn').props('color=positive')
```

### ❌ Incorrect Pattern
DO NOT wrap the entire content including actions in a column:

```python
def _render_body(self) -> None:
    """Render dialog content."""
    # ❌ WRONG - Don't wrap everything in a column!
    with ui.column().classes('full-width gap-md'):
        self.create_section_title('Section Title')
        # ... content ...
        
        # Actions inside the column wrapper breaks the layout!
        with self.create_actions_row():
            ui.button('Cancel', on_click=self.close).classes('btn')
            ui.button('Save', on_click=self._save).classes('btn').props('color=positive')
```

### ❌ Also Incorrect
DO NOT nest buttons inside additional containers within the actions row:

```python
# ❌ WRONG - Don't nest buttons in a row within actions row!
with self.create_actions_row():
    ui.button('Delete', on_click=self._delete).classes('btn')
    with ui.row().classes('gap-2'):  # ❌ This breaks the layout!
        ui.button('Cancel', on_click=self.close).classes('btn')
        ui.button('Save', on_click=self._save).classes('btn')
```

## Why This Pattern?

The `create_actions_row()` method creates a container with CSS class `.dialog-actions`:

```css
.dialog-actions {
    display: flex;
    justify-content: space-between;  /* This spaces first and last buttons to opposite ends */
    gap: var(--spacing-sm);
    margin-top: var(--spacing-md);
}
```

The `justify-content: space-between` property works on **direct children** of the flex container. When you:
- Wrap the actions row in a column with `full-width` class, OR
- Nest buttons in additional containers

...you break this layout because the flex container no longer has the buttons as direct children.

## Button Placement Convention

### Standard Two-Button Layout
```python
with self.create_actions_row():
    # Left side - neutral/negative action
    ui.button('Cancel', on_click=self.close).classes('btn')
    # Right side - primary/positive action
    ui.button('Save', on_click=self._save).classes('btn').props('color=positive')
```

**Result:** Cancel on far left, Save on far right

### Three-Button Layout (Destructive Action)
```python
with self.create_actions_row():
    # Left side - destructive action
    ui.button('Delete', on_click=self._delete).classes('btn').props('color=negative')
    # Right side - primary action (positive takes precedence)
    ui.button('Save', on_click=self._save).classes('btn').props('color=positive')
```

**Result:** Delete on far left, Save on far right

**Note:** If you need Cancel + Delete + Save, consider whether all three are necessary. The pattern supports two primary actions best.

### Conditional Button Layout
For dialogs with conditional buttons (e.g., Delete only shown when editing):

```python
with self.create_actions_row():
    # Left side - conditional destructive or neutral
    if self.is_editing and self._on_delete:
        ui.button('Delete', on_click=self._delete).classes('btn').props('color=negative')
    else:
        ui.button('Cancel', on_click=self.close).classes('btn')
    
    # Right side - always primary action
    ui.button('Save', on_click=self._save).classes('btn').props('color=positive')
```

## Scoped Columns Are OK

You **can** use columns for specific content sections, just keep actions at root level:

```python
def _render_body(self):
    """Render dialog content."""
    # Section 1 - scoped column ✅
    self.create_section_title('Section 1')
    with ui.column().classes('gap-sm w-full'):
        self.create_info_row('Field 1', 'Value 1')
        self.create_info_row('Field 2', 'Value 2')
    
    ui.separator()
    
    # Section 2 - another scoped column ✅
    self.create_section_title('Section 2')
    with ui.column().classes('gap-md w-full'):
        ui.input(label='Input').classes('w-full')
        ui.textarea(label='Notes').classes('w-full')
    
    ui.separator()
    
    # Actions at root level ✅
    with self.create_actions_row():
        ui.button('Cancel', on_click=self.close).classes('btn')
        ui.button('Save', on_click=self._save).classes('btn').props('color=positive')
```

## Checklist for New Dialogs

When creating a new dialog, ensure:

- [ ] Dialog extends `BaseDialog`
- [ ] `_render_body()` does NOT start with `with ui.column().classes('full-width ...')`
- [ ] `create_actions_row()` is called at the root level of `_render_body()`
- [ ] Buttons are direct children of `create_actions_row()` (not nested in additional containers)
- [ ] Neutral/Cancel button is first (left side)
- [ ] Primary/Positive button is last (right side)
- [ ] Destructive actions (if any) are on the left

## Testing

After creating or modifying a dialog:

1. Open the dialog on desktop viewport
2. Verify Cancel/neutral button is on the far left
3. Verify Save/positive button is on the far right
4. Check mobile viewport to ensure buttons still work (may stack on small screens based on responsive CSS)

## Examples

### Good Examples
- `components/dialogs/admin/user_edit_dialog.py`
- `components/dialogs/tournaments/match_seed_dialog.py`
- `components/dialogs/tournaments/race_review_dialog.py`
- `components/dialogs/organization/invite_member_dialog.py`

### Previously Fixed (Reference)
These dialogs were fixed to follow the correct pattern:
- `components/dialogs/tournaments/add_crew_dialog.py` (removed outer column wrapper)
- `components/dialogs/admin/racetime_bot_organizations_dialog.py` (removed outer column wrapper)
- `components/dialogs/organization/preset_editor_dialog.py` (removed outer column wrapper)

## Related Documentation
- [BasePage Guide](BASEPAGE_GUIDE.md)
- [Components Guide](../COMPONENTS_GUIDE.md)
- [Dialog Styling Standards](../.github/copilot-instructions.md#dialog-styling-standards)
