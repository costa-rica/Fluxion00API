"""
API module for Fluxion00API.

This module provides the FastAPI application with WebSocket endpoints
and static file serving.
"""

from .app import app

__all__ = ["app"]
