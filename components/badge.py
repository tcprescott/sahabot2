"""
Badge component for SahaBot2.

Provides reusable badge UI elements with consistent styling for status,
permissions, visibility, and custom badges.
"""

from nicegui import ui
from models.user import Permission


class Badge:
    """
    Reusable badge component with standardized styling.

    Provides consistent badge rendering for common use cases like status indicators,
    permission levels, visibility states, and custom badges.
    """

    @staticmethod
    def status(is_active: bool, active_text: str = "Active", inactive_text: str = "Inactive"):
        """
        Render an active/inactive status badge.

        Args:
            is_active: Whether the item is active
            active_text: Text to display when active (default: "Active")
            inactive_text: Text to display when inactive (default: "Inactive")

        Returns:
            The badge element

        Example:
            Badge.status(user.is_active)
            Badge.status(tournament.is_active, "Open", "Closed")
        """
        badge_class = 'badge-success' if is_active else 'badge-danger'
        text = active_text if is_active else inactive_text

        with ui.element('span').classes(f'badge {badge_class}'):
            ui.label(text)

    @staticmethod
    def permission(permission: Permission):
        """
        Render a permission level badge.

        Args:
            permission: Permission level enum value

        Returns:
            The badge element

        Example:
            Badge.permission(user.permission)
        """
        badge_class_map = {
            Permission.SUPERADMIN: 'badge-danger',
            Permission.ADMIN: 'badge-admin',
            Permission.MODERATOR: 'badge-moderator',
            Permission.USER: 'badge-user',
        }

        badge_class = badge_class_map.get(permission, 'badge')

        with ui.element('span').classes(f'badge {badge_class}'):
            ui.label(permission.name)

    @staticmethod
    def visibility(is_public: bool, public_text: str = "Public", private_text: str = "Private"):
        """
        Render a public/private visibility badge.

        Args:
            is_public: Whether the item is public
            public_text: Text to display when public (default: "Public")
            private_text: Text to display when private (default: "Private")

        Returns:
            The badge element

        Example:
            Badge.visibility(preset.is_public)
            Badge.visibility(namespace.is_public, "Shared", "Personal")
        """
        badge_class = 'badge-success' if is_public else 'badge-warning'
        text = public_text if is_public else private_text

        with ui.element('span').classes(f'badge {badge_class}'):
            ui.label(text)

    @staticmethod
    def custom(text: str, variant: str = "default"):
        """
        Render a custom badge with specified text and color variant.

        Args:
            text: Badge text content
            variant: Color variant - one of: success, danger, warning, info,
                    primary, secondary, admin, moderator, user, or default

        Returns:
            The badge element

        Example:
            Badge.custom("Verified", "success")
            Badge.custom("Pending", "warning")
            Badge.custom("Expired", "danger")
        """
        badge_class = f'badge-{variant}' if variant != "default" else 'badge'

        with ui.element('span').classes(f'badge {badge_class}'):
            ui.label(text)

    @staticmethod
    def race_status(status: str):
        """
        Render a race status badge with appropriate styling.

        Args:
            status: Race status (finished, in_progress, pending, forfeit, disqualified)

        Returns:
            The badge element

        Example:
            Badge.race_status(race.status)
        """
        status_badge_map = {
            'finished': 'badge-success',
            'in_progress': 'badge-info',
            'pending': 'badge-warning',
            'forfeit': 'badge-danger',
            'disqualified': 'badge-danger',
        }

        badge_class = status_badge_map.get(status, 'badge')
        display_text = status.replace('_', ' ').title()

        with ui.element('span').classes(f'badge {badge_class}'):
            ui.label(display_text)

    @staticmethod
    def enabled(is_enabled: bool, enabled_text: str = "Enabled", disabled_text: str = "Disabled"):
        """
        Render an enabled/disabled badge.

        Args:
            is_enabled: Whether the item is enabled
            enabled_text: Text to display when enabled (default: "Enabled")
            disabled_text: Text to display when disabled (default: "Disabled")

        Returns:
            The badge element

        Example:
            Badge.enabled(command.is_enabled)
        """
        badge_class = 'badge-success' if is_enabled else 'badge-warning'
        text = enabled_text if is_enabled else disabled_text

        with ui.element('span').classes(f'badge {badge_class}'):
            ui.label(text)

    @staticmethod
    def count(count: int, label: str = "", variant: str = "info"):
        """
        Render a count badge (e.g., for notifications, items).

        Args:
            count: Number to display
            label: Optional label suffix (e.g., "items", "new")
            variant: Color variant (default: "info")

        Returns:
            The badge element

        Example:
            Badge.count(5, "new")
            Badge.count(users_count, "users")
        """
        text = str(count)
        if label:
            text += f" {label}"

        badge_class = f'badge-{variant}'

        with ui.element('span').classes(f'badge {badge_class}'):
            ui.label(text)

    @staticmethod
    def placeholder(is_placeholder: bool):
        """
        Render a placeholder user indicator badge.

        Args:
            is_placeholder: Whether the user is a placeholder user

        Returns:
            The badge element or None if not a placeholder

        Example:
            Badge.placeholder(user.is_placeholder)
        """
        if is_placeholder:
            with ui.element('span').classes('badge badge-warning'):
                ui.label('Placeholder')
