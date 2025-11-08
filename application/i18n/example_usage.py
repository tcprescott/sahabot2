"""
Example usage of the i18n translation system.

This file demonstrates how to use translations in various contexts
within the SahaBot2 application.
"""

from nicegui import ui
from application.i18n import translate as _


def example_ui_labels():
    """Example: Using translations in UI labels."""
    with ui.card():
        ui.label(_("Welcome to SahaBot2")).classes('text-xl font-bold')
        ui.label(_("Please select an option below"))


def example_buttons():
    """Example: Using translations in buttons."""
    with ui.row():
        ui.button(_("Save"), on_click=lambda: ui.notify(_("Saved successfully!")))
        ui.button(_("Cancel"), on_click=lambda: ui.notify(_("Cancelled")))
        ui.button(_("Delete"), on_click=lambda: ui.notify(_("Deleted")))


def example_format_strings(username: str, message_count: int):
    """Example: Using translations with format strings."""
    # Simple format
    greeting = _("Hello, {name}!").format(name=username)
    ui.label(greeting)

    # Multiple variables
    status = _("You have {count} new messages").format(count=message_count)
    ui.label(status)

    # Conditional formatting
    if message_count > 0:
        ui.notify(_("New messages available"), type='positive')
    else:
        ui.notify(_("No new messages"), type='info')


def example_notifications():
    """Example: Using translations in notifications."""
    # Success
    ui.notify(_("Operation completed successfully"), type='positive')

    # Error
    ui.notify(_("An error occurred"), type='negative')

    # Warning
    ui.notify(_("Please try again"), type='warning')

    # Info
    ui.notify(_("Loading..."), type='info')


def example_dialog_content():
    """Example: Using translations in dialog content."""
    with ui.dialog() as dialog:
        with ui.card():
            ui.label(_("Confirm Action")).classes('text-xl font-bold')
            ui.label(_("Are you sure you want to proceed?"))

            with ui.row():
                ui.button(_("Confirm"), on_click=dialog.close)
                ui.button(_("Cancel"), on_click=dialog.close)

    return dialog


def example_table_headers():
    """Example: Using translations in table headers."""
    columns = [
        {'name': 'name', 'label': _("Name"), 'field': 'name'},
        {'name': 'email', 'label': _("Email"), 'field': 'email'},
        {'name': 'status', 'label': _("Status"), 'field': 'status'},
        {'name': 'actions', 'label': _("Actions"), 'field': 'actions'},
    ]

    rows = [
        {'name': 'John Doe', 'email': 'john@example.com', 'status': _("Active"), 'actions': '...'},
        {'name': 'Jane Smith', 'email': 'jane@example.com', 'status': _("Active"), 'actions': '...'},
    ]

    ui.table(columns=columns, rows=rows)


def example_form_labels():
    """Example: Using translations in form labels."""
    with ui.card():
        ui.label(_("User Profile")).classes('text-xl font-bold')

        ui.input(
            label=_("Username"),
            placeholder=_("Enter your username")
        )

        ui.input(
            label=_("Email"),
            placeholder=_("Enter your email address")
        )

        ui.select(
            label=_("Language"),
            options=[_("English"), _("Spanish"), _("French")]
        )

        with ui.row():
            ui.button(_("Save"), on_click=lambda: None)
            ui.button(_("Cancel"), on_click=lambda: None)


def example_validation_messages(field_name: str, value: str):
    """Example: Using translations in validation messages."""
    # Required field
    if not value:
        return _("{field} is required").format(field=field_name)

    # Length validation
    if len(value) < 3:
        return _("{field} must be at least {min} characters").format(
            field=field_name,
            min=3
        )

    # Success
    return None


# Example usage in a complete page
async def example_complete_page():
    """Example: Complete page with translations."""
    from components import BasePage

    base = BasePage.authenticated_page(title=_("Dashboard"))

    async def content(page: BasePage):
        """Render page content with translations."""
        with ui.element('div').classes('page-container'):
            # Header
            ui.label(_("Welcome to your dashboard")).classes('text-2xl font-bold mb-4')

            # Stats cards
            with ui.row().classes('gap-md'):
                with ui.card().classes('flex-1'):
                    ui.label(str(42)).classes('text-3xl font-bold')
                    ui.label(_("Active Users")).classes('text-sm')

                with ui.card().classes('flex-1'):
                    ui.label(str(123)).classes('text-3xl font-bold')
                    ui.label(_("Total Items")).classes('text-sm')

            # Action buttons
            with ui.row().classes('gap-md mt-4'):
                ui.button(_("Create New"), icon='add').classes('btn btn-primary')
                ui.button(_("Settings"), icon='settings').classes('btn btn-secondary')

            # Information message
            ui.label(_("Last updated: {time}").format(time="2 hours ago")).classes('text-sm text-secondary mt-4')

    await base.render(content)()
