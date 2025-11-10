"""
Privacy Policy page.

Displays the application's privacy policy and data handling practices.
"""

from nicegui import ui
from components.base_page import BasePage


def register():
    """Register privacy policy page routes."""

    @ui.page("/privacy")
    async def privacy_page():
        """Display privacy policy page."""
        base = BasePage.simple_page(title="Privacy Policy")

        async def content(page: BasePage):
            """Render privacy policy content."""
            # Render custom sidebar with just Home link
            page._render_sidebar(
                [
                    {
                        "label": "Home",
                        "icon": "home",
                        "action": lambda: ui.navigate.to("/"),
                    }
                ]
            )

            with ui.element("div").classes("card"):
                with ui.element("div").classes("card-header"):
                    ui.label("Privacy Policy").classes("text-2xl text-bold")

                with ui.element("div").classes("card-body"):
                    ui.label("Last Updated: November 6, 2025").classes(
                        "text-sm text-gray-600 mb-4"
                    )

                    ui.separator()

                    # Introduction
                    ui.label("Introduction").classes("text-xl text-bold mt-4 mb-2")
                    ui.label(
                        'SahaBot2 ("we", "our", or "us") is committed to protecting your privacy. '
                        "This Privacy Policy explains how we collect, use, and safeguard your information "
                        "when you use our application."
                    ).classes("mb-4")

                    # Data Collection
                    ui.label("Information We Collect").classes(
                        "text-xl text-bold mt-4 mb-2"
                    )
                    ui.label(
                        "We collect the following information through Discord OAuth2:"
                    ).classes("mb-2")
                    with ui.element("ul").classes("list-disc ml-6 mb-4"):
                        with ui.element("li"):
                            ui.label("Discord user ID (unique identifier)")
                        with ui.element("li"):
                            ui.label("Discord username and discriminator")
                        with ui.element("li"):
                            ui.label("Discord avatar")
                        with ui.element("li"):
                            ui.label("Discord email address")

                    # Data Usage
                    ui.label("How We Use Your Information").classes(
                        "text-xl text-bold mt-4 mb-2"
                    )
                    ui.label("We use your information to:").classes("mb-2")
                    with ui.element("ul").classes("list-disc ml-6 mb-4"):
                        with ui.element("li"):
                            ui.label(
                                "Authenticate and identify you within the application"
                            )
                        with ui.element("li"):
                            ui.label("Display your Discord profile information")
                        with ui.element("li"):
                            ui.label(
                                "Manage your organization memberships and permissions"
                            )
                        with ui.element("li"):
                            ui.label("Track and audit actions for security purposes")
                        with ui.element("li"):
                            ui.label(
                                "Provide tournament and randomizer preset functionality"
                            )

                    # Data Storage
                    ui.label("Data Storage and Security").classes(
                        "text-xl text-bold mt-4 mb-2"
                    )
                    ui.label(
                        "Your information is stored securely in our database. We implement industry-standard "
                        "security measures to protect your data from unauthorized access, alteration, or disclosure. "
                        "Your email address is only visible to SUPERADMIN users for administrative purposes."
                    ).classes("mb-4")

                    # Third-Party Services
                    ui.label("Third-Party Services").classes(
                        "text-xl text-bold mt-4 mb-2"
                    )
                    ui.label(
                        "We integrate with the following third-party services:"
                    ).classes("mb-2")
                    with ui.element("ul").classes("list-disc ml-6 mb-4"):
                        with ui.element("li"):
                            ui.label(
                                "Discord - for authentication and user identification"
                            )
                        with ui.element("li"):
                            ui.label(
                                "RaceTime.gg - for racing functionality (optional)"
                            )
                        with ui.element("li"):
                            ui.label(
                                "Sentry.io - for error tracking and performance monitoring. Sentry may collect "
                                "error information, performance data, and user context when errors occur. "
                                "This data is used solely for debugging and improving application reliability. "
                            )
                            with ui.link(
                                "Learn more about Sentry's privacy practices",
                                "https://sentry.io/privacy/",
                                new_tab=True,
                            ).classes("text-blue-600 hover:text-blue-800"):
                                pass

                    # User Rights
                    ui.label("Your Rights").classes("text-xl text-bold mt-4 mb-2")
                    ui.label("You have the right to:").classes("mb-2")
                    with ui.element("ul").classes("list-disc ml-6 mb-4"):
                        with ui.element("li"):
                            ui.label("Access your personal information")
                        with ui.element("li"):
                            ui.label("Request correction of inaccurate data")
                        with ui.element("li"):
                            ui.label(
                                "Request deletion of your account and associated data"
                            )
                        with ui.element("li"):
                            ui.label(
                                "Opt-out of certain data collection (by not using the service)"
                            )

                    # Data Retention
                    ui.label("Data Retention").classes("text-xl text-bold mt-4 mb-2")
                    ui.label(
                        "We retain your information for as long as your account is active or as needed to provide "
                        "services. Audit logs and certain historical data may be retained for compliance and "
                        "security purposes even after account deletion."
                    ).classes("mb-4")

                    # Changes to Policy
                    ui.label("Changes to This Policy").classes(
                        "text-xl text-bold mt-4 mb-2"
                    )
                    ui.label(
                        "We may update this Privacy Policy from time to time. We will notify users of any material "
                        'changes by updating the "Last Updated" date at the top of this page.'
                    ).classes("mb-4")

                    # Contact
                    ui.label("Contact Us").classes("text-xl text-bold mt-4 mb-2")
                    ui.label(
                        "If you have questions or concerns about this Privacy Policy, please contact us through "
                        "our GitHub repository or Discord server."
                    ).classes("mb-4")

        await base.render(content)
