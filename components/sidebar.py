from __future__ import annotations
from typing import Callable, Any
from nicegui import ui


class Sidebar:
    """Reusable sidebar component with backdrop and collapsible sections.

    Usage:
        sidebar = Sidebar(toggle_callback)
        container, backdrop = sidebar.render(items)
    """

    def __init__(self, toggle_callback: Callable[[], None]):
        """Initialize the sidebar.

        Args:
            toggle_callback: Callback to toggle open/closed state (typically BasePage._toggle_sidebar)
        """
        self.toggle_callback = toggle_callback
        self._container = None
        self._backdrop = None

    def render(self, items: list[dict]) -> tuple[Any, Any]:
        """Render the sidebar and its backdrop.

        Args:
            items: List of item dicts. Supports keys: label, icon, action, children, type='separator'

        Returns:
            Tuple of (sidebar_container, backdrop_element)
        """
        # Backdrop for mobile (hidden on desktop via CSS) - start hidden by default
        self._backdrop = (
            ui.element("div")
            .classes("sidebar-backdrop hidden")
            .props('role="presentation"')
        )
        self._backdrop.on("click", self.toggle_callback)

        # Sidebar container - starts closed on mobile, CSS controls desktop state
        self._container = (
            ui.element("div")
            .classes("sidebar-flyout sidebar-closed")
            .props('role="navigation" aria-label="Main navigation"')
        )
        with self._container:
            # Sidebar header
            with ui.element("div").classes("sidebar-header"):
                ui.label("Navigation").classes("sidebar-title")
                # Close button (hidden on desktop via CSS)
                ui.button(icon="close", on_click=self.toggle_callback).props(
                    'flat round dense aria-label="Close navigation menu"'
                ).classes("sidebar-close-btn")

            # Sidebar items
            with ui.element("div").classes("sidebar-items"):
                for item in items or []:
                    self._render_item(item)

        return self._container, self._backdrop

    def _render_item(self, item: dict) -> None:
        """Render a single item, a collapsible section, or a separator."""
        # Separator support
        if item.get("type") == "separator":
            ui.element("div").classes("sidebar-separator")
            return

        # Collapsible section
        children = item.get("children") if isinstance(item, dict) else None
        if children and isinstance(children, list):
            exp = ui.expansion(
                text=item.get("label", ""), icon=item.get("icon", None)
            ).classes("sidebar-section")
            with exp:
                for child in children:
                    self._render_item(child)
            return

        # Leaf navigation item
        def handle_click():
            action = item.get("action")
            if callable(action):
                action()
            # Close sidebar after clicking (useful on mobile)
            self.toggle_callback()

        with ui.element("div").classes("sidebar-item").on("click", handle_click):
            icon = item.get("icon")
            if icon:
                ui.icon(icon).classes("sidebar-item-icon")
            ui.label(item.get("label", "")).classes("sidebar-item-label")
