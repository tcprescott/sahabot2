# Authorization Architecture Redesign

## Current State Analysis

### Current Authorization Model

SahaBot2 currently uses a **hybrid authorization system** with two separate mechanisms:

#### 1. Global Roles (User Model)
- **Location**: `models/user.py` - `Permission` enum
- **Levels**: 
  - `USER = 0` - Standard user
  - `MODERATOR = 50` - Can moderate content
  - `ADMIN = 100` - Administrative access
  - `SUPERADMIN = 200` - Full system access
- **Stored**: Single `permission` field on `User` model
- **Scope**: Application-wide, not organization-specific

#### 2. Organization-Level Permissions
- **Location**: `models/organizations.py` - `OrganizationPermission` model
- **Implementation**: String-based permission names stored in database
- **Current Permissions** (defined in `OrganizationService`):
  - `ADMIN` - Full administrative access within organization
  - `TOURNAMENT_MANAGER` - Create and manage tournaments
  - `MEMBER_MANAGER` - Add/remove members and set permissions
  - `SCHEDULE_MANAGER` - Create and manage schedules/events
  - `MODERATOR` - Moderate interactions and content
  - `ASYNC_REVIEWER` - Review and approve async race submissions
- **Assignment**: Many-to-many relationship between members and permissions
- **Scope**: Organization-specific

### Current Authorization Logic

**Authorization checks are scattered across:**
1. `AuthorizationService` (global checks)
2. `OrganizationService` (organization checks)
3. Individual service methods (business logic mixed with authorization)

**Example patterns:**

```python
# Global role check
if user.has_permission(Permission.ADMIN):
    # Allow action

# Organization permission check
if await org_service.user_can_admin_org(user, org_id):
    # Allow action

# Mixed check
if user.has_permission(Permission.SUPERADMIN):
    return True  # Global override
# ... then check organization permissions
```

### Problems with Current Model

1. **Inconsistent Patterns**: Authorization logic split between multiple services
2. **Hard-coded Strings**: Organization permissions are string-based with no enum
3. **No Policy Framework**: No centralized policy evaluation
4. **Limited Granularity**: Can't express complex conditions (e.g., "can edit own tournaments only")
5. **No Resource-Level Permissions**: Can't specify permissions on specific resources
6. **Difficult to Audit**: Authorization decisions not logged consistently
7. **No Deny Policies**: Can only grant permissions, not explicitly deny
8. **Mixing Concerns**: Authorization logic embedded in service methods

---

## Proposed Authorization Architecture

### Design Goals

1. **Policy-Based Access Control (PBAC)** following AWS IAM-style patterns
2. **Clear Separation**: Roles vs Policies vs Permissions
3. **Granular Control**: Support resource-level and action-level permissions
4. **Centralized Evaluation**: Single policy engine for all authorization
5. **Auditable**: All authorization decisions logged
6. **Extensible**: Easy to add new actions, resources, and conditions
7. **Performance**: Efficient policy evaluation with caching

### Core Concepts

#### 1. Principals
**Who** is making the request?
- User (identified by user_id)
- System (SYSTEM_USER_ID)
- Service Account (future)

#### 2. Actions
**What** are they trying to do?
- Format: `service:action` (e.g., `tournament:create`, `member:invite`)
- Hierarchical: Can use wildcards (e.g., `tournament:*`, `*:read`)

#### 3. Resources
**What** are they trying to access?
- Format: `resource_type:resource_id` (e.g., `tournament:123`, `organization:5`)
- Special values: `*` (any resource), `organization:*` (any org)
- Support for resource hierarchies
- **Organization Scoping**: 
  - Organization-scoped resources: Use actual organization ID (e.g., `organization_id=5`)
  - Non-organization resources (system-wide): Use `organization_id=-1`

#### 4. Effect
**Allow** or **Deny** the action?
- `ALLOW`: Grant permission
- `DENY`: Explicitly deny (overrides allows)

#### 5. Conditions (Optional)
**Under what circumstances?**
- Context-based conditions (time, IP, MFA status, etc.)
- Resource attributes (e.g., tournament status, privacy settings)

---

## Proposed Database Schema

#### 1. Global Roles (Simplified)

```python
class GlobalRole(IntEnum):
    """Global system roles."""
    USER = 0              # Standard user
    ADMIN = 100           # System administrator - bypasses all policy checks
```

**Keep on User model:**
```python
class User(Model):
    # ... existing fields ...
    global_role = fields.IntEnumField(GlobalRole, default=GlobalRole.USER)  # Renamed from 'permission'
```

**Important**: 
- **USER**: Default role, all permissions determined by organization-scoped policies (including system org)
- **ADMIN**: Global administrator - automatically passes ALL policy checks (full system access)
- **System Organization**: We use a special organization with `id=-1` to represent the "System" organization
  - Regular users can be assigned roles in the System organization for platform-wide permissions
  - Allows ADMIN to delegate system-level access without granting full ADMIN role
  - Uses the same role/policy framework as regular organizations

### 2. Organization Roles

```python
class OrganizationRole(Model):
    """
    Roles within an organization.
    
    Built-in vs Custom Roles:
    - Built-in roles (is_builtin=True): Standard roles automatically created for all orgs
      - Defined statically in code (not in database policies)
      - Cannot be deleted, renamed, or modified
      - Same permissions across all organizations
      - Examples: "Admin", "Tournament Manager", "Async Reviewer"
    - Custom roles (is_builtin=False): Organization-specific roles
      - Can be created, modified, deleted by org admins
      - Fully customizable policies
      - Created when customization is needed
    
    Special case: When organization_id=-1, this represents a System-wide role
    for platform administration delegation.
    """
    id = fields.IntField(pk=True)
    organization = fields.ForeignKeyField('models.Organization', related_name='roles')
    name = fields.CharField(max_length=100)  # e.g., "Admin", "Tournament Manager", "User Manager"
    description = fields.TextField(null=True)
    is_builtin = fields.BooleanField(default=False)  # True for standard/built-in roles
    is_locked = fields.BooleanField(default=False)  # True to prevent deletion (for critical built-in roles)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    # Relations
    members: fields.ReverseRelation["OrganizationMemberRole"]
    policies: fields.ReverseRelation["RolePolicy"]
    
    class Meta:
        table = "organization_roles"
        unique_together = [("organization", "name")]
```

