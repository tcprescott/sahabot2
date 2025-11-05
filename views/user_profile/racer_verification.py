"""
Racer verification view for users.

Allows users to verify themselves for racer roles by checking their
RaceTime race completion against organization requirements.
"""

import logging
from nicegui import ui
from models import User
from application.services.racer_verification_service import RacerVerificationService
from application.services.discord_guild_service import DiscordGuildService

logger = logging.getLogger(__name__)


class RacerVerificationView:
    """View for users to verify themselves for racer roles."""

    def __init__(self, user: User, verification_id: int = None):
        """
        Initialize view.

        Args:
            user: Current user
            verification_id: Optional specific verification to check
        """
        self.user = user
        self.verification_id = verification_id
        self.service = RacerVerificationService()
        self.guild_service = DiscordGuildService()

        # State
        self.verifications = []
        self.user_verifications = {}

    async def render(self):
        """Render the racer verification view."""
        with ui.element('div').classes('card'):
            with ui.element('div').classes('card-header'):
                ui.label('Racer Verification').classes('text-lg font-bold')

            with ui.element('div').classes('card-body'):
                # Check if user has linked RaceTime account
                if not self.user.racetime_id:
                    await self._render_link_account_prompt()
                    return

                # If specific verification ID provided, show only that one
                if self.verification_id:
                    await self._render_single_verification()
                else:
                    await self._render_all_verifications()

    async def _render_link_account_prompt(self):
        """Render prompt to link RaceTime account."""
        with ui.column().classes('gap-4 items-center text-center'):
            ui.icon('link_off', size='4rem').classes('text-warning')

            ui.label('RaceTime Account Required').classes('text-xl font-bold')

            ui.label(
                'You need to link your RaceTime.gg account to verify for racer roles.'
            ).classes('text-secondary')

            ui.separator()

            # Instructions
            with ui.column().classes('gap-2 w-full max-w-md'):
                ui.label('How to Link Your Account:').classes('font-bold')

                with ui.element('ol').classes('text-left space-y-2 ml-4'):
                    with ui.element('li'):
                        ui.label('1. Go to your Profile page')
                    with ui.element('li'):
                        ui.label('2. Click the "RaceTime Account" tab')
                    with ui.element('li'):
                        ui.label('3. Click "Link Account" and authorize on RaceTime.gg')
                    with ui.element('li'):
                        ui.label('4. Return here to verify for racer roles')

            ui.separator()

            # Link to profile
            ui.button(
                'Go to Profile',
                icon='person',
                on_click=lambda: ui.navigate.to('/profile')
            ).classes('btn btn-primary')

    async def _render_single_verification(self):
        """Render single verification check."""
        # Get verification config
        verification = await self.service.repository.get_by_id(self.verification_id)

        if not verification:
            ui.label('Verification not found').classes('text-secondary')
            return

        # Check eligibility
        eligibility = await self.service.check_user_eligibility(
            user=self.user,
            verification_id=self.verification_id
        )

        # Get verification status
        user_verification = await self.service.get_user_verification_status(
            user=self.user,
            verification_id=self.verification_id
        )

        # Render verification card
        await self._render_verification_card(verification, eligibility, user_verification)

    async def _render_all_verifications(self):
        """Render all available verifications."""
        # Get all verifications from user's organizations
        from application.repositories.organization_repository import OrganizationRepository
        org_repo = OrganizationRepository()

        # Get user's organization memberships
        memberships = await org_repo.list_memberships_for_user(self.user.id)

        if not memberships:
            ui.label('You are not a member of any organizations.').classes('text-secondary')
            return

        # Get verifications for all user's organizations
        all_verifications = []
        for membership in memberships:
            verifications = await self.service.get_verifications_for_organization(
                current_user=self.user,
                organization_id=membership.organization_id
            )
            all_verifications.extend(verifications)

        if not all_verifications:
            ui.label('No racer verifications available.').classes('text-secondary')
            ui.label(
                'Contact your organization administrator to set up racer role verifications.'
            ).classes('text-secondary text-sm mt-2')
            return

        # Render each verification
        for verification in all_verifications:
            # Check eligibility
            eligibility = await self.service.check_user_eligibility(
                user=self.user,
                verification_id=verification.id
            )

            # Get verification status
            user_verification = await self.service.get_user_verification_status(
                user=self.user,
                verification_id=verification.id
            )

            # Render verification card
            await self._render_verification_card(verification, eligibility, user_verification)

            ui.element('div').classes('my-4')  # Spacing

    async def _render_verification_card(self, verification, eligibility, user_verification):
        """Render a single verification card."""
        with ui.element('div').classes('card'):
            with ui.element('div').classes('card-header'):
                with ui.row().classes('w-full items-center justify-between'):
                    with ui.column().classes('gap-1'):
                        # Display categories
                        categories_str = ', '.join([cat.upper() for cat in verification.categories]) if verification.categories else 'N/A'
                        ui.label(categories_str).classes('text-lg font-bold')
                        ui.label(f'Role: {verification.role_name}').classes('text-sm text-secondary')

                    # Status badge
                    if user_verification and user_verification.is_verified:
                        ui.label('Verified').classes('badge badge-success')
                    elif eligibility['is_eligible']:
                        ui.label('Eligible').classes('badge badge-info')
                    else:
                        ui.label('Not Eligible').classes('badge badge-secondary')

            with ui.element('div').classes('card-body'):
                # Requirements
                with ui.column().classes('gap-2'):
                    ui.label('Requirements:').classes('font-medium')

                    # Minimum races
                    race_count = eligibility.get('race_count', 0)
                    minimum_required = eligibility.get('minimum_required', 0)

                    with ui.row().classes('items-center gap-2'):
                        if race_count >= minimum_required:
                            ui.icon('check_circle', color='positive')
                        else:
                            ui.icon('cancel', color='negative')

                        ui.label(f'{race_count} / {minimum_required} races completed')

                    # Counting rules
                    rules = []
                    if not verification.count_forfeits and not verification.count_dq:
                        rules.append('Only finished races count')
                    else:
                        if verification.count_forfeits:
                            rules.append('Forfeits count')
                        if verification.count_dq:
                            rules.append('Disqualifications count')

                    ui.label(f'Rules: {", ".join(rules)}').classes('text-sm text-secondary')

                # Error message
                if eligibility.get('error'):
                    ui.label(f'Error: {eligibility["error"]}').classes('text-negative mt-2')

                # Verification button
                ui.separator()

                if user_verification and user_verification.is_verified:
                    # Already verified
                    with ui.column().classes('gap-2'):
                        ui.label('You have been verified for this role!').classes('text-positive')

                        if user_verification.role_granted:
                            ui.label('The Discord role has been granted.').classes('text-sm text-secondary')
                        else:
                            ui.label(
                                'Role grant failed - please contact an administrator.'
                            ).classes('text-sm text-warning')

                        if user_verification.verified_at:
                            from components.datetime_label import DateTimeLabel
                            with ui.row().classes('items-center gap-1'):
                                ui.label('Verified:')
                                DateTimeLabel.create(user_verification.verified_at, format_type='relative')

                elif eligibility['is_eligible']:
                    # Eligible to verify
                    ui.button(
                        'Verify Now',
                        icon='verified',
                        on_click=lambda v=verification: self._verify(v)
                    ).classes('btn btn-primary')
                else:
                    # Not eligible
                    races_needed = minimum_required - race_count
                    ui.label(
                        f'Complete {races_needed} more race{"s" if races_needed != 1 else ""} to become eligible.'
                    ).classes('text-secondary')

    async def _verify(self, verification):
        """Verify user for a verification."""
        try:
            result = await self.service.verify_user(
                user=self.user,
                verification_id=verification.id
            )

            if result:
                if result.role_granted:
                    ui.notify(
                        f'Verified! Discord role "{verification.role_name}" has been granted.',
                        type='positive'
                    )
                else:
                    ui.notify(
                        'Verified! However, the Discord role could not be granted. Please contact an administrator.',
                        type='warning'
                    )

                # Reload page to show updated status
                ui.navigate.reload()
            else:
                ui.notify('Verification failed - you may not be eligible.', type='negative')

        except Exception as e:
            logger.error("Error verifying user: %s", e, exc_info=True)
            ui.notify(f'Error: {str(e)}', type='negative')
