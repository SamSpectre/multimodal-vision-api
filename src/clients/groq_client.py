"""
Groq Client - Singleton Implementation for Low-Latency Vision

This module provides a singleton Groq client for real-time robotics vision.

=== WHY GROQ FOR ROBOTICS? ===

Groq's LPU (Language Processing Unit) provides:
  - ~50ms latency for Llama 3.2 11B Vision
  - 2.6x faster than OpenAI's GPT-4o-mini
  - Consistent performance for real-time applications
  - Low cost: $0.18/1M tokens

For robotics applications requiring real-time vision:
  - Sub-100ms response time is critical
  - Groq provides cloud inference matching edge latency
  - Perfect for: object detection, pose estimation, scene understanding

=== SINGLETON PATTERN ===

Same pattern as mistral_client.py:
  1. Create client once
  2. Reuse everywhere
  3. Lazy initialization
"""

import os
from typing import Optional
from functools import lru_cache

# Import Groq SDK
try:
    from groq import Groq
except ImportError:
    Groq = None  # Will handle gracefully


# === Classic Singleton with Global Variable ===

_groq_client: Optional["Groq"] = None


def get_groq_client() -> "Groq":
    """
    Get or create the singleton Groq client.

    Returns:
        Groq: The Groq client instance

    Raises:
        ImportError: If groq package is not installed
        ValueError: If GROQ_API_KEY is not set

    Example:
        >>> client = get_groq_client()
        >>> response = client.chat.completions.create(
        ...     model="llama-3.2-11b-vision-preview",
        ...     messages=[...]
        ... )
    """
    global _groq_client

    if _groq_client is None:
        # Validate that the package is installed
        if Groq is None:
            raise ImportError(
                "groq package is not installed. "
                "Please run: pip install groq"
            )

        # Get the API key from environment
        api_key = os.getenv("GROQ_API_KEY")

        # Validate the API key exists
        if not api_key or api_key == "your_groq_api_key_here":
            raise ValueError(
                "GROQ_API_KEY is not set or is a placeholder. "
                "Please set it in your .env file. "
                "Get your API key from: https://console.groq.com/"
            )

        # Create the client
        _groq_client = Groq(api_key=api_key)
        print("[GroqClient] Created new Groq client instance (~50ms latency)")

    return _groq_client


# === Alternative: @lru_cache Singleton ===

@lru_cache(maxsize=1)
def get_groq_client_cached() -> "Groq":
    """
    Alternative singleton using lru_cache.
    Thread-safe and more Pythonic.
    """
    if Groq is None:
        raise ImportError("groq package is not installed")

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_groq_api_key_here":
        raise ValueError("GROQ_API_KEY is not set")

    return Groq(api_key=api_key)


# === Helper Functions ===

def reset_groq_client() -> None:
    """Reset the singleton (useful for testing or config changes)."""
    global _groq_client
    _groq_client = None
    get_groq_client_cached.cache_clear()
    print("[GroqClient] Client reset - will be recreated on next access")


def is_groq_available() -> bool:
    """
    Check if Groq client can be created.
    Useful for health checks and fallback logic.
    """
    try:
        if Groq is None:
            return False

        api_key = os.getenv("GROQ_API_KEY")
        return bool(api_key and api_key != "your_groq_api_key_here")
    except Exception:
        return False


# === Available Vision Models on Groq ===

GROQ_VISION_MODELS = {
    "llama-3.2-11b-vision-preview": {
        "description": "Llama 3.2 11B Vision - Fast, good accuracy",
        "latency": "~50ms",
        "recommended_for": "real-time robotics, video analysis"
    },
    "llama-3.2-90b-vision-preview": {
        "description": "Llama 3.2 90B Vision - Higher accuracy, slower",
        "latency": "~150ms",
        "recommended_for": "complex scene understanding"
    }
}


def get_recommended_vision_model(use_case: str = "robotics") -> str:
    """
    Get the recommended Groq vision model for a use case.

    Args:
        use_case: "robotics" (fast) or "accuracy" (slower but better)

    Returns:
        Model name string
    """
    if use_case == "accuracy":
        return "llama-3.2-90b-vision-preview"
    return "llama-3.2-11b-vision-preview"  # Default: fast for robotics


# === Quick Test ===

if __name__ == "__main__":
    print("Testing Groq Client for Low-Latency Robotics Vision")
    print("=" * 50)

    if not is_groq_available():
        print("Groq is not available. Check:")
        print("  1. Is groq installed? pip install groq")
        print("  2. Is GROQ_API_KEY set in .env?")
        exit(1)

    # Test singleton behavior
    print("\nGetting client (first time - should create):")
    client1 = get_groq_client()
    print(f"Client ID: {id(client1)}")

    print("\nGetting client (second time - should reuse):")
    client2 = get_groq_client()
    print(f"Client ID: {id(client2)}")

    print(f"\nSame instance? {client1 is client2}")

    print("\n" + "=" * 50)
    print("Available Vision Models:")
    for model, info in GROQ_VISION_MODELS.items():
        print(f"  - {model}")
        print(f"    Latency: {info['latency']}")
        print(f"    Use: {info['recommended_for']}")
