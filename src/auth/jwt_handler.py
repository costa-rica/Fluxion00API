"""
JWT authentication handler for Fluxion00API.

This module provides JWT token verification compatible with News Nexus API
(ExpressJS/TypeScript) tokens using the same JWT_SECRET.
"""

import os
import jwt
from typing import Optional, Dict, Any
from src.database import get_db


class JWTAuthError(Exception):
    """Exception raised when JWT authentication fails."""

    def __init__(self, message: str, code: str):
        """
        Initialize JWT authentication error.

        Args:
            message: Human-readable error message
            code: Machine-readable error code
        """
        super().__init__(message)
        self.message = message
        self.code = code


def get_jwt_secret() -> str:
    """
    Get JWT secret from environment variables.

    Returns:
        str: JWT secret key

    Raises:
        ValueError: If JWT_SECRET not found in environment
    """
    secret = os.getenv('JWT_SECRET')
    if not secret:
        raise ValueError(
            "JWT_SECRET environment variable is required for authentication"
        )
    return secret


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode JWT token.

    Verifies token signature using shared JWT_SECRET and decodes payload.
    Compatible with News Nexus API tokens (Node.js jsonwebtoken library).

    Args:
        token: JWT token string

    Returns:
        Dict containing decoded payload: { "id": <user_id> }

    Raises:
        JWTAuthError: If token is invalid, expired, or malformed

    Example:
        >>> payload = verify_token("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
        >>> user_id = payload["id"]
    """
    if not token:
        raise JWTAuthError("Token is required", "token_missing")

    try:
        secret = get_jwt_secret()

        # Decode and verify token
        # algorithm='HS256' matches Node.js jsonwebtoken default
        # options={'verify_exp': False} because NN API tokens don't have expiration
        payload = jwt.decode(
            token,
            secret,
            algorithms=['HS256'],
            options={'verify_exp': False}
        )

        # Validate payload structure
        if 'id' not in payload:
            raise JWTAuthError(
                "Invalid token payload: missing 'id' field",
                "invalid_payload"
            )

        return payload

    except jwt.InvalidTokenError as e:
        raise JWTAuthError(f"Invalid token: {str(e)}", "invalid_token")
    except jwt.DecodeError as e:
        raise JWTAuthError(f"Token decode error: {str(e)}", "decode_error")
    except Exception as e:
        raise JWTAuthError(f"Authentication error: {str(e)}", "auth_error")


def verify_user_exists(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Verify that user exists in the database.

    After successfully decoding JWT, verify the user still exists
    in the Users table (user might be deleted/deactivated).

    Args:
        user_id: User ID from JWT payload

    Returns:
        Dict containing user data if found, None otherwise

    Example:
        >>> user = verify_user_exists(1)
        >>> if user:
        ...     print(f"User {user['username']} authenticated")
    """
    db = get_db()

    query = """
        SELECT id, username, email, isAdmin, createdAt, updatedAt
        FROM Users
        WHERE id = ?
    """

    with db.get_cursor() as cursor:
        cursor.execute(query, (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def authenticate_token(token: str) -> Dict[str, Any]:
    """
    Complete authentication: verify token and validate user.

    This is the main authentication function that combines token verification
    and user validation. Use this for WebSocket authentication middleware.

    Args:
        token: JWT token string

    Returns:
        Dict containing authenticated user data:
            - id: User ID
            - username: Username
            - email: Email address
            - isAdmin: Admin flag
            - createdAt: Account creation timestamp
            - updatedAt: Last update timestamp

    Raises:
        JWTAuthError: If authentication fails at any step

    Example:
        >>> user = authenticate_token(token)
        >>> print(f"Authenticated user: {user['username']}")
    """
    # Step 1: Verify and decode token
    payload = verify_token(token)
    user_id = payload['id']

    # Step 2: Verify user exists in database
    user = verify_user_exists(user_id)

    if not user:
        raise JWTAuthError(
            f"User with id {user_id} not found in database",
            "user_not_found"
        )

    return user


def extract_token_from_query(query_params: Dict[str, str]) -> Optional[str]:
    """
    Extract JWT token from query parameters.

    Args:
        query_params: Dictionary of query parameters

    Returns:
        Token string if found, None otherwise

    Example:
        >>> token = extract_token_from_query({"token": "eyJhbGci..."})
    """
    return query_params.get('token')
