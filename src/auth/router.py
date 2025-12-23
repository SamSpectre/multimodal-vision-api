"""
Authentication Router - Login & Token Endpoints

Provides endpoints for:
- POST /token - OAuth2 compatible token endpoint
- POST /login - User-friendly login endpoint
- GET /me - Get current user info
- POST /api-key - Generate new API key (admin only)

=== OAUTH2 PASSWORD FLOW ===

The standard OAuth2 password flow:

1. Client sends POST to /token with:
   - username (form field)
   - password (form field)
   - Content-Type: application/x-www-form-urlencoded

2. Server validates credentials

3. Server returns:
   {
       "access_token": "eyJ0eXAi...",
       "token_type": "bearer"
   }

4. Client uses token in subsequent requests:
   Authorization: Bearer eyJ0eXAi...
"""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from config.settings import settings
from .models import Token, User, LoginRequest, APIKeyResponse
from .utils import create_access_token, generate_api_key
from .dependencies import (
    authenticate_user,
    get_current_user,
    get_current_active_user,
    require_admin,
)


router = APIRouter()


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token endpoint.

    This endpoint follows the OAuth2 password flow standard.
    Use this if you're integrating with OAuth2 clients.

    **Request:**
    - Content-Type: application/x-www-form-urlencoded
    - Body: username=admin&password=admin123

    **Response:**
    ```json
    {
        "access_token": "eyJ0eXAi...",
        "token_type": "bearer"
    }
    ```

    **Usage:**
    Include the token in subsequent requests:
    ```
    Authorization: Bearer eyJ0eXAi...
    ```
    """
    user = authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")


@router.post("/login", response_model=Token)
async def login(request: LoginRequest):
    """
    User-friendly login endpoint.

    Alternative to /token that accepts JSON body.
    Easier to use with REST clients and JavaScript.

    **Request:**
    ```json
    {
        "username": "admin",
        "password": "admin123"
    }
    ```

    **Response:**
    ```json
    {
        "access_token": "eyJ0eXAi...",
        "token_type": "bearer"
    }
    ```

    **Default Credentials (Development):**
    - Username: admin
    - Password: admin123

    ⚠️ Change these in production by setting ADMIN_PASSWORD_HASH in .env
    """
    user = authenticate_user(request.username, request.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user information.

    Returns the profile of the authenticated user.
    Useful for checking if the token is valid and getting user details.

    **Requires:** Valid JWT token in Authorization header

    **Response:**
    ```json
    {
        "username": "admin",
        "email": "admin@example.com",
        "full_name": "Administrator",
        "disabled": false,
        "is_admin": true
    }
    ```
    """
    return current_user


@router.get("/verify")
async def verify_token_endpoint(
    current_user: User = Depends(get_current_user)
):
    """
    Verify if the current token is valid.

    Quick endpoint to check token validity without retrieving full user info.

    **Requires:** Valid JWT token

    **Response:**
    ```json
    {
        "valid": true,
        "username": "admin"
    }
    ```
    """
    return {
        "valid": True,
        "username": current_user.username
    }


@router.post("/api-key", response_model=APIKeyResponse)
async def create_api_key(
    current_user: User = Depends(require_admin)
):
    """
    Generate a new API key.

    **Requires:** Admin privileges

    ⚠️ **IMPORTANT:** The API key is only shown ONCE!
    Store it securely - it cannot be retrieved later.

    **Response:**
    ```json
    {
        "key": "vp_abc123...",
        "name": "Generated API Key",
        "created_at": "2024-12-23T...",
        "expires_at": null
    }
    ```

    **Usage:**
    Include the key in requests:
    ```
    X-API-Key: vp_abc123...
    ```
    """
    from datetime import datetime

    key = generate_api_key()

    return APIKeyResponse(
        key=key,
        name="Generated API Key",
        created_at=datetime.now().isoformat(),
        expires_at=None  # Keys don't expire by default
    )


@router.get("/status")
async def auth_status():
    """
    Get authentication system status.

    Public endpoint to check auth configuration.

    **Response:**
    ```json
    {
        "auth_enabled": true,
        "jwt_algorithm": "HS256",
        "token_expire_minutes": 30,
        "api_key_configured": false
    }
    ```
    """
    return {
        "auth_enabled": settings.AUTH_ENABLED,
        "jwt_algorithm": settings.JWT_ALGORITHM,
        "token_expire_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        "api_key_configured": bool(settings.API_KEY),
        "admin_configured": bool(settings.ADMIN_PASSWORD_HASH),
    }
