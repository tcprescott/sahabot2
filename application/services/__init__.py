"""
Application services package.

This package contains all service classes for business logic.
Services are organized by domain:
- core: Foundational services (user, audit, settings, rate limiting)
- authorization: Permission and authorization services
- organizations: Organization management
- tournaments: Tournament and race management
- discord: Discord integration
- racetime: RaceTime.gg integration
- randomizer: Game randomizer services
- speedgaming: SpeedGaming integration
- notifications: Notification system
- tasks: Task scheduling
- security: API tokens and security
"""

# Import commonly used services for convenience
from application.services.core import UserService, AuditService
from application.services.authorization import AuthorizationServiceV2
from application.services.randomizer.randomizer_service import RandomizerService

__all__ = [
    "UserService",
    "AuthorizationServiceV2",
    "AuditService",
    "RandomizerService",
]
