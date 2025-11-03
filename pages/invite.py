"""
Organization invite join page.

Public page for users to join organizations via invite links.
"""

from nicegui import ui
from components import BasePage, Card
from application.services.organization_invite_service import OrganizationInviteService


def register():
    """Register invite join route."""

    @ui.page('/invite/{slug}')
    async def invite_join_page(slug: str):
        """Public page to join an organization via invite link."""
        base = BasePage.simple_page(title="Join Organization")
        invite_service = OrganizationInviteService()

        async def content(page: BasePage):
            """Render invite join page."""
            # Get the invite
            invite = await invite_service.get_invite_by_slug(slug)
            
            if not invite:
                with Card.create(title='Invalid Invite'):
                    ui.label('This invite link is not valid or has been removed.')
                    ui.button('Go to Home', on_click=lambda: ui.navigate.to('/')).classes('btn mt-2')
                return

            # Load organization
            await invite.fetch_related('organization')
            org = invite.organization

            # Check if invite can be used
            can_use, reason = await invite_service.can_use_invite(invite)

            with ui.column().classes('full-width gap-md'):
                if not page.user:
                    # User not logged in
                    Card.simple(
                        title=f'Join {org.name}',
                        description='Please log in with Discord to accept this invitation.'
                    )
                    Card.action(
                        title='Sign In Required',
                        description='You need to be logged in to join an organization.',
                        button_text='Login with Discord',
                        on_click=lambda: ui.navigate.to(f'/auth/login?redirect=/invite/{slug}')
                    )
                elif not can_use:
                    # Invite cannot be used
                    Card.simple(
                        title=f'Invite to {org.name}',
                        description=f'This invite cannot be used: {reason}'
                    )
                    ui.button('Go to Home', on_click=lambda: ui.navigate.to('/')).classes('btn mt-2')
                else:
                    # User logged in and invite valid
                    Card.simple(
                        title=f'Join {org.name}',
                        description=org.description or 'You have been invited to join this organization.'
                    )

                    async def accept_invite():
                        success, error = await invite_service.use_invite(slug, page.user.id)
                        if success:
                            ui.notify('Successfully joined the organization!', type='positive')
                            ui.navigate.to(f'/org/{org.id}')
                        else:
                            ui.notify(error or 'Failed to join organization', type='negative')

                    with Card.create(title='Accept Invitation'):
                        ui.label('Click below to join this organization.')
                        with ui.row().classes('gap-2 mt-2'):
                            ui.button('Accept & Join', icon='check', on_click=accept_invite).props('color=positive').classes('btn')
                            ui.button('Decline', icon='close', on_click=lambda: ui.navigate.to('/')).classes('btn')

        await base.render(content)
