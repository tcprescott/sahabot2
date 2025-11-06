"""
Tournament Match Settings Submission page.

This page allows tournament players to submit settings for their matches.
Form fields are dynamically generated based on tournament configuration.
"""

from __future__ import annotations
from nicegui import ui
from components.base_page import BasePage
from components.dynamic_form_builder import DynamicFormBuilder
from application.services.tournaments.tournament_match_settings_service import TournamentMatchSettingsService
from models.match_schedule import Match
import logging

logger = logging.getLogger(__name__)


def register():
    """Register tournament match settings submission page routes."""

    @ui.page('/tournaments/matches/{match_id}/submit')
    async def match_settings_submission_page(match_id: int):
        """Match settings submission page."""
        base = BasePage.authenticated_page(title='Submit Match Settings')

        # Pre-check: get match and validate it exists
        from middleware.auth import DiscordAuthService
        user = await DiscordAuthService.get_current_user()
        if not user:
            return

        match = await Match.get_or_none(id=match_id).prefetch_related('tournament', 'players')
        if not match:
            ui.notify('Match not found', color='negative')
            ui.navigate.to('/')
            return

        async def content(page: BasePage):
            """Render submission form content."""
            # Verify authorization - try to get any existing submission
            # If user doesn't have access, service will return None
            service = TournamentMatchSettingsService()
            existing_submission = await service.get_submission(page.user, match_id, game_number=1)

            # Additional check: try to list submissions to verify access
            accessible_submissions = await service.list_submissions_for_match(page.user, match_id)
            if existing_submission is None and not accessible_submissions:
                # User has no access to this match
                ui.notify('You do not have permission to submit settings for this match', color='negative')
                ui.navigate.to('/')
                return

            # Page header
            with ui.element('div').classes('card mb-4'):
                with ui.element('div').classes('card-header'):
                    ui.label('Submit Match Settings').classes('text-2xl font-bold')

            # Match info card
            with ui.element('div').classes('card mb-4'):
                with ui.element('div').classes('card-header'):
                    ui.label('Match Information')
                with ui.element('div').classes('card-body'):
                    ui.label(f'Tournament: {match.tournament.name}')
                    if match.title:
                        ui.label(f'Match: {match.title}')
                    if match.scheduled_at:
                        from components.datetime_label import DateTimeLabel
                        with ui.row().classes('items-center gap-2'):
                            ui.label('Scheduled:')
                            DateTimeLabel.create(match.scheduled_at, format_type='datetime')

            # Submission form card
            with ui.element('div').classes('card mb-4'):
                with ui.element('div').classes('card-header'):
                    ui.label('Settings Submission')

                with ui.element('div').classes('card-body'):
                    # Game number selector
                    with ui.row().classes('items-center gap-4 mb-4'):
                        ui.label('Game Number:')
                        game_number_input = ui.number(
                            label='',
                            value=1,
                            min=1,
                            max=10,
                            step=1,
                            format='%.0f'
                        ).classes('w-32')

                    # Dynamic form based on tournament configuration
                    form_builder = DynamicFormBuilder(match.tournament.settings_form_schema)
                    existing_values = existing_submission.settings if existing_submission else None
                    form_builder.render(existing_values)

                    # Notes input
                    notes_input = ui.textarea(
                        label='Notes (optional)',
                        placeholder='Any special requests or notes for tournament admins...'
                    ).classes('w-full mt-4').props('rows=3')
                    if existing_submission and existing_submission.notes:
                        notes_input.value = existing_submission.notes

                    # Validation message
                    validation_msg = ui.label('').classes('mt-2')

                    # Submit button
                    with ui.row().classes('mt-4 gap-4'):
                        async def submit_settings():
                            """Handle settings submission."""
                            try:
                                # Validate form
                                is_valid, error_msg = form_builder.validate()
                                if not is_valid:
                                    validation_msg.text = error_msg
                                    validation_msg.classes('text-negative', remove='text-positive')
                                    ui.notify(error_msg, color='negative')
                                    return

                                # Get form values
                                settings = form_builder.get_values()

                                if not settings:
                                    validation_msg.text = 'Settings cannot be empty'
                                    validation_msg.classes('text-negative', remove='text-positive')
                                    return

                                # Submit via service
                                submission = await service.submit_settings(
                                    user=page.user,
                                    match_id=match_id,
                                    settings=settings,
                                    game_number=int(game_number_input.value),
                                    notes=notes_input.value.strip() or None
                                )

                                if submission:
                                    ui.notify('Settings submitted successfully!', color='positive')
                                    validation_msg.text = 'Settings submitted successfully!'
                                    validation_msg.classes('text-positive', remove='text-negative')

                                    # Redirect to match page after short delay
                                    await ui.run_javascript('setTimeout(() => { window.location.href = "/"; }, 2000);')
                                else:
                                    ui.notify('Failed to submit settings', color='negative')
                                    validation_msg.text = 'Failed to submit settings'
                                    validation_msg.classes('text-negative', remove='text-positive')

                            except Exception as e:
                                logger.error("Error submitting settings: %s", str(e), exc_info=True)
                                validation_msg.text = f'Error: {str(e)}'
                                validation_msg.classes('text-negative', remove='text-positive')
                                ui.notify('An error occurred', color='negative')

                        submit_btn = ui.button('Submit Settings', on_click=submit_settings).props('color=primary')

                        # Cancel button
                        ui.button('Cancel', on_click=lambda: ui.navigate.to('/')).props('outline')

            # Show existing submission if any
            if existing_submission:
                with ui.element('div').classes('card'):
                    with ui.element('div').classes('card-header'):
                        ui.label('Current Submission')
                    with ui.element('div').classes('card-body'):
                        from components.datetime_label import DateTimeLabel
                        with ui.row().classes('items-center gap-2 mb-2'):
                            ui.label('Submitted:')
                            DateTimeLabel.create(existing_submission.submitted_at, format_type='relative')
                        ui.label(f'Game: {existing_submission.game_number}')
                        if existing_submission.notes:
                            ui.label(f'Notes: {existing_submission.notes}')

        await base.render(content)()
