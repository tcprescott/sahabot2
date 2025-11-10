"""
Utility functions for rendering audit log details.

Shared helper functions for formatting audit log details across views.
"""

from typing import Any
from nicegui import ui


def render_audit_log_details(log: Any) -> None:
    """
    Render audit log details in a readable format.

    Args:
        log: AuditLog instance to render details for
    """
    if not log.details:
        ui.label("—").classes("text-secondary")
        return

    # Format common details
    details_text = []

    if "entity_id" in log.details:
        details_text.append(f"ID: {log.details['entity_id']}")
    if "target_user_id" in log.details:
        details_text.append(f"Target: User #{log.details['target_user_id']}")
    if "target_username" in log.details:
        details_text.append(f"User: {log.details['target_username']}")
    if "tournament_name" in log.details:
        details_text.append(f"Tournament: {log.details['tournament_name']}")
    if "organization_name" in log.details:
        details_text.append(f"Org: {log.details['organization_name']}")
    if "member_user_id" in log.details:
        details_text.append(f"Member: User #{log.details['member_user_id']}")

    if details_text:
        ui.label(" • ".join(details_text)).classes("text-sm")
    else:
        # Show count of detail keys if no common fields
        ui.label(f"{len(log.details)} details").classes("text-sm text-secondary")
