"""
Notification subscription models.

Manages user subscriptions to event notifications.
"""

from enum import IntEnum
from tortoise import fields
from tortoise.models import Model


class NotificationMethod(IntEnum):
    """Notification delivery method."""

    DISCORD_DM = 1  # Discord direct message
    EMAIL = 2  # Email (future)
    WEBHOOK = 3  # Webhook callback (future)
    SMS = 4  # SMS (future)


class NotificationEventType(IntEnum):
    """
    Event types that users can subscribe to for notifications.
    
    These map to a subset of the events already emitted in the system.
    """

    # User-specific events
    USER_PERMISSION_CHANGED = 100
    
    # Organization events (requires org membership)
    ORGANIZATION_MEMBER_ADDED = 200
    ORGANIZATION_MEMBER_REMOVED = 201
    ORGANIZATION_PERMISSION_CHANGED = 202
    
    # Tournament events (requires tournament participation or admin)
    TOURNAMENT_CREATED = 300
    TOURNAMENT_STARTED = 301
    TOURNAMENT_ENDED = 302
    TOURNAMENT_UPDATED = 303
    
    # Match/Race events (requires participation)
    MATCH_SCHEDULED = 400
    MATCH_RESCHEDULED = 401
    MATCH_COMPLETED = 402
    MATCH_CANCELLED = 403
    RACE_SUBMITTED = 410
    RACE_APPROVED = 411
    RACE_REJECTED = 412
    
    # Invite events (requires being the invitee)
    INVITE_RECEIVED = 500
    INVITE_ACCEPTED = 501
    INVITE_REJECTED = 502
    INVITE_EXPIRED = 503


class NotificationSubscription(Model):
    """
    User subscription to event notifications.
    
    Users can subscribe to specific event types and choose how to be notified.
    Some events are personal (e.g., match scheduled for user), others are
    organization-wide (e.g., tournament created in org).
    """

    id = fields.IntField(pk=True)
    
    # User who created this subscription
    user = fields.ForeignKeyField("models.User", related_name="notification_subscriptions")
    
    # Event type to subscribe to
    event_type = fields.IntEnumField(NotificationEventType)
    
    # How to deliver the notification
    notification_method = fields.IntEnumField(NotificationMethod)
    
    # Optional: organization scope (for org-wide events like tournament creation)
    # If None, applies to all organizations the user is a member of
    organization = fields.ForeignKeyField(
        "models.Organization",
        related_name="notification_subscriptions",
        null=True
    )
    
    # Whether this subscription is active
    is_active = fields.BooleanField(default=True)
    
    # Timestamps
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "notification_subscriptions"
        unique_together = (("user", "event_type", "notification_method", "organization"),)
        indexes = (
            ("user", "is_active"),
            ("event_type", "is_active"),
            ("organization", "is_active"),
        )

    def __str__(self) -> str:
        org_id = getattr(self, 'organization_id', None)
        user_id = getattr(self, 'user_id', None)
        org_suffix = f" (org: {org_id})" if org_id else ""
        return (
            f"Subscription({user_id}: "
            f"{NotificationEventType(self.event_type).name} → "
            f"{NotificationMethod(self.notification_method).name}{org_suffix})"
        )
