"""
Configuration settings for the Langchain Vision Agentic System.
Loads API keys, models, and manages project settings.

=== CONFIGURATION ARCHITECTURE ===

This file uses Pydantic Settings for configuration management:

1. Environment Variables (.env file)
   - Sensitive data (API keys)
   - Environment-specific settings

2. Default Values (in code)
   - Development defaults
   - Safe fallbacks

3. Type Validation
   - Pydantic validates types automatically
   - Catches configuration errors early

=== ADDING NEW SETTINGS ===

To add a new setting:
1. Add field with type hint: my_setting: str = "default"
2. Add to .env file if it's sensitive
3. Access via: settings.my_setting
"""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Get the project root directory (parent of config/)
PROJECT_ROOT = Path(__file__).parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

# Load .env file with explicit path
# This ensures it works regardless of where the script is run from
load_dotenv(dotenv_path=ENV_FILE)

# Debug: Print if .env was found (remove in production)
if ENV_FILE.exists():
    print(f"[Config] Loaded .env from: {ENV_FILE}")
else:
    print(f"[Config] WARNING: .env not found at: {ENV_FILE}")


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    These settings are loaded from a .env file in the project root.
    """

    # ============================================
    # API KEYS
    # ============================================

    OPENAI_API_KEY: str = Field(..., description="OpenAI API key")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, description="Anthropic API key")

    # Mistral AI - For OCR 3 document processing
    MISTRAL_API_KEY: Optional[str] = Field(
        default=None,
        description="Mistral AI API key for OCR 3"
    )

    # Groq - Low-latency inference for real-time robotics vision
    GROQ_API_KEY: Optional[str] = Field(
        default=None,
        description="Groq API key for low-latency vision (Llama 3.2 Vision)"
    )

    # ============================================
    # MODEL CONFIGURATION
    # ============================================

    default_llm_model: str = "gpt-4o"  # Supports vision
    default_vlm_model: str = "gpt-4o"  # Vision-Language Model
    temperature: float = 0.7
    max_tokens: int = 2000

    # Mistral OCR 3 Settings
    mistral_ocr_model: str = "mistral-ocr-2512"  # Latest OCR 3 model
    mistral_ocr_batch_enabled: bool = True  # Use batch API for 50% discount

    # ============================================
    # PER-AGENT MODEL CONFIGURATION
    # Optimized for cost, performance, and latency
    # ============================================

    # Supervisor Agent - Cheap, fast routing decisions
    # Uses GPT-4o-mini for cost efficiency (~$0.15/1M tokens)
    supervisor_model: str = "gpt-4o-mini"
    supervisor_provider: str = "openai"  # openai, mistral
    supervisor_temperature: float = 0.1

    # Document Agent - Mistral for document intelligence
    # Best synergy with Mistral OCR 3 tools
    document_agent_model: str = "mistral-large-latest"
    document_agent_provider: str = "mistral"  # mistral, openai
    document_agent_temperature: float = 0.1

    # Video/Robotics Agent - Low-latency vision for real-time
    # Groq's Llama 3.2 Vision: ~50ms latency, 2.6x faster than OpenAI
    video_agent_model: str = "llama-3.2-11b-vision-preview"
    video_agent_provider: str = "groq"  # groq, openai
    video_agent_temperature: float = 0.3

    # ============================================
    # FASTAPI / API SETTINGS
    # ============================================

    # Server Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4  # For production
    api_reload: bool = True  # For development (auto-reload on code changes)

    # API Features
    api_debug: bool = Field(default=False, description="Enable debug mode")
    api_docs_enabled: bool = True  # Enable Swagger docs at /docs

    # CORS Settings (Cross-Origin Resource Sharing)
    cors_origins: list[str] = ["*"]  # Allow all origins (restrict in production)
    cors_allow_credentials: bool = True

    # Rate Limiting (per minute)
    rate_limit_default: int = 60  # Requests per minute
    rate_limit_burst: int = 10  # Burst allowance

    # ============================================
    # VISION SETTINGS
    # ============================================

    max_image_size: int = 2048  # Max width/height for images
    max_file_size_mb: int = 50  # Max file size in MB (Mistral limit)
    supported_image_formats: list[str] = [
        "jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp"
    ]

    # ============================================
    # PROJECT PATHS
    # ============================================

    project_root: Path = Path(__file__).parent.parent
    test_dir: Path = project_root / "test_images"

    # ============================================
    # MEMORY / CHECKPOINTING
    # ============================================

    use_memory: bool = True
    checkpoint_dir: Path = project_root / "checkpoints"

    # ============================================
    # DEPLOYMENT SETTINGS
    # ============================================

    # Deployment mode: development, saas, on_premise
    deployment_mode: str = "development"

    # Multi-tenancy (for SaaS)
    enable_multi_tenant: bool = False

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),  # Use absolute path
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create necessary directories
        self.checkpoint_dir.mkdir(exist_ok=True)
        self.test_dir.mkdir(exist_ok=True)
    
    def validate_api_keys(self) -> dict[str, bool]:
        """Check which API keys are configured."""
        return {
            "openai": bool(self.OPENAI_API_KEY),
            "anthropic": bool(self.ANTHROPIC_API_KEY),
            "mistral": bool(self.MISTRAL_API_KEY) and self.MISTRAL_API_KEY != "your_mistral_api_key_here",
            "groq": bool(self.GROQ_API_KEY) and self.GROQ_API_KEY != "your_groq_api_key_here"
        }

    def get_available_models(self) -> list[str]:
        """Return list of available models based on configured API keys."""
        models = []
        if self.OPENAI_API_KEY:
            models.extend(["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"])
        if self.ANTHROPIC_API_KEY:
            models.extend(["claude-sonnet-4-20250514", "claude-sonnet-3-5-20241022"])
        if self.MISTRAL_API_KEY and self.MISTRAL_API_KEY != "your_mistral_api_key_here":
            models.extend(["mistral-large-latest", "mistral-ocr-2512"])
        if self.GROQ_API_KEY and self.GROQ_API_KEY != "your_groq_api_key_here":
            models.extend(["llama-3.2-11b-vision-preview", "llama-3.2-90b-vision-preview"])
        return models

    def get_available_services(self) -> dict[str, dict]:
        """Return available services based on configured API keys."""
        return {
            "vision_analysis": {
                "available": bool(self.OPENAI_API_KEY),
                "model": "gpt-4o",
                "provider": "OpenAI"
            },
            "document_ocr": {
                "available": bool(self.MISTRAL_API_KEY) and self.MISTRAL_API_KEY != "your_mistral_api_key_here",
                "model": "mistral-ocr-2512",
                "provider": "Mistral AI"
            },
            "robotics_vision": {
                "available": bool(self.GROQ_API_KEY) and self.GROQ_API_KEY != "your_groq_api_key_here",
                "model": "llama-3.2-11b-vision-preview",
                "provider": "Groq",
                "latency": "~50ms"
            },
            "text_generation": {
                "available": bool(self.OPENAI_API_KEY) or bool(self.ANTHROPIC_API_KEY),
                "providers": ["OpenAI" if self.OPENAI_API_KEY else None,
                             "Anthropic" if self.ANTHROPIC_API_KEY else None]
            }
        }


# Global settings instance
settings = Settings()


# Convenience functions
def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings


def check_setup() -> bool:
    """
    Check if the project is properly set up with API keys.
    Returns True if at least one API key is configured.
    """
    api_keys = settings.validate_api_keys()
    has_keys = any(api_keys.values())
    
    if not has_keys:
        print("WARNING: No API keys configured!")
        print("Please create a .env file with at least one of:")
        print("  - OPENAI_API_KEY=your_key_here")
        print("  - ANTHROPIC_API_KEY=your_key_here")
        return False

    print("API Keys configured:")
    for provider, configured in api_keys.items():
        status = "[OK]" if configured else "[--]"
        print(f" {status} {provider.upper()}")
    
    return True


if __name__ == "__main__":
    # Test the configuration
    print("=" * 60)
    print("VISION PLATFORM - Configuration Test")
    print("=" * 60)

    check_setup()

    print("\n" + "-" * 60)
    print("Available Models:")
    for model in settings.get_available_models():
        print(f"  - {model}")

    print("\n" + "-" * 60)
    print("Available Services:")
    services = settings.get_available_services()
    for service, info in services.items():
        status = "[OK]" if info.get("available") else "[--]"
        print(f"  {status} {service}: {info.get('provider', 'N/A')}")

    print("\n" + "-" * 60)
    print("API Configuration:")
    print(f"  Host: {settings.api_host}:{settings.api_port}")
    print(f"  Workers: {settings.api_workers}")
    print(f"  Debug: {settings.api_debug}")
    print(f"  Docs enabled: {settings.api_docs_enabled}")

    print("\n" + "-" * 60)
    print("Paths:")
    print(f"  Project root: {settings.project_root}")
    print(f"  Checkpoint dir: {settings.checkpoint_dir}")
    print("=" * 60)


    

