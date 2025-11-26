"""
Authentication module for Fluxion00API.

Provides JWT token verification for WebSocket authentication.
Compatible with News Nexus API tokens.
"""

from .jwt_handler import (
    JWTAuthError,
    verify_token,
    verify_user_exists,
    authenticate_token,
    extract_token_from_query
)

__all__ = [
    'JWTAuthError',
    'verify_token',
    'verify_user_exists',
    'authenticate_token',
    'extract_token_from_query'
]
