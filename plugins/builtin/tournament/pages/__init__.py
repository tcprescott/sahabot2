"""
Tournament plugin pages.

This module re-exports tournament-related pages from the core application.
In a future phase, these pages may be moved directly into the plugin.

For now, this provides a stable import path for plugin-internal use.
"""

# Pages are registered via the plugin's get_pages() method
# The actual page implementations are still in pages/tournaments.py and pages/tournament_admin.py
