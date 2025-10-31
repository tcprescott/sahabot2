"""
Home page for SahaBot2.

This module provides the main landing page.
"""

from nicegui import ui
from components import BasePage
from views.home import OverviewView, WelcomeView


def register():
    """Register home page routes."""

    @ui.page('/')
    async def home_page():
        """Main home page."""
        base = BasePage.simple_page(title="SahaBot2 - Home")

        async def content(page: BasePage):
            """Render home page content."""
            if page.user:
                # Authenticated user - show overview
                await OverviewView.render(page.user)
            else:
                # Guest - show welcome
                await WelcomeView.render()
        
        await base.render(content)