# Plugin Security Model

## Executive Summary

This document defines the security model for the SahaBot2 plugin system. It covers threat analysis, security controls, sandboxing approaches, and best practices for secure plugin development.

## Threat Model

### Assets to Protect

1. **User Data**: Personal information, credentials, preferences
2. **Organization Data**: Multi-tenant data isolation
3. **System Resources**: CPU, memory, disk, network
4. **Core Application**: Integrity and availability
5. **Other Plugins**: Isolation between plugins

### Threat Actors

1. **Malicious Plugin Developer**: Creates plugin to steal data or harm system
2. **Compromised Plugin**: Legitimate plugin with vulnerability exploited
3. **Careless Plugin Developer**: Introduces security bugs unintentionally
4. **Insider Threat**: Organization member with excessive plugin permissions

### Attack Vectors

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Attack Vectors                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐            │
│  │  Data Exfil     │   │  Privilege Esc  │   │  Code Injection │            │
│  │  - API abuse    │   │  - Bypass authz │   │  - SQL injection│            │
│  │  - Direct DB    │   │  - Token theft  │   │  - XSS          │            │
│  │  - Event snoop  │   │  - Session hijack│   │  - Template inj │            │
│  └─────────────────┘   └─────────────────┘   └─────────────────┘            │
│                                                                              │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐            │
│  │  DoS Attacks    │   │  Malware        │   │  Supply Chain   │            │
│  │  - Resource     │   │  - Backdoors    │   │  - Dependency   │            │
│  │    exhaustion   │   │  - Crypto mining│   │    compromise   │            │
│  │  - Infinite     │   │  - Keyloggers   │   │  - Typosquatting│            │
│  │    loops        │   │                 │   │                 │            │
│  └─────────────────┘   └─────────────────┘   └─────────────────┘            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Security Architecture

### Defense in Depth

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Defense Layers                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Layer 1: Plugin Validation                                                  │
│  ├── Manifest validation                                                     │
│  ├── Dependency verification                                                 │
│  ├── Code signing (external plugins)                                         │
│  └── Security scanning                                                       │
│                                                                              │
│  Layer 2: Runtime Isolation                                                  │
│  ├── Resource limits                                                         │
│  ├── API access control                                                      │
│  ├── Network restrictions                                                    │
│  └── Filesystem sandboxing                                                   │
│                                                                              │
│  Layer 3: Authorization                                                      │
│  ├── Plugin capability system                                                │
│  ├── Per-organization permissions                                            │
│  ├── Action-based access control                                             │
│  └── Resource-level authorization                                            │
│                                                                              │
│  Layer 4: Monitoring & Auditing                                              │
│  ├── Plugin activity logging                                                 │
│  ├── Anomaly detection                                                       │
│  ├── Rate limiting                                                           │
│  └── Security alerts                                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Plugin Type Security Levels

| Plugin Type | Trust Level | Security Controls |
|-------------|-------------|-------------------|
| **Built-in** | High | Part of codebase, code-reviewed, signed by maintainers |
| **Verified External** | Medium | Third-party reviewed, signed, listed in registry |
| **Unverified External** | Low | User-installed, requires explicit approval, extra restrictions |

## Security Controls

### 1. Plugin Validation

#### Manifest Validation

