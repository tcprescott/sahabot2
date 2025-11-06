"""
StatCard component for SahaBot2.

Provides reusable statistic display components with consistent styling for
metrics, dashboards, and summary views.
"""

from nicegui import ui
from typing import Optional, List, Dict, Any


class StatCard:
    """
    Reusable statistic card component with standardized styling.

    Displays a single statistic with a value and label, optionally with
    custom styling and colors.
    """

    @staticmethod
    def render(
        value: str,
        label: str,
        color: Optional[str] = None,
        icon: Optional[str] = None,
        classes: str = ""
    ):
        """
        Render a single statistic card.

        Args:
            value: The statistic value to display (e.g., "42", "85.5%")
            label: Label describing the statistic
            color: Optional color class (primary, success, danger, warning, info, secondary)
            icon: Optional Material icon name to display above value
            classes: Additional CSS classes to apply

        Example:
            StatCard.render("42", "Active Users", color="success")
            StatCard.render("15", "Pending", color="warning", icon="hourglass_empty")
        """
        card_classes = f'stat-card {classes}'
        value_classes = 'stat-value'
        if color:
            value_classes += f' text-{color}'

        with ui.element('div').classes(card_classes):
            if icon:
                ui.icon(icon).classes('text-2xl mb-2')
            ui.label(value).classes(value_classes)
            ui.label(label).classes('stat-label')

    @staticmethod
    def simple(value: str, label: str, color: Optional[str] = None):
        """
        Render a simple inline statistic (no card wrapper).

        Args:
            value: The statistic value to display
            label: Label describing the statistic
            color: Optional color class

        Example:
            StatCard.simple("50", "Participants", color="primary")
        """
        value_classes = 'stat-value text-lg'
        if color:
            value_classes += f' text-{color}'

        with ui.element('div').classes('text-center'):
            ui.label(value).classes(value_classes)
            ui.label(label).classes('stat-label text-xs')


class StatGrid:
    """
    Grid container for displaying multiple statistics in a responsive layout.

    Automatically arranges stat cards in a responsive grid that adapts to
    screen size.
    """

    @staticmethod
    def render(stats: List[Dict[str, Any]], columns: int = 4):
        """
        Render a responsive grid of statistic cards.

        Args:
            stats: List of stat dictionaries with keys:
                - value: str - The statistic value
                - label: str - The statistic label
                - color: Optional[str] - Color variant
                - icon: Optional[str] - Material icon name
            columns: Number of columns on desktop (2, 3, or 4; default: 4)

        Example:
            StatGrid.render([
                {'value': '42', 'label': 'Active Users', 'color': 'success'},
                {'value': '15', 'label': 'Pending', 'color': 'warning'},
                {'value': '128', 'label': 'Total', 'color': 'primary'},
            ], columns=3)
        """
        grid_class_map = {
            2: 'grid grid-cols-1 md:grid-cols-2 gap-md',
            3: 'grid grid-cols-1 md:grid-cols-3 gap-md',
            4: 'grid grid-cols-2 md:grid-cols-4 gap-md',
        }

        grid_classes = grid_class_map.get(columns, grid_class_map[4])

        with ui.element('div').classes(grid_classes):
            for stat in stats:
                StatCard.render(
                    value=stat.get('value', '0'),
                    label=stat.get('label', ''),
                    color=stat.get('color'),
                    icon=stat.get('icon'),
                    classes=stat.get('classes', '')
                )

    @staticmethod
    def simple_row(stats: List[Dict[str, Any]]):
        """
        Render a simple row of inline statistics (no card wrappers).

        Args:
            stats: List of stat dictionaries with keys:
                - value: str - The statistic value
                - label: str - The statistic label
                - color: Optional[str] - Color variant

        Example:
            StatGrid.simple_row([
                {'value': '50', 'label': 'Participants'},
                {'value': '3', 'label': 'Runs/Pool'},
            ])
        """
        with ui.element('div').classes('flex gap-md'):
            for stat in stats:
                StatCard.simple(
                    value=stat.get('value', '0'),
                    label=stat.get('label', ''),
                    color=stat.get('color')
                )


class StatsSection:
    """
    Complete statistics section with title and grid of stats.

    Provides a card-based section for displaying multiple related statistics
    with a title.
    """

    @staticmethod
    def render(
        title: str,
        stats: List[Dict[str, Any]],
        columns: int = 4,
        description: Optional[str] = None
    ):
        """
        Render a complete statistics section with title and stats grid.

        Args:
            title: Section title
            stats: List of stat dictionaries (see StatGrid.render)
            columns: Number of columns (default: 4)
            description: Optional description text below title

        Example:
            StatsSection.render(
                title="Tournament Statistics",
                description="Overview of tournament participation",
                stats=[
                    {'value': '42', 'label': 'Participants', 'color': 'success'},
                    {'value': '128', 'label': 'Races Complete', 'color': 'info'},
                ],
                columns=2
            )
        """
        from components.card import Card

        with Card.create(title=title):
            if description:
                ui.label(description).classes('text-secondary mb-4')
            StatGrid.render(stats, columns=columns)
