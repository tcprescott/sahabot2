"""
Authorization models for policy-based access control.

Models:
- OrganizationRole: Named roles within organizations (built-in and custom)
- OrganizationMemberRole: Role assignments (many-to-many)
- PolicyStatement: Individual policies with Effect/Actions/Resources/Conditions
- RolePolicy: Links policies to roles
- UserPolicy: Direct user policy assignments
"""

from tortoise import fields
from tortoise.models import Model


class OrganizationRole(Model):
    """
    Roles within an organization (both built-in and custom).
    
    Built-in roles (is_builtin=True):
    - Auto-created when organization is created
    - Permissions defined statically in code (not in database)
    - Cannot be modified, renamed, or deleted (if is_locked=True)
    - Same across all organizations
    
    Custom roles (is_builtin=False):
    - Created by organization admins
    - Permissions defined via PolicyStatement records
    - Fully customizable
    """
    
    id = fields.IntField(pk=True)
    organization = fields.ForeignKeyField(
        'models.Organization',
        related_name='roles',
        on_delete=fields.CASCADE
    )
    name = fields.CharField(max_length=100)
    description = fields.TextField(null=True)
    
    # Built-in role flags
    is_builtin = fields.BooleanField(default=False)
    is_locked = fields.BooleanField(default=False)
    
    # Timestamps
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    created_by = fields.ForeignKeyField(
        'models.User',
        related_name='created_roles',
        null=True,
        on_delete=fields.SET_NULL
    )
    
    class Meta:
        table = "organization_roles"
        unique_together = (("organization", "name"),)
        indexes = [
            ("organization", "is_builtin"),
            ("organization", "is_locked"),
        ]


class OrganizationMemberRole(Model):
    """
    Many-to-many relationship between organization members and roles.
    
    A member can have multiple roles in an organization.
    """
    
    id = fields.IntField(pk=True)
    member = fields.ForeignKeyField(
        'models.OrganizationMember',
        related_name='role_assignments',
        on_delete=fields.CASCADE
    )
    role = fields.ForeignKeyField(
        'models.OrganizationRole',
        related_name='member_assignments',
        on_delete=fields.CASCADE
    )
    
    # Timestamps
    assigned_at = fields.DatetimeField(auto_now_add=True)
    assigned_by = fields.ForeignKeyField(
        'models.User',
        related_name='role_assignments_made',
        null=True,
        on_delete=fields.SET_NULL
    )
    
    class Meta:
        table = "organization_member_roles"
        unique_together = (("member", "role"),)
        indexes = [
            ("member",),
            ("role",),
        ]


class PolicyStatement(Model):
    """
    Individual policy statement with Effect/Actions/Resources/Conditions.
    
    Only used for custom roles (is_builtin=False).
    Built-in roles use static permissions defined in code.
    
    Fields:
    - effect: "ALLOW" or "DENY"
    - actions: JSON array of action strings (e.g., ["tournament:create", "tournament:update"])
    - resources: JSON array of resource patterns (e.g., ["tournament:*", "organization:{org_id}"])
    - conditions: JSON object with conditional logic (optional)
    """
    
    id = fields.IntField(pk=True)
    
    # Policy components
    effect = fields.CharField(max_length=10)  # "ALLOW" or "DENY"
    actions = fields.JSONField()  # List[str]
    resources = fields.JSONField()  # List[str]
    conditions = fields.JSONField(null=True)  # Optional dict
    
    # Metadata
    description = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "policy_statements"


class RolePolicy(Model):
    """
    Links PolicyStatement to OrganizationRole.
    
    Only used for custom roles (is_builtin=False).
    Built-in roles don't have policy records.
    """
    
    id = fields.IntField(pk=True)
    role = fields.ForeignKeyField(
        'models.OrganizationRole',
        related_name='policies',
        on_delete=fields.CASCADE
    )
    policy_statement = fields.ForeignKeyField(
        'models.PolicyStatement',
        related_name='role_links',
        on_delete=fields.CASCADE
    )
    
    # Metadata
    created_at = fields.DatetimeField(auto_now_add=True)
    created_by = fields.ForeignKeyField(
        'models.User',
        related_name='role_policies_created',
        null=True,
        on_delete=fields.SET_NULL
    )
    
    class Meta:
        table = "role_policies"
        unique_together = (("role", "policy_statement"),)
        indexes = [
            ("role",),
            ("policy_statement",),
        ]


class UserPolicy(Model):
    """
    Direct policy assignments to users (bypassing roles).
    
    Allows for user-specific permissions without creating a role.
    Scoped to a specific organization.
    """
    
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField(
        'models.User',
        related_name='direct_policies',
        on_delete=fields.CASCADE
    )
    organization = fields.ForeignKeyField(
        'models.Organization',
        related_name='user_policies',
        on_delete=fields.CASCADE
    )
    policy_statement = fields.ForeignKeyField(
        'models.PolicyStatement',
        related_name='user_links',
        on_delete=fields.CASCADE
    )
    
    # Metadata
    created_at = fields.DatetimeField(auto_now_add=True)
    created_by = fields.ForeignKeyField(
        'models.User',
        related_name='user_policies_created',
        null=True,
        on_delete=fields.SET_NULL
    )
    
    class Meta:
        table = "user_policies"
        unique_together = (("user", "organization", "policy_statement"),)
        indexes = [
            ("user", "organization"),
        ]
