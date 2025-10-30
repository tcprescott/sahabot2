# CSS Architecture Documentation

## Overview
The CSS has been restructured into a modular architecture for better maintainability and organization. The old monolithic 1610-line `main.css` has been split into focused, single-purpose files.

## File Structure

### 1. **variables.css** (77 lines)
- CSS custom properties (CSS variables)
- Official color palette (light & dark modes)
- Spacing scale
- Border radius values
- Shadow definitions
- **When to edit**: Changing design tokens, colors, spacing values

### 2. **base.css** (41 lines)
- CSS reset
- Body styles
- Dynamic text/background helper classes
- **When to edit**: Changing base typography, global resets

### 3. **components.css** (149 lines)
- Reusable UI components
- Buttons (primary, secondary, danger)
- Cards and card variants
- Badges (admin, moderator, user, status)
- Icons
- **When to edit**: Adding new component styles, modifying button/card appearance

### 4. **layout.css** (268 lines)
- Page layout structures
- Header bar
- Navigation
- Sidebar and flyout sidebar
- Content containers
- Hero sections
- **When to edit**: Changing page structure, header/sidebar behavior

### 5. **quasar-overrides.css** (148 lines)
- Customizations for Quasar components
- Menu styling
- Toggle/switch styling
- Table styling
- Dialog styling
- Input field styling
- Button overrides
- **When to edit**: Customizing third-party Quasar components

### 6. **utilities.css** (200 lines)
- Utility classes for rapid development
- Flexbox helpers
- Spacing utilities (margin/padding)
- Text alignment
- Display utilities
- Width/height helpers
- **When to edit**: Adding new utility classes

### 7. **responsive.css** (110 lines)
- Media queries for all breakpoints
- Mobile (< 768px)
- Tablet (768px - 1024px)
- Desktop (> 1024px)
- Large desktop (> 1440px)
- **When to edit**: Adjusting responsive behavior

### 8. **main.css** (174 lines)
- Imports all modular CSS files
- Application-specific styles that don't fit elsewhere
- Data tables
- User avatars
- Feature grids
- Statistics cards
- Search/filter controls
- **When to edit**: Adding page-specific styles

## Import Order
The order of imports in `main.css` is critical:

1. **Variables** - Must be first so other files can use them
2. **Base** - Foundation styles
3. **Components** - Reusable pieces
4. **Layout** - Page structure
5. **Quasar Overrides** - Third-party customizations
6. **Utilities** - Helper classes (override everything)
7. **Responsive** - Media queries last

## Benefits of This Structure

### Maintainability
- Easy to find and edit specific styles
- Clear separation of concerns
- Smaller files are easier to understand

### Performance
- Browser can cache individual files
- Only load what you need (future optimization)
- Easier to identify unused CSS

### Collaboration
- Multiple developers can work on different files
- Reduces merge conflicts
- Clear conventions

### Scalability
- Easy to add new components
- Simple to extend utilities
- Clear place for everything

## Usage in Templates

Include the main CSS file in your HTML/templates:
```html
<link rel="stylesheet" href="/static/css/main.css">
```

The main.css file will automatically import all other CSS files.

## Development Workflow

### Adding a New Component
1. Edit `components.css`
2. Add your component styles
3. Use existing CSS variables for consistency

### Modifying Colors
1. Edit `variables.css`
2. Update color variables in `:root` or `.body--dark`
3. Changes propagate everywhere automatically

### Adding Utility Classes
1. Edit `utilities.css`
2. Follow existing naming conventions
3. Keep utilities single-purpose

### Customizing Quasar
1. Edit `quasar-overrides.css`
2. Target Quasar class names (`.q-*`)
3. Use CSS variables for theming

## Backup
The original monolithic CSS is preserved as `main-backup.css` for reference.

## Migration Notes
- All existing styles have been preserved
- No breaking changes to class names
- Dark mode support maintained
- Official color palette implemented throughout
