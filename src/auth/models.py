"""
Authentication Models

Defines the data structures for authentication:
- User: Represents a user in the system
- Token: The JWT token response
- TokenData: Data extracted from a JWT token

=== WHY PYDANTIC MODELS? ===

Pydantic models provide:
1. Automatic validation - Invalid data raises clear errors
2. Type conversion - Strings become ints, etc.
3. Serialization - Easy JSON conversion
4. Documentation - FastAPI uses these for API docs
"""

from typing import Optional
from pydantic import BaseModel, Field


class User(BaseModel):
    """
    Represents a user in the system.

    This is the internal user representation.
    Password is NEVER stored in plain text - only the hash.
    """
    username: str = Field(..., description="Unique username")
    email: Optional[str] = Field(default=None, description="User email address")
    full_name: Optional[str] = Field(default=None, description="User's full name")
    disabled: bool = Field(default=False, description="Is user account disabled?")
    is_admin: bool = Field(default=False, description="Does user have admin privileges?")


class UserInDB(User):
    """
    User model with hashed password.

    This is used internally - NEVER expose password_hash to clients.
    The password_hash is a bcrypt hash, not the actual password.
    """
    password_hash: str = Field(..., description="Bcrypt hash of password")


class Token(BaseModel):
    """
    JWT Token response.

    This is what the /login endpoint returns.
    The client stores this and sends it with each request.

    Example response:
    {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "token_type": "bearer"
    }
    """
    access_token: str = Field(..., description="The JWT access token")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")


class TokenData(BaseModel):
    """
    Data extracted from a JWT token.

    When we decode a JWT, this is what we extract.
    Used internally to identify the user making a request.
    """
    username: Optional[str] = Field(default=None, description="Username from token")
    exp: Optional[int] = Field(default=None, description="Expiration timestamp")


class LoginRequest(BaseModel):
    """
    Login request body.

    Sent by client to /api/v1/auth/login
    """
    username: str = Field(..., description="Username", min_length=3, max_length=50)
    password: str = Field(..., description="Password", min_length=6)


class APIKeyCreate(BaseModel):
    """
    Request to create a new API key.
    """
    name: str = Field(..., description="Descriptive name for the API key")
    expires_days: Optional[int] = Field(default=365, description="Days until expiration")


class APIKeyResponse(BaseModel):
    """
    API key creation response.

    IMPORTANT: The full key is only shown ONCE at creation.
    Store it securely - it cannot be retrieved later.
    """
    key: str = Field(..., description="The API key (only shown once!)")
    name: str = Field(..., description="Name of the API key")
    created_at: str = Field(..., description="Creation timestamp")
    expires_at: Optional[str] = Field(default=None, description="Expiration timestamp")