**Built-in Role Behavior**:
- Created automatically when organization is created (role record only, no policy records)
- Permissions defined statically in code, not in database
- System organization (id=-1) has its own set of built-in roles
- Regular organizations (id>0) get standard built-in roles
- Built-in roles are read-only (cannot modify permissions)
- Custom roles must be created if customization is needed

### 3. Organization Member Roles (Assignment)

```python
class OrganizationMemberRole(Model):
    """
    Links members to roles within organizations.
    
    Special case: When member.organization_id=-1, this represents system-wide
    role assignments for platform administration.
    """
    id = fields.IntField(pk=True)
    member = fields.ForeignKeyField('models.OrganizationMember', related_name='roles')
    role = fields.ForeignKeyField('models.OrganizationRole', related_name='member_assignments')
    granted_by = fields.ForeignKeyField('models.User', related_name='granted_roles', null=True)
    granted_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "organization_member_roles"
        unique_together = [("member", "role")]
```

**Note**: OrganizationMember records with organization_id=-1 represent system-wide memberships.

### 4. Policy Statements

```python
class PolicyEffect(IntEnum):
    """Policy effect."""
    ALLOW = 1
    DENY = 2

class PolicyStatement(Model):
    """Individual policy statement (Effect, Action, Resource, Condition)."""
    id = fields.IntField(pk=True)
    
    # Core policy components
    effect = fields.IntEnumField(PolicyEffect)
    actions = fields.JSONField()  # List of actions, e.g., ["tournament:create", "tournament:update"]
    resources = fields.JSONField()  # List of resource patterns, e.g., ["tournament:*", "organization:5"]
    conditions = fields.JSONField(null=True)  # Optional conditions (future)
    
    # Metadata
    description = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "policy_statements"
```

### 5. Role-Policy Attachments

```python
class RolePolicy(Model):
    """Links policies to roles."""
    id = fields.IntField(pk=True)
    role = fields.ForeignKeyField('models.OrganizationRole', related_name='attached_policies')
    policy_statement = fields.ForeignKeyField('models.PolicyStatement', related_name='attached_to_roles')
    attached_at = fields.DatetimeField(auto_now_add=True)
    attached_by = fields.ForeignKeyField('models.User', related_name='attached_policies', null=True)
    
    class Meta:
        table = "role_policies"
        unique_together = [("role", "policy_statement")]
```

### 6. Direct User Policies (Optional)

```python
class UserPolicy(Model):
    """
    Direct policy assignments to users (bypass roles).
    
    Use cases:
    - Grant specific user access to specific resource without role
    - Temporary elevated permissions
    - Explicit deny for specific user (security)
    
    Can be used for both:
    - Regular organizations (organization_id > 0)
    - System organization (organization_id = -1) for platform-wide policies
    
    Note: Global ADMIN users don't need these - they bypass all checks.
    """
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='direct_policies')
    organization = fields.ForeignKeyField('models.Organization', related_name='user_policies')  # Includes system org (id=-1)
    policy_statement = fields.ForeignKeyField('models.PolicyStatement', related_name='user_assignments')
    granted_by = fields.ForeignKeyField('models.User', related_name='granted_policies', null=True)
    granted_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "user_policies"
```

---

---

## Built-in Roles

### Concept

Built-in roles are standard roles automatically created for all organizations (including System organization). They provide a consistent set of common roles across all organizations while allowing customization of policies.

### Built-in Role Characteristics

1. **Auto-created**: Role records created automatically when organization is created
2. **Statically defined**: Permissions defined in code, not database (no PolicyStatement records)
3. **Read-only**: Cannot be deleted, renamed, or modified
4. **Consistent**: Same permissions across all organizations
5. **Standard set**: Same built-in roles for all regular organizations
6. **System org has different set**: System organization has its own built-in roles
7. **Use custom roles for customization**: Create custom role if different permissions needed

### Built-in Roles for Regular Organizations (id > 0)

#### 1. Admin (Built-in)
- **Name**: "Admin"
- **is_builtin**: True
- **is_locked**: True
- **Description**: "Full administrative access to organization"
- **Static Permissions**: All organization, member, tournament, match actions
- **Hardcoded Actions**: `organization:*`, `member:*`, `tournament:*`, `match:*`, `async_race:*`

#### 2. Tournament Manager (Built-in)
- **Name**: "Tournament Manager"
- **is_builtin**: True
- **is_locked**: True
- **Description**: "Manage tournaments and matches"
- **Static Permissions**: Tournament and match management
- **Hardcoded Actions**: `tournament:*`, `match:*`, `organization:read`

#### 3. Async Reviewer (Built-in)
- **Name**: "Async Reviewer"
- **is_builtin**: True
- **is_locked**: True
- **Description**: "Review and approve async race submissions"
- **Static Permissions**: Async race review/approve/reject
- **Hardcoded Actions**: `async_race:review`, `async_race:approve`, `async_race:reject`, `tournament:read`, `match:read`

#### 4. Member Manager (Built-in)
- **Name**: "Member Manager"
- **is_builtin**: True
- **is_locked**: True
- **Description**: "Manage organization members and invites"
- **Static Permissions**: Member invite/remove/edit
- **Hardcoded Actions**: `member:*`, `organization:read`

#### 5. Moderator (Built-in)
- **Name**: "Moderator"
- **is_builtin**: True
- **is_locked**: False  # Can be deleted if org doesn't need it
- **Description**: "View-only access to organization resources"
- **Static Permissions**: Read-only access to organization data
- **Hardcoded Actions**: `organization:read`, `member:read`, `tournament:read`, `match:read`

### Built-in Roles for System Organization (id = -1)

#### 1. User Manager (Built-in, System)
- **Name**: "User Manager"
- **is_builtin**: True
- **is_locked**: True
- **Description**: "Manage platform user accounts"
- **Static Permissions**: system:view_users, system:manage_users
- **Hardcoded Actions**: `system:view_users`, `system:manage_users`

#### 2. Organization Manager (Built-in, System)
- **Name**: "Organization Manager"
- **is_builtin**: True
- **is_locked**: True
- **Description**: "Create and manage organizations"
- **Static Permissions**: system:create_organization, system:manage_organizations
- **Hardcoded Actions**: `system:create_organization`, `system:manage_organizations`

#### 3. Analytics Viewer (Built-in, System)
- **Name**: "Analytics Viewer"
- **is_builtin**: True
- **is_locked**: True
- **Description**: "View platform analytics and reports"
- **Static Permissions**: system:view_analytics, system:view_audit_logs
- **Hardcoded Actions**: `system:view_analytics`, `system:view_audit_logs`

