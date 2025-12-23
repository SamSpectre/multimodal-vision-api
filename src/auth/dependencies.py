"""
Authentication Dependencies for FastAPI

FastAPI dependencies are reusable components that:
1. Run before your endpoint code
2. Can validate/extract data
3. Can return values to your endpoint
4. Handle common tasks like authentication

=== HOW DEPENDENCIES WORK ===

    @router.get("/protected")
    async def protected_route(user: User = Depends(get_current_user)):
        # 'user' is automatically populated by get_current_user
        # If auth fails, HTTP 401 is raised automatically
        return {"message": f"Hello {user.username}"}

=== AUTHENTICATION FLOW ===

1. Client sends request with header:
   Authorization: Bearer eyJ0eXAiOiJKV1Q...

2. oauth2_scheme extracts the token

3. get_current_user:
   - Decodes the token
   - Looks up the user
   - Returns User object or raises 401

4. Your endpoint receives the authenticated user
"""

from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader

from config.settings import settings
from .models import User, UserInDB, TokenData
from .utils import decode_token, verify_password


# === OAUTH2 SCHEME ===

# This tells FastAPI where to get the token from
# tokenUrl is where clients should POST to get a token
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/token",
    auto_error=False  # Don't auto-raise, we'll handle it
)

# API Key header scheme
api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False  # Don't auto-raise, we'll handle it
)


# === FAKE USER DATABASE ===
# In production, replace with real database queries

def get_user_from_db(username: str) -> Optional[UserInDB]:
    """
    Get user from database.

    Currently uses environment variables for the admin user.
    In production, replace with real database queries.

    Args:
        username: Username to look up

    Returns:
        UserInDB if found, None otherwise
    """
    # Check if it's the admin user
    if username == settings.ADMIN_USERNAME:
        # Get password hash from settings (loaded from .env)
        password_hash = settings.ADMIN_PASSWORD_HASH

        if not password_hash:
            # If no hash is set, create a default one for development
            # WARNING: Change this in production!
            from .utils import get_password_hash
            password_hash = get_password_hash("admin123")

        return UserInDB(
            username=settings.ADMIN_USERNAME,
            email="admin@example.com",
            full_name="Administrator",
            disabled=False,
            is_admin=True,
            password_hash=password_hash
        )

    return None


def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """
    Authenticate a user by username and password.

    Args:
        username: The username
        password: Plain text password

    Returns:
        UserInDB if credentials valid, None otherwise
    """
    user = get_user_from_db(username)
    if not user:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


# === DEPENDENCY FUNCTIONS ===

async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme)
) -> User:
    """
    Get the current authenticated user from JWT token.

    This is the main authentication dependency.
    Use it to protect endpoints that require login.

    Usage:
        @router.get("/protected")
        async def route(user: User = Depends(get_current_user)):
            return {"user": user.username}

    Raises:
        HTTPException 401: If token is missing or invalid
    """
    # Check if path is public
    if request.url.path in settings.PUBLIC_PATHS:
        # Return a dummy user for public paths
        return User(username="anonymous", disabled=False)

    # Check if auth is disabled (development mode)
    if not settings.AUTH_ENABLED:
        return User(username="dev_user", disabled=False, is_admin=True)

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    # Decode the token
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    # Get user from database
    user = get_user_from_db(username)
    if user is None:
        raise credentials_exception

    return User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        disabled=user.disabled,
        is_admin=user.is_admin
    )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current user, but only if account is active.

    Use this instead of get_current_user when you need
    to ensure the user's account isn't disabled.

    Raises:
        HTTPException 403: If user account is disabled
    """
    if current_user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    return current_user


async def verify_api_key(
    request: Request,
    api_key: Optional[str] = Depends(api_key_header)
) -> str:
    """
    Verify API key from X-API-Key header.

    Use this for service-to-service authentication.

    Usage:
        @router.get("/service")
        async def route(api_key: str = Depends(verify_api_key)):
            return {"message": "Authorized"}

    Raises:
        HTTPException 401: If API key is missing or invalid
    """
    # Check if path is public
    if request.url.path in settings.PUBLIC_PATHS:
        return "public"

    # Check if auth is disabled
    if not settings.AUTH_ENABLED:
        return "auth_disabled"

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Check against configured API key
    if settings.API_KEY and api_key == settings.API_KEY:
        return api_key

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
        headers={"WWW-Authenticate": "ApiKey"},
    )


async def require_auth(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    api_key: Optional[str] = Depends(api_key_header)
) -> User:
    """
    Require either JWT token OR API key.

    Flexible authentication that accepts either method.
    Useful for endpoints that should work with both users and services.

    Priority:
    1. JWT token (if provided)
    2. API key (if provided)
    3. Raise 401

    Usage:
        @router.get("/flexible")
        async def route(user: User = Depends(require_auth)):
            return {"user": user.username}
    """
    # Check if path is public
    if request.url.path in settings.PUBLIC_PATHS:
        return User(username="anonymous", disabled=False)

    # Check if auth is disabled
    if not settings.AUTH_ENABLED:
        return User(username="dev_user", disabled=False, is_admin=True)

    # Try JWT first
    if token:
        try:
            return await get_current_user(request, token)
        except HTTPException:
            pass  # Fall through to try API key

    # Try API key
    if api_key:
        try:
            await verify_api_key(request, api_key)
            return User(username="api_key_user", disabled=False, is_admin=False)
        except HTTPException:
            pass

    # Neither worked
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide JWT token or API key.",
        headers={"WWW-Authenticate": "Bearer, ApiKey"},
    )


async def require_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Require admin privileges.

    Use for admin-only endpoints.

    Raises:
        HTTPException 403: If user is not an admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user