```python
# application/plugins/security/validator.py

from typing import List, Optional
from dataclasses import dataclass
import re


@dataclass
class ValidationResult:
    """Result of plugin validation."""
    valid: bool
    errors: List[str]
    warnings: List[str]


class PluginValidator:
    """Validates plugins before loading."""

    # Allowed permissions for plugins
    ALLOWED_PERMISSIONS = {
        # Data access
        "read:own_data",
        "write:own_data",
        "read:org_data",
        "write:org_data",
        # Network
        "network:internal",
        "network:external",
        # Filesystem
        "filesystem:plugin_data",
        # Discord
        "discord:send_messages",
        "discord:read_messages",
    }

    # Dangerous patterns to reject
    DANGEROUS_PATTERNS = [
        r"eval\s*\(",
        r"exec\s*\(",
        r"__import__\s*\(",
        r"importlib\.import_module",
        r"subprocess\.",
        r"os\.system",
        r"os\.popen",
        r"shutil\.rmtree",
    ]

    def validate_manifest(self, manifest: dict) -> ValidationResult:
        """
        Validate plugin manifest.

        Args:
            manifest: Parsed manifest dictionary

        Returns:
            ValidationResult with errors and warnings
        """
        errors = []
        warnings = []

        # Required fields
        required = ["id", "name", "version", "description", "author", "type"]
        for field in required:
            if field not in manifest:
                errors.append(f"Missing required field: {field}")

        # ID format
        if "id" in manifest:
            if not re.match(r'^[a-z][a-z0-9_]*$', manifest["id"]):
                errors.append(
                    "Plugin ID must start with lowercase letter and "
                    "contain only lowercase letters, numbers, and underscores"
                )

        # Version format (semver)
        if "version" in manifest:
            if not re.match(r'^\d+\.\d+\.\d+', manifest["version"]):
                errors.append("Version must follow semver format (X.Y.Z)")

        # Type validation
        if manifest.get("type") not in ["builtin", "external"]:
            errors.append("Type must be 'builtin' or 'external'")

        # Permission validation
        if "permissions" in manifest:
            for action in manifest["permissions"].get("actions", []):
                if action not in self.ALLOWED_PERMISSIONS:
                    if manifest.get("type") == "external":
                        warnings.append(
                            f"Non-standard permission: {action} - "
                            "requires admin approval"
                        )

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def scan_code(self, code: str) -> ValidationResult:
        """
        Scan plugin code for dangerous patterns.

        Args:
            code: Source code to scan

        Returns:
            ValidationResult with findings
        """
        errors = []
        warnings = []

        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, code):
                errors.append(f"Dangerous pattern detected: {pattern}")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
```

#### Dependency Verification

```python
# application/plugins/security/dependency_checker.py

import subprocess
import json
from typing import List, Dict


class DependencyChecker:
    """Check plugin dependencies for known vulnerabilities."""

    def check_dependencies(self, requirements: List[str]) -> Dict[str, List[str]]:
        """
        Check dependencies for known vulnerabilities.

        Uses pip-audit or similar tool.

        Args:
            requirements: List of requirement strings

        Returns:
            Dict mapping package to list of vulnerabilities
        """
        vulnerabilities = {}

        # Write requirements to temp file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('\n'.join(requirements))
            temp_path = f.name

        try:
            # Run pip-audit
            result = subprocess.run(
                ['pip-audit', '-r', temp_path, '--format', 'json'],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.stdout:
                data = json.loads(result.stdout)
                for vuln in data.get('vulnerabilities', []):
                    package = vuln['package']
                    if package not in vulnerabilities:
                        vulnerabilities[package] = []
                    vulnerabilities[package].append({
                        'id': vuln['vuln_id'],
                        'severity': vuln.get('severity', 'unknown'),
                        'description': vuln.get('description', '')
                    })

        except Exception as e:
            # Log error but don't fail
            import logging
            logging.getLogger(__name__).error(
                "Dependency check failed: %s", e
            )

        return vulnerabilities
```

### 2. Runtime Isolation

#### Resource Limits