#### 4. Platform Moderator (Built-in, System)
- **Name**: "Platform Moderator"
- **is_builtin**: True
- **is_locked**: True
- **Description**: "Platform-wide moderation capabilities"
- **Static Permissions**: system:moderate_content, system:view_reports
- **Hardcoded Actions**: `system:moderate_content`, `system:view_reports`

### Organization Creation Flow

```python
async def create_organization(name: str, creator: User) -> Organization:
    """
    Create organization with built-in roles.
    
    Steps:
    1. Create Organization record
    2. Create built-in role records (no policies - permissions are hardcoded)
    3. Assign creator to "Admin" role
    """
    # 1. Create org
    org = await Organization.create(name=name, created_by=creator)
    
    # 2. Create built-in role records only (permissions in code)
    await create_builtin_roles_for_organization(org)
    
    # 3. Assign creator to Admin role
    admin_role = await OrganizationRole.get(organization=org, name="Admin")
    member = await OrganizationMember.create(organization=org, user=creator)
    await OrganizationMemberRole.create(member=member, role=admin_role)
    
    return org

async def create_builtin_roles_for_organization(org: Organization):
    """
    Create built-in role records (no policy records).
    
    Permissions are defined statically in code, not in database.
    """
    builtin_roles = get_builtin_role_definitions()  # From config
    
    for role_def in builtin_roles:
        # Create role record only - no policy records
        await OrganizationRole.create(
            organization=org,
            name=role_def.name,
            description=role_def.description,
            is_builtin=True,
            is_locked=role_def.is_locked
        )
        # Note: No PolicyStatement or RolePolicy records created
        # Permissions are evaluated from static definitions in code
```

### Custom Roles

Organizations can create custom roles when built-in roles don't fit their needs:

```python
async def create_custom_role(
    org: Organization,
    name: str,
    description: str,
    creator: User
) -> OrganizationRole:
    """Create a custom role with customizable policies."""
    # 1. Create role record
    role = await OrganizationRole.create(
        organization=org,
        name=name,
        description=description,
        is_builtin=False,  # Custom role
        is_locked=False    # Can be deleted
    )
    
    # 2. Create policy statements for custom role
    # (Unlike built-in roles, custom roles use database policies)
    policy = await PolicyStatement.create(
        effect="ALLOW",
        actions=["tournament:read", "match:read"],
        resources=["organization:{org_id}", "tournament:*", "match:*"]
    )
    
    # 3. Link policy to role
    await RolePolicy.create(role=role, policy_statement=policy)
    
    return role
```

**Use Cases for Custom Roles**:
- Need different permissions than built-in roles
- Want to combine permissions in unique ways
- Need organization-specific role (e.g., "Tournament Scheduler")
- Want to restrict permissions more than built-in roles allow

### Role Management Rules

1. **Built-in roles**:
   - ✅ Can assign/unassign members
   - ❌ Cannot modify permissions (defined in code)
   - ❌ Cannot modify name or description
   - ❌ Cannot delete (if is_locked=True)
   - ℹ️ Create custom role if different permissions needed

2. **Custom roles**:
   - ✅ Can assign/unassign members
   - ✅ Can create/modify/delete policies
   - ✅ Can modify name and description
   - ✅ Can delete (will unassign all members first)

### Benefits

1. **Consistency**: All organizations have identical built-in roles with same permissions
2. **Ease of Use**: New organizations don't need to create roles from scratch
3. **Performance**: Built-in role permissions evaluated from code (no database lookups)
4. **Safety**: Built-in roles can't be accidentally modified or deleted
5. **Flexibility**: Custom roles available when customization needed
6. **Simplicity**: No policy records to maintain for built-in roles
7. **Discoverability**: Users know what roles to expect and what they do

---

## System Organization (ID = -1)

### Concept

To enable ADMIN users to delegate system-wide permissions without granting full ADMIN role, we create a special "System" organization with `id=-1`.

### Database Setup

```python
async def create_system_organization():
    """
    Create system organization with built-in system roles.
    
    Called during application initialization.
    """
    # Create system organization record
    system_org = await Organization.create(
        id=-1,
        name="System",
        description="Special organization for platform-wide administration",
        is_active=True
    )
    
    # Create built-in system roles
    await create_builtin_roles_for_organization(system_org)
    
    return system_org
```

### System Organization Roles

The system organization (id=-1) has its own set of built-in roles for platform administration:

#### User Manager (Built-in)
- **Name**: "User Manager"
- **is_builtin**: True
- **is_locked**: True
- **Permissions**: Manage user accounts (view all users, edit users, change permissions)
- **Policy**:
  ```json
  {
    "effect": "ALLOW",
    "actions": ["system:view_users", "system:manage_users"],
    "resources": ["system"]
  }
  ```

#### Organization Manager (Built-in)
- **Name**: "Organization Manager"
- **is_builtin**: True
- **is_locked**: True
- **Permissions**: Create and manage organizations
- **Policy**:
  ```json
  {
    "effect": "ALLOW",
    "actions": ["system:create_organization", "system:manage_organizations"],
    "resources": ["system", "organization:*"]
  }
  ```

#### Analytics Viewer (Built-in)
- **Name**: "Analytics Viewer"
- **is_builtin**: True
- **is_locked**: True
- **Permissions**: View platform-wide analytics and reports
- **Policy**:
  ```json
  {
    "effect": "ALLOW",
    "actions": ["system:view_analytics", "system:view_audit_logs"],
    "resources": ["system"]
  }
  ```

#### Platform Moderator (Built-in)
- **Name**: "Platform Moderator"
- **is_builtin**: True
- **is_locked**: True
- **Permissions**: Platform-wide moderation capabilities
- **Policy**:
  ```json
  {
    "effect": "ALLOW",
    "actions": ["system:moderate_content", "system:view_reports"],
    "resources": ["system"]
  }
  ```

**Note**: These are built-in roles automatically created when the System organization is initialized. Organizations cannot create custom system roles (system org is locked to ADMIN-only management).

### How It Works

1. **ADMIN Assignment**: Only global ADMIN users can assign roles in the System organization
2. **Membership**: Create `OrganizationMember` record with `organization_id=-1`
3. **Role Assignment**: Assign user to roles in System organization (same as regular orgs)
4. **Policy Evaluation**: When `organization_id=-1`, policies from System org roles apply
5. **Delegation**: ADMIN can grant specific system permissions without full ADMIN access

