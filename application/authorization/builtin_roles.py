"""
Built-in role definitions and static permission mappings.

Built-in roles are standard roles automatically created for all organizations.
Their permissions are defined statically in code (not in database) for:
- Consistency across all organizations
- Performance (no database lookups)
- Safety (cannot be accidentally modified)

Organizations can create custom roles if different permissions are needed.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class BuiltinRoleDefinition:
    """
    Definition of a built-in role.

    Attributes:
        name: Role name (e.g., "Admin", "Tournament Manager")
        description: Human-readable description
        is_locked: If True, role cannot be deleted
        actions: List of actions this role can perform (e.g., "tournament:*")
        scope: "organization" or "system" - which type of org this role is for
    """

    name: str
    description: str
    is_locked: bool
    actions: List[str]
    scope: str  # "organization" or "system"


# =============================================================================
# Regular Organization Built-in Roles
# =============================================================================

REGULAR_ORG_BUILTIN_ROLES = [
    BuiltinRoleDefinition(
        name="Admin",
        description="Full administrative access to organization",
        is_locked=True,
        actions=[
            "organization:*",  # All organization actions
            "member:*",  # All member actions
            "tournament:*",  # All tournament actions
            "match:*",  # All match actions
            "async_race:*",  # All async race actions
            "async_tournament:*",  # All async tournament actions
            "async_live_race:*",  # All async live race actions
            "scheduled_task:*",  # All scheduled task actions
            "race_room_profile:*",  # All race room profile actions
        ],
        scope="organization",
    ),
    BuiltinRoleDefinition(
        name="Tournament Manager",
        description="Manage tournaments and matches",
        is_locked=True,
        actions=[
            "tournament:*",  # All tournament actions
            "match:*",  # All match actions
            "async_tournament:*",  # All async tournament actions
            "scheduled_task:*",  # All scheduled task actions (for tournament scheduling)
            "race_room_profile:*",  # All race room profile actions (for tournament setup)
            "organization:read",  # Read org info
        ],
        scope="organization",
    ),
    BuiltinRoleDefinition(
        name="Async Reviewer",
        description="Review and approve async race submissions",
        is_locked=True,
        actions=[
            "async_race:review",  # Review submissions
            "async_race:approve",  # Approve submissions
            "async_race:reject",  # Reject submissions
            "tournament:read",  # Read tournament info
            "match:read",  # Read match info
        ],
        scope="organization",
    ),
    BuiltinRoleDefinition(
        name="Member Manager",
        description="Manage organization members and invites",
        is_locked=True,
        actions=[
            "member:*",  # All member actions
            "organization:read",  # Read org info
        ],
        scope="organization",
    ),
    BuiltinRoleDefinition(
        name="Moderator",
        description="View-only access to organization resources",
        is_locked=False,  # Can be deleted if org doesn't need it
        actions=[
            "organization:read",
            "member:read",
            "tournament:read",
            "match:read",
        ],
        scope="organization",
    ),
]


# =============================================================================
# System Organization Built-in Roles (for organization_id = -1)
# =============================================================================

SYSTEM_ORG_BUILTIN_ROLES = [
    BuiltinRoleDefinition(
        name="User Manager",
        description="Manage platform user accounts",
        is_locked=True,
        actions=[
            "system:view_users",
            "system:manage_users",
        ],
        scope="system",
    ),
    BuiltinRoleDefinition(
        name="Organization Manager",
        description="Create and manage organizations",
        is_locked=True,
        actions=[
            "system:create_organization",
            "system:manage_organizations",
        ],
        scope="system",
    ),
    BuiltinRoleDefinition(
        name="Analytics Viewer",
        description="View platform analytics and reports",
        is_locked=True,
        actions=[
            "system:view_analytics",
            "system:view_audit_logs",
        ],
        scope="system",
    ),
    BuiltinRoleDefinition(
        name="Platform Moderator",
        description="Platform-wide moderation capabilities",
        is_locked=True,
        actions=[
            "system:moderate_content",
            "system:view_reports",
        ],
        scope="system",
    ),
]


# =============================================================================
# Public API Functions
# =============================================================================


def get_builtin_role_definitions(organization_id: int) -> List[BuiltinRoleDefinition]:
    """
    Get built-in role definitions for an organization.

    Args:
        organization_id: Organization ID
            -1 for System organization
            >0 for regular organizations

    Returns:
        List of built-in role definitions for this organization type
    """
    if organization_id == -1:
        return SYSTEM_ORG_BUILTIN_ROLES
    else:
        return REGULAR_ORG_BUILTIN_ROLES


def get_builtin_role_actions(
    role_name: str, organization_id: int
) -> Optional[List[str]]:
    """
    Get static actions for a built-in role.

    Args:
        role_name: Name of built-in role (e.g., "Admin", "User Manager")
        organization_id: Organization ID (-1 for system, >0 for regular)

    Returns:
        List of actions this role can perform, or None if role not found
    """
    role_defs = get_builtin_role_definitions(organization_id)

    for role_def in role_defs:
        if role_def.name == role_name:
            return role_def.actions

    return None


def is_builtin_role(role_name: str, organization_id: int) -> bool:
    """
    Check if a role name is a built-in role for this organization.

    Args:
        role_name: Role name to check
        organization_id: Organization ID

    Returns:
        True if this is a built-in role for this org type
    """
    role_defs = get_builtin_role_definitions(organization_id)
    return any(role_def.name == role_name for role_def in role_defs)