```python
# application/plugins/security/resource_limiter.py

import resource
import asyncio
from functools import wraps
from typing import Callable


class ResourceLimiter:
    """Enforce resource limits on plugin execution."""

    # Default limits
    DEFAULT_LIMITS = {
        "max_memory_mb": 256,      # Maximum memory per plugin
        "max_cpu_seconds": 30,     # Maximum CPU time per operation
        "max_execution_time": 60,  # Maximum wall-clock time
        "max_open_files": 100,     # Maximum open file descriptors
    }

    def __init__(self, limits: dict = None):
        self.limits = {**self.DEFAULT_LIMITS, **(limits or {})}

    def apply_limits(self):
        """Apply resource limits to current process."""
        # Memory limit
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        max_bytes = self.limits["max_memory_mb"] * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (max_bytes, hard))

        # CPU time limit
        soft, hard = resource.getrlimit(resource.RLIMIT_CPU)
        resource.setrlimit(
            resource.RLIMIT_CPU,
            (self.limits["max_cpu_seconds"], hard)
        )

        # Open files limit
        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        resource.setrlimit(
            resource.RLIMIT_NOFILE,
            (self.limits["max_open_files"], hard)
        )

    def with_timeout(self, timeout: float = None):
        """
        Decorator to enforce execution timeout.

        Args:
            timeout: Maximum execution time in seconds
        """
        if timeout is None:
            timeout = self.limits["max_execution_time"]

        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                try:
                    return await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=timeout
                    )
                except asyncio.TimeoutError:
                    raise PluginTimeoutError(
                        f"Plugin operation exceeded {timeout}s timeout"
                    )
            return wrapper
        return decorator


class PluginTimeoutError(Exception):
    """Raised when plugin operation times out."""
    pass
```

#### API Access Control

```python
# application/plugins/security/api_guard.py

from typing import Set, Optional
from functools import wraps


class PluginAPIGuard:
    """
    Controls plugin access to core APIs.

    Plugins can only access APIs they have permission for.
    """

    # API capabilities and their required permissions
    API_PERMISSIONS = {
        "user.get": "read:user_data",
        "user.update": "write:user_data",
        "organization.get": "read:org_data",
        "organization.members": "read:org_data",
        "tournament.create": "write:tournament",
        "tournament.update": "write:tournament",
        "tournament.delete": "write:tournament",
        "event.emit": "emit:events",
        "task.schedule": "schedule:tasks",
        "discord.send": "discord:send_messages",
        "network.fetch": "network:external",
    }

    def __init__(self, plugin_id: str, granted_permissions: Set[str]):
        """
        Initialize API guard for a plugin.

        Args:
            plugin_id: Plugin identifier
            granted_permissions: Set of granted permission strings
        """
        self.plugin_id = plugin_id
        self.permissions = granted_permissions

    def can_access(self, api: str) -> bool:
        """
        Check if plugin can access an API.

        Args:
            api: API identifier (e.g., "user.get")

        Returns:
            True if access allowed
        """
        required = self.API_PERMISSIONS.get(api)
        if required is None:
            # Unknown API - deny by default
            return False
        return required in self.permissions

    def require(self, api: str):
        """
        Decorator to enforce API access check.

        Args:
            api: API identifier

        Raises:
            PluginAccessDeniedError: If access not allowed
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                if not self.can_access(api):
                    raise PluginAccessDeniedError(
                        f"Plugin '{self.plugin_id}' denied access to '{api}'"
                    )
                return await func(*args, **kwargs)
            return wrapper
        return decorator


class PluginAccessDeniedError(Exception):
    """Raised when plugin access is denied."""
    pass
```

### 3. Authorization System

#### Plugin Capability System