### Example: Grant User Manager Access

```python
# Admin grants "User Manager" role to a user
from application.services.system_org_service import SystemOrgService

system_org_service = SystemOrgService()

# 1. Ensure user has membership in System org
system_member = await system_org_service.add_member(
    user=target_user,
    added_by=admin_user
)

# 2. Get built-in "User Manager" role in System org
user_manager_role = await OrganizationRole.get(
    organization_id=-1,
    name="User Manager",
    is_builtin=True  # This is a built-in role
)

# 3. Assign role to member
await OrganizationMemberRole.create(
    member=system_member,
    role=user_manager_role,
    granted_by=admin_user
)

# Now target_user can manage users, but can't do other admin actions
```

### Benefits

1. **Granular Delegation**: ADMIN can grant specific system permissions
2. **Consistent Framework**: Uses same role/policy system as organizations
3. **Audit Trail**: All system role assignments are tracked
4. **Revocable**: Easy to remove system permissions without affecting global role
5. **Flexible**: Can create custom system roles for specific needs

---

## Policy Engine Architecture

### Core Components

```python
# application/authorization/policy_engine.py

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from enum import IntEnum

@dataclass
class AuthorizationContext:
    """Context for authorization evaluation."""
    principal_id: int  # User ID
    action: str  # e.g., "tournament:create"
    resource: str  # e.g., "tournament:123" or "organization:5"
    organization_id: int  # Organization context: actual org ID, or -1 for system-wide resources
    resource_attributes: Optional[Dict[str, Any]] = None  # For condition evaluation
    request_context: Optional[Dict[str, Any]] = None  # IP, time, etc.

@dataclass
class PolicyEvaluationResult:
    """Result of policy evaluation."""
    allowed: bool
    matched_policies: List[int]  # Policy statement IDs that matched
    effect: str  # "ALLOW", "DENY", or "IMPLICIT_DENY"
    reason: str  # Human-readable explanation

class PolicyEngine:
    """
    Central policy evaluation engine.
    
    Evaluation logic:
    1. Collect all applicable policies (from roles + direct assignments)
    2. Evaluate each policy against the context
    3. DENY always wins (explicit deny overrides any allow)
    4. If no DENY and at least one ALLOW, grant access
    5. Otherwise, implicit deny (default deny)
    """
    
    def __init__(self):
        self.cache = PolicyCache()
    
    async def evaluate(self, context: AuthorizationContext) -> PolicyEvaluationResult:
        """
        Evaluate authorization request.
        
        Args:
            context: Authorization context
            
        Returns:
            PolicyEvaluationResult with decision and explanation
        """
        # 1. Check global role overrides (ADMIN bypasses all policy checks)
        user = await User.get(id=context.principal_id)
        if user.global_role == GlobalRole.ADMIN:
            return PolicyEvaluationResult(
                allowed=True,
                matched_policies=[],
                effect="ALLOW",
                reason="Global ADMIN role - bypasses all policy checks"
            )
        
        # 2. For USER role, collect applicable policies
        # Check for system-wide resources (organization_id=-1)
        if context.organization_id == -1:
            # System action - check if user has roles in System organization
            policies = await self._collect_policies(context)
            
            if not policies:
                # No system org membership or policies
                return PolicyEvaluationResult(
                    allowed=False,
                    matched_policies=[],
                    effect="IMPLICIT_DENY",
                    reason="No system organization permissions - requires Global ADMIN or system role assignment"
                )
            # Continue to policy evaluation below
        else:
            # Organization-scoped resource - collect policies
            policies = await self._collect_policies(context)
        
        # 3. Evaluate policies
        denies = []
        allows = []
        
        for policy in policies:
            if self._matches_policy(policy, context):
                if policy.effect == PolicyEffect.DENY:
                    denies.append(policy.id)
                elif policy.effect == PolicyEffect.ALLOW:
                    allows.append(policy.id)
        
        # 4. Apply decision logic
        if denies:
            return PolicyEvaluationResult(
                allowed=False,
                matched_policies=denies,
                effect="DENY",
                reason=f"Explicit deny from {len(denies)} policy(s)"
            )
        
        if allows:
            return PolicyEvaluationResult(
                allowed=True,
                matched_policies=allows,
                effect="ALLOW",
                reason=f"Allowed by {len(allows)} policy(s)"
            )
        
        return PolicyEvaluationResult(
            allowed=False,
            matched_policies=[],
            effect="IMPLICIT_DENY",
            reason="No matching allow policies"
        )
    
    async def _collect_policies(self, context: AuthorizationContext) -> List[PolicyStatement]:
        """
        Collect all policies applicable to this user/org/action.
        
        Collection order:
        1. Built-in role permissions (evaluated from static definitions, not database)
        2. User's direct policies (UserPolicy) for this organization
        3. User's custom role policies (OrganizationMemberRole -> RolePolicy) for custom roles
        
        When organization_id=-1 (System organization):
        - Checks for membership in System organization
        - Evaluates built-in system role permissions from code
        - Collects policies from custom system roles (if any)
        
        Note: Global ADMIN users never reach this method - they bypass in evaluate()
        """
        policies = []
        
        # 1. Check built-in roles first (permissions defined in code)
        builtin_role_names = await self._get_user_builtin_roles(
            context.user_id,
            context.organization_id
        )
        for role_name in builtin_role_names:
            # Get static permissions from code (not database)
            static_actions = get_builtin_role_actions(role_name, context.organization_id)
            if self._action_matches(context.action, static_actions):
                # Create virtual PolicyStatement for built-in role
                policies.append(PolicyStatement(
                    effect="ALLOW",
                    actions=static_actions,
                    resources=["*"]  # Built-in roles apply to all resources in org
                ))
        
        # 2. User's direct policies (UserPolicy) for this organization
        # 3. User's custom role policies (RolePolicy for is_builtin=False roles)
        # TODO: Implement database policy collection
        pass
    
    def _matches_policy(self, policy: PolicyStatement, context: AuthorizationContext) -> bool:
        """Check if a policy statement matches the context."""
        # Check action match (support wildcards)
        if not self._matches_action(policy.actions, context.action):
            return False
        
        # Check resource match (support wildcards)
        if not self._matches_resource(policy.resources, context.resource):
            return False
        
        # Check conditions (if any)
        if policy.conditions and not self._evaluate_conditions(policy.conditions, context):
            return False
        
        return True
    
    def _matches_action(self, policy_actions: List[str], requested_action: str) -> bool:
        """Check if requested action matches any policy action pattern."""
        for pattern in policy_actions:
            if pattern == "*":
                return True
            if pattern.endswith(":*"):
                # Service wildcard: "tournament:*" matches "tournament:create"
                service = pattern[:-2]
                if requested_action.startswith(f"{service}:"):
                    return True
            elif pattern == requested_action:
                return True
        return False
    
    def _matches_resource(self, policy_resources: List[str], requested_resource: str) -> bool:
        """Check if requested resource matches any policy resource pattern."""
        for pattern in policy_resources:
            if pattern == "*":
                return True
            if pattern.endswith(":*"):
                # Resource type wildcard: "tournament:*" matches "tournament:123"
                resource_type = pattern[:-2]
                if requested_resource.startswith(f"{resource_type}:"):
                    return True
            elif pattern == requested_resource:
                return True
        return False
    
    def _evaluate_conditions(self, conditions: Dict[str, Any], context: AuthorizationContext) -> bool:
        """Evaluate policy conditions (future implementation)."""
        # TODO: Implement condition evaluation
        return True
```

