"""
Developer Dashboard Web Module

FastAPI application serving the health monitoring dashboard.
"""

from .app import app, get_collector_for_component

__all__ = ["app", "get_collector_for_component"]