```python
# application/plugins/security/capabilities.py

from enum import IntFlag, auto
from typing import Set


class PluginCapability(IntFlag):
    """
    Plugin capabilities (permissions).

    Uses bitwise flags for efficient storage and checking.
    """

    # Data access
    READ_OWN_DATA = auto()       # Read data created by the plugin
    WRITE_OWN_DATA = auto()      # Write data for the plugin
    READ_ORG_DATA = auto()       # Read organization data
    WRITE_ORG_DATA = auto()      # Write organization data
    READ_USER_DATA = auto()      # Read user profiles
    WRITE_USER_DATA = auto()     # Modify user profiles

    # System access
    EMIT_EVENTS = auto()         # Emit events to EventBus
    LISTEN_EVENTS = auto()       # Listen to events
    SCHEDULE_TASKS = auto()      # Create scheduled tasks
    ACCESS_NETWORK = auto()      # Make network requests

    # Discord access
    DISCORD_SEND = auto()        # Send Discord messages
    DISCORD_READ = auto()        # Read Discord messages
    DISCORD_COMMANDS = auto()    # Register Discord commands

    # Admin capabilities
    MANAGE_PLUGINS = auto()      # Manage other plugins
    SYSTEM_ADMIN = auto()        # Full system access

    # Convenience groups
    BASIC = READ_OWN_DATA | WRITE_OWN_DATA | EMIT_EVENTS
    STANDARD = BASIC | READ_ORG_DATA | LISTEN_EVENTS
    DISCORD_FULL = DISCORD_SEND | DISCORD_READ | DISCORD_COMMANDS


class CapabilityManager:
    """Manages plugin capabilities."""

    # Default capabilities by plugin type
    DEFAULT_CAPABILITIES = {
        "builtin": PluginCapability.STANDARD | PluginCapability.DISCORD_FULL,
        "external": PluginCapability.BASIC,
    }

    def __init__(self):
        self._plugin_capabilities: dict[str, PluginCapability] = {}

    def grant(self, plugin_id: str, capability: PluginCapability) -> None:
        """Grant capability to plugin."""
        current = self._plugin_capabilities.get(plugin_id, PluginCapability(0))
        self._plugin_capabilities[plugin_id] = current | capability

    def revoke(self, plugin_id: str, capability: PluginCapability) -> None:
        """Revoke capability from plugin."""
        current = self._plugin_capabilities.get(plugin_id, PluginCapability(0))
        self._plugin_capabilities[plugin_id] = current & ~capability

    def check(self, plugin_id: str, capability: PluginCapability) -> bool:
        """Check if plugin has capability."""
        current = self._plugin_capabilities.get(plugin_id, PluginCapability(0))
        return bool(current & capability)

    def get_capabilities(self, plugin_id: str) -> PluginCapability:
        """Get all capabilities for a plugin."""
        return self._plugin_capabilities.get(plugin_id, PluginCapability(0))
```

#### Per-Organization Permissions

```python
# application/plugins/security/org_permissions.py

from typing import Optional, Set
from models.plugin import OrganizationPlugin


class OrganizationPluginPermissions:
    """
    Manages organization-specific plugin permissions.

    Organizations can grant/revoke specific permissions to plugins.
    """

    async def get_permissions(
        self,
        organization_id: int,
        plugin_id: str
    ) -> Set[str]:
        """
        Get permissions granted to plugin for organization.

        Args:
            organization_id: Organization ID
            plugin_id: Plugin identifier

        Returns:
            Set of permission strings
        """
        org_plugin = await OrganizationPlugin.filter(
            organization_id=organization_id,
            plugin_id=plugin_id
        ).first()

        if not org_plugin:
            return set()

        # Get from config
        config = org_plugin.config or {}
        return set(config.get("permissions", []))

    async def grant_permission(
        self,
        organization_id: int,
        plugin_id: str,
        permission: str,
        granted_by_id: int
    ) -> bool:
        """
        Grant permission to plugin for organization.

        Args:
            organization_id: Organization ID
            plugin_id: Plugin identifier
            permission: Permission string
            granted_by_id: User ID who granted

        Returns:
            True if granted successfully
        """
        org_plugin = await OrganizationPlugin.filter(
            organization_id=organization_id,
            plugin_id=plugin_id
        ).first()

        if not org_plugin:
            return False

        config = org_plugin.config or {}
        permissions = set(config.get("permissions", []))
        permissions.add(permission)
        config["permissions"] = list(permissions)
        org_plugin.config = config
        await org_plugin.save()

        # Audit log
        import logging
        logging.getLogger(__name__).info(
            "Permission '%s' granted to plugin '%s' for org %s by user %s",
            permission, plugin_id, organization_id, granted_by_id
        )

        return True

    async def revoke_permission(
        self,
        organization_id: int,
        plugin_id: str,
        permission: str,
        revoked_by_id: int
    ) -> bool:
        """Revoke permission from plugin for organization."""
        org_plugin = await OrganizationPlugin.filter(
            organization_id=organization_id,
            plugin_id=plugin_id
        ).first()

        if not org_plugin:
            return False

        config = org_plugin.config or {}
        permissions = set(config.get("permissions", []))
        permissions.discard(permission)
        config["permissions"] = list(permissions)
        org_plugin.config = config
        await org_plugin.save()

        # Audit log
        import logging
        logging.getLogger(__name__).info(
            "Permission '%s' revoked from plugin '%s' for org %s by user %s",
            permission, plugin_id, organization_id, revoked_by_id
        )

        return True
```