### Policy Cache

```python
# application/authorization/policy_cache.py

class PolicyCache:
    """
    Cache for policy evaluation results.
    
    Cache key format: "user:{user_id}:action:{action}:resource:{resource}"
    TTL: 5 minutes (configurable)
    
    Invalidation:
    - On role assignment/removal
    - On policy creation/update/deletion
    - On user permission changes
    """
    
    def __init__(self):
        self._cache = {}  # In-memory cache (use Redis in production)
    
    async def get(self, key: str) -> Optional[PolicyEvaluationResult]:
        """Get cached result."""
        pass
    
    async def set(self, key: str, result: PolicyEvaluationResult, ttl: int = 300):
        """Cache result with TTL."""
        pass
    
    async def invalidate_user(self, user_id: int):
        """Invalidate all cache entries for a user."""
        pass
    
    async def invalidate_organization(self, org_id: int):
        """Invalidate all cache entries for an organization."""
        pass
```

---

## Standard Actions

### Tournament Actions
- `tournament:create` - Create new tournament
- `tournament:read` - View tournament details
- `tournament:update` - Modify tournament settings
- `tournament:delete` - Delete tournament
- `tournament:start` - Start tournament
- `tournament:end` - End tournament
- `tournament:manage_participants` - Add/remove participants
- `tournament:*` - All tournament actions

### Match Actions
- `match:create` - Create new match
- `match:read` - View match details
- `match:update` - Modify match
- `match:delete` - Delete match
- `match:schedule` - Schedule match time
- `match:submit_result` - Submit match result
- `match:approve_result` - Approve submitted result
- `match:*` - All match actions

### Organization Actions
- `organization:read` - View organization info
- `organization:update` - Modify organization settings
- `organization:delete` - Delete organization
- `organization:manage_members` - Add/remove members
- `organization:manage_roles` - Create/modify roles
- `organization:assign_roles` - Assign roles to members
- `organization:*` - All organization actions

### Member Actions
- `member:read` - View member information
- `member:invite` - Invite new members
- `member:remove` - Remove members
- `member:update_permissions` - Modify member permissions
- `member:*` - All member actions

### Async Race Actions
- `async_race:submit` - Submit race result
- `async_race:review` - Review submitted result
- `async_race:approve` - Approve submission
- `async_race:reject` - Reject submission
- `async_race:*` - All async race actions

### System Actions (Non-Organization Scoped)

These actions operate on system-wide resources and use `organization_id=-1`:

- `system:view_users` - View all users (admin panel)
- `system:manage_users` - Create/modify users globally
- `system:view_audit_logs` - View system-wide audit logs
- `system:create_organization` - Create new organizations
- `system:manage_organizations` - Modify any organization
- `system:view_analytics` - View platform-wide analytics
- `system:moderate_content` - Platform-wide moderation
- `system:view_reports` - View system reports
- `system:*` - All system actions

**Authorization for System Actions**:
- **Global ADMIN**: Automatically allowed (bypass all checks)
- **Global USER with System Org Role**: Allowed based on policies in System organization (id=-1)
- **Global USER without System Org Role**: Denied (no policies)
- **Organization ID**: Always `-1` for system actions

**Example Delegation**:
An ADMIN can grant a user "User Manager" role in the System organization, giving them `system:view_users` and `system:manage_users` permissions without making them a full ADMIN.

---

## Standard Roles & Policies

### Global Roles

#### ADMIN (Global)
- **Special Behavior**: Bypasses ALL policy checks automatically
- **No policies needed**: ADMIN users pass all authorization checks by default
- **Use Case**: Full system administrators who need unrestricted access
- **Delegation**: Can assign users to roles in System organization (id=-1) for delegated permissions
- **Implementation**: Policy engine returns immediate ALLOW for any ADMIN user

#### USER (Global)
- **Default Role**: All new users start as USER
- **Policy-Based**: All permissions determined by organization-scoped roles and policies
- **Regular Organizations**: Access based on membership and roles in organizations (id > 0)
- **System Organization**: Can be granted roles in System organization (id=-1) for platform-wide permissions
- **No implicit privileges**: Cannot access anything without explicit organization membership and roles

### Organization Roles (Built-in)

All regular organizations (id > 0) automatically receive these built-in roles on creation:

#### Organization Admin (Built-in)
- **Name**: "Admin"
- **is_builtin**: True
- **is_locked**: True
- **Scope**: Regular organizations (id > 0)
- **Policies**:
  ```json
  [
    {
      "effect": "ALLOW",
      "actions": ["organization:*", "member:*", "tournament:*", "match:*"],
      "resources": ["organization:{org_id}", "tournament:*", "match:*"]
    }
  ]
  ```

#### Tournament Manager (Built-in)
- **Name**: "Tournament Manager"
- **is_builtin**: True
- **is_locked**: True
- **Scope**: Regular organizations (id > 0)
- **Policies**:
  ```json
  [
    {
      "effect": "ALLOW",
      "actions": ["tournament:*", "match:*"],
      "resources": ["organization:{org_id}", "tournament:*", "match:*"]
    },
    {
      "effect": "ALLOW",
      "actions": ["organization:read"],
      "resources": ["organization:{org_id}"]
    }
  ]
  ```

