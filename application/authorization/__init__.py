"""
Authorization package for policy-based access control.

This package implements a policy-based authorization system with:
- Built-in roles (static permissions defined in code)
- Custom roles (database-driven policies)
- PolicyEngine for centralized evaluation
- Support for organization-scoped and system-wide permissions
"""

from application.authorization.builtin_roles import (
    get_builtin_role_definitions,
    get_builtin_role_actions,
    BuiltinRoleDefinition,
)
from application.authorization.policy_engine import (
    PolicyEngine,
    AuthorizationContext,
    PolicyEvaluationResult,
)

__all__ = [
    "get_builtin_role_definitions",
    "get_builtin_role_actions",
    "BuiltinRoleDefinition",
    "PolicyEngine",
    "AuthorizationContext",
    "PolicyEvaluationResult",
]
