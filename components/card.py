"""
Card component for SahaBot2.

Provides reusable card UI elements with consistent styling.
"""

from nicegui import ui
from typing import Optional, Callable


class Card:
    """
    A styled card component with header and body sections.

    This component provides a consistent card design across the application,
    with support for headers, body content, and optional actions.
    """

    @staticmethod
    def create(
        title: Optional[str] = None,
        content_fn: Optional[Callable] = None,
        classes: str = "",
    ):
        """
        Create a card with optional title and content.

        Args:
            title: Optional card title
            content_fn: Callable that renders the card body content
            classes: Additional CSS classes to apply to the card

        Returns:
            The card element context

        Example:
            with Card.create(title="My Card"):
                ui.label("Card content goes here")
        """
        card_classes = f"card bg-dynamic-surface {classes}"
        card_element = ui.element("div").classes(card_classes)

        with card_element:
            if title:
                with ui.element("div").classes("card-header"):
                    ui.label(title).classes("text-dynamic-primary")

            with ui.element("div").classes("card-body"):
                if content_fn:
                    content_fn()

        return card_element

    @staticmethod
    def simple(title: str, description: str, classes: str = ""):
        """
        Create a simple card with title and description.

        Args:
            title: Card title
            description: Card description text
            classes: Additional CSS classes

        Example:
            Card.simple("Welcome", "This is the home page")
        """
        with Card.create(title=title, classes=classes):
            ui.label(description).classes("text-dynamic-secondary")

    @staticmethod
    def info(title: str, items: list[tuple[str, str]], classes: str = ""):
        """
        Create an info card with key-value pairs.

        Args:
            title: Card title
            items: List of (label, value) tuples
            classes: Additional CSS classes

        Example:
            Card.info("User Info", [
                ("Name", "John Doe"),
                ("Email", "john@example.com")
            ])
        """
        with Card.create(title=title, classes=classes):
            for label, value in items:
                with ui.row().classes("full-width items-center gap-md"):
                    ui.label(f"{label}:").classes("text-dynamic-secondary font-bold")
                    ui.label(value).classes("text-dynamic-primary")

    @staticmethod
    def action(
        title: str,
        description: str,
        button_text: str,
        on_click: Callable,
        classes: str = "",
    ):
        """
        Create an action card with a button.

        Args:
            title: Card title
            description: Card description
            button_text: Text for the action button
            on_click: Callback for button click
            classes: Additional CSS classes

        Example:
            Card.action(
                "Get Started",
                "Click below to begin",
                "Start Now",
                lambda: print("Started!")
            )
        """
        with Card.create(title=title, classes=classes):
            ui.label(description).classes("text-dynamic-secondary mb-2")
            ui.button(button_text, on_click=on_click).classes("btn btn-primary")
