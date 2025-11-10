from nicegui import ui


class Footer:
    """Reusable footer component for the application."""

    @staticmethod
    def render() -> None:
        """Render the footer content."""
        with ui.element("footer").classes("footer"):
            # Copyright and branding
            with ui.row().classes("footer-row"):
                ui.label("© 2025 Thomas Prescott | All rights reserved.")
                ui.label("Powered by NiceGUI & FastAPI").classes("footer-powered")

            # Footer links
            with ui.row().classes("footer-links"):
                ui.link("API Documentation", "/docs").classes("footer-link")
                ui.label("•").classes("footer-separator")
                ui.link(
                    "GitHub Repository",
                    "https://github.com/tcprescott/sahabot2",
                    new_tab=True,
                ).classes("footer-link")
                ui.label("•").classes("footer-separator")
                ui.link("Privacy Policy", "/privacy").classes("footer-link")
                ui.label("•").classes("footer-separator")
                ui.link("RaceTime.gg", "https://racetime.gg", new_tab=True).classes(
                    "footer-link"
                )
