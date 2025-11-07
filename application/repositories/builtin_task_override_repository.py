"""
Builtin Task Override repository for SahaBot2.

This module provides data access layer for builtin task overrides.
"""
from __future__ import annotations
from typing import Optional, List, Dict
from models.builtin_task_override import BuiltinTaskOverride


class BuiltinTaskOverrideRepository:
    """
    Repository for builtin task override data access.

    Handles CRUD operations for built-in task overrides.
    """

    async def get_by_task_id(self, task_id: str) -> Optional[BuiltinTaskOverride]:
        """
        Get a builtin task override by task ID.

        Args:
            task_id: The built-in task identifier

        Returns:
            BuiltinTaskOverride instance or None if not found
        """
        return await BuiltinTaskOverride.filter(task_id=task_id).first()

    async def create(self, task_id: str, is_active: bool) -> BuiltinTaskOverride:
        """
        Create a new builtin task override.

        Args:
            task_id: The built-in task identifier
            is_active: Whether the task should be active

        Returns:
            Created BuiltinTaskOverride instance
        """
        return await BuiltinTaskOverride.create(
            task_id=task_id,
            is_active=is_active
        )

    async def update(self, task_id: str, is_active: bool) -> Optional[BuiltinTaskOverride]:
        """
        Update a builtin task override.

        Args:
            task_id: The built-in task identifier
            is_active: Whether the task should be active

        Returns:
            Updated BuiltinTaskOverride instance or None if not found
        """
        override = await self.get_by_task_id(task_id)
        if override:
            override.is_active = is_active
            await override.save()
        return override

    async def set_active(self, task_id: str, is_active: bool) -> BuiltinTaskOverride:
        """
        Set the active status for a builtin task (create or update).

        Args:
            task_id: The built-in task identifier
            is_active: Whether the task should be active

        Returns:
            BuiltinTaskOverride instance
        """
        override = await self.get_by_task_id(task_id)
        if override:
            override.is_active = is_active
            await override.save()
        else:
            override = await self.create(task_id, is_active)
        return override

    async def delete(self, task_id: str) -> bool:
        """
        Delete a builtin task override.

        Args:
            task_id: The built-in task identifier

        Returns:
            True if deleted, False if not found
        """
        override = await self.get_by_task_id(task_id)
        if override:
            await override.delete()
            return True
        return False

    async def list_all(self) -> List[BuiltinTaskOverride]:
        """
        Get all builtin task overrides.

        Returns:
            List of all BuiltinTaskOverride instances
        """
        return await BuiltinTaskOverride.all()

    async def get_overrides_dict(self) -> Dict[str, bool]:
        """
        Get all overrides as a dictionary mapping task_id to is_active.

        Returns:
            Dictionary mapping task_id to is_active status
        """
        overrides = await self.list_all()
        return {override.task_id: override.is_active for override in overrides}
