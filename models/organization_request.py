"""
Organization request database model.

This module defines the database model for organization creation requests.
"""

from tortoise import fields
from tortoise.models import Model


class OrganizationRequest(Model):
    """
    Model for organization creation requests.

    Users can request the creation of new organizations, which must be
    approved by a SUPERADMIN before the organization is created.

    Attributes:
        id: Primary key
        name: Requested organization name
        description: Organization description
        requested_by: User who requested the organization
        status: Request status (pending, approved, rejected)
        reviewed_by: SUPERADMIN who reviewed the request
        review_notes: Optional notes from reviewer
        requested_at: When the request was created
        reviewed_at: When the request was reviewed
    """

    class RequestStatus(str):
        """Organization request status enum."""
        PENDING = "pending"
        APPROVED = "approved"
        REJECTED = "rejected"

    id = fields.IntField(pk=True)
    name = fields.CharField(
        200,
        description="Requested organization name"
    )
    description = fields.TextField(
        null=True,
        description="Organization description"
    )
    requested_by = fields.ForeignKeyField(
        'models.User',
        related_name='organization_requests',
        description="User who requested the organization"
    )
    status = fields.CharField(
        20,
        default=RequestStatus.PENDING,
        description="Request status"
    )
    reviewed_by = fields.ForeignKeyField(
        'models.User',
        related_name='reviewed_org_requests',
        null=True,
        description="SUPERADMIN who reviewed the request"
    )
    review_notes = fields.TextField(
        null=True,
        description="Optional notes from reviewer"
    )
    requested_at = fields.DatetimeField(auto_now_add=True)
    reviewed_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "organization_requests"
        indexes = (
            ("requested_by_id",),
            ("status",),
            ("requested_at",),
        )

    def __str__(self):
        """Return string representation of request."""
        return f"{self.name} ({self.status})"

    @property
    def is_pending(self) -> bool:
        """Check if request is pending."""
        return self.status == self.RequestStatus.PENDING

    @property
    def is_approved(self) -> bool:
        """Check if request is approved."""
        return self.status == self.RequestStatus.APPROVED

    @property
    def is_rejected(self) -> bool:
        """Check if request is rejected."""
        return self.status == self.RequestStatus.REJECTED
