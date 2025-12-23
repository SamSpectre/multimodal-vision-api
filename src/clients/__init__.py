"""
Client modules for external API services.

This package contains singleton clients for external services like:
- Mistral AI (OCR 3 for document processing)
- Future: OpenAI, Anthropic, etc.

Why Singleton Pattern?
- External API clients are expensive to create (auth, connection setup)
- Reusing the same client instance improves performance
- Ensures consistent configuration across the application
"""

from src.clients.mistral_client import get_mistral_client

__all__ = ["get_mistral_client"]
