"""
Notification log models.

Tracks notification delivery history and status.
"""

from enum import IntEnum
from tortoise import fields
from tortoise.models import Model


class NotificationDeliveryStatus(IntEnum):
    """Status of notification delivery attempt."""

    PENDING = 0  # Queued for delivery
    SENT = 1  # Successfully sent
    FAILED = 2  # Failed to send
    RETRYING = 3  # Failed but will retry


class NotificationLog(Model):
    """
    Log of sent/attempted notifications.

    Tracks all notification delivery attempts for auditing and debugging.
    """

    id = fields.IntField(pk=True)

    # User who should receive this notification
    user = fields.ForeignKeyField("models.User", related_name="notification_logs")

    # Type of event that triggered this notification
    event_type = fields.IntField()  # NotificationEventType value

    # How the notification was/should be delivered
    notification_method = fields.IntField()  # NotificationMethod value

    # Event data (JSON) - contains details about what happened
    event_data = fields.JSONField(default=dict)

    # Delivery status
    delivery_status = fields.IntEnumField(
        NotificationDeliveryStatus, default=NotificationDeliveryStatus.PENDING
    )

    # Error message if delivery failed
    error_message = fields.TextField(null=True)

    # Number of delivery attempts
    retry_count = fields.IntField(default=0)

    # Timestamps
    created_at = fields.DatetimeField(auto_now_add=True)  # When notification was queued
    sent_at = fields.DatetimeField(null=True)  # When successfully delivered
    updated_at = fields.DatetimeField(auto_now=True)  # Last status update

    class Meta:
        table = "notification_logs"
        indexes = (
            ("user", "created_at"),
            ("delivery_status",),
            ("event_type",),
        )
        ordering = ["-created_at"]

    def __str__(self) -> str:
        user_id = getattr(self, "user_id", None)
        status_name = NotificationDeliveryStatus(self.delivery_status).name
        return (
            f"NotificationLog({user_id}: event={self.event_type}, status={status_name})"
        )
