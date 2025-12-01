"""
Base plugin class and provider interfaces.

This package contains the abstract base classes that all plugins must implement.
"""

from application.plugins.base.plugin import BasePlugin
from application.plugins.base.model_provider import ModelProvider
from application.plugins.base.route_provider import RouteProvider, PageRoute, APIRoute
from application.plugins.base.page_provider import PageProvider, PageRegistration
from application.plugins.base.command_provider import CommandProvider
from application.plugins.base.event_provider import EventProvider, EventListenerRegistration
from application.plugins.base.task_provider import TaskProvider, TaskRegistration

__all__ = [
    "BasePlugin",
    "ModelProvider",
    "RouteProvider",
    "PageRoute",
    "APIRoute",
    "PageProvider",
    "PageRegistration",
    "CommandProvider",
    "EventProvider",
    "EventListenerRegistration",
    "TaskProvider",
    "TaskRegistration",
]
