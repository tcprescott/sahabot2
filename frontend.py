"""
Frontend routes registration.

This module registers all NiceGUI pages and routes for the application.
"""

from pages import home, auth, admin


def register_routes():
    """
    Register all frontend routes.
    
    This function is called from main.py to register all NiceGUI pages.
    """
    # Register pages
    home.register()
    auth.register()
    admin.register()
    
    print("Frontend routes registered")
