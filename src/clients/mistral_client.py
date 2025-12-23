"""
Mistral AI Client - Singleton Implementation

This module provides a singleton Mistral client for OCR 3 document processing.

=== SINGLETON PATTERN EXPLAINED ===

Problem: Every time we call the Mistral API, we need a client object.
Creating a new client each time is wasteful because:
  1. Network connection setup is slow
  2. Authentication (API key validation) takes time
  3. Memory is wasted creating duplicate objects

Solution: Create the client ONCE, reuse it everywhere.

How it works:
  1. _mistral_client starts as None (no client exists)
  2. First call to get_mistral_client() creates the client and stores it
  3. Future calls return the SAME stored client (no recreation)

This is called "lazy initialization" - we don't create the object
until someone actually needs it.

=== ENTERPRISE PATTERNS ===

In production systems, you'll often see:
  - Singleton for database connections
  - Singleton for API clients
  - Singleton for configuration managers
  - Singleton for logging systems

These are all expensive-to-create objects that should be shared.
"""

import os
from typing import Optional
from functools import lru_cache

# Note: Import will fail if mistralai is not installed
# Run: pip install mistralai
try:
    from mistralai import Mistral
except ImportError:
    Mistral = None  # Will handle gracefully


# === APPROACH 1: Classic Singleton with Global Variable ===
# This is the traditional way - simple and explicit

_mistral_client: Optional["Mistral"] = None  # Private global variable


def get_mistral_client() -> "Mistral":
    """
    Get or create the singleton Mistral client.

    This function implements the Singleton pattern:
    - First call: Creates the client and stores it
    - Subsequent calls: Returns the stored client

    Returns:
        Mistral: The Mistral client instance

    Raises:
        ImportError: If mistralai package is not installed
        ValueError: If MISTRAL_API_KEY is not set

    Example:
        >>> client = get_mistral_client()
        >>> result = client.ocr.process(model="mistral-ocr-2512", document={...})
    """
    global _mistral_client  # Tells Python we're using the module-level variable

    # Check if client already exists (the singleton check)
    if _mistral_client is None:
        # First time - need to create the client

        # Validate that the package is installed
        if Mistral is None:
            raise ImportError(
                "mistralai package is not installed. "
                "Please run: pip install mistralai"
            )

        # Get the API key from environment
        api_key = os.getenv("MISTRAL_API_KEY")

        # Validate the API key exists
        if not api_key or api_key == "your_mistral_api_key_here":
            raise ValueError(
                "MISTRAL_API_KEY is not set or is a placeholder. "
                "Please set it in your .env file. "
                "Get your API key from: https://console.mistral.ai/"
            )

        # Create the client (this is the expensive operation we want to do only once)
        _mistral_client = Mistral(api_key=api_key)

        # Log that we created a new client (helpful for debugging)
        print("[MistralClient] Created new Mistral client instance")

    return _mistral_client


# === APPROACH 2: Using @lru_cache (Modern Python Way) ===
# This is more Pythonic and thread-safe

@lru_cache(maxsize=1)  # Cache the result, only store 1 item
def get_mistral_client_cached() -> "Mistral":
    """
    Alternative singleton implementation using functools.lru_cache.

    @lru_cache is a decorator that caches function results.
    With maxsize=1, it effectively creates a singleton.

    Benefits over global variable approach:
    - Thread-safe (important for web servers)
    - More Pythonic
    - Can be cleared with get_mistral_client_cached.cache_clear()

    Drawbacks:
    - Slightly less explicit about what's happening
    - Arguments become part of cache key (we have none, so it's fine)
    """
    if Mistral is None:
        raise ImportError("mistralai package is not installed")

    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key or api_key == "your_mistral_api_key_here":
        raise ValueError("MISTRAL_API_KEY is not set")

    return Mistral(api_key=api_key)


# === HELPER FUNCTIONS ===

def reset_mistral_client() -> None:
    """
    Reset the singleton (useful for testing or config changes).

    In production, you rarely need this. But during development
    or testing, you might want to recreate the client with
    different settings.
    """
    global _mistral_client
    _mistral_client = None

    # Also clear the cached version
    get_mistral_client_cached.cache_clear()

    print("[MistralClient] Client reset - will be recreated on next access")


def is_mistral_available() -> bool:
    """
    Check if Mistral client can be created.

    Useful for health checks and graceful degradation.
    Returns False if:
    - Package not installed
    - API key not configured
    """
    try:
        if Mistral is None:
            return False

        api_key = os.getenv("MISTRAL_API_KEY")
        return bool(api_key and api_key != "your_mistral_api_key_here")
    except Exception:
        return False


# === ENTERPRISE PATTERN: Context Manager ===
# For explicit resource management (not needed for Mistral, but good to know)

class MistralClientManager:
    """
    Context manager for Mistral client (demonstration of pattern).

    Context managers use __enter__ and __exit__ to manage resources.
    They're used with the 'with' statement:

        with MistralClientManager() as client:
            result = client.ocr.process(...)

    This pattern is commonly used for:
    - Database connections
    - File handles
    - Network connections
    - Any resource that needs cleanup

    Note: Mistral's client doesn't require explicit cleanup,
    so this is more for educational purposes.
    """

    def __init__(self):
        self.client = None

    def __enter__(self) -> "Mistral":
        """Called when entering 'with' block."""
        self.client = get_mistral_client()
        return self.client

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Called when exiting 'with' block (even if exception occurred)."""
        # Mistral client doesn't need cleanup, but this is where you'd do it
        # For example: self.client.close() for database connections
        pass


# === QUICK TEST ===

if __name__ == "__main__":
    """
    Run this file directly to test the singleton:
    python src/clients/mistral_client.py
    """
    print("Testing Mistral Client Singleton Pattern")
    print("=" * 50)

    # Check availability first
    if not is_mistral_available():
        print("Mistral is not available. Check:")
        print("  1. Is mistralai installed? pip install mistralai")
        print("  2. Is MISTRAL_API_KEY set in .env?")
        exit(1)

    # Test singleton behavior
    print("\nGetting client (first time - should create):")
    client1 = get_mistral_client()
    print(f"Client ID: {id(client1)}")

    print("\nGetting client (second time - should reuse):")
    client2 = get_mistral_client()
    print(f"Client ID: {id(client2)}")

    print(f"\nSame instance? {client1 is client2}")  # Should be True

    print("\n" + "=" * 50)
    print("Singleton working correctly!" if client1 is client2 else "ERROR: Not a singleton!")
