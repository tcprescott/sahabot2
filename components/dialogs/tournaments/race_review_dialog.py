"""
Race Review Dialog for async tournaments.

Allows reviewers to view race details, edit finish times, and approve/reject submissions.
"""

from nicegui import ui
from typing import Optional, Callable
import httpx

from components.dialogs.common.base_dialog import BaseDialog


class RaceReviewDialog(BaseDialog):
    """Dialog for reviewing an async tournament race."""

    def __init__(
        self,
        race_data: dict,
        organization_id: int,
        on_save: Optional[Callable] = None
    ):
        """
        Initialize the race review dialog.

        Args:
            race_data: Race data from API
            organization_id: Organization ID
            on_save: Optional callback when review is saved
        """
        super().__init__()
        self.race_data = race_data
        self.organization_id = organization_id
        self.on_save = on_save

        # Form inputs (will be set in _render_body)
        self.review_status_select = None
        self.reviewer_notes_input = None
        self.elapsed_time_input = None

    async def show(self):
        """Display the dialog."""
        self.create_dialog(
            title=f'Review Race #{self.race_data["id"]}',
            icon='rate_review',
            max_width='800px'
        )
        await super().show()

    def _render_body(self):
        """Render dialog content."""
        # Race Information Section
        self.create_section_title('Race Information')

        with ui.column().classes('gap-sm w-full'):
            self.create_info_row('Player', self.race_data['user']['discord_username'])
            self.create_info_row('Pool', self.race_data.get('pool_name', 'N/A'))
            self.create_info_row('Status', self.race_data['status'].title())

            if self.race_data.get('permalink_url'):
                with ui.row().classes('gap-sm items-center'):
                    ui.label('Permalink:').classes('font-semibold text-sm')
                    ui.link(
                        self.race_data['permalink_url'],
                        self.race_data['permalink_url'],
                        new_tab=True
                    ).classes('text-primary')

            self.create_info_row('Finish Time', self.race_data['elapsed_time_formatted'])

            if self.race_data.get('runner_vod_url'):
                with ui.row().classes('gap-sm items-center'):
                    ui.label('VOD:').classes('font-semibold text-sm')
                    ui.link(
                        self.race_data['runner_vod_url'],
                        self.race_data['runner_vod_url'],
                        new_tab=True
                    ).classes('text-primary')

            if self.race_data.get('runner_notes'):
                ui.label('Runner Notes:').classes('font-semibold text-sm mt-2')
                with ui.card().classes('w-full p-2 bg-gray-100'):
                    ui.label(self.race_data['runner_notes']).classes('text-sm whitespace-pre-wrap')

        ui.separator()

        # Review Section
        self.create_section_title('Review')

        with ui.column().classes('gap-md w-full'):
            # Review Status
            ui.label('Review Status').classes('font-semibold text-sm')
            self.review_status_select = ui.select(
                options={
                    'pending': 'Pending',
                    'accepted': 'Accepted',
                    'rejected': 'Pending Second Review'
                },
                value=self.race_data.get('review_status', 'pending')
            ).classes('w-full')

            # Elapsed Time Override (optional)
            ui.label('Elapsed Time Override (HH:MM:SS) - Optional').classes('font-semibold text-sm')
            ui.label('Only change this if correcting an incorrect time').classes('text-xs text-secondary')
            self.elapsed_time_input = ui.input(
                placeholder='HH:MM:SS (e.g., 01:23:45)',
                validation={'Invalid format': lambda v: not v or self._validate_time_format(v)}
            ).classes('w-full')

            # Reviewer Notes
            ui.label('Reviewer Notes').classes('font-semibold text-sm')
            self.reviewer_notes_input = ui.textarea(
                placeholder='Add notes about this review...',
                value=self.race_data.get('reviewer_notes', '')
            ).classes('w-full').props('rows=4')

            # Current review info if already reviewed
            if self.race_data.get('reviewed_by'):
                with ui.card().classes('w-full p-2 bg-blue-50 mt-2'):
                    ui.label(f"Previously reviewed by {self.race_data['reviewed_by']['discord_username']}").classes('text-sm font-semibold')
                    if self.race_data.get('reviewed_at'):
                        ui.label(f"at {self.race_data['reviewed_at']}").classes('text-xs text-secondary')

        ui.separator()

        # Action Buttons
        with self.create_actions_row():
            ui.button('Cancel', on_click=self.close).classes('btn')
            ui.button('Save Review', on_click=self._save_review).classes('btn').props('color=positive')

    def _validate_time_format(self, value: str) -> bool:
        """Validate HH:MM:SS time format."""
        if not value:
            return True

        parts = value.split(':')
        if len(parts) != 3:
            return False

        try:
            hours, minutes, seconds = map(int, parts)
            return 0 <= hours < 100 and 0 <= minutes < 60 and 0 <= seconds < 60
        except ValueError:
            return False

    def _parse_time_to_seconds(self, time_str: str) -> Optional[int]:
        """Parse HH:MM:SS to total seconds."""
        if not time_str:
            return None

        try:
            parts = time_str.split(':')
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
        except (ValueError, IndexError):
            return None

    async def _save_review(self):
        """Save the review."""
        # Validate elapsed time if provided
        elapsed_seconds = None
        if self.elapsed_time_input.value:
            elapsed_seconds = self._parse_time_to_seconds(self.elapsed_time_input.value)
            if elapsed_seconds is None:
                ui.notify('Invalid time format. Use HH:MM:SS', type='negative')
                return

        # Prepare request payload
        payload = {
            'review_status': self.review_status_select.value,
            'reviewer_notes': self.reviewer_notes_input.value or None,
            'elapsed_time_seconds': elapsed_seconds,
        }

        # Submit review
        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f'/api/async-tournaments/races/{self.race_data["id"]}/review',
                    params={'organization_id': self.organization_id},
                    json=payload
                )

                if response.status_code == 200:
                    ui.notify('Review saved successfully', type='positive')

                    if self.on_save:
                        await self.on_save()

                    await self.close()
                else:
                    error_detail = response.json().get('detail', 'Unknown error')
                    ui.notify(f'Failed to save review: {error_detail}', type='negative')

        except Exception as e:
            ui.notify(f'Error saving review: {str(e)}', type='negative')
