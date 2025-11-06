"""API endpoints for audit logs."""

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from api.schemas.audit_log import AuditLogOut, AuditLogListResponse
from api.deps import get_current_user, enforce_rate_limit
from application.services.core.audit_service import AuditService
from models import User, Permission

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


@router.get(
    "/",
    response_model=AuditLogListResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="List Audit Logs",
    description="List audit logs. Requires SUPERADMIN permission.",
)
async def list_audit_logs(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of logs to return"),
    offset: int = Query(0, ge=0, description="Number of logs to skip"),
    user_id: int | None = Query(None, description="Filter by user ID"),
    action: str | None = Query(None, description="Filter by action"),
    organization_id: int | None = Query(None, description="Filter by organization ID"),
    current_user: User = Depends(get_current_user)
) -> AuditLogListResponse:
    """
    List audit logs with optional filters.

    Only SUPERADMIN users can view audit logs.

    Args:
        limit: Maximum number of logs to return
        offset: Number of logs to skip
        user_id: Optional user ID filter
        action: Optional action filter
        organization_id: Optional organization ID filter
        current_user: Authenticated user

    Returns:
        AuditLogListResponse: List of audit logs

    Raises:
        HTTPException: 403 if not authorized
    """
    if not current_user.has_permission(Permission.SUPERADMIN):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    service = AuditService()
    logs, total = await service.list_audit_logs(
        limit=limit,
        offset=offset,
        user_id=user_id,
        action=action,
        organization_id=organization_id
    )

    items = [AuditLogOut.model_validate(log) for log in logs]
    return AuditLogListResponse(items=items, count=len(items), total=total)


@router.get(
    "/organizations/{organization_id}",
    response_model=AuditLogListResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="List Organization Audit Logs",
    description="List audit logs for a specific organization.",
)
async def list_organization_audit_logs(
    organization_id: int = Path(..., description="Organization ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of logs to return"),
    offset: int = Query(0, ge=0, description="Number of logs to skip"),
    user_id: int | None = Query(None, description="Filter by user ID"),
    action: str | None = Query(None, description="Filter by action"),
    current_user: User = Depends(get_current_user)
) -> AuditLogListResponse:
    """
    List audit logs for an organization.

    User must be able to admin the organization.

    Args:
        organization_id: Organization ID
        limit: Maximum number of logs to return
        offset: Number of logs to skip
        user_id: Optional user ID filter
        action: Optional action filter
        current_user: Authenticated user

    Returns:
        AuditLogListResponse: List of audit logs

    Raises:
        HTTPException: 403 if not authorized
    """
    # Check authorization
    from application.services.organizations.organization_service import OrganizationService
    org_service = OrganizationService()
    can_admin = await org_service.user_can_admin_org(current_user, organization_id)
    if not can_admin:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    service = AuditService()
    logs, total = await service.list_audit_logs(
        limit=limit,
        offset=offset,
        user_id=user_id,
        action=action,
        organization_id=organization_id
    )

    items = [AuditLogOut.model_validate(log) for log in logs]
    return AuditLogListResponse(items=items, count=len(items), total=total)


@router.get(
    "/users/{user_id}",
    response_model=AuditLogListResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="List User Audit Logs",
    description="List audit logs for a specific user.",
)
async def list_user_audit_logs(
    user_id: int = Path(..., description="User ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of logs to return"),
    offset: int = Query(0, ge=0, description="Number of logs to skip"),
    action: str | None = Query(None, description="Filter by action"),
    organization_id: int | None = Query(None, description="Filter by organization ID"),
    current_user: User = Depends(get_current_user)
) -> AuditLogListResponse:
    """
    List audit logs for a specific user.

    Users can view their own logs. SUPERADMIN can view any user's logs.

    Args:
        user_id: User ID
        limit: Maximum number of logs to return
        offset: Number of logs to skip
        action: Optional action filter
        organization_id: Optional organization ID filter
        current_user: Authenticated user

    Returns:
        AuditLogListResponse: List of audit logs

    Raises:
        HTTPException: 403 if not authorized
    """
    # Users can view their own logs, SUPERADMIN can view any
    if current_user.id != user_id and not current_user.has_permission(Permission.SUPERADMIN):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    service = AuditService()
    logs, total = await service.list_audit_logs(
        limit=limit,
        offset=offset,
        user_id=user_id,
        action=action,
        organization_id=organization_id
    )

    items = [AuditLogOut.model_validate(log) for log in logs]
    return AuditLogListResponse(items=items, count=len(items), total=total)
