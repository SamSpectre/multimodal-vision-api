"""
FastAPI Application Entry Point

This is the main file that creates and configures the FastAPI application.

=== FASTAPI EXPLAINED ===

What is FastAPI?
    A modern, high-performance web framework for building APIs with Python.
    Key features:
    - Type hints become automatic validation
    - Automatic API documentation (Swagger UI)
    - Async support for high concurrency
    - Built on Starlette (async) and Pydantic (validation)

How it compares to Flask:
    Flask: Simple, synchronous, minimal
    FastAPI: Type-safe, async, automatic docs, validation

=== THIS FILE'S RESPONSIBILITIES ===

1. Create the FastAPI app instance
2. Configure middleware (logging, CORS, error handling)
3. Include routers (endpoints)
4. Define global exception handlers
5. Add startup/shutdown events

=== RUNNING THE APP ===

Development (with auto-reload):
    uvicorn api.main:app --reload --port 8000

Production:
    uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4

Then visit:
    http://localhost:8000/docs - Swagger UI (interactive docs)
    http://localhost:8000/redoc - ReDoc (alternative docs)
"""

import os
import time
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import settings FIRST to ensure .env is loaded
from config.settings import settings

# Import routers
from api.routers import health, documents, agent

# Import auth router
from src.auth.router import router as auth_router
from src.auth.dependencies import require_auth, get_current_user


# === LIFESPAN EVENTS ===
# These run when the app starts up and shuts down

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events.

    This is the modern way (FastAPI 0.93+) to handle:
    - Startup: Initialize resources (database connections, ML models)
    - Shutdown: Clean up resources (close connections, save state)

    The 'yield' separates startup from shutdown:
    - Code before yield: runs on startup
    - Code after yield: runs on shutdown
    """
    # === STARTUP ===
    print("=" * 60)
    print("VISION PLATFORM API - STARTING UP")
    print("=" * 60)

    # Check if required API keys are configured using settings
    api_keys = settings.validate_api_keys()

    print(f"OpenAI API Key: {'Configured' if api_keys['openai'] else 'NOT SET'}")
    print(f"Mistral API Key: {'Configured' if api_keys['mistral'] else 'NOT SET'}")
    print(f"Anthropic API Key: {'Configured' if api_keys['anthropic'] else 'NOT SET'}")

    # Validate at least one vision provider is available
    if not api_keys['openai']:
        print("WARNING: OPENAI_API_KEY not set")

    # Show available services
    print("-" * 60)
    services = settings.get_available_services()
    for name, info in services.items():
        status = "OK" if info.get('available') else "--"
        print(f"  [{status}] {name}")

    # Show authentication status
    print("-" * 60)
    print("SECURITY:")
    auth_status = "ENABLED" if settings.AUTH_ENABLED else "DISABLED (dev mode)"
    print(f"  Authentication: {auth_status}")
    print(f"  JWT Expiry: {settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutes")
    print(f"  API Key: {'Configured' if settings.API_KEY else 'Not set'}")
    print(f"  Admin User: {settings.ADMIN_USERNAME}")

    if settings.SECRET_KEY == "CHANGE_ME_IN_PRODUCTION_USE_OPENSSL_RAND_HEX_32":
        print("  ⚠️  WARNING: Using default SECRET_KEY! Generate a secure one:")
        print("     openssl rand -hex 32")

    print("=" * 60)
    print("API is ready! Visit http://localhost:8000/docs for Swagger UI")
    print("=" * 60)

    yield  # App runs here

    # === SHUTDOWN ===
    print("\n" + "=" * 60)
    print("VISION PLATFORM API - SHUTTING DOWN")
    print("=" * 60)


# === CREATE THE FASTAPI APP ===

app = FastAPI(
    # Basic metadata (appears in docs)
    title="Vision Platform API",
    description="""
    Enterprise Multimodal Vision Platform API

    ## Features

    * **Document Processing** - OCR, classification, data extraction using Mistral OCR 3
    * **Face Analysis** - Detection, emotions, attributes (coming soon)
    * **Video Processing** - Object detection, scene analysis (coming soon)

    ## Authentication

    API key required in header: `X-API-Key: your_api_key`

    ## Rate Limits

    - Standard: 60 requests/minute
    - Enterprise: Custom limits
    """,
    version="1.0.0",

    # OpenAPI settings
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc

    # Lifespan handler
    lifespan=lifespan,

    # Contact info
    contact={
        "name": "Vision Platform Support",
        "email": "support@example.com",
    },

    # License
    license_info={
        "name": "MIT",
    },
)


# === MIDDLEWARE ===

# CORS (Cross-Origin Resource Sharing)
# This allows web browsers to call your API from different domains
app.add_middleware(
    CORSMiddleware,
    # In production, replace with specific origins:
    # allow_origins=["https://yourfrontend.com"]
    allow_origins=["*"],  # Allow all origins (development only!)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next: Callable):
    """
    Middleware to add processing time to response headers.

    Middleware wraps around your request handlers:
    1. Code before 'call_next' runs BEFORE the request handler
    2. 'call_next' calls the actual request handler
    3. Code after 'call_next' runs AFTER the response is ready

    This is useful for:
    - Logging
    - Authentication
    - Request modification
    - Response modification
    """
    start_time = time.time()

    # Call the actual endpoint
    response = await call_next(request)

    # Calculate processing time
    process_time = time.time() - start_time

    # Add custom header to response
    response.headers["X-Process-Time"] = f"{process_time:.4f}"

    return response


# === EXCEPTION HANDLERS ===

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Custom handler for HTTP exceptions.

    This provides consistent error responses across the API.
    All errors follow the same format:
    {
        "success": false,
        "error": {
            "code": 404,
            "message": "Not Found",
            "detail": "The requested resource was not found"
        }
    }
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "path": str(request.url.path),
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Catch-all exception handler for unexpected errors.

    IMPORTANT: In production, don't expose internal error details!
    Log the full error internally, but return a generic message.
    """
    # In production, you'd log this:
    # logger.error(f"Unexpected error: {exc}", exc_info=True)
    print(f"[ERROR] Unexpected error on {request.url.path}: {exc}")

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": 500,
                "message": "Internal Server Error",
                "path": str(request.url.path),
                # Don't include exc details in production!
                "detail": str(exc) if os.getenv("DEBUG") else "An unexpected error occurred"
            }
        }
    )


# === INCLUDE ROUTERS ===
# Routers group related endpoints together

# Authentication endpoints (public)
app.include_router(
    auth_router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

# Health check endpoints (public)
app.include_router(
    health.router,
    prefix="/api/v1/health",
    tags=["Health"]  # Groups in Swagger UI
)

# Document processing endpoints (protected)
app.include_router(
    documents.router,
    prefix="/api/v1/documents",
    tags=["Documents"],
    dependencies=[],  # Auth is handled per-endpoint in router
)

# Document Intelligence Agent endpoints (protected)
app.include_router(
    agent.router,
    prefix="/api/v1/agent",
    tags=["Agent"],
    dependencies=[],  # Auth is handled per-endpoint in router
)


# === ROOT ENDPOINT ===

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - API information.

    Returns basic info about the API.
    Visit /docs for interactive documentation.
    """
    return {
        "name": "Vision Platform API",
        "version": "1.0.0",
        "status": "running",
        "documentation": "/docs",
        "health": "/api/v1/health"
    }


# === MAIN ENTRY POINT ===

if __name__ == "__main__":
    """
    Run with: python api/main.py

    For development, prefer:
    uvicorn api.main:app --reload
    """
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )
