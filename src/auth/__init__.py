"""
Authentication Module for Vision Platform API

This module provides secure authentication for the API using:
1. JWT (JSON Web Tokens) - For user authentication
2. API Keys - For service-to-service communication

=== HOW JWT AUTHENTICATION WORKS ===

1. User sends username/password to /api/v1/auth/login
2. Server validates credentials
3. Server creates a JWT token containing:
   - User ID
   - Expiration time
   - Signature (using SECRET_KEY)
4. User includes token in requests: Authorization: Bearer <token>
5. Server validates token on each request

=== HOW API KEY AUTHENTICATION WORKS ===

1. Admin creates an API key in .env
2. Client sends key in header: X-API-Key: <key>
3. Server validates key on each request

Usage:
    from src.auth import get_current_user, verify_api_key

    # Protect an endpoint with JWT
    @router.get("/protected")
    async def protected_route(user: User = Depends(get_current_user)):
        return {"message": f"Hello {user.username}"}

    # Protect with API key
    @router.get("/service")
    async def service_route(api_key: str = Depends(verify_api_key)):
        return {"message": "API key valid"}
"""

from .models import User, Token, TokenData
from .utils import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_token,
    generate_api_key,
)
from .dependencies import (
    get_current_user,
    get_current_active_user,
    verify_api_key,
    require_auth,
)

__all__ = [
    # Models
    "User",
    "Token",
    "TokenData",
    # Utils
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "decode_token",
    "generate_api_key",
    # Dependencies
    "get_current_user",
    "get_current_active_user",
    "verify_api_key",
    "require_auth",
]
