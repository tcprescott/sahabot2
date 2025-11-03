"""API schemas for audit logs."""

from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class AuditLogOut(BaseModel):
    """Schema for audit log output."""

    id: int
    user_id: Optional[int] = None
    action: str
    details: Optional[dict[str, Any]] = None
    ip_address: Optional[str] = None
    organization_id: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    """Schema for audit log list response."""

    items: list[AuditLogOut]
    count: int
    total: int  # Total matching records before pagination
