"""
Authentication Utilities

Provides core security functions:
- Password hashing with bcrypt
- JWT token creation and validation
- API key generation

=== PASSWORD SECURITY ===

NEVER store passwords in plain text!
We use bcrypt which:
1. Hashes the password (one-way transformation)
2. Adds a random "salt" (prevents rainbow table attacks)
3. Uses slow hashing (prevents brute force)

=== JWT TOKENS ===

JWT (JSON Web Token) structure:
    header.payload.signature

Example decoded:
{
    "sub": "username",      # Subject (who)
    "exp": 1234567890,      # Expiration time
    "iat": 1234567800       # Issued at
}

The signature proves the token wasn't tampered with.
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from config.settings import settings


# === PASSWORD HASHING ===

# CryptContext manages password hashing
# - bcrypt: Current recommended algorithm
# - deprecated="auto": Automatically upgrade old hashes
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    This is used during login to check if the provided password
    matches the stored hash.

    Args:
        plain_password: The password user entered (e.g., "secret123")
        hashed_password: The stored bcrypt hash

    Returns:
        True if password matches, False otherwise

    Example:
        >>> hashed = get_password_hash("secret123")
        >>> verify_password("secret123", hashed)
        True
        >>> verify_password("wrong", hashed)
        False
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    This is used when:
    - Creating a new user
    - Changing a password

    IMPORTANT: Store the hash, NEVER the plain password!

    Args:
        password: Plain text password

    Returns:
        Bcrypt hash string (starts with $2b$)

    Example:
        >>> hash = get_password_hash("mypassword")
        >>> print(hash)
        '$2b$12$...'  # 60 character hash
    """
    return pwd_context.hash(password)


# === JWT TOKENS ===

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.

    This is called after successful login to generate
    the token the client will use for authentication.

    Args:
        data: Dictionary with claims (usually {"sub": username})
        expires_delta: How long until token expires

    Returns:
        Encoded JWT string

    Example:
        >>> token = create_access_token({"sub": "admin"})
        >>> print(token)
        'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
    """
    to_encode = data.copy()

    # Set expiration time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # Add standard claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),  # Issued at
    })

    # Encode and sign the token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT token.

    This is called on each request to verify the token
    is valid and extract the user information.

    Args:
        token: The JWT string from Authorization header

    Returns:
        Decoded payload dict, or None if invalid

    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def verify_token(token: str) -> Optional[str]:
    """
    Verify token and extract username.

    Convenience function that decodes token and returns
    just the username if valid.

    Args:
        token: JWT token string

    Returns:
        Username if valid, None otherwise
    """
    payload = decode_token(token)
    if payload is None:
        return None

    username: str = payload.get("sub")
    if username is None:
        return None

    return username


# === API KEY GENERATION ===

def generate_api_key(prefix: str = "vp") -> str:
    """
    Generate a secure API key.

    Creates a random, URL-safe API key with a prefix
    for easy identification.

    Args:
        prefix: Prefix to identify key type (default: "vp" for Vision Platform)

    Returns:
        API key string like "vp_abc123def456..."

    Example:
        >>> key = generate_api_key()
        >>> print(key)
        'vp_7f8g9h0i1j2k3l4m5n6o7p8q9r0s'
    """
    # Generate 32 random bytes, encode as hex (64 chars)
    random_part = secrets.token_hex(32)
    return f"{prefix}_{random_part}"


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key for secure storage.

    Like passwords, we store a hash of the API key,
    not the key itself.

    Args:
        api_key: The plain API key

    Returns:
        Bcrypt hash of the key
    """
    return pwd_context.hash(api_key)


def verify_api_key_hash(plain_key: str, hashed_key: str) -> bool:
    """
    Verify an API key against its stored hash.

    Args:
        plain_key: The API key from the request
        hashed_key: The stored hash

    Returns:
        True if key matches, False otherwise
    """
    return pwd_context.verify(plain_key, hashed_key)


# === UTILITY FUNCTIONS ===

def generate_password_hash_for_env(password: str) -> str:
    """
    Generate a password hash to put in .env file.

    Run this to generate the ADMIN_PASSWORD_HASH value:
        python -c "from src.auth.utils import generate_password_hash_for_env; print(generate_password_hash_for_env('your_password'))"

    Args:
        password: The admin password you want to use

    Returns:
        Bcrypt hash to put in .env
    """
    return get_password_hash(password)


# === TESTING ===

if __name__ == "__main__":
    print("=" * 60)
    print("AUTHENTICATION UTILITIES TEST")
    print("=" * 60)

    # Test password hashing
    print("\n[1] Password Hashing")
    password = "test_password_123"
    hashed = get_password_hash(password)
    print(f"  Password: {password}")
    print(f"  Hash: {hashed[:40]}...")
    print(f"  Verify correct: {verify_password(password, hashed)}")
    print(f"  Verify wrong: {verify_password('wrong', hashed)}")

    # Test JWT
    print("\n[2] JWT Token")
    token = create_access_token({"sub": "testuser"})
    print(f"  Token: {token[:50]}...")
    decoded = decode_token(token)
    print(f"  Decoded: {decoded}")

    # Test API key
    print("\n[3] API Key Generation")
    api_key = generate_api_key()
    print(f"  Key: {api_key}")

    # Generate admin password hash
    print("\n[4] Admin Password Hash (for .env)")
    admin_hash = generate_password_hash_for_env("admin123")
    print(f"  Hash for 'admin123': {admin_hash}")

    print("\n" + "=" * 60)
    print("All utilities working correctly!")
    print("=" * 60)
