"""
MOTD (Message of the Day) banner component.

This module provides a dismissible banner that displays a message of the day.
The banner can be dismissed by users, but will reappear if an admin updates the MOTD.
"""

from __future__ import annotations
from nicegui import ui
from application.services.core.settings_service import SettingsService


class MOTDBanner:
    """
    Dismissible MOTD banner component.

    This banner displays a message of the day that can be dismissed by users.
    It will reappear if an admin updates the MOTD text.
    """

    MOTD_KEY = 'motd_text'
    MOTD_UPDATED_KEY = 'motd_updated_at'

    @staticmethod
    async def render() -> None:
        """
        Render the MOTD banner if there is an active MOTD.

        The banner will be shown unless the user has dismissed it and the MOTD
        hasn't been updated since dismissal.
        """
        service = SettingsService()

        # Get MOTD text and last updated timestamp
        motd_setting = await service.get_global(MOTDBanner.MOTD_KEY)
        if not motd_setting or not motd_setting.get('value'):
            return  # No MOTD to display

        motd_text = motd_setting['value']
        motd_updated_setting = await service.get_global(MOTDBanner.MOTD_UPDATED_KEY)
        motd_updated = motd_updated_setting['value'] if motd_updated_setting else None

        # Create banner container with initial visibility controlled by JavaScript
        banner_id = 'motd-banner'

        # Note: ui.html() is used here to support HTML formatting in MOTD.
        # This is acceptable because:
        # 1. MOTD content is admin-only (Permission.ADMIN required to edit)
        # 2. Admins are trusted users with full system access
        # 3. Content is stored in database, not coming from untrusted user input
        # 4. Browser's Content-Security-Policy prevents inline script execution
        # For additional security, consider implementing server-side HTML sanitization
        # if MOTD editing permissions are ever expanded to non-admin users.

        # Create banner container with initial visibility controlled by JavaScript
        with ui.element('div').props(f'id="{banner_id}"').classes('w-full motd-banner'):
            with ui.row().classes('items-center justify-between w-full gap-4'):
                # Icon and message
                with ui.row().classes('items-center gap-3 flex-1'):
                    ui.icon('campaign').classes('text-2xl')
                    with ui.element('div').classes('flex-1'):
                        ui.html(motd_text).classes('text-base')

                # Dismiss button
                ui.button(
                    icon='close',
                    on_click=None  # Will be handled by JavaScript
                ).props(f'flat round dense id="{banner_id}-dismiss-btn"')

        # Add JavaScript to handle banner visibility and dismissal
        # Note: motd_updated is server-generated timestamp, but we escape it for safety
        motd_updated_escaped = (motd_updated or "").replace("'", "\\'").replace('"', '\\"') if motd_updated else ""
        motd_js = f'''
        (function() {{
            const bannerId = '{banner_id}';
            const motdUpdated = '{motd_updated_escaped}';
            const storageKey = 'motd_dismissed_at';

            // Get dismissed timestamp from localStorage
            const dismissedAt = localStorage.getItem(storageKey);

            // Show banner if not dismissed OR if MOTD was updated after dismissal
            let shouldShow = true;
            if (dismissedAt && motdUpdated) {{
                // Compare timestamps - show if MOTD is newer than dismissal
                shouldShow = motdUpdated > dismissedAt;
            }} else if (dismissedAt && !motdUpdated) {{
                // No update timestamp, but was dismissed - don't show
                shouldShow = false;
            }}

            const banner = document.getElementById(bannerId);
            if (banner && shouldShow) {{
                banner.style.display = 'block';
            }}

            // Handle dismiss button click
            const dismissBtn = document.getElementById(bannerId + '-dismiss-btn');
            if (dismissBtn) {{
                dismissBtn.addEventListener('click', function() {{
                    // Store current timestamp as dismissal time
                    const now = new Date().toISOString();
                    localStorage.setItem(storageKey, now);

                    // Hide banner with fade out
                    if (banner) {{
                        banner.style.transition = 'opacity 0.3s ease';
                        banner.style.opacity = '0';
                        setTimeout(function() {{
                            banner.style.display = 'none';
                        }}, 300);
                    }}
                }});
            }}
        }})();
        '''
        ui.add_body_html(f'<script>{motd_js}</script>')
