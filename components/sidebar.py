"""
Sidebar component for SahaBot2.

Simple, reliable sidebar navigation for tabbed interfaces.
"""

from nicegui import app, ui
from typing import Optional


class Sidebar:
    """Simple sidebar component for tab navigation."""
    
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
    
    def _toggle_collapsed(self) -> None:
        """Toggle the sidebar collapsed state."""
        self.collapsed = not self.collapsed
        app.storage.user['sidebar_collapsed'] = self.collapsed
        # Force page refresh to apply new state
        ui.navigate.reload()
    
    def _select_tab(self, label: str) -> None:
        """
        Select a tab.
        
        Args:
            label: Label of the tab to select
        """
        if self.panels is not None:
            self.panels.value = label
    
    def render(self, content_container=None) -> None:
        """
        Render the sidebar.
        
        Args:
            content_container: Unused parameter for backwards compatibility
        """
        # Determine sidebar width based on collapsed state
        sidebar_width = '64px' if self.collapsed else '240px'
        
        # Sidebar - full height from top to bottom
        with ui.element('div').style(f'position: fixed; left: 0; top: 0; bottom: 0; width: {sidebar_width}; background: var(--surface-color); overflow-y: auto; transition: width 0.3s ease; z-index: 1000; padding: 1rem 0.5rem; display: flex; flex-direction: column; gap: 0.5rem; border-right: 1px solid var(--q-dark-page);'):
            # Toggle button
            menu_icon = 'menu_open' if not self.collapsed else 'menu'
            ui.button(icon=menu_icon, on_click=self._toggle_collapsed).props('flat dense').classes('full-width')
            
            # Tab buttons
            for tab in self.tabs:
                icon = tab.get('icon', 'chevron_right')
                label = tab['label']
                
                if self.collapsed:
                    # Icon only
                    btn = ui.button(icon=icon, on_click=lambda l=label: self._select_tab(l))
                    btn.props('flat dense').classes('full-width')
                    btn.tooltip(label)
                else:
                    # Icon + label
                    btn = ui.button(label, icon=icon, on_click=lambda l=label: self._select_tab(l))
                    btn.props('flat dense').classes('full-width justify-start')
