# Accessibility (A11y) Implementation

## Overview

This document outlines the accessibility features implemented in SahaBot2 to ensure the application is usable by everyone, including people with disabilities.

## WCAG Compliance

SahaBot2 aims to meet **WCAG 2.1 Level AA** standards.

## Implemented Features

### 1. Keyboard Navigation

- **Focus Indicators**: All interactive elements (buttons, links, inputs) have visible focus indicators (2px solid outline)
- **Skip Navigation**: A skip link allows keyboard users to jump directly to main content
- **Logical Tab Order**: Tab order follows visual layout and logical reading order
- **Keyboard-Accessible Menus**: All dropdown menus and dialogs are keyboard-navigable

### 2. Screen Reader Support

#### ARIA Labels and Roles
- Icon-only buttons have descriptive `aria-label` attributes
- Navigation sidebar has `role="navigation"` and `aria-label="Main navigation"`
- Data tables include proper `role="table"`, `role="row"`, and `role="cell"` attributes
- Table headers use `scope="col"` for proper column association
- Loading states have `role="status"` and `aria-live="polite"`
- Alert banners (MOTD) have `role="alert"` and `aria-live="polite"`

#### Decorative Elements
- Decorative icons are marked with `aria-hidden="true"` to prevent screen reader clutter
- All meaningful images have `alt` text

### 3. Color and Contrast

All text and interactive elements meet WCAG AA contrast requirements:

#### Light Mode
- **Primary text** (#000000) on background (#f8f8f8): 19.77:1 ✓
- **Secondary text** (#333333) on background (#f8f8f8): 11.90:1 ✓
- **Tertiary text** (#666666) on background (#f8f8f8): 5.41:1 ✓
- **Error color** (#dc2626) on background: 4.55:1 ✓
- **Warning color** (#ad5d06) on background: 4.55:1 ✓
- **Success color** (#2c7b46) on background: 4.91:1 ✓

#### Dark Mode
- **Primary text** (#f2f2f2) on background (#0f0f0f): 17.12:1 ✓
- **Secondary text** (#cfcfcf) on background (#0f0f0f): 12.30:1 ✓
- **Tertiary text** (#999999) on background (#0f0f0f): 6.73:1 ✓

#### Badges and Buttons
- **White on primary purple** (#7c3aed): 5.70:1 ✓
- **White on error red** (#dc2626): 4.83:1 ✓
- **White on warning orange** (#ad5d06): 4.83:1 ✓
- **White on success green** (#2c7b46): 5.21:1 ✓

### 4. Semantic HTML

- Proper use of HTML5 semantic elements:
  - `<header>` for page header
  - `<nav>` for navigation (sidebar)
  - `<main>` for main content (via `id="main-content"`)
  - `<footer>` for page footer
  - `<table>` for tabular data (with proper `<thead>`, `<tbody>`, `<th>`, `<td>`)
- Document language set to English (`lang="en"`)

### 5. Form Accessibility

- All form inputs have associated `<label>` elements
- Checkboxes include text labels
- Required fields are clearly marked
- Form validation errors are announced to screen readers
- Placeholders are used as hints, not as replacements for labels

### 6. Responsive Design

- Mobile-first responsive design
- Touch targets are at least 44x44 pixels
- Text can be resized up to 200% without loss of functionality
- Horizontal scrolling is minimized

### 7. Dynamic Content

- Loading states announce to screen readers via `aria-live="polite"`
- Notifications use NiceGUI's built-in accessible notification system
- Dynamic content updates preserve keyboard focus

## Testing Recommendations

### Keyboard Testing
1. Navigate through the entire site using only Tab, Shift+Tab, Enter, and arrow keys
2. Verify all interactive elements are reachable
3. Ensure focus indicators are clearly visible
4. Test dialog opening/closing with keyboard

### Screen Reader Testing
Test with:
- **NVDA** (Windows, free)
- **JAWS** (Windows, commercial)
- **VoiceOver** (macOS/iOS, built-in)
- **TalkBack** (Android, built-in)

### Color Contrast Testing
Tools:
- **axe DevTools** (browser extension)
- **WAVE** (browser extension)
- **Lighthouse** (Chrome DevTools)

### Automated Testing
- Run Lighthouse accessibility audit
- Use axe accessibility checker
- Validate HTML with W3C validator

## Known Limitations

- Third-party components (Quasar, NiceGUI) may have their own accessibility considerations
- Some dynamic content may require additional ARIA attributes as features evolve
- External integrations (Discord, RaceTime.gg) accessibility depends on their implementations

## Future Improvements

- [ ] Add keyboard shortcuts documentation
- [ ] Implement reduced motion preferences
- [ ] Add high contrast mode toggle
- [ ] Provide text alternatives for any future video/audio content
- [ ] Implement comprehensive end-to-end accessibility testing in CI/CD

## Resources

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [MDN Accessibility Guide](https://developer.mozilla.org/en-US/docs/Web/Accessibility)
- [A11y Project Checklist](https://www.a11yproject.com/checklist/)
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)

## Contact

For accessibility issues or suggestions, please open an issue on GitHub with the "accessibility" label.

---

**Last Updated**: November 7, 2024