#### Async Reviewer (Built-in)
- **Name**: "Async Reviewer"
- **is_builtin**: True
- **is_locked**: True
- **Scope**: Regular organizations (id > 0)
- **Policies**:
  ```json
  [
    {
      "effect": "ALLOW",
      "actions": ["async_race:review", "async_race:approve", "async_race:reject"],
      "resources": ["organization:{org_id}", "async_race:*"]
    },
    {
      "effect": "ALLOW",
      "actions": ["tournament:read", "match:read"],
      "resources": ["tournament:*", "match:*"]
    }
  ]
  ```

#### Member Manager (Built-in)
- **Name**: "Member Manager"
- **is_builtin**: True
- **is_locked**: True
- **Scope**: Regular organizations (id > 0)
- **Policies**:
  ```json
  [
    {
      "effect": "ALLOW",
      "actions": ["member:*"],
      "resources": ["organization:{org_id}"]
    }
  ]
  ```

#### Moderator (Built-in)
- **Name**: "Moderator"
- **is_builtin**: True
- **is_locked**: False  # Can be deleted if organization doesn't need it
- **Scope**: Regular organizations (id > 0)
- **Policies**:
  ```json
  [
    {
      "effect": "ALLOW",
      "actions": ["member:read", "tournament:read", "match:read"],
      "resources": ["organization:{org_id}", "tournament:*", "match:*"]
    }
  ]
  ```

### System Organization Roles (Built-in)

The System organization (id=-1) has its own set of built-in roles for platform administration:

#### User Manager (Built-in, System)
- **Name**: "User Manager"
- **is_builtin**: True
- **is_locked**: True
- **Scope**: System organization (id=-1)
- **Policies**:
  ```json
  [
    {
      "effect": "ALLOW",
      "actions": ["system:view_users", "system:manage_users"],
      "resources": ["system"]
    }
  ]
  ```

#### Organization Manager (Built-in, System)
- **Name**: "Organization Manager"
- **is_builtin**: True
- **is_locked**: True
- **Scope**: System organization (id=-1)
- **Policies**:
  ```json
  [
    {
      "effect": "ALLOW",
      "actions": ["system:create_organization", "system:manage_organizations"],
      "resources": ["system", "organization:*"]
    }
  ]
  ```

#### Analytics Viewer (Built-in, System)
- **Name**: "Analytics Viewer"
- **is_builtin**: True
- **is_locked**: True
- **Scope**: System organization (id=-1)
- **Policies**:
  ```json
  [
    {
      "effect": "ALLOW",
      "actions": ["system:view_analytics", "system:view_audit_logs"],
      "resources": ["system"]
    }
  ]
  ```

#### Platform Moderator (Built-in, System)
- **Name**: "Platform Moderator"
- **is_builtin**: True
- **is_locked**: True
- **Scope**: System organization (id=-1)
- **Policies**:
  ```json
  [
    {
      "effect": "ALLOW",
      "actions": ["system:moderate_content", "system:view_reports"],
      "resources": ["system"]
    }
  ]
  ```

---

## Service Layer Integration

### New Authorization Service

```python
# application/services/authorization_service_v2.py

class AuthorizationServiceV2:
    """
    New authorization service using policy engine.
    
    Replaces scattered authorization checks with centralized policy evaluation.
    """
    
    def __init__(self):
        self.engine = PolicyEngine()
    
    async def authorize(
        self,
        user: User,
        action: str,
        resource: str,
        organization_id: int = -1,  # Default to -1 for system-wide resources
        resource_attributes: Optional[Dict[str, Any]] = None
    ) -> PolicyEvaluationResult:
        """
        Authorize an action.
        
        Args:
            user: User attempting action
            action: Action being attempted (e.g., "tournament:create")
            resource: Resource being accessed (e.g., "tournament:123")
            organization_id: Organization context (actual org ID, or -1 for system-wide)
            resource_attributes: Additional resource attributes for conditions
            
        Returns:
            PolicyEvaluationResult
            
        Examples:
            # Organization-scoped action
            result = await auth.authorize(
                user=current_user,
                action="tournament:create",
                resource=f"organization:{org_id}",
                organization_id=org_id
            )
            
            # System-wide action
            result = await auth.authorize(
                user=current_user,
                action="system:create_organization",
                resource="system",
                organization_id=-1  # System-wide
            )
            
            if not result.allowed:
                raise PermissionDenied(result.reason)
        """
        context = AuthorizationContext(
            principal_id=user.id,
            action=action,
            resource=resource,
            organization_id=organization_id,
            resource_attributes=resource_attributes
        )
        
        result = await self.engine.evaluate(context)
        
        # Log authorization decision
        await self._log_authorization(user, context, result)
        
        return result
    
    async def require(
        self,
        user: User,
        action: str,
        resource: str,
        organization_id: int = -1
    ) -> None:
        """
        Require authorization or raise exception.
        
        Args:
            user: User attempting action
            action: Action being attempted
            resource: Resource being accessed
            organization_id: Organization context
            
        Raises:
            PermissionDenied: If authorization fails
        """
        result = await self.authorize(user, action, resource, organization_id)
        if not result.allowed:
            raise PermissionDenied(f"Access denied: {result.reason}")
    
    async def can(
        self,
        user: User,
        action: str,
        resource: str,
        organization_id: int = -1
    ) -> bool:
        """
        Check if user can perform action (boolean result).
        
        Args:
            user: User attempting action
            action: Action being attempted
            resource: Resource being accessed
            organization_id: Organization context
            
        Returns:
            True if authorized, False otherwise
        """
        result = await self.authorize(user, action, resource, organization_id)
        return result.allowed
```

### Updated Service Methods

```python
# Example: TournamentService using new authorization

class TournamentService:
    def __init__(self):
        self.repository = TournamentRepository()
        self.auth = AuthorizationServiceV2()
    
    async def create_tournament(
        self,
        user: User,
        organization_id: int,
        name: str,
        **kwargs
    ) -> Tournament:
        """Create a new tournament."""
        # Authorization check using policy engine
        await self.auth.require(
            user=user,
            action="tournament:create",
            resource=f"organization:{organization_id}",
            organization_id=organization_id
        )
        
        # Business logic
        tournament = await self.repository.create(
            organization_id=organization_id,
            name=name,
            **kwargs
        )
        
        # Emit event, etc.
        await EventBus.emit(TournamentCreatedEvent(...))
        
        return tournament
    
    async def update_tournament(
        self,
        user: User,
        tournament_id: int,
        **updates
    ) -> Tournament:
        """Update a tournament."""
        # Get tournament to check organization
        tournament = await self.repository.get_by_id(tournament_id)
        if not tournament:
            raise NotFound("Tournament not found")
        
        # Authorization check
        await self.auth.require(
            user=user,
            action="tournament:update",
            resource=f"tournament:{tournament_id}",
            organization_id=tournament.organization_id
        )
        
        # Business logic
        updated = await self.repository.update(tournament_id, **updates)
        
        return updated
```

