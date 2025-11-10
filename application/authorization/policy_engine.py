"""
Policy-based authorization engine.

The PolicyEngine evaluates authorization requests based on:
1. Global role (ADMIN bypasses all checks, USER uses policies)
2. Built-in role permissions (static, defined in code)
3. Custom role policies (from database)
4. Direct user policies (from database)

Evaluation uses DENY-wins logic: if any policy denies, access is denied.
"""

import logging
import fnmatch
from dataclasses import dataclass
from typing import List
from models import User, Permission, OrganizationMember, OrganizationMemberRole
from models import PolicyStatement, RolePolicy, UserPolicy
from application.authorization.builtin_roles import get_builtin_role_actions
from application.authorization.policy_cache import PolicyCache

logger = logging.getLogger(__name__)


@dataclass
class AuthorizationContext:
    """
    Context for an authorization request.

    Attributes:
        user_id: ID of user making the request
        action: Action being performed (e.g., "tournament:create")
        resource: Resource being accessed (e.g., "tournament:123")
        organization_id: Organization context (-1 for system, >0 for org)
    """

    user_id: int
    action: str
    resource: str
    organization_id: int


@dataclass
class PolicyEvaluationResult:
    """
    Result of policy evaluation.

    Attributes:
        allowed: True if access is granted
        reason: Human-readable explanation of decision
        matched_policies: List of policy IDs that matched
    """

    allowed: bool
    reason: str
    matched_policies: List[int]