### 4. Monitoring & Auditing

#### Plugin Activity Logger

```python
# application/plugins/security/activity_logger.py

import logging
from datetime import datetime, timezone
from typing import Optional, Any
from dataclasses import dataclass


@dataclass
class PluginActivity:
    """Record of plugin activity."""
    plugin_id: str
    action: str
    organization_id: Optional[int]
    user_id: Optional[int]
    details: dict
    timestamp: datetime
    success: bool
    error: Optional[str]


class PluginActivityLogger:
    """
    Logs plugin activities for security monitoring.

    All significant plugin actions are logged for auditing.
    """

    def __init__(self):
        self.logger = logging.getLogger("plugin.security")
        self._activities: list[PluginActivity] = []  # In-memory buffer
        self._max_buffer = 1000

    async def log_activity(
        self,
        plugin_id: str,
        action: str,
        organization_id: Optional[int] = None,
        user_id: Optional[int] = None,
        details: dict = None,
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """
        Log a plugin activity.

        Args:
            plugin_id: Plugin identifier
            action: Action performed
            organization_id: Organization context
            user_id: User who triggered action
            details: Additional details
            success: Whether action succeeded
            error: Error message if failed
        """
        activity = PluginActivity(
            plugin_id=plugin_id,
            action=action,
            organization_id=organization_id,
            user_id=user_id,
            details=details or {},
            timestamp=datetime.now(timezone.utc),
            success=success,
            error=error
        )

        # Log to structured logger
        self.logger.info(
            "Plugin activity: plugin=%s action=%s org=%s user=%s success=%s",
            plugin_id, action, organization_id, user_id, success,
            extra={"activity": activity.__dict__}
        )

        # Buffer for analysis
        self._activities.append(activity)
        if len(self._activities) > self._max_buffer:
            self._activities = self._activities[-self._max_buffer:]

        # Check for anomalies
        await self._check_anomalies(activity)

    async def _check_anomalies(self, activity: PluginActivity) -> None:
        """
        Check for suspicious activity patterns.

        Args:
            activity: Activity to check
        """
        # Count recent activities from this plugin
        recent = [
            a for a in self._activities[-100:]
            if a.plugin_id == activity.plugin_id
        ]

        # Alert if too many activities in short time
        if len(recent) > 50:
            self.logger.warning(
                "High activity detected for plugin %s: %d actions in buffer",
                activity.plugin_id, len(recent)
            )

        # Alert on repeated failures
        failures = [a for a in recent if not a.success]
        if len(failures) > 10:
            self.logger.warning(
                "Multiple failures for plugin %s: %d failures",
                activity.plugin_id, len(failures)
            )
```

#### Rate Limiting