---

## Migration Strategy

### Phase 1: Foundation (Week 1-2)
1. **Create new database models**:
   - `OrganizationRole` (with is_builtin and is_locked fields)
   - `OrganizationMemberRole`
   - `PolicyStatement`
   - `RolePolicy`
   - `UserPolicy`

2. **Create Built-in Role Configuration**:
   - Define built-in role definitions in code (not database)
   - Create `application/authorization/builtin_roles.py` with:
     - Role definitions (name, description, is_locked)
     - Static permission mappings (role name → actions)
     - Helper functions: `get_builtin_role_actions(role_name, org_id)`
   - Regular organization roles: Admin, Tournament Manager, Async Reviewer, Member Manager, Moderator
   - System organization roles: User Manager, Organization Manager, Analytics Viewer, Platform Moderator

3. **Create System Organization**:
   - Special Organization record with `id=-1`
   - Automatically create built-in system roles
   - Seeded during database initialization
   - Cannot be deleted or modified by regular operations

4. **Create migrations**:
   ```bash
   poetry run aerich migrate --name "add_policy_framework"
   ```

5. **Implement PolicyEngine core**:
   - Create `application/authorization/` package
   - Implement `policy_engine.py`
   - Implement `policy_cache.py`
   - Implement `builtin_roles.py`
   - Add unit tests

### Phase 2: Standard Roles & Policies (Week 2-3)
1. **Auto-create built-in roles**:
   - Modify organization creation to automatically create built-in roles
   - Create helper function `create_builtin_roles_for_organization(org)`
   - Called whenever new organization is created

2. **Create System organization with built-in roles**:
   - Create Organization with id=-1
   - Automatically create built-in system roles
   - Initialize with default policies

3. **Migration script** to convert existing permissions:
   ```python
   # tools/migrate_permissions_to_policies.py
   async def migrate_organization_permissions():
       """Convert old OrganizationPermission to new role-based system."""
       # For each existing organization:
       #   1. Create built-in role records (no policies)
       #   2. Assign users to built-in roles based on old permissions
       #   3. Map old permissions to built-in roles:
       #      - ADMIN → "Admin" role
       #      - TOURNAMENT_MANAGER → "Tournament Manager" role
       #      - ASYNC_REVIEWER → "Async Reviewer" role
       #      - MEMBER_MANAGER → "Member Manager" role
       #      - MODERATOR → "Moderator" role
       #   4. Verify all users have correct access
   
   async def create_system_organization():
       """Create System organization and built-in system roles."""
       # 1. Create Organization with id=-1
       # 2. Create built-in system role records (no policies)
       # 3. Verify system roles created correctly
       # Note: System role permissions defined in builtin_roles.py, not database
   
   async def backfill_builtin_roles_for_existing_orgs():
       """Add built-in roles to organizations created before redesign."""
       # For each organization without built-in roles:
       #   1. Create built-in role records (no policies)
       #   2. Optionally migrate existing members to appropriate roles
       # Note: Permissions come from code, not database policies
   ```

### Phase 3: Service Integration (Week 3-4)
1. **Create AuthorizationServiceV2**
2. **Update one service at a time**:
   - Start with `TournamentService`
   - Then `OrganizationService`
   - Then `AsyncTournamentService`
   - etc.

3. **Run parallel testing**: Keep old auth alongside new for comparison

### Phase 4: UI Integration (Week 4-5)
1. **Update API route authorization**
2. **Update page authorization checks**
3. **Add role management UI**:
   - View built-in roles (read-only, show static permissions from code)
   - View/create/delete custom roles
   - Modify policies for custom roles only
   - Assign roles (built-in and custom) to members
   - View effective permissions (combination of built-in + custom roles)
4. **Add system org management UI**:
   - ADMIN panel for managing system roles
   - Assign users to built-in system roles
   - View system organization members
   - Cannot create custom system roles (system org locked)

### Phase 5: Cleanup (Week 5-6)
1. **Remove old authorization code**:
   - Delete old `AuthorizationService` methods
   - Remove `OrganizationPermission` model
   - Remove string-based permission checks

2. **Documentation**:
   - Update architecture docs
   - Create policy administration guide
   - Update developer guide

### Phase 6: Advanced Features (Week 6+)
1. **Condition evaluation**:
   - Time-based conditions
   - IP-based restrictions
   - Resource attribute conditions

2. **Policy templates**:
   - Predefined policy sets
   - Organization policy templates

3. **Audit & Compliance**:
   - Policy change audit logs
   - Authorization decision logs
   - Compliance reports

---

## Benefits of New System

### 1. **Centralized Authorization**
- All authorization logic in one place (PolicyEngine)
- Consistent evaluation across entire application
- Easy to audit and test

### 2. **Granular Control**
- Resource-level permissions (not just organization-level)
- Action-level permissions (specific operations)
- Condition-based access (future)

### 3. **Explicit Deny**
- Can explicitly deny actions (security enhancement)
- Deny always wins (prevents privilege escalation)

### 4. **Flexible Roles**
- Organizations can create custom roles
- Multiple roles per member
- Easy to add new permissions without code changes

### 5. **Built-in Roles**
- Standard roles automatically created for all organizations
- Permissions defined statically in code (not database)
- Consistent role structure and permissions across platform
- Cannot be modified, renamed, or deleted (read-only)
- Custom roles available when customization needed

### 6. **System Permission Delegation**
- ADMIN can delegate specific system permissions
- No need to grant full ADMIN for limited access
- Uses same framework as organization roles
- Built-in system roles for common delegation patterns
- Easy to revoke delegated permissions

### 7. **Auditable**
- All authorization decisions logged
- Can trace why access was granted/denied
- Compliance-ready

### 8. **Performance**
- Built-in role permissions evaluated from code (no database queries)
- Policy caching for custom roles reduces database queries
- Batch policy evaluation possible
- Optimized policy matching

### 9. **Developer Experience**
- Simple API: `await auth.require(user, action, resource, org_id)`
- Clear error messages
- Easy to understand authorization logic

