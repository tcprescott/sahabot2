"""
Notification Preferences view.

Allows users to manage their notification subscriptions.
"""

import logging
from nicegui import ui
from models import User
from models.notification_subscription import NotificationEventType, NotificationMethod
from application.services.notifications.notification_service import NotificationService
from application.repositories.organization_repository import OrganizationRepository
from components.data_table import ResponsiveTable, TableColumn

logger = logging.getLogger(__name__)


class NotificationPreferencesView:
    """View for managing notification preferences."""

    # Events that are organization-scoped (require org selection)
    ORG_SCOPED_EVENTS = {
        NotificationEventType.ORGANIZATION_MEMBER_ADDED,
        NotificationEventType.ORGANIZATION_MEMBER_REMOVED,
        NotificationEventType.ORGANIZATION_PERMISSION_CHANGED,
        NotificationEventType.TOURNAMENT_CREATED,
        NotificationEventType.TOURNAMENT_STARTED,
        NotificationEventType.TOURNAMENT_ENDED,
        NotificationEventType.TOURNAMENT_UPDATED,
        NotificationEventType.MATCH_SCHEDULED,
        NotificationEventType.MATCH_COMPLETED,
        NotificationEventType.RACE_SUBMITTED,
        NotificationEventType.CREW_APPROVED,
        NotificationEventType.CREW_REMOVED,
    }

    def __init__(self, user: User):
        """
        Initialize the notification preferences view.

        Args:
            user: Current user
        """
        self.user = user
        self.service = NotificationService()
        self.org_repo = OrganizationRepository()
        self.subscriptions = []
        self.table = None
        self.table_container = None
        self.user_organizations = []

    async def render(self):
        """Render the notification preferences view."""
        # Fetch user's organizations for org-scoped subscriptions
        memberships = await self.org_repo.list_memberships_for_user(self.user.id)
        self.user_organizations = [m.organization for m in memberships]

        with ui.element('div').classes('card'):
            # Header
            with ui.element('div').classes('card-header'):
                with ui.row().classes('items-center gap-2'):
                    ui.icon('notifications').classes('icon-medium')
                    ui.label('Notification Preferences').classes('text-xl text-bold')

            # Body
            with ui.element('div').classes('card-body'):
                ui.label(
                    'Configure which events you want to be notified about and how.'
                ).classes('text-muted mb-4')

                # Add subscription section
                with ui.expansion('Add New Subscription', icon='add').classes('mb-4'):
                    await self._render_add_subscription_form()

                ui.separator()

                # Current subscriptions (with container for refresh)
                with ui.element('div').classes('mt-4'):
                    ui.label('Your Subscriptions').classes('text-lg font-bold mb-2')
                    self.table_container = ui.element('div')
                    with self.table_container:
                        await self._render_subscriptions_table()

    async def _render_add_subscription_form(self):
        """Render the form to add a new subscription."""
        with ui.column().classes('gap-4 p-4'):
            # Event type selection
            event_type_select = ui.select(
                label='Event Type',
                options={
                    NotificationEventType.MATCH_SCHEDULED: 'Match Scheduled',
                    NotificationEventType.TOURNAMENT_CREATED: 'Tournament Created',
                    NotificationEventType.INVITE_RECEIVED: 'Organization Invite',
                    NotificationEventType.TOURNAMENT_STARTED: 'Tournament Started',
                    NotificationEventType.TOURNAMENT_ENDED: 'Tournament Ended',
                    NotificationEventType.ORGANIZATION_MEMBER_ADDED: 'Organization Member Added',
                    NotificationEventType.MATCH_COMPLETED: 'Match Completed',
                    NotificationEventType.RACE_SUBMITTED: 'Race Submitted',
                    NotificationEventType.CREW_APPROVED: 'Crew Approved',
                    NotificationEventType.CREW_REMOVED: 'Crew Removed',
                },
                value=NotificationEventType.MATCH_SCHEDULED,
            ).classes('w-full')

            # Notification method selection
            method_select = ui.select(
                label='Notification Method',
                options={
                    NotificationMethod.DISCORD_DM: 'Discord DM',
                    NotificationMethod.EMAIL: 'Email (Coming Soon)',
                },
                value=NotificationMethod.DISCORD_DM,
            ).classes('w-full')

            # Organization selection (shown for org-scoped events)
            org_select_container = ui.element('div')
            org_select = None

            def update_org_visibility():
                """Show/hide organization selector based on event type."""
                org_select_container.clear()
                with org_select_container:
                    nonlocal org_select
                    if event_type_select.value in self.ORG_SCOPED_EVENTS:
                        if not self.user_organizations:
                            ui.label('You are not a member of any organizations yet.').classes('text-warning')
                            org_select = None
                        else:
                            # Build options with "All Organizations" option
                            org_options = {'ALL': 'All Organizations (Default)'}
                            org_options.update({
                                org.id: org.name for org in self.user_organizations
                            })

                            org_select = ui.select(
                                label='Organization',
                                options=org_options,
                                value='ALL',
                            ).classes('w-full')

                            ui.label(
                                'Select "All Organizations" to receive notifications for all organizations you belong to, '
                                'or choose a specific organization.'
                            ).classes('text-muted text-sm')
                    else:
                        org_select = None

            # Initial visibility
            update_org_visibility()

            # Update when event type changes
            event_type_select.on('update:model-value', lambda: update_org_visibility())

            # Add button
            async def add_subscription():
                try:
                    # Determine organization based on selection
                    organization = None
                    if event_type_select.value in self.ORG_SCOPED_EVENTS:
                        if not self.user_organizations:
                            ui.notify('You must be a member of an organization to subscribe to this event', type='warning')
                            return

                        if org_select and org_select.value != 'ALL':
                            # Find the selected organization
                            organization = next(
                                (org for org in self.user_organizations if org.id == org_select.value),
                                None
                            )

                    await self.service.subscribe(
                        user=self.user,
                        event_type=event_type_select.value,
                        notification_method=method_select.value,
                        organization=organization,
                    )
                    ui.notify('Subscription added successfully', type='positive')
                    await self._refresh_subscriptions()
                except Exception as e:
                    logger.exception("Error adding subscription")
                    ui.notify(f'Error: {str(e)}', type='negative')

            ui.button(
                'Add Subscription',
                on_click=add_subscription,
                icon='add'
            ).classes('btn').props('color=positive')

    async def _render_subscriptions_table(self):
        """Render the table of current subscriptions."""
        # Fetch subscriptions
        self.subscriptions = await self.service.get_user_subscriptions(self.user)

        if not self.subscriptions:
            ui.label('No subscriptions yet. Add one above!').classes('text-muted')
            return

        # Define table columns
        columns = [
            TableColumn(
                label='Event Type',
                key='event_type',
                cell_render=lambda row: ui.label(
                    NotificationEventType(row.event_type).name.replace('_', ' ').title()
                ),
            ),
            TableColumn(
                label='Method',
                key='notification_method',
                cell_render=lambda row: ui.label(
                    'Discord DM' if row.notification_method == NotificationMethod.DISCORD_DM else 'Email'
                ),
            ),
            TableColumn(
                label='Organization',
                key='organization',
                cell_render=self._render_organization_scope,
            ),
            TableColumn(
                label='Status',
                key='is_active',
                cell_render=lambda row: ui.badge(
                    'Active' if row.is_active else 'Paused',
                    color='positive' if row.is_active else 'grey'
                ),
            ),
            TableColumn(
                label='Actions',
                key='actions',
                cell_render=self._render_actions,
            ),
        ]

        # Render table
        self.table = ResponsiveTable(
            columns=columns,
            rows=self.subscriptions,
        )
        await self.table.render()

    def _render_organization_scope(self, subscription):
        """Render the organization scope for a subscription."""
        org_id = getattr(subscription, 'organization_id', None)
        if not org_id:
            # Check if this is an org-scoped event
            if subscription.event_type in self.ORG_SCOPED_EVENTS:
                ui.label('All Organizations').classes('text-muted')
            else:
                ui.label('—').classes('text-muted')
        else:
            # Use prefetched organization or fall back to searching
            org = getattr(subscription, 'organization', None)
            if org:
                ui.label(org.name)
            else:
                # Fallback: search in cached user organizations
                org_name = 'Unknown'
                for user_org in self.user_organizations:
                    if user_org.id == org_id:
                        org_name = user_org.name
                        break
                ui.label(org_name)

    def _render_actions(self, subscription):
        """Render action buttons for a subscription row."""
        with ui.row().classes('gap-2'):
            # Toggle active/inactive
            if subscription.is_active:
                ui.button(
                    icon='pause',
                    on_click=lambda: self._toggle_subscription(subscription),
                ).props('flat dense round').tooltip('Pause')
            else:
                ui.button(
                    icon='play_arrow',
                    on_click=lambda: self._toggle_subscription(subscription),
                ).props('flat dense round').tooltip('Resume')

            # Delete
            ui.button(
                icon='delete',
                on_click=lambda: self._delete_subscription(subscription),
            ).props('flat dense round color=negative').tooltip('Delete')

    async def _toggle_subscription(self, subscription):
        """Toggle a subscription's active status."""
        try:
            await self.service.toggle_subscription(
                subscription_id=subscription.id,
                user=self.user,
            )
            ui.notify(
                f"Subscription {'paused' if subscription.is_active else 'resumed'}",
                type='positive'
            )
            await self._refresh_subscriptions()
        except Exception as e:
            logger.exception("Error toggling subscription")
            ui.notify(f'Error: {str(e)}', type='negative')

    async def _delete_subscription(self, subscription):
        """Delete a subscription."""
        try:
            # Get organization object from subscription (prefetched) or fallback to search
            organization = None
            org_id = getattr(subscription, 'organization_id', None)
            if org_id:
                # Try prefetched organization first
                organization = getattr(subscription, 'organization', None)

                # Fallback: find organization from our cached list
                if not organization:
                    organization = next(
                        (org for org in self.user_organizations if org.id == org_id),
                        None
                    )

            # Unsubscribe using the service API (match by event_type + method + org)
            await self.service.unsubscribe(
                user=self.user,
                event_type=subscription.event_type,
                notification_method=subscription.notification_method,
                organization=organization,
            )
            ui.notify('Subscription removed', type='positive')
            await self._refresh_subscriptions()
        except Exception as e:
            logger.exception("Error deleting subscription")
            ui.notify(f'Error: {str(e)}', type='negative')

    async def _refresh_subscriptions(self):
        """Refresh the subscriptions table."""
        # Re-fetch subscriptions
        self.subscriptions = await self.service.get_user_subscriptions(self.user)

        # Clear and re-render the table container
        if self.table_container:
            self.table_container.clear()
            with self.table_container:
                await self._render_subscriptions_table()

        logger.info("Subscriptions refreshed for user %s", self.user.id)