```python
# application/plugins/security/rate_limiter.py

import time
from collections import defaultdict
from typing import Dict, Tuple


class PluginRateLimiter:
    """
    Rate limiter for plugin operations.

    Prevents plugins from overwhelming the system.
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self._minute_windows: Dict[str, list] = defaultdict(list)
        self._hour_windows: Dict[str, list] = defaultdict(list)

    def check_rate_limit(self, plugin_id: str) -> Tuple[bool, str]:
        """
        Check if plugin is within rate limits.

        Args:
            plugin_id: Plugin identifier

        Returns:
            Tuple of (allowed, reason)
        """
        now = time.time()

        # Check minute window
        minute_ago = now - 60
        minute_requests = [
            t for t in self._minute_windows[plugin_id]
            if t > minute_ago
        ]
        self._minute_windows[plugin_id] = minute_requests

        if len(minute_requests) >= self.requests_per_minute:
            return False, f"Rate limit exceeded: {self.requests_per_minute}/minute"

        # Check hour window
        hour_ago = now - 3600
        hour_requests = [
            t for t in self._hour_windows[plugin_id]
            if t > hour_ago
        ]
        self._hour_windows[plugin_id] = hour_requests

        if len(hour_requests) >= self.requests_per_hour:
            return False, f"Rate limit exceeded: {self.requests_per_hour}/hour"

        return True, ""

    def record_request(self, plugin_id: str) -> None:
        """Record a request from a plugin."""
        now = time.time()
        self._minute_windows[plugin_id].append(now)
        self._hour_windows[plugin_id].append(now)

    def with_rate_limit(self, plugin_id: str):
        """
        Decorator to enforce rate limit.

        Args:
            plugin_id: Plugin identifier

        Raises:
            PluginRateLimitError: If rate limit exceeded
        """
        def decorator(func):
            async def wrapper(*args, **kwargs):
                allowed, reason = self.check_rate_limit(plugin_id)
                if not allowed:
                    raise PluginRateLimitError(reason)
                self.record_request(plugin_id)
                return await func(*args, **kwargs)
            return wrapper
        return decorator


class PluginRateLimitError(Exception):
    """Raised when plugin rate limit is exceeded."""
    pass
```

## Multi-Tenant Security

### Data Isolation

```python
# application/plugins/security/tenant_isolation.py

from typing import Optional
from functools import wraps


class TenantIsolationGuard:
    """
    Ensures plugins cannot access data from other organizations.

    All database queries must include organization_id filter.
    """

    def __init__(self, plugin_id: str):
        self.plugin_id = plugin_id
        self._current_org: Optional[int] = None

    def set_organization_context(self, organization_id: int) -> None:
        """Set the current organization context."""
        self._current_org = organization_id

    def clear_organization_context(self) -> None:
        """Clear the organization context."""
        self._current_org = None

    def require_org_context(self):
        """
        Decorator requiring organization context.

        Raises:
            TenantViolationError: If no org context set
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                if self._current_org is None:
                    raise TenantViolationError(
                        f"Plugin '{self.plugin_id}' attempted operation "
                        "without organization context"
                    )
                return await func(*args, **kwargs)
            return wrapper
        return decorator

    def validate_org_access(self, organization_id: int) -> bool:
        """
        Validate plugin can access organization.

        Args:
            organization_id: Organization to access

        Returns:
            True if access allowed
        """
        if self._current_org is None:
            return False
        return organization_id == self._current_org


class TenantViolationError(Exception):
    """Raised when tenant isolation is violated."""
    pass
```

### Cross-Plugin Security

```python
# application/plugins/security/cross_plugin.py

from typing import Set, Dict


class CrossPluginSecurityManager:
    """
    Manages security between plugins.

    Plugins cannot directly access each other's resources.
    """

    def __init__(self):
        # Which plugins can interact with which
        self._allowed_interactions: Dict[str, Set[str]] = {}

    def allow_interaction(
        self,
        source_plugin: str,
        target_plugin: str
    ) -> None:
        """
        Allow source plugin to interact with target.

        Must be configured by admin or in manifest.
        """
        if source_plugin not in self._allowed_interactions:
            self._allowed_interactions[source_plugin] = set()
        self._allowed_interactions[source_plugin].add(target_plugin)

    def can_interact(
        self,
        source_plugin: str,
        target_plugin: str
    ) -> bool:
        """Check if source can interact with target."""
        if source_plugin == target_plugin:
            return True  # Can always interact with self
        allowed = self._allowed_interactions.get(source_plugin, set())
        return target_plugin in allowed

    def check_interaction(
        self,
        source_plugin: str,
        target_plugin: str
    ) -> None:
        """
        Check and raise if interaction not allowed.

        Raises:
            CrossPluginViolationError: If not allowed
        """
        if not self.can_interact(source_plugin, target_plugin):
            raise CrossPluginViolationError(
                f"Plugin '{source_plugin}' cannot interact with '{target_plugin}'"
            )


class CrossPluginViolationError(Exception):
    """Raised when cross-plugin access is violated."""
    pass
```