### 10. **Consistency**
- Same role framework for regular organizations and system organization
- Same policies structure everywhere
- Same evaluation logic for all resources

---

## Examples

### Example 1: Create Tournament (Organization-Scoped)

```python
# User trying to create tournament in organization 5
user = await User.get(id=123)

# Old way (scattered checks):
if not await org_service.user_can_manage_tournaments(user, 5):
    return None

# New way (policy-based):
await auth.require(
    user=user,
    action="tournament:create",
    resource="organization:5",
    organization_id=5  # Organization context
)
```

### Example 2: Review Async Race

```python
# Old way:
if not await org_service.user_can_review_async_races(user, org_id):
    raise PermissionDenied()

# New way:
await auth.require(
    user=user,
    action="async_race:review",
    resource=f"async_race:{race_id}",
    organization_id=org_id
)
```

### Example 3: Conditional UI

```python
# Show "Create Tournament" button only if authorized
if await auth.can(user, "tournament:create", f"organization:{org_id}", organization_id=org_id):
    ui.button("Create Tournament", on_click=create_handler)
```

### Example 4: System-Wide Action (ADMIN)

```python
# Global ADMIN can view all users (automatic bypass)
result = await auth.authorize(
    user=admin_user,  # global_role=ADMIN
    action="system:view_users",
    resource="system",
    organization_id=-1  # System-wide resource
)

# Result: allowed=True, reason="Global ADMIN role - bypasses all policy checks"
```

### Example 5: System-Wide Action (Delegated Permission)

```python
# Regular USER with "User Manager" role in System organization
result = await auth.authorize(
    user=user_manager,  # global_role=USER, has system role
    action="system:view_users",
    resource="system",
    organization_id=-1
)

# Result: allowed=True, reason="Allowed by 1 policy(s)"
# Policy from "User Manager" role in System organization

# Same user trying different system action without permission
result = await auth.authorize(
    user=user_manager,
    action="system:create_organization",  # Not in their role
    resource="system",
    organization_id=-1
)

# Result: allowed=False, reason="No matching allow policies"
```

### Example 6: System-Wide Action (No Permission)

```python
# Regular USER without system organization membership
result = await auth.authorize(
    user=regular_user,  # global_role=USER, no system roles
    action="system:view_users",
    resource="system",
    organization_id=-1
)

# Result: allowed=False, reason="No system organization permissions - requires Global ADMIN or system role assignment"
```

### Example 5: Custom Role

```python
# Create custom "Event Coordinator" role
role = await role_service.create_role(
    organization_id=5,
    name="Event Coordinator",
    description="Can manage scheduled events and tournaments"
)

# Attach policies
await role_service.attach_policy(
    role_id=role.id,
    policy_statement={
        "effect": "ALLOW",
        "actions": ["tournament:create", "tournament:update", "tournament:read"],
        "resources": ["organization:5", "tournament:*"]
    }
)

await role_service.attach_policy(
    role_id=role.id,
    policy_statement={
        "effect": "ALLOW",
        "actions": ["schedule:*"],
        "resources": ["organization:5"]
    }
)

### Example 7: Delegate System Permission

```python
# ADMIN wants to grant user management access without full ADMIN
from application.services.system_org_service import SystemOrgService

system_org_service = SystemOrgService()

# 1. Add user to System organization
await system_org_service.add_member(
    user=trusted_user,
    added_by=admin_user
)

# 2. Assign "User Manager" role
await system_org_service.assign_role(
    user=trusted_user,
    role_name="User Manager",
    assigned_by=admin_user
)

# 3. User can now manage users (but nothing else)
result = await auth.can(
    trusted_user,
    "system:manage_users",
    "system",
    organization_id=-1
)
# Returns True

# But can't create organizations
result = await auth.can(
    trusted_user,
    "system:create_organization",
    "system",
    organization_id=-1
)
# Returns False (not in their role)
```

---

## Next Steps

1. **Review this design** - Validate approach and models
2. **Prototype PolicyEngine** - Build core evaluation logic
3. **Create database migrations** - Add new tables
4. **Implement standard roles** - Define default policies
5. **Migrate one service** - Prove the concept
6. **Full migration** - Convert all services
7. **Admin UI** - Build role/policy management

## Key Design Decisions

### Global Role Simplification

**Only 2 Global Roles**:
1. **USER** (default) - All permissions from organization-scoped policies
2. **ADMIN** - Bypasses all policy checks, full system access

**Rationale**:
- Simplifies authorization logic (no intermediate global roles)
- Clear separation: ADMIN = platform management, USER = organization-based access
- Reduces complexity in policy evaluation
- Makes it impossible to accidentally grant too much global access

**Implications**:
- No global "MODERATOR" or "SUPERADMIN" distinctions
- All non-ADMIN users are equal at global level
- All granular permissions handled via organization roles (including System org)
- For platform-wide access delegation, use System organization (id=-1) roles
- ADMIN has full unrestricted access and can delegate specific system permissions via System org roles

### Non-Organization Services

Some services don't have organization context:
- User management (global user list, profile management)
- Organization creation
- Platform analytics
- System settings

**Authorization Strategy**:
1. **Use `organization_id=-1`**: All system-wide resources use -1 (System organization)
2. **Global ADMIN**: Automatically allowed for all system actions (bypass)
3. **Global USER with System Org Role**: Policies from System organization apply
4. **Global USER without System Org Role**: Denied (no system policies)
5. **Delegation**: ADMIN assigns roles in System organization for delegated access

**Example - Organization Creation**:
```python
# Only ADMIN (or users with "Organization Manager" system role) can create organizations
await auth.require(
    user=user,
    action="system:create_organization",
    resource="system",
    organization_id=-1  # System organization
)
# ADMIN: passes (bypass)
# USER with "Organization Manager" role in System org: passes (policy)
# Regular USER: denied
```

## Questions to Consider

1. Should policies be JSON in database or have dedicated fields?
2. Do we need policy versioning?
3. Should we support policy inheritance?
4. How granular should resource identifiers be?
5. What conditions do we need initially?
6. Should we log all authorization decisions or just denials?
7. What's the cache invalidation strategy?
8. Do we need policy dry-run/testing mode?
9. Should we create a special "Platform" organization for platform-wide roles? (alternative to global ADMIN for limited system access)
   - **Answer**: Yes! Use organization with `id=-1` as System organization for delegation

---

**Last Updated**: November 5, 2025
