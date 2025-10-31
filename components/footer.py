from nicegui import ui

class Footer:
    """Reusable footer component for the application."""
    @staticmethod
    def render() -> None:
        """Render the footer content."""
        with ui.element('footer').classes('footer'):
            ui.label('© 2025 Thomas Prescott | All rights reserved.')
            ui.label('Powered by NiceGUI & FastAPI').classes('footer-powered')
