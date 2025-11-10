"""
EmptyState component for SahaBot2.

Provides reusable empty state UI elements with consistent styling for
displaying when lists, tables, or content areas have no data.
"""

from nicegui import ui
from typing import Optional, Callable


class EmptyState:
    """
    Reusable empty state component with standardized styling.

    Provides consistent empty state rendering with icons, messages, and
    optional action buttons.
    """

    @staticmethod
    def render(
        icon: str,
        title: str,
        message: Optional[str] = None,
        action_text: Optional[str] = None,
        action_callback: Optional[Callable] = None,
        in_card: bool = False,
        classes: str = "",
    ):
        """
        Render an empty state with icon, title, message, and optional action.

        Args:
            icon: Material icon name (e.g., 'people', 'folder_open')
            title: Main title text
            message: Optional secondary message text
            action_text: Optional action button text
            action_callback: Optional callback for action button
            in_card: If True, wraps in a card with card-body styling
            classes: Additional CSS classes to apply to container

        Example:
            EmptyState.render(
                icon='people',
                title='No members yet',
                message='Add members to get started',
                action_text='Invite Member',
                action_callback=self._open_invite_dialog,
                in_card=True
            )
        """
        container_classes = f"text-center py-8 {classes}"

        def render_content():
            ui.icon(icon).classes("text-secondary icon-large").props(
                'aria-hidden="true"'
            )
            ui.label(title).classes("text-secondary text-lg mt-4")
            if message:
                ui.label(message).classes("text-secondary mt-2")
            if action_text and action_callback:
                ui.button(action_text, on_click=action_callback).classes(
                    "btn btn-primary mt-4"
                )

        if in_card:
            with ui.element("div").classes("card"):
                with ui.element("div").classes("card-body text-center"):
                    render_content()
        else:
            with ui.element("div").classes(container_classes):
                render_content()

    @staticmethod
    def no_results(
        title: str = "No results found",
        message: str = "Try adjusting your search or filters",
        in_card: bool = True,
    ):
        """
        Render a standard "no results" empty state for filtered lists.

        Args:
            title: Title text (default: "No results found")
            message: Message text (default: "Try adjusting your search or filters")
            in_card: If True, wraps in a card (default: True)

        Example:
            if not filtered_items:
                EmptyState.no_results()
        """
        EmptyState.render(
            icon="search_off", title=title, message=message, in_card=in_card
        )

    @staticmethod
    def no_items(
        item_name: str,
        message: Optional[str] = None,
        icon: str = "inbox",
        action_text: Optional[str] = None,
        action_callback: Optional[Callable] = None,
        in_card: bool = True,
    ):
        """
        Render a standard "no items" empty state for empty lists.

        Args:
            item_name: Name of items (e.g., "users", "tournaments", "races")
            message: Optional custom message (default: "Click 'Add' to create one")
            icon: Material icon (default: 'inbox')
            action_text: Optional action button text (e.g., "Add User")
            action_callback: Optional callback for action button
            in_card: If True, wraps in a card (default: True)

        Example:
            if not users:
                EmptyState.no_items(
                    item_name='users',
                    action_text='Add User',
                    action_callback=self._open_add_dialog
                )
        """
        title = f"No {item_name} found"
        if message is None:
            message = (
                "Click 'Add' to create one"
                if not action_text
                else f"Click '{action_text}' to get started"
            )

        EmptyState.render(
            icon=icon,
            title=title,
            message=message,
            action_text=action_text,
            action_callback=action_callback,
            in_card=in_card,
        )

    @staticmethod
    def loading(message: str = "Loading...", in_card: bool = False):
        """
        Render a loading state with spinner.

        Args:
            message: Loading message text (default: "Loading...")
            in_card: If True, wraps in a card (default: False)

        Example:
            EmptyState.loading("Loading users...")
        """
        container_classes = "text-center py-8"

        def render_content():
            with ui.element("div").props('role="status" aria-live="polite"'):
                ui.spinner(size="lg")
                ui.label(message).classes("text-secondary mt-4")

        if in_card:
            with ui.element("div").classes("card"):
                with ui.element("div").classes("card-body text-center"):
                    render_content()
        else:
            with ui.element("div").classes(container_classes):
                render_content()

    @staticmethod
    def error(
        title: str = "Error loading data",
        message: Optional[str] = None,
        retry_callback: Optional[Callable] = None,
        in_card: bool = True,
    ):
        """
        Render an error state with optional retry button.

        Args:
            title: Error title (default: "Error loading data")
            message: Optional error message
            retry_callback: Optional callback for retry button
            in_card: If True, wraps in a card (default: True)

        Example:
            try:
                data = await load_data()
            except Exception:
                EmptyState.error(
                    message="Failed to load users",
                    retry_callback=self._refresh
                )
        """
        action_text = "Retry" if retry_callback else None

        EmptyState.render(
            icon="error",
            title=title,
            message=message,
            action_text=action_text,
            action_callback=retry_callback,
            in_card=in_card,
        )

    @staticmethod
    def hidden(
        title: str = "Content Hidden",
        message: str = "You do not have permission to view this content",
        in_card: bool = True,
    ):
        """
        Render a hidden/restricted content state.

        Args:
            title: Title text (default: "Content Hidden")
            message: Message text
            in_card: If True, wraps in a card (default: True)

        Example:
            if not can_view:
                EmptyState.hidden()
        """
        EmptyState.render(
            icon="visibility_off", title=title, message=message, in_card=in_card
        )

    @staticmethod
    def coming_soon(
        feature_name: str, message: Optional[str] = None, in_card: bool = True
    ):
        """
        Render a "coming soon" placeholder state.

        Args:
            feature_name: Name of the upcoming feature
            message: Optional additional message
            in_card: If True, wraps in a card (default: True)

        Example:
            EmptyState.coming_soon("Advanced Analytics", "This feature is under development")
        """
        title = f"{feature_name} - Coming Soon"
        if message is None:
            message = "This feature is currently under development"

        EmptyState.render(
            icon="schedule", title=title, message=message, in_card=in_card
        )