## External Plugin Security

### Code Signing

```python
# application/plugins/security/signing.py

import hashlib
import hmac
from typing import Optional
from pathlib import Path


class PluginSigner:
    """
    Signs and verifies external plugins.

    Ensures plugin code hasn't been tampered with.
    """

    def __init__(self, signing_key: str):
        self.signing_key = signing_key.encode()

    def sign_plugin(self, plugin_path: Path) -> str:
        """
        Create signature for plugin.

        Args:
            plugin_path: Path to plugin directory

        Returns:
            Signature string
        """
        content_hash = self._hash_directory(plugin_path)
        signature = hmac.new(
            self.signing_key,
            content_hash.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature

    def verify_signature(
        self,
        plugin_path: Path,
        signature: str
    ) -> bool:
        """
        Verify plugin signature.

        Args:
            plugin_path: Path to plugin directory
            signature: Expected signature

        Returns:
            True if valid
        """
        expected = self.sign_plugin(plugin_path)
        return hmac.compare_digest(expected, signature)

    def _hash_directory(self, path: Path) -> str:
        """Create hash of directory contents."""
        hasher = hashlib.sha256()

        for file_path in sorted(path.rglob("*")):
            if file_path.is_file():
                # Include relative path in hash
                rel_path = file_path.relative_to(path)
                hasher.update(str(rel_path).encode())
                hasher.update(file_path.read_bytes())

        return hasher.hexdigest()
```

### Installation Approval

```python
# application/plugins/security/approval.py

from enum import Enum
from datetime import datetime, timezone
from typing import Optional


class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class PluginApprovalManager:
    """
    Manages approval workflow for external plugins.

    External plugins require admin approval before installation.
    """

    async def request_approval(
        self,
        plugin_id: str,
        manifest: dict,
        requested_by_id: int
    ) -> int:
        """
        Request approval for plugin installation.

        Args:
            plugin_id: Plugin identifier
            manifest: Plugin manifest
            requested_by_id: User requesting installation

        Returns:
            Approval request ID
        """
        # Create approval request
        from models.plugin import PluginApprovalRequest
        request = await PluginApprovalRequest.create(
            plugin_id=plugin_id,
            manifest=manifest,
            status=ApprovalStatus.PENDING,
            requested_by_id=requested_by_id,
            requested_at=datetime.now(timezone.utc)
        )
        return request.id

    async def approve(
        self,
        request_id: int,
        approved_by_id: int,
        notes: Optional[str] = None
    ) -> bool:
        """
        Approve plugin installation request.

        Args:
            request_id: Approval request ID
            approved_by_id: Admin approving
            notes: Optional approval notes

        Returns:
            True if approved successfully
        """
        from models.plugin import PluginApprovalRequest
        request = await PluginApprovalRequest.get_or_none(id=request_id)

        if not request or request.status != ApprovalStatus.PENDING:
            return False

        request.status = ApprovalStatus.APPROVED
        request.reviewed_by_id = approved_by_id
        request.reviewed_at = datetime.now(timezone.utc)
        request.review_notes = notes
        await request.save()

        return True

    async def reject(
        self,
        request_id: int,
        rejected_by_id: int,
        reason: str
    ) -> bool:
        """Reject plugin installation request."""
        from models.plugin import PluginApprovalRequest
        request = await PluginApprovalRequest.get_or_none(id=request_id)

        if not request or request.status != ApprovalStatus.PENDING:
            return False

        request.status = ApprovalStatus.REJECTED
        request.reviewed_by_id = rejected_by_id
        request.reviewed_at = datetime.now(timezone.utc)
        request.review_notes = reason
        await request.save()

        return True
```

