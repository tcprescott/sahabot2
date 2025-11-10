"""
Authorization Service V2 - Service layer wrapper around PolicyEngine.

This service provides the main API for authorization checks in the application.
It wraps the PolicyEngine with a cleaner service-level interface and handles
logging, error handling, and common authorization patterns.
"""

import logging
from typing import Optional
from dataclasses import dataclass

from models import User, Permission
from application.authorization.policy_engine import PolicyEngine, AuthorizationContext
from application.authorization.policy_cache import (
    invalidate_user_cache,
    invalidate_organization_cache,
)

logger = logging.getLogger(__name__)


@dataclass
class AuthorizationResult:
    """Result of an authorization check with additional context."""

    allowed: bool
    reason: str
    user_id: int
    action: str
    resource: str
    organization_id: Optional[int]


class AuthorizationServiceV2:
    """
    Service layer wrapper around PolicyEngine.

    This service provides the main authorization API for the application.
    All authorization checks should go through this service.
    """

    def __init__(self):
        """Initialize the authorization service."""
        self.engine = PolicyEngine()

    async def authorize(
        self,
        user: User,
        action: str,
        resource: str,
        organization_id: Optional[int] = None,
    ) -> AuthorizationResult:
        """
        Check if a user is authorized to perform an action on a resource.

        This is the main authorization check method. It returns detailed information
        about the authorization decision, including whether access was allowed and why.

        Args:
            user: User attempting the action
            action: Action being attempted (e.g., "tournament:create")
            resource: Resource being accessed (e.g., "tournament:123")
            organization_id: Organization context (None for global actions)

        Returns:
            AuthorizationResult with decision and reason

        Examples:
            # Check tournament creation
            result = await auth.authorize(user, "tournament:create", "tournament:*", org_id=1)
            if result.allowed:
                # Proceed with tournament creation
                pass

            # Check user management
            result = await auth.authorize(user, "user:update", f"user:{target_user.id}")
            if not result.allowed:
                logger.warning("Unauthorized: %s", result.reason)
        """
        # Create authorization context
        context = AuthorizationContext(
            user_id=user.id,
            action=action,
            resource=resource,
            organization_id=organization_id,
        )

        # Evaluate policy
        policy_result = await self.engine.evaluate(context)

        # Convert to service-level result
        result = AuthorizationResult(
            allowed=policy_result.allowed,
            reason=policy_result.reason,
            user_id=user.id,
            action=action,
            resource=resource,
            organization_id=organization_id,
        )

        # Log authorization decision
        if not result.allowed:
            logger.warning(
                "Authorization denied: user=%s action=%s resource=%s org=%s reason=%s",
                user.id,
                action,
                resource,
                organization_id,
                result.reason,
            )
        else:
            logger.debug(
                "Authorization granted: user=%s action=%s resource=%s org=%s",
                user.id,
                action,
                resource,
                organization_id,
            )

        return result

    async def require(
        self,
        user: User,
        action: str,
        resource: str,
        organization_id: Optional[int] = None,
    ) -> None:
        """
        Require authorization for an action, raising exception if denied.

        This is a convenience wrapper around authorize() that raises an exception
        if the user is not authorized. Use this when you want to fail fast on
        unauthorized access.

        Args:
            user: User attempting the action
            action: Action being attempted
            resource: Resource being accessed
            organization_id: Organization context

        Raises:
            PermissionError: If user is not authorized

        Examples:
            # Require tournament management permission
            await auth.require(user, "tournament:update", f"tournament:{tournament_id}", org_id=1)
            # If we get here, user is authorized - proceed with update

            # Require global admin permission
            await auth.require(user, "user:delete", f"user:{user_id}")
            # If we get here, user is authorized - proceed with deletion
        """
        result = await self.authorize(user, action, resource, organization_id)

        if not result.allowed:
            raise PermissionError(
                f"User {user.id} not authorized for action '{action}' on resource '{resource}': {result.reason}"
            )

    async def can(
        self,
        user: User,
        action: str,
        resource: str,
        organization_id: Optional[int] = None,
    ) -> bool:
        """
        Simple boolean check for authorization.

        This is a convenience wrapper around authorize() that returns just a
        boolean. Use this when you only need a yes/no answer and don't need
        the detailed reason.

        Args:
            user: User attempting the action
            action: Action being attempted
            resource: Resource being accessed
            organization_id: Organization context

        Returns:
            True if authorized, False otherwise

        Examples:
            # Check if user can create tournaments
            if await auth.can(user, "tournament:create", "tournament:*", org_id=1):
                # Show create button
                pass

            # Check if user can view analytics
            if await auth.can(user, "analytics:view", "analytics:*", org_id=-1):
                # Show analytics dashboard
                pass
        """
        result = await self.authorize(user, action, resource, organization_id)
        return result.allowed

    async def invalidate_user_permissions(self, user_id: int) -> None:
        """
        Invalidate cached permissions for a user.

        Call this when a user's permissions change (e.g., role assignment/removal,
        user policy changes, etc.).

        Args:
            user_id: User whose permissions changed
        """
        invalidate_user_cache(user_id)
        logger.info("Invalidated permission cache for user %s", user_id)

    async def invalidate_organization_permissions(self, organization_id: int) -> None:
        """
        Invalidate cached permissions for an entire organization.

        Call this when organization-wide permissions change (e.g., role policy
        changes, built-in role modifications, etc.).

        Args:
            organization_id: Organization whose permissions changed
        """
        invalidate_organization_cache(organization_id)
        logger.info("Invalidated permission cache for organization %s", organization_id)

    def get_action_for_operation(self, resource_type: str, operation: str) -> str:
        """
        Build an action string from resource type and operation.

        Helper method to construct consistent action strings following the
        "resource:operation" pattern.

        Args:
            resource_type: Type of resource (e.g., "tournament", "user")
            operation: Operation being performed (e.g., "create", "update", "delete")

        Returns:
            Action string in format "resource:operation"

        Examples:
            action = auth.get_action_for_operation("tournament", "create")
            # Returns: "tournament:create"

            action = auth.get_action_for_operation("user", "update")
            # Returns: "user:update"
        """
        return f"{resource_type}:{operation}"

    def get_resource_identifier(
        self, resource_type: str, resource_id: Optional[int] = None
    ) -> str:
        """
        Build a resource identifier string.

        Helper method to construct consistent resource identifiers following the
        "resource:id" pattern, or "resource:*" for wildcards.

        Args:
            resource_type: Type of resource (e.g., "tournament", "user")
            resource_id: ID of specific resource (None for wildcard)

        Returns:
            Resource identifier in format "resource:id" or "resource:*"

        Examples:
            resource = auth.get_resource_identifier("tournament", 123)
            # Returns: "tournament:123"

            resource = auth.get_resource_identifier("tournament")
            # Returns: "tournament:*"
        """
        if resource_id is not None:
            return f"{resource_type}:{resource_id}"
        return f"{resource_type}:*"

    async def check_global_admin(self, user: User) -> bool:
        """
        Check if user has global admin permissions.

        This is a convenience method for checking if a user has the ADMIN global
        permission. Global admins bypass all authorization checks.

        Args:
            user: User to check

        Returns:
            True if user is global admin, False otherwise
        """
        return user.permission == Permission.ADMIN

    async def check_superadmin(self, user: User) -> bool:
        """
        Check if user has superadmin permissions.

        This is a convenience method for checking if a user has the SUPERADMIN
        global permission. Superadmins have elevated privileges for platform
        management.

        Args:
            user: User to check

        Returns:
            True if user is superadmin, False otherwise
        """
        return user.permission == Permission.SUPERADMIN
