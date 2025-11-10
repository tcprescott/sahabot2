from nicegui import ui
from components.user_menu import UserMenu


class Header:
    """Reusable header component for the application."""

    def __init__(self, user, toggle_sidebar):
        """Initialize header with user and sidebar toggle callback."""
        self.user = user
        self.toggle_sidebar = toggle_sidebar

    def render(self) -> None:
        """Render the header bar with logo, app name, and user menu."""
        with ui.header().classes("header-bar"):
            with ui.row().classes("header-container"):
                # Left side: Hamburger menu, logo and app name
                with ui.row().classes("header-left gap-md"):
                    ui.button(icon="menu", on_click=self.toggle_sidebar).props(
                        'flat round aria-label="Open navigation menu"'
                    ).classes("header-hamburger")
                    with ui.link(target="/").classes("header-brand-link").props(
                        'aria-label="Go to home page"'
                    ):
                        ui.icon("smart_toy", size="lg").classes("header-logo")
                        ui.label("SahasrahBot").classes("header-brand")
                # Right side: User info and menu
                with ui.row().classes("header-right gap-md"):
                    user_menu = UserMenu(self.user)
                    user_menu.render()
