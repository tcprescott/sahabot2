"""
RacerVerification Plugin for SahaBot2.

Provides Discord role-based racer verification:
- Configuration of verification requirements per organization
- Automatic role granting based on RaceTime.gg race completion
- User verification status tracking
"""

from plugins.builtin.racer_verification.plugin import RacerVerificationPlugin

__all__ = ["RacerVerificationPlugin"]
