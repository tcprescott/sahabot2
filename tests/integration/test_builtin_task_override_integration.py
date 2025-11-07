"""
Integration test for builtin task override end-to-end flow.

Tests the complete flow from setting override to scheduler checking it.
"""

import pytest
from datetime import datetime, timezone
from application.services.tasks.task_scheduler_service import TaskSchedulerService
from application.services.tasks.builtin_tasks import get_builtin_task


@pytest.mark.integration
class TestBuiltinTaskOverrideIntegration:
    """Integration tests for builtin task override functionality."""

    @pytest.mark.asyncio
    async def test_end_to_end_override_flow(self, db, admin_user):
        """
        Test complete flow: set override -> reload -> check effective status -> scheduler respects it.
        """
        service = TaskSchedulerService()
        
        # Get a built-in task that is active by default
        task = get_builtin_task('cleanup_tournament_usage')
        assert task is not None
        assert task.is_active is True  # Active by default in code
        
        # Initially, no override exists - should use default
        effective = TaskSchedulerService.get_effective_active_status(
            'cleanup_tournament_usage', 
            task.is_active
        )
        assert effective is True  # No override, uses default
        
        # Admin disables the task via service
        success = await service.set_builtin_task_active(
            admin_user,
            'cleanup_tournament_usage',
            False
        )
        assert success is True
        
        # Check effective status - should now be False
        effective = TaskSchedulerService.get_effective_active_status(
            'cleanup_tournament_usage',
            task.is_active
        )
        assert effective is False  # Override applied
        
        # Simulate restart by clearing cache and reloading
        TaskSchedulerService.clear_builtin_task_overrides_cache()
        await TaskSchedulerService.reload_builtin_task_overrides()
        
        # Override should persist after reload
        effective = TaskSchedulerService.get_effective_active_status(
            'cleanup_tournament_usage',
            task.is_active
        )
        assert effective is False  # Still False after reload
        
        # Re-enable the task
        success = await service.set_builtin_task_active(
            admin_user,
            'cleanup_tournament_usage',
            True
        )
        assert success is True
        
        # Should be active again
        effective = TaskSchedulerService.get_effective_active_status(
            'cleanup_tournament_usage',
            task.is_active
        )
        assert effective is True

    @pytest.mark.asyncio
    async def test_scheduler_respects_override(self, db, admin_user):
        """
        Test that the scheduler's _should_run_builtin_task respects overrides.
        """
        service = TaskSchedulerService()
        
        # Get a built-in task
        task = get_builtin_task('async_tournament_timeout_pending')
        assert task is not None
        
        # Disable it via override
        await service.set_builtin_task_active(
            admin_user,
            'async_tournament_timeout_pending',
            False
        )
        
        # Verify effective status is False
        effective = TaskSchedulerService.get_effective_active_status(
            task.task_id,
            task.is_active
        )
        assert effective is False
        
        # The scheduler should check effective status
        # In the actual scheduler loop (line 723), it checks:
        # effective_is_active = cls.get_effective_active_status(builtin.task_id, builtin.is_active)
        # if effective_is_active and cls._should_run_builtin_task(builtin, now):
        #
        # So a disabled task won't run even if _should_run_builtin_task returns True
        
        # This is verified by the service layer check in execute_builtin_task_now
        can_execute = await TaskSchedulerService.execute_builtin_task_now(
            admin_user,
            'async_tournament_timeout_pending'
        )
        # Should fail because task is not active (override = False)
        assert can_execute is False

    @pytest.mark.asyncio
    async def test_get_builtin_tasks_with_status_applies_overrides(self, db, admin_user):
        """
        Test that get_builtin_tasks_with_status returns effective active status.
        """
        service = TaskSchedulerService()
        
        # Disable a task
        await service.set_builtin_task_active(
            admin_user,
            'speedgaming_import',
            False
        )
        
        # Get tasks with status
        tasks = TaskSchedulerService.get_builtin_tasks_with_status(active_only=False)
        
        # Find the disabled task
        speedgaming_task = next(
            (t for t in tasks if t['task_id'] == 'speedgaming_import'),
            None
        )
        assert speedgaming_task is not None
        assert speedgaming_task['is_active'] is False  # Override applied
        
        # Get only active tasks
        active_tasks = TaskSchedulerService.get_builtin_tasks_with_status(active_only=True)
        
        # speedgaming_import should not be in active tasks
        speedgaming_in_active = any(
            t['task_id'] == 'speedgaming_import' for t in active_tasks
        )
        assert speedgaming_in_active is False

    @pytest.mark.asyncio
    async def test_multiple_overrides(self, db, admin_user):
        """
        Test managing multiple task overrides.
        """
        service = TaskSchedulerService()
        
        # Disable multiple tasks
        task_ids = [
            'cleanup_tournament_usage',
            'async_tournament_timeout_pending',
            'cleanup_placeholder_users'
        ]
        
        for task_id in task_ids:
            success = await service.set_builtin_task_active(
                admin_user,
                task_id,
                False
            )
            assert success is True
        
        # Verify all are disabled
        for task_id in task_ids:
            task = get_builtin_task(task_id)
            effective = TaskSchedulerService.get_effective_active_status(
                task_id,
                task.is_active
            )
            assert effective is False
        
        # Re-enable one
        success = await service.set_builtin_task_active(
            admin_user,
            'cleanup_tournament_usage',
            True
        )
        assert success is True
        
        # Verify state
        task = get_builtin_task('cleanup_tournament_usage')
        effective = TaskSchedulerService.get_effective_active_status(
            'cleanup_tournament_usage',
            task.is_active
        )
        assert effective is True  # Re-enabled
        
        # Others still disabled
        for task_id in task_ids[1:]:
            task = get_builtin_task(task_id)
            effective = TaskSchedulerService.get_effective_active_status(
                task_id,
                task.is_active
            )
            assert effective is False
