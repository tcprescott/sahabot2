"""
Plugin configuration service.

This module provides configuration management for plugins,
including validation, merging, and persistence.
"""

import logging
from typing import Any, Dict, Optional

from application.plugins.manifest import PluginConfig
from application.plugins.registry import PluginRegistry
from application.plugins.exceptions import (
    PluginNotFoundError,
    PluginConfigurationError,
)

logger = logging.getLogger(__name__)

# Organization ID used for global (non-organization-specific) configuration
GLOBAL_CONFIG_ORG_ID = 0


class PluginConfigService:
    """
    Service for managing plugin configuration.

    This service handles:
    - Merging configuration from multiple sources
    - Validating configuration against plugin schema
    - Persisting configuration to database
    """

    async def get_config(
        self,
        plugin_id: str,
        organization_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get merged configuration for a plugin.

        Priority (highest first):
        1. Organization-specific settings
        2. Global plugin settings
        3. Manifest defaults
        4. Code defaults

        Args:
            plugin_id: Plugin identifier
            organization_id: Optional org for org-specific config

        Returns:
            Merged configuration dictionary
        """
        if not PluginRegistry.has(plugin_id):
            raise PluginNotFoundError(f"Plugin '{plugin_id}' not found")

        plugin = PluginRegistry.get(plugin_id)
        manifest = plugin.manifest

        # Start with defaults from config_schema
        config = self._get_schema_defaults(manifest.config_schema)

        # Merge global plugin config
        global_config = PluginRegistry.get_config(plugin_id, GLOBAL_CONFIG_ORG_ID)
        config.update(global_config.settings)

        # Merge organization-specific config if provided
        if organization_id is not None:
            org_config = PluginRegistry.get_config(plugin_id, organization_id)
            config.update(org_config.settings)

        return config

    async def set_config(
        self,
        plugin_id: str,
        settings: Dict[str, Any],
        organization_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> None:
        """
        Update plugin configuration.

        Args:
            plugin_id: Plugin identifier
            settings: Settings to update
            organization_id: Optional org for org-specific config
            user_id: User making the change (for audit)

        Raises:
            PluginConfigurationError: If validation fails
        """
        if not PluginRegistry.has(plugin_id):
            raise PluginNotFoundError(f"Plugin '{plugin_id}' not found")

        # Validate settings
        self.validate_config(plugin_id, settings)

        # Get existing config
        org_id = organization_id or GLOBAL_CONFIG_ORG_ID
        existing = PluginRegistry.get_config(plugin_id, org_id)

        # Merge with new settings
        merged = existing.settings.copy()
        merged.update(settings)

        # Update in registry
        new_config = PluginConfig(
            enabled=existing.enabled,
            settings=merged,
        )
        PluginRegistry.set_config(plugin_id, org_id, new_config)

        logger.info(
            "Updated config for plugin %s (org=%s) by user %s",
            plugin_id,
            organization_id,
            user_id,
        )

    def validate_config(
        self,
        plugin_id: str,
        settings: Dict[str, Any],
    ) -> None:
        """
        Validate settings against plugin's config schema.

        Args:
            plugin_id: Plugin identifier
            settings: Settings to validate

        Raises:
            PluginConfigurationError: If validation fails
        """
        if not PluginRegistry.has(plugin_id):
            raise PluginNotFoundError(f"Plugin '{plugin_id}' not found")

        plugin = PluginRegistry.get(plugin_id)
        schema = plugin.manifest.config_schema

        if not schema:
            # No schema means no validation needed
            return

        # Basic type validation from schema
        properties = schema.get("properties", {})
        for key, value in settings.items():
            if key not in properties:
                # Unknown setting - allow for flexibility
                logger.warning("Unknown config key '%s' for plugin %s", key, plugin_id)
                continue

            prop_schema = properties[key]
            expected_type = prop_schema.get("type")

            if expected_type and not self._validate_type(value, expected_type):
                raise PluginConfigurationError(
                    f"Invalid type for '{key}': expected {expected_type}, "
                    f"got {type(value).__name__}"
                )

    def _get_schema_defaults(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract default values from a JSON Schema.

        Args:
            schema: JSON Schema dictionary

        Returns:
            Dictionary of default values
        """
        defaults = {}
        properties = schema.get("properties", {})

        for key, prop in properties.items():
            if "default" in prop:
                defaults[key] = prop["default"]

        return defaults

    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """
        Validate a value against a JSON Schema type.

        Args:
            value: Value to validate
            expected_type: Expected JSON Schema type

        Returns:
            True if valid, False otherwise
        """
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None),
        }

        expected = type_map.get(expected_type)
        if expected is None:
            return True  # Unknown type, allow

        return isinstance(value, expected)
