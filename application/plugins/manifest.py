"""
Plugin manifest schema.

This module defines the PluginManifest Pydantic model that describes
plugin metadata, dependencies, and contributions.
"""

from typing import Any, Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class PluginType(str, Enum):
    """Plugin installation type."""

    BUILTIN = "builtin"
    EXTERNAL = "external"


class PluginCategory(str, Enum):
    """Plugin category classification."""

    GLOBAL = "global"
    CORE = "core"
    COMPETITION = "competition"
    INTEGRATION = "integration"
    UTILITY = "utility"
    AUTOMATION = "automation"
    RANDOMIZER = "randomizer"


class RouteScope(str, Enum):
    """Scope for route registration."""

    GLOBAL = "global"
    ADMIN = "admin"
    ORGANIZATION = "organization"
    ROOT = "root"


class PageDefinition(BaseModel):
    """Page route definition in manifest."""

    path: str
    name: str
    scope: RouteScope = RouteScope.ORGANIZATION
    requires_auth: bool = True
    reason: Optional[str] = None

    @field_validator("reason")
    @classmethod
    def validate_root_reason(cls, v: Optional[str], info) -> Optional[str]:
        """Ensure root-scoped routes have a reason."""
        # Access other field values via info.data
        if info.data.get("scope") == RouteScope.ROOT and not v:
            raise ValueError("Root-scoped routes must provide a 'reason' field")
        return v


class APIRouteDefinition(BaseModel):
    """API route definition in manifest."""

    prefix: str
    scope: RouteScope = RouteScope.ORGANIZATION
    tags: List[str] = Field(default_factory=list)
    reason: Optional[str] = None


class DiscordCommandDefinition(BaseModel):
    """Discord command definition in manifest."""

    name: str
    description: str


class PluginDependency(BaseModel):
    """Plugin dependency specification."""

    plugin_id: str
    version: str = "*"


class PluginRequirements(BaseModel):
    """Plugin requirements specification."""

    sahabot2: str = ">=1.0.0"
    python: str = ">=3.11"
    plugins: List[PluginDependency] = Field(default_factory=list)


class PluginProvides(BaseModel):
    """What the plugin provides/contributes."""

    models: List[str] = Field(default_factory=list)
    pages: List[PageDefinition] = Field(default_factory=list)
    api_routes: List[APIRouteDefinition] = Field(default_factory=list)
    discord_commands: List[DiscordCommandDefinition] = Field(default_factory=list)
    events: List[str] = Field(default_factory=list)
    tasks: List[str] = Field(default_factory=list)
    services: List[str] = Field(default_factory=list)
    exports: List[str] = Field(default_factory=list)


class PluginPermissions(BaseModel):
    """Plugin permission requirements."""

    actions: List[str] = Field(default_factory=list)
    roles: List[str] = Field(default_factory=list)


class PluginManifest(BaseModel):
    """
    Plugin manifest schema.

    Contains all metadata about a plugin including its identity,
    dependencies, and contributions.
    """

    # Required fields
    id: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z][a-z0-9_]*$")
    name: str = Field(..., min_length=1, max_length=255)
    version: str = Field(..., min_length=1, max_length=50)
    description: str = Field(default="")

    # Optional metadata
    author: str = ""
    website: str = ""
    license: str = ""

    # Plugin classification
    type: PluginType = PluginType.BUILTIN
    category: PluginCategory = PluginCategory.UTILITY

    # Organization defaults
    enabled_by_default: bool = True
    private: bool = False
    global_plugin: bool = False

    # Dependencies
    requires: PluginRequirements = Field(default_factory=PluginRequirements)
    optional: PluginRequirements = Field(default_factory=PluginRequirements)
    conflicts: List[str] = Field(default_factory=list)

    # Feature contributions
    provides: PluginProvides = Field(default_factory=PluginProvides)

    # Authorization
    permissions: PluginPermissions = Field(default_factory=PluginPermissions)

    # Feature flags required
    feature_flags: List[str] = Field(default_factory=list)

    # Configuration schema (JSON Schema format)
    config_schema: Dict[str, Any] = Field(default_factory=dict)


class PluginConfig(BaseModel):
    """
    Plugin configuration.

    Represents the runtime configuration for a plugin,
    including whether it's enabled and any custom settings.
    """

    enabled: bool = True
    settings: Dict[str, Any] = Field(default_factory=dict)
