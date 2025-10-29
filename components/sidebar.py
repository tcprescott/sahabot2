"""
Sidebar component for SahaBot2.

This module provides a responsive sidebar navigation component that can be used
with tabbed interfaces. The sidebar supports collapsed/expanded states and works
seamlessly on both mobile and desktop devices.
"""

from nicegui import app, ui
from typing import Optional


class Sidebar:
    """
    Responsive sidebar component for tab navigation.
    
    Provides an overlay sidebar with toggle functionality, supporting both
    icon-only (collapsed) and full-label (expanded) modes.
    """
    
    def __init__(self, tabs: list, panels: Optional[ui.tabs] = None):
        """
        Initialize the sidebar component.
        
        Args:
            tabs: List of tab dictionaries with 'label' and optional 'icon'
            panels: Reference to the ui.tabs component to control tab selection
        """
        self.tabs = tabs
        self.panels = panels
        self.collapsed: bool = bool(app.storage.user.get('sidebar_collapsed', False))
        self._sidebar_element = None
        self._content_element = None
        self._backdrop_element = None
    
    def _toggle_drawer(self) -> None:
        """Toggle the sidebar expansion (icons-only vs full labels)."""
        self.collapsed = not self.collapsed
        app.storage.user['sidebar_collapsed'] = self.collapsed
        
        # Update CSS classes dynamically without page reload
        if self._sidebar_element and self._content_element:
            # Update sidebar classes
            sidebar_classes = 'sidebar sidebar-overlay' + (' collapsed' if self.collapsed else '')
            self._sidebar_element.classes(replace=sidebar_classes)
            
            # Update content classes  
            content_classes = 'full-width content-with-sidebar' + (' content-sidebar-collapsed' if self.collapsed else ' content-sidebar-expanded')
            self._content_element.classes(replace=content_classes)
            
            # Toggle backdrop on mobile
            if self._backdrop_element:
                backdrop_classes = 'sidebar-backdrop' + ('' if self.collapsed else ' active')
                self._backdrop_element.classes(replace=backdrop_classes)
            
            # Clear and re-render sidebar buttons
            self._sidebar_element.clear()
            with self._sidebar_element:
                self._render_buttons()
    
    def _on_select_tab(self, label: str) -> None:
        """
        Select a tab in the panels.
        
        Args:
            label: Label of the tab to select
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info("_on_select_tab called with label='%s', panels=%s", label, self.panels)
        
        if self.panels is not None:
            try:
                logger.info("Setting panels.value to '%s'", label)
                self.panels.value = label
                logger.info("Successfully set panels.value to '%s'", label)
            except Exception as e:
                # If panels reference is stale or broken, log but don't crash
                logger.error("Failed to select tab '%s': %s", label, e)
                # Try to recover by not doing anything - user can click again
        else:
            logger.warning("Cannot select tab '%s' - panels is None!", label)
    
    def _render_buttons(self) -> None:
        """Render sidebar buttons based on collapsed state."""
        # Menu button to toggle expansion
        menu_icon = 'menu_open' if not self.collapsed else 'menu'
        ui.button(
            icon=menu_icon,
            on_click=self._toggle_drawer
        ).props('flat').classes('q-mb-sm full-width justify-between')\
             .tooltip('Toggle Menu')
        
        # Tab buttons - use explicit function creation to avoid closure issues
        def make_click_handler(label: str):
            """Create a click handler for a specific tab label."""
            def handler():
                self._on_select_tab(label)
            return handler
        
        for tab in self.tabs:
            click_handler = make_click_handler(tab['label'])
            
            if self.collapsed:
                # Icons only - stretch justified
                ui.button(
                    icon=tab.get('icon') or 'chevron_right',
                    on_click=click_handler
                ).props('flat').classes('q-mb-sm full-width justify-between')\
                 .tooltip(tab['label'])
            else:
                # Full buttons with labels
                ui.button(
                    tab['label'],
                    icon=tab.get('icon') or 'chevron_right',
                    on_click=click_handler
                ).props('flat').classes('sidebar-item full-width justify-between')
    
    def render(self, content_container: ui.column) -> tuple[ui.element, ui.element]:
        """
        Render the sidebar and backdrop elements.
        
        Args:
            content_container: The content area column to apply padding classes to
        
        Returns:
            tuple: (sidebar_element, backdrop_element) for reference
        """
        # Backdrop for mobile (dims content when menu is open)
        backdrop_classes = 'sidebar-backdrop' + ('' if self.collapsed else ' active')
        self._backdrop_element = ui.element('div').classes(backdrop_classes)
        self._backdrop_element.on('click', self._toggle_drawer)
        
        # Sidebar overlay (positioned absolutely)
        sidebar_classes = 'sidebar sidebar-overlay' + (' collapsed' if self.collapsed else '')
        self._sidebar_element = ui.element('div').classes(sidebar_classes)
        
        with self._sidebar_element:
            self._render_buttons()
        
        # Store reference to content container and apply classes
        self._content_element = content_container
        content_classes = 'full-width content-with-sidebar' + (' content-sidebar-collapsed' if self.collapsed else ' content-sidebar-expanded')
        self._content_element.classes(content_classes)
        
        return self._sidebar_element, self._backdrop_element