class PolicyEngine:
    """
    Centralized policy evaluation engine.

    Evaluates authorization requests using:
    1. Global ADMIN bypass (always allowed)
    2. Built-in role permissions (static from code)
    3. Custom role policies (from database)
    4. Direct user policies (from database)

    Uses DENY-wins logic: if any policy denies, access is denied.
    """

    def __init__(self, cache: PolicyCache = None):
        """
        Initialize the PolicyEngine.

        Args:
            cache: Optional PolicyCache instance (defaults to new cache)
        """
        self._cache = cache if cache is not None else PolicyCache()
        self._cache_enabled = True

    async def evaluate(self, context: AuthorizationContext) -> PolicyEvaluationResult:
        """
        Evaluate an authorization request.

        Args:
            context: Authorization context

        Returns:
            PolicyEvaluationResult with decision and explanation
        """
        # Check cache first (if enabled)
        if self._cache_enabled:
            cached_result = self._cache.get(
                context.user_id,
                context.organization_id,
                context.action,
                context.resource,
            )
            if cached_result is not None:
                return PolicyEvaluationResult(
                    allowed=cached_result, reason="Cached result", matched_policies=[]
                )

        # Step 1: Load user
        user = await User.get_or_none(id=context.user_id)
        if not user:
            return PolicyEvaluationResult(
                allowed=False, reason="User not found", matched_policies=[]
            )

        # Step 2: Check global ADMIN bypass (includes SUPERADMIN)
        if user.permission >= Permission.ADMIN:
            logger.info(
                "User %s granted access (ADMIN bypass) for action %s on resource %s",
                user.id,
                context.action,
                context.resource,
            )
            return PolicyEvaluationResult(
                allowed=True, reason="Global ADMIN bypass", matched_policies=[]
            )

        # Step 3: Check organization membership
        is_member = await self._check_organization_membership(
            context.user_id, context.organization_id
        )

        if not is_member:
            logger.warning(
                "User %s denied access - not a member of organization %s",
                user.id,
                context.organization_id,
            )
            return PolicyEvaluationResult(
                allowed=False,
                reason=f"Not a member of organization {context.organization_id}",
                matched_policies=[],
            )

        # Step 4: Collect all applicable policies
        policies = await self._collect_policies(context)

        # Step 5: Evaluate policies (DENY wins)
        allow_policies = []
        deny_policies = []

        for policy in policies:
            if self._policy_matches(policy, context):
                if policy.effect == "DENY":
                    deny_policies.append(policy.id)
                elif policy.effect == "ALLOW":
                    allow_policies.append(policy.id)

        # Step 6: Make decision
        if deny_policies:
            logger.warning(
                "User %s denied access for action %s on resource %s (DENY policy matched)",
                user.id,
                context.action,
                context.resource,
            )
            result = PolicyEvaluationResult(
                allowed=False,
                reason="Access explicitly denied by policy",
                matched_policies=deny_policies,
            )
            # Cache the result
            if self._cache_enabled:
                self._cache.set(
                    context.user_id,
                    context.organization_id,
                    context.action,
                    context.resource,
                    result.allowed,
                )
            return result

        if allow_policies:
            logger.info(
                "User %s granted access for action %s on resource %s",
                user.id,
                context.action,
                context.resource,
            )
            result = PolicyEvaluationResult(
                allowed=True,
                reason="Access allowed by policy",
                matched_policies=allow_policies,
            )
            # Cache the result
            if self._cache_enabled:
                self._cache.set(
                    context.user_id,
                    context.organization_id,
                    context.action,
                    context.resource,
                    result.allowed,
                )
            return result

        # No matching policies
        logger.warning(
            "User %s denied access for action %s on resource %s (no matching policies)",
            user.id,
            context.action,
            context.resource,
        )
        result = PolicyEvaluationResult(
            allowed=False, reason="No policy grants access", matched_policies=[]
        )

        # Cache the result
        if self._cache_enabled:
            self._cache.set(
                context.user_id,
                context.organization_id,
                context.action,
                context.resource,
                result.allowed,
            )

        return result

    async def _check_organization_membership(
        self, user_id: int, organization_id: int
    ) -> bool:
        """
        Check if user is a member of the organization.

        Args:
            user_id: User ID
            organization_id: Organization ID (-1 for system, >0 for regular)

        Returns:
            True if user is a member
        """
        member = await OrganizationMember.get_or_none(
            organization_id=organization_id, user_id=user_id
        )
        return member is not None

    async def _collect_policies(
        self, context: AuthorizationContext
    ) -> List[PolicyStatement]:
        """
        Collect all policies applicable to this user/org/action.

        Collection order:
        1. Built-in role permissions (static from code)
        2. Custom role policies (database)
        3. Direct user policies (database)

        Args:
            context: Authorization context

        Returns:
            List of PolicyStatement objects (including virtual ones for built-in roles)
        """
        policies = []

        # 1. Check built-in roles (permissions from code)
        builtin_role_names = await self._get_user_builtin_roles(
            context.user_id, context.organization_id
        )

        for role_name in builtin_role_names:
            # Get static actions from code
            static_actions = get_builtin_role_actions(
                role_name, context.organization_id
            )
            if static_actions and self._action_matches_any(
                context.action, static_actions
            ):
                # Create virtual PolicyStatement for built-in role
                virtual_policy = PolicyStatement(
                    id=-1,  # Virtual policy (not in database)
                    effect="ALLOW",
                    actions=static_actions,
                    resources=["*"],  # Built-in roles apply to all resources in org
                    conditions=None,
                )
                policies.append(virtual_policy)

        # 2. Get custom role policies from database
        custom_role_policies = await self._get_custom_role_policies(
            context.user_id, context.organization_id
        )
        policies.extend(custom_role_policies)

        # 3. Get direct user policies from database
        user_policies = await self._get_user_policies(
            context.user_id, context.organization_id
        )
        policies.extend(user_policies)

        return policies

    async def _get_user_builtin_roles(
        self, user_id: int, organization_id: int
    ) -> List[str]:
        """
        Get built-in role names assigned to user in organization.

        Args:
            user_id: User ID
            organization_id: Organization ID

        Returns:
            List of built-in role names (e.g., ["Admin", "Tournament Manager"])
        """
        # Get member record
        member = await OrganizationMember.get_or_none(
            organization_id=organization_id, user_id=user_id
        )

        if not member:
            return []

        # Get role assignments
        role_assignments = await OrganizationMemberRole.filter(
            member=member
        ).prefetch_related("role")

        # Filter for built-in roles
        builtin_role_names = []
        for assignment in role_assignments:
            if assignment.role.is_builtin:
                builtin_role_names.append(assignment.role.name)

        return builtin_role_names

    async def _get_custom_role_policies(
        self, user_id: int, organization_id: int
    ) -> List[PolicyStatement]:
        """
        Get policies from custom roles assigned to user.

        Args:
            user_id: User ID
            organization_id: Organization ID

        Returns:
            List of PolicyStatement objects from custom roles
        """
        # Get member record
        member = await OrganizationMember.get_or_none(
            organization_id=organization_id, user_id=user_id
        )

        if not member:
            return []

        # Get role assignments for custom roles
        role_assignments = await OrganizationMemberRole.filter(
            member=member
        ).prefetch_related("role__policies__policy_statement")

        # Collect policies from custom roles only
        policies = []
        for assignment in role_assignments:
            if not assignment.role.is_builtin:
                # Get policies linked to this custom role
                role_policies = await RolePolicy.filter(
                    role=assignment.role
                ).prefetch_related("policy_statement")

                for role_policy in role_policies:
                    policies.append(role_policy.policy_statement)

        return policies

    async def _get_user_policies(
        self, user_id: int, organization_id: int
    ) -> List[PolicyStatement]:
        """
        Get direct policies assigned to user.

        Args:
            user_id: User ID
            organization_id: Organization ID

        Returns:
            List of PolicyStatement objects directly assigned to user
        """
        user_policies = await UserPolicy.filter(
            user_id=user_id, organization_id=organization_id
        ).prefetch_related("policy_statement")

        return [up.policy_statement for up in user_policies]

    def _policy_matches(
        self, policy: PolicyStatement, context: AuthorizationContext
    ) -> bool:
        """
        Check if a policy matches the authorization context.

        Args:
            policy: Policy to check
            context: Authorization context

        Returns:
            True if policy applies to this context
        """
        # Check if action matches
        if not self._action_matches_any(context.action, policy.actions):
            return False

        # Check if resource matches
        if not self._resource_matches_any(context.resource, policy.resources):
            return False

        # Note: Condition evaluation not yet implemented
        # Conditions will be added in future iteration

        return True

    def _action_matches_any(self, action: str, patterns: List[str]) -> bool:
        """
        Check if action matches any of the patterns.

        Supports wildcards:
        - "tournament:*" matches "tournament:create", "tournament:update", etc.
        - "tournament:create" matches exactly "tournament:create"

        Args:
            action: Action to check (e.g., "tournament:create")
            patterns: List of patterns (e.g., ["tournament:*", "match:read"])

        Returns:
            True if action matches any pattern
        """
        for pattern in patterns:
            if fnmatch.fnmatch(action, pattern):
                return True
        return False

    def _resource_matches_any(self, resource: str, patterns: List[str]) -> bool:
        """
        Check if resource matches any of the patterns.

        Supports wildcards:
        - "*" matches any resource
        - "tournament:*" matches "tournament:123", "tournament:456", etc.
        - "tournament:123" matches exactly "tournament:123"

        Args:
            resource: Resource to check (e.g., "tournament:123")
            patterns: List of patterns (e.g., ["*", "tournament:*"])

        Returns:
            True if resource matches any pattern
        """
        for pattern in patterns:
            if pattern == "*" or fnmatch.fnmatch(resource, pattern):
                return True
        return False