## Security Best Practices for Plugin Developers

### Do's

1. **Always validate input** - Never trust user or external input
2. **Use parameterized queries** - Prevent SQL injection
3. **Escape output** - Prevent XSS in UI
4. **Check authorization** - Use AuthorizationServiceV2
5. **Log security events** - Help detect attacks
6. **Handle errors gracefully** - Don't expose internals
7. **Minimize permissions** - Request only what's needed
8. **Keep dependencies updated** - Patch vulnerabilities

### Don'ts

1. **Don't store secrets in code** - Use environment variables
2. **Don't disable security checks** - Even for debugging
3. **Don't access other plugins directly** - Use events
4. **Don't bypass organization context** - Maintain tenant isolation
5. **Don't use eval/exec** - Avoid code injection
6. **Don't trust client data** - Always validate server-side
7. **Don't log sensitive data** - Mask passwords, tokens
8. **Don't hardcode credentials** - Use config service

### Security Checklist for Plugin Review

```markdown
## Plugin Security Review Checklist

### Manifest Review
- [ ] Plugin ID follows naming conventions
- [ ] Version uses semver format
- [ ] Permissions are minimal and justified
- [ ] Dependencies are up-to-date

### Code Review
- [ ] No dangerous functions (eval, exec, etc.)
- [ ] All database queries filter by organization
- [ ] Authorization checks before operations
- [ ] Input validation on all endpoints
- [ ] Output escaping in UI
- [ ] Error handling doesn't expose internals
- [ ] Logging uses lazy formatting
- [ ] No hardcoded secrets or credentials

### Data Handling
- [ ] Sensitive data is encrypted at rest
- [ ] PII is handled according to policy
- [ ] Data retention policies followed
- [ ] Cross-tenant access is prevented

### Network Security
- [ ] Network requests are necessary
- [ ] HTTPS is used for external calls
- [ ] Timeouts are configured
- [ ] Error responses are handled

### Testing
- [ ] Security test cases exist
- [ ] Authorization is tested
- [ ] Input validation is tested
- [ ] Error handling is tested
```

## Incident Response

### Security Incident Handling

1. **Detection**: Monitor plugin activity logs for anomalies
2. **Containment**: Disable affected plugin immediately
3. **Investigation**: Review logs, code, and affected data
4. **Remediation**: Fix vulnerability, restore data if needed
5. **Recovery**: Re-enable plugin after verification
6. **Lessons Learned**: Update security controls

### Emergency Plugin Disable

```python
# Emergency disable function for security incidents

async def emergency_disable_plugin(
    plugin_id: str,
    reason: str,
    disabled_by_id: int
) -> None:
    """
    Emergency disable a plugin across all organizations.

    Args:
        plugin_id: Plugin to disable
        reason: Reason for emergency disable
        disabled_by_id: Admin performing action
    """
    import logging
    logger = logging.getLogger("plugin.security")

    # Disable globally
    from application.plugins.registry import PluginRegistry
    await PluginRegistry.emergency_disable(plugin_id)

    # Disable for all organizations
    from models.plugin import OrganizationPlugin
    await OrganizationPlugin.filter(plugin_id=plugin_id).update(
        enabled=False
    )

    # Create security incident record
    logger.critical(
        "SECURITY: Plugin '%s' emergency disabled by user %s. Reason: %s",
        plugin_id, disabled_by_id, reason
    )

    # Notify administrators
    # (Implementation depends on notification system)
```

---

**Last Updated**: November 30, 2025
