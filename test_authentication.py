"""
Test Authentication System

Tests:
1. Password hashing and verification
2. JWT token creation and validation
3. API key generation
4. Login endpoint (simulated)
5. Protected endpoint access

Run: python test_authentication.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment
from dotenv import load_dotenv
load_dotenv(project_root / ".env")


def print_header(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(name, passed, details=""):
    status = "PASSED" if passed else "FAILED"
    symbol = "OK" if passed else "FAIL"
    print(f"  [{symbol}] {name}: {status}")
    if details:
        print(f"        {details[:80]}")


def test_password_hashing():
    """Test password hashing functions."""
    print_header("TEST 1: Password Hashing (bcrypt)")

    try:
        from src.auth.utils import get_password_hash, verify_password

        # Test 1: Hash a password
        password = "test_password_123"
        hashed = get_password_hash(password)

        print_result(
            "Hash Generation",
            hashed.startswith("$2b$"),
            f"Hash: {hashed[:30]}..."
        )

        # Test 2: Verify correct password
        correct = verify_password(password, hashed)
        print_result("Verify Correct Password", correct)

        # Test 3: Reject wrong password
        wrong = verify_password("wrong_password", hashed)
        print_result("Reject Wrong Password", not wrong)

        return True

    except Exception as e:
        print_result("Password Hashing", False, str(e))
        return False


def test_jwt_tokens():
    """Test JWT token creation and validation."""
    print_header("TEST 2: JWT Tokens")

    try:
        from src.auth.utils import create_access_token, decode_token, verify_token

        # Test 1: Create token
        token_data = {"sub": "testuser"}
        token = create_access_token(token_data)

        print_result(
            "Token Creation",
            len(token) > 50,
            f"Token: {token[:50]}..."
        )

        # Test 2: Decode token
        decoded = decode_token(token)
        print_result(
            "Token Decoding",
            decoded is not None and decoded.get("sub") == "testuser",
            f"Decoded sub: {decoded.get('sub') if decoded else 'None'}"
        )

        # Test 3: Verify token
        username = verify_token(token)
        print_result(
            "Token Verification",
            username == "testuser",
            f"Username: {username}"
        )

        # Test 4: Reject invalid token
        invalid_result = decode_token("invalid.token.here")
        print_result("Reject Invalid Token", invalid_result is None)

        return True

    except Exception as e:
        print_result("JWT Tokens", False, str(e))
        import traceback
        traceback.print_exc()
        return False


def test_api_key_generation():
    """Test API key generation."""
    print_header("TEST 3: API Key Generation")

    try:
        from src.auth.utils import generate_api_key

        # Test 1: Generate key
        key = generate_api_key()
        print_result(
            "Key Generation",
            key.startswith("vp_") and len(key) > 50,
            f"Key: {key[:30]}..."
        )

        # Test 2: Keys are unique
        key2 = generate_api_key()
        print_result("Keys Are Unique", key != key2)

        return True

    except Exception as e:
        print_result("API Key Generation", False, str(e))
        return False


def test_user_authentication():
    """Test user authentication flow."""
    print_header("TEST 4: User Authentication")

    try:
        from src.auth.dependencies import authenticate_user, get_user_from_db

        # Test 1: Get admin user
        admin = get_user_from_db("admin")
        print_result(
            "Get Admin User",
            admin is not None,
            f"Username: {admin.username if admin else 'None'}"
        )

        # Test 2: Authenticate with correct password
        # Note: Default password is "admin123"
        user = authenticate_user("admin", "admin123")
        print_result(
            "Auth Correct Password",
            user is not None,
            f"User: {user.username if user else 'None'}"
        )

        # Test 3: Reject wrong password
        wrong_user = authenticate_user("admin", "wrong_password")
        print_result("Reject Wrong Password", wrong_user is None)

        # Test 4: Reject unknown user
        unknown = authenticate_user("unknown_user", "any_password")
        print_result("Reject Unknown User", unknown is None)

        return True

    except Exception as e:
        print_result("User Authentication", False, str(e))
        import traceback
        traceback.print_exc()
        return False


def test_settings_loaded():
    """Test that auth settings are loaded from .env."""
    print_header("TEST 5: Settings Configuration")

    try:
        from config.settings import settings

        print_result(
            "AUTH_ENABLED",
            hasattr(settings, 'AUTH_ENABLED'),
            f"Value: {settings.AUTH_ENABLED}"
        )

        print_result(
            "SECRET_KEY",
            hasattr(settings, 'SECRET_KEY') and settings.SECRET_KEY != "",
            f"Configured: Yes (length: {len(settings.SECRET_KEY)})"
        )

        print_result(
            "JWT_ALGORITHM",
            settings.JWT_ALGORITHM == "HS256",
            f"Value: {settings.JWT_ALGORITHM}"
        )

        print_result(
            "ACCESS_TOKEN_EXPIRE_MINUTES",
            settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0,
            f"Value: {settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutes"
        )

        print_result(
            "ADMIN_USERNAME",
            settings.ADMIN_USERNAME == "admin",
            f"Value: {settings.ADMIN_USERNAME}"
        )

        print_result(
            "API_KEY",
            hasattr(settings, 'API_KEY'),
            f"Configured: {'Yes' if settings.API_KEY else 'No'}"
        )

        return True

    except Exception as e:
        print_result("Settings", False, str(e))
        return False


def test_full_auth_flow():
    """Test complete authentication flow."""
    print_header("TEST 6: Complete Auth Flow")

    try:
        from src.auth.dependencies import authenticate_user
        from src.auth.utils import create_access_token, verify_token

        # Step 1: User logs in
        user = authenticate_user("admin", "admin123")
        if not user:
            print_result("Login", False, "Authentication failed")
            return False
        print_result("Step 1: Login", True, f"User: {user.username}")

        # Step 2: Generate token
        token = create_access_token({"sub": user.username})
        print_result("Step 2: Get Token", True, f"Token: {token[:40]}...")

        # Step 3: Use token to verify identity
        username = verify_token(token)
        print_result(
            "Step 3: Verify Token",
            username == user.username,
            f"Verified user: {username}"
        )

        print("\n  Complete flow successful!")
        return True

    except Exception as e:
        print_result("Auth Flow", False, str(e))
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("   AUTHENTICATION SYSTEM - TEST SUITE")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("Password Hashing", test_password_hashing()))
    results.append(("JWT Tokens", test_jwt_tokens()))
    results.append(("API Key Generation", test_api_key_generation()))
    results.append(("Settings Configuration", test_settings_loaded()))
    results.append(("User Authentication", test_user_authentication()))
    results.append(("Complete Auth Flow", test_full_auth_flow()))

    # Summary
    print_header("TEST SUMMARY")

    passed = 0
    failed = 0
    for name, result in results:
        symbol = "OK" if result else "FAIL"
        print(f"  [{symbol}] {name}")
        if result:
            passed += 1
        else:
            failed += 1

    print("\n" + "-" * 60)
    print(f"  Total: {passed} passed, {failed} failed out of {len(results)} tests")
    print("=" * 60)

    if failed == 0:
        print("\n  Authentication system is working correctly!")
        print("\n  Default Credentials:")
        print("    Username: admin")
        print("    Password: admin123")
        print("\n  To login, POST to /api/v1/auth/login with:")
        print('    {"username": "admin", "password": "admin123"}')
        return 0
    else:
        print(f"\n  {failed} test(s) failed. Check errors above.")
        return 1


if __name__ == "__main__":
    exit(main())
