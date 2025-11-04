"""
Discord notification handler.

Handles sending notifications via Discord DMs using the Discord bot.
"""

import logging
from typing import Optional
from datetime import datetime, timezone
import discord

from discordbot.client import get_bot_instance
from models import User
from models.notification_log import NotificationDeliveryStatus
from models.notification_subscription import NotificationEventType
from application.services.notification_handlers.base_handler import BaseNotificationHandler

logger = logging.getLogger(__name__)


class DiscordNotificationHandler(BaseNotificationHandler):
    """
    Handler for sending notifications via Discord DMs.

    Uses the Discord bot to send direct messages to users.
    Handles rate limits, user privacy settings, and delivery status.
    """

    def __init__(self):
        """Initialize the Discord notification handler."""
        self.bot = get_bot_instance()

    async def send_notification(
        self,
        user: User,
        event_type: NotificationEventType,
        event_data: dict
    ) -> tuple[NotificationDeliveryStatus, Optional[str]]:
        """
        Send a Discord DM notification to a user.

        Routes to event-specific handler methods based on event type.

        Args:
            user: User to send notification to
            event_type: Type of notification event
            event_data: Event-specific data for formatting the notification

        Returns:
            Tuple of (delivery_status, error_message)
            - delivery_status: SENT if successful, FAILED if failed
            - error_message: Error description if failed, None if successful
        """
        # Route to specific handler method based on event type
        handler_map = {
            NotificationEventType.MATCH_SCHEDULED: self._send_match_scheduled,
            NotificationEventType.MATCH_COMPLETED: self._send_match_completed,
            NotificationEventType.TOURNAMENT_CREATED: self._send_tournament_created,
            NotificationEventType.TOURNAMENT_STARTED: self._send_tournament_started,
            NotificationEventType.TOURNAMENT_ENDED: self._send_tournament_ended,
            NotificationEventType.TOURNAMENT_UPDATED: self._send_tournament_updated,
            NotificationEventType.RACE_SUBMITTED: self._send_race_submitted,
            NotificationEventType.RACE_APPROVED: self._send_race_approved,
            NotificationEventType.RACE_REJECTED: self._send_race_rejected,
            NotificationEventType.CREW_APPROVED: self._send_crew_approved,
            NotificationEventType.CREW_REMOVED: self._send_crew_removed,
            NotificationEventType.INVITE_RECEIVED: self._send_invite_received,
            NotificationEventType.ORGANIZATION_MEMBER_ADDED: self._send_organization_member_added,
            NotificationEventType.ORGANIZATION_MEMBER_REMOVED: self._send_organization_member_removed,
            NotificationEventType.ORGANIZATION_PERMISSION_CHANGED: self._send_organization_permission_changed,
            NotificationEventType.USER_PERMISSION_CHANGED: self._send_user_permission_changed,
        }

        # Get handler for this event type
        handler = handler_map.get(event_type)

        if handler:
            return await handler(user, event_data)
        else:
            # Generic fallback for event types without dedicated handlers
            logger.info(
                "No dedicated handler for event type %s, using generic notification",
                event_type.name
            )
            message = f"Notification: {event_type.name}\n{event_data}"
            return await self._send_discord_dm(user, message)

    async def _send_discord_dm(
        self,
        user: User,
        message: str,
        embed: Optional[discord.Embed] = None
    ) -> tuple[NotificationDeliveryStatus, Optional[str]]:
        """
        Send a Discord DM to a user.

        Low-level method for actually sending the Discord message.

        Args:
            user: User to send notification to
            message: Text message to send
            embed: Optional Discord embed for rich formatting

        Returns:
            Tuple of (delivery_status, error_message)
        """
        if not self.bot:
            logger.error("Discord bot not available for notifications")
            return (
                NotificationDeliveryStatus.FAILED,
                "Discord bot not initialized"
            )

        try:
            # Get Discord user object
            discord_user = await self.bot.fetch_user(int(user.discord_id))
            if not discord_user:
                logger.warning(
                    "Could not fetch Discord user %s for notification",
                    user.discord_id
                )
                return (
                    NotificationDeliveryStatus.FAILED,
                    f"Could not find Discord user {user.discord_id}"
                )

            # Send DM
            if embed:
                await discord_user.send(content=message, embed=embed)
            else:
                await discord_user.send(message)

            logger.info(
                "Sent Discord notification to user %s (%s)",
                user.get_display_name(),
                user.discord_id
            )
            return (NotificationDeliveryStatus.SENT, None)

        except discord.Forbidden:
            # User has DMs disabled or blocked the bot
            logger.warning(
                "Cannot send DM to user %s - DMs disabled or bot blocked",
                user.discord_id
            )
            return (
                NotificationDeliveryStatus.FAILED,
                "User has DMs disabled or has blocked the bot"
            )

        except discord.HTTPException as e:
            # Rate limit, server error, etc.
            logger.error(
                "HTTP error sending Discord notification to user %s: %s",
                user.discord_id,
                str(e)
            )
            if e.status == 429:
                # Rate limited - should retry later
                return (
                    NotificationDeliveryStatus.RETRYING,
                    f"Rate limited: {str(e)}"
                )
            return (
                NotificationDeliveryStatus.FAILED,
                f"Discord API error: {str(e)}"
            )

        except Exception as e:
            # Unexpected error
            logger.exception(
                "Unexpected error sending Discord notification to user %s",
                user.discord_id
            )
            return (
                NotificationDeliveryStatus.FAILED,
                f"Unexpected error: {str(e)}"
            )

    def _create_embed(
        self,
        title: str,
        description: str,
        color: discord.Color = discord.Color.blue(),
        fields: Optional[list[tuple[str, str, bool]]] = None,
        thumbnail_url: Optional[str] = None,
        footer_text: Optional[str] = None
    ) -> discord.Embed:
        """
        Create a Discord embed for rich notifications.

        Args:
            title: Embed title
            description: Embed description
            color: Embed color (default: blue)
            fields: List of (name, value, inline) tuples for embed fields
            thumbnail_url: URL for thumbnail image
            footer_text: Footer text

        Returns:
            Discord Embed object
        """
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.now(timezone.utc)
        )

        if fields:
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)

        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)

        if footer_text:
            embed.set_footer(text=footer_text)

        return embed

    async def _send_match_scheduled(
        self,
        user: User,
        event_data: dict
    ) -> tuple[NotificationDeliveryStatus, Optional[str]]:
        """
        Send a match scheduled notification.

        Args:
            user: User to notify
            event_data: Event data with match details

        Returns:
            Tuple of (delivery_status, error_message)
        """
        embed = self._create_embed(
            title="⚔️ Match Scheduled",
            description=f"You have a match scheduled in **{event_data.get('tournament_name', 'Unknown Tournament')}**",
            color=discord.Color.green(),
            fields=[
                ("Opponent", event_data.get('opponent_name', 'TBD'), True),
                ("Scheduled Time", event_data.get('scheduled_time', 'TBD'), True),
                ("Round", event_data.get('round_name', 'TBD'), False),
            ],
            footer_text="Check the tournament page for more details"
        )

        message = f"Hey {user.get_display_name()}! You have a new match scheduled."
        return await self._send_discord_dm(user, message, embed)

    async def _send_tournament_created(
        self,
        user: User,
        event_data: dict
    ) -> tuple[NotificationDeliveryStatus, Optional[str]]:
        """
        Send a tournament created notification.

        Args:
            user: User to notify
            event_data: Event data with tournament details

        Returns:
            Tuple of (delivery_status, error_message)
        """
        embed = self._create_embed(
            title="🏆 New Tournament",
            description=f"**{event_data.get('tournament_name', 'Unknown')}** has been created!",
            color=discord.Color.gold(),
            fields=[
                ("Format", event_data.get('format', 'TBD'), True),
                ("Start Date", event_data.get('start_date', 'TBD'), True),
            ],
            footer_text="Check the tournament page to register"
        )

        message = f"Hey {user.get_display_name()}! A new tournament has been created."
        return await self._send_discord_dm(user, message, embed)

    async def _send_invite_received(
        self,
        user: User,
        event_data: dict
    ) -> tuple[NotificationDeliveryStatus, Optional[str]]:
        """
        Send an organization invite notification.

        Args:
            user: User to notify
            event_data: Event data with invite details

        Returns:
            Tuple of (delivery_status, error_message)
        """
        embed = self._create_embed(
            title="📬 Organization Invite",
            description=f"You've been invited to join **{event_data.get('organization_name', 'Unknown Organization')}**",
            color=discord.Color.purple(),
            fields=[
                ("Invited By", event_data.get('invited_by', 'Unknown'), False),
            ],
            footer_text="Check your invites page to accept or decline"
        )

        message = f"Hey {user.get_display_name()}! You have a new organization invite."
        return await self._send_discord_dm(user, message, embed)

    async def _send_crew_approved(
        self,
        user: User,
        event_data: dict
    ) -> tuple[NotificationDeliveryStatus, Optional[str]]:
        """
        Send a crew approved notification.

        Args:
            user: User to notify
            event_data: Event data with crew details

        Returns:
            Tuple of (delivery_status, error_message)
        """
        role = event_data.get('role', 'crew').title()
        auto_approved = event_data.get('auto_approved', False)
        approver = event_data.get('added_by') if auto_approved else event_data.get('approved_by')
        
        # Get match details
        tournament_name = event_data.get('tournament_name')
        stream_channel = event_data.get('stream_channel')
        players = event_data.get('players', [])
        
        title = "🎬 Crew Role Assigned" if auto_approved else "✅ Crew Signup Approved"
        
        # Build description with tournament info if available
        if tournament_name:
            description = (
                f"You've been assigned as **{role}** for a match in **{tournament_name}**!"
                if auto_approved
                else f"Your **{role}** signup for **{tournament_name}** has been approved!"
            )
        else:
            description = (
                f"You've been assigned as **{role}** for a match!"
                if auto_approved
                else f"Your **{role}** signup has been approved!"
            )
        
        fields = [
            ("Role", role, True),
            ("Match ID", str(event_data.get('match_id', 'N/A')), True),
        ]
        
        # Add stream channel if available
        if stream_channel:
            fields.append(("Stream Channel", stream_channel, False))
        
        # Add players if available
        if players:
            players_str = ", ".join(players) if len(players) <= 4 else f"{', '.join(players[:3])}, +{len(players)-3} more"
            fields.append(("Players", players_str, False))
        
        # Add approver/adder
        if approver:
            fields.append((
                "Assigned By" if auto_approved else "Approved By",
                approver,
                False
            ))
        
        embed = self._create_embed(
            title=title,
            description=description,
            color=discord.Color.green(),
            fields=fields,
            footer_text="Check the match schedule for full details"
        )

        message = f"Hey {user.get_display_name()}! You've been approved for a crew role."
        return await self._send_discord_dm(user, message, embed)

    async def _send_crew_removed(
        self,
        user: User,
        event_data: dict
    ) -> tuple[NotificationDeliveryStatus, Optional[str]]:
        """
        Send a crew removed notification.

        Args:
            user: User to notify
            event_data: Event data with crew details

        Returns:
            Tuple of (delivery_status, error_message)
        """
        role = event_data.get('role', 'crew').title()
        
        embed = self._create_embed(
            title="❌ Crew Role Removed",
            description=f"You've been removed from the **{role}** role for a match.",
            color=discord.Color.red(),
            fields=[
                ("Role", role, True),
                ("Match ID", str(event_data.get('match_id', 'N/A')), True),
            ],
            footer_text="Contact an admin if you have questions"
        )

        message = f"Hey {user.get_display_name()}, you've been removed from a crew role."
        return await self._send_discord_dm(user, message, embed)

    async def _send_race_submitted(
        self,
        user: User,
        event_data: dict
    ) -> tuple[NotificationDeliveryStatus, Optional[str]]:
        """
        Send a race submitted notification.

        Args:
            user: User to notify
            event_data: Event data with race details

        Returns:
            Tuple of (delivery_status, error_message)
        """
        embed = self._create_embed(
            title="🏁 Race Submitted",
            description="Your race result has been submitted and is pending review.",
            color=discord.Color.blue(),
            fields=[
                ("Tournament ID", str(event_data.get('tournament_id', 'N/A')), True),
                ("Time", event_data.get('time_seconds', 'N/A'), True),
            ],
            footer_text="You'll be notified once it's reviewed"
        )

        message = f"Hey {user.get_display_name()}, your race has been submitted!"
        return await self._send_discord_dm(user, message, embed)

    async def _send_race_approved(
        self,
        user: User,
        event_data: dict
    ) -> tuple[NotificationDeliveryStatus, Optional[str]]:
        """
        Send a race approved notification.

        Args:
            user: User to notify
            event_data: Event data with race details

        Returns:
            Tuple of (delivery_status, error_message)
        """
        reviewer = event_data.get('reviewer', 'Admin')
        
        embed = self._create_embed(
            title="✅ Race Approved",
            description="Your race result has been approved!",
            color=discord.Color.green(),
            fields=[
                ("Tournament ID", str(event_data.get('tournament_id', 'N/A')), True),
                ("Reviewed By", reviewer, True),
            ],
            footer_text="Your time is now official"
        )

        message = f"Hey {user.get_display_name()}, your race has been approved!"
        return await self._send_discord_dm(user, message, embed)

    async def _send_race_rejected(
        self,
        user: User,
        event_data: dict
    ) -> tuple[NotificationDeliveryStatus, Optional[str]]:
        """
        Send a race rejected notification.

        Args:
            user: User to notify
            event_data: Event data with race details

        Returns:
            Tuple of (delivery_status, error_message)
        """
        reviewer = event_data.get('reviewer', 'Admin')
        reason = event_data.get('reason', 'No reason provided')
        
        embed = self._create_embed(
            title="❌ Race Rejected",
            description="Your race result was not approved.",
            color=discord.Color.red(),
            fields=[
                ("Tournament ID", str(event_data.get('tournament_id', 'N/A')), True),
                ("Reviewed By", reviewer, True),
                ("Reason", reason, False),
            ],
            footer_text="Contact an admin if you have questions"
        )

        message = f"Hey {user.get_display_name()}, your race submission was rejected."
        return await self._send_discord_dm(user, message, embed)

    async def _send_match_completed(
        self,
        user: User,
        event_data: dict
    ) -> tuple[NotificationDeliveryStatus, Optional[str]]:
        """
        Send a match completed notification.

        Args:
            user: User to notify
            event_data: Event data with match details

        Returns:
            Tuple of (delivery_status, error_message)
        """
        winner = event_data.get('winner', 'Unknown')
        
        embed = self._create_embed(
            title="🏆 Match Completed",
            description="A match you participated in has been completed.",
            color=discord.Color.gold(),
            fields=[
                ("Match ID", str(event_data.get('match_id', 'N/A')), True),
                ("Winner", winner, True),
                ("Tournament ID", str(event_data.get('tournament_id', 'N/A')), True),
            ],
            footer_text="Check the tournament page for standings"
        )

        message = f"Hey {user.get_display_name()}, your match is complete!"
        return await self._send_discord_dm(user, message, embed)

    async def _send_tournament_started(
        self,
        user: User,
        event_data: dict
    ) -> tuple[NotificationDeliveryStatus, Optional[str]]:
        """
        Send a tournament started notification.

        Args:
            user: User to notify
            event_data: Event data with tournament details

        Returns:
            Tuple of (delivery_status, error_message)
        """
        tournament_name = event_data.get('tournament_name', 'Unknown Tournament')
        
        embed = self._create_embed(
            title="🎮 Tournament Started",
            description=f"**{tournament_name}** has started!",
            color=discord.Color.green(),
            fields=[
                ("Tournament", tournament_name, False),
            ],
            footer_text="Good luck!"
        )

        message = f"Hey {user.get_display_name()}, the tournament has started!"
        return await self._send_discord_dm(user, message, embed)

    async def _send_tournament_ended(
        self,
        user: User,
        event_data: dict
    ) -> tuple[NotificationDeliveryStatus, Optional[str]]:
        """
        Send a tournament ended notification.

        Args:
            user: User to notify
            event_data: Event data with tournament details

        Returns:
            Tuple of (delivery_status, error_message)
        """
        tournament_name = event_data.get('tournament_name', 'Unknown Tournament')
        winner = event_data.get('winner', 'TBD')
        
        embed = self._create_embed(
            title="🏁 Tournament Ended",
            description=f"**{tournament_name}** has concluded!",
            color=discord.Color.purple(),
            fields=[
                ("Tournament", tournament_name, False),
                ("Winner", winner, False),
            ],
            footer_text="Thanks for participating!"
        )

        message = f"Hey {user.get_display_name()}, the tournament has ended!"
        return await self._send_discord_dm(user, message, embed)

    async def _send_organization_member_added(
        self,
        user: User,
        event_data: dict
    ) -> tuple[NotificationDeliveryStatus, Optional[str]]:
        """
        Send organization member added notification.

        Args:
            user: User to notify
            event_data: Event data with organization details

        Returns:
            Tuple of (delivery_status, error_message)
        """
        org_name = event_data.get('organization_name', 'Unknown Organization')
        added_by = event_data.get('added_by', 'Admin')
        
        embed = self._create_embed(
            title="👥 Added to Organization",
            description=f"You've been added to **{org_name}**!",
            color=discord.Color.blue(),
            fields=[
                ("Organization", org_name, False),
                ("Added By", added_by, False),
            ],
            footer_text="Welcome to the organization!"
        )

        message = f"Hey {user.get_display_name()}, you've been added to an organization!"
        return await self._send_discord_dm(user, message, embed)

    async def _send_user_permission_changed(
        self,
        user: User,
        event_data: dict
    ) -> tuple[NotificationDeliveryStatus, Optional[str]]:
        """
        Send user permission changed notification.

        Args:
            user: User to notify
            event_data: Event data with permission details

        Returns:
            Tuple of (delivery_status, error_message)
        """
        old_permission = event_data.get('old_permission', 'Unknown')
        new_permission = event_data.get('new_permission', 'Unknown')
        changed_by = event_data.get('changed_by', 'Admin')
        
        embed = self._create_embed(
            title="🔐 Permissions Updated",
            description="Your global permissions have been updated.",
            color=discord.Color.blue(),
            fields=[
                ("Old Permission", old_permission, True),
                ("New Permission", new_permission, True),
                ("Changed By", changed_by, False),
            ],
            footer_text="Your access level has been modified"
        )

        message = f"Hey {user.get_display_name()}, your permissions have been updated!"
        return await self._send_discord_dm(user, message, embed)

    async def _send_organization_permission_changed(
        self,
        user: User,
        event_data: dict
    ) -> tuple[NotificationDeliveryStatus, Optional[str]]:
        """
        Send organization permission changed notification.

        Args:
            user: User to notify
            event_data: Event data with permission details

        Returns:
            Tuple of (delivery_status, error_message)
        """
        org_name = event_data.get('organization_name', 'Unknown Organization')
        old_permission = event_data.get('old_permission', 'Unknown')
        new_permission = event_data.get('new_permission', 'Unknown')
        changed_by = event_data.get('changed_by', 'Admin')
        
        embed = self._create_embed(
            title="🔐 Organization Permissions Updated",
            description=f"Your permissions in **{org_name}** have been updated.",
            color=discord.Color.blue(),
            fields=[
                ("Organization", org_name, False),
                ("Old Permission", old_permission, True),
                ("New Permission", new_permission, True),
                ("Changed By", changed_by, False),
            ],
            footer_text="Your organization access level has been modified"
        )

        message = f"Hey {user.get_display_name()}, your organization permissions have been updated!"
        return await self._send_discord_dm(user, message, embed)

    async def _send_tournament_updated(
        self,
        user: User,
        event_data: dict
    ) -> tuple[NotificationDeliveryStatus, Optional[str]]:
        """
        Send tournament updated notification.

        Args:
            user: User to notify
            event_data: Event data with tournament details

        Returns:
            Tuple of (delivery_status, error_message)
        """
        tournament_name = event_data.get('tournament_name', 'Unknown Tournament')
        changed_fields = event_data.get('changed_fields', [])
        
        fields_str = ", ".join(changed_fields) if changed_fields else "Multiple fields"
        
        embed = self._create_embed(
            title="📝 Tournament Updated",
            description=f"**{tournament_name}** has been updated.",
            color=discord.Color.orange(),
            fields=[
                ("Tournament", tournament_name, False),
                ("Updated Fields", fields_str, False),
            ],
            footer_text="Check the tournament page for details"
        )

        message = f"Hey {user.get_display_name()}, a tournament has been updated!"
        return await self._send_discord_dm(user, message, embed)

    async def _send_organization_member_removed(
        self,
        user: User,
        event_data: dict
    ) -> tuple[NotificationDeliveryStatus, Optional[str]]:
        """
        Send organization member removed notification.

        Args:
            user: User to notify
            event_data: Event data with organization details

        Returns:
            Tuple of (delivery_status, error_message)
        """
        org_name = event_data.get('organization_name', 'Unknown Organization')
        removed_by = event_data.get('removed_by', 'Admin')
        
        embed = self._create_embed(
            title="👋 Removed from Organization",
            description=f"You've been removed from **{org_name}**.",
            color=discord.Color.red(),
            fields=[
                ("Organization", org_name, False),
                ("Removed By", removed_by, False),
            ],
            footer_text="Contact an admin if you have questions"
        )

        message = f"Hey {user.get_display_name()}, you've been removed from an organization."
        return await self._send_discord_dm(user, message, embed)
