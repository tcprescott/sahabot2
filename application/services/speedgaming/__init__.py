"""SpeedGaming integration services."""

from application.services.speedgaming.speedgaming_service import SpeedGamingService
from application.services.speedgaming.speedgaming_etl_service import SpeedGamingETLService

__all__ = [
    'SpeedGamingService',
    'SpeedGamingETLService',
]
