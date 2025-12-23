"""
API Package - FastAPI Application

This package contains the REST API layer for the Vision Platform.

=== API ARCHITECTURE ===

Structure:
    api/
    ├── main.py          # FastAPI app entry point, configuration
    ├── dependencies.py  # Dependency injection (shared resources)
    ├── routers/         # Endpoint definitions (grouped by feature)
    │   ├── documents.py # /api/v1/documents/* endpoints
    │   ├── faces.py     # /api/v1/faces/* endpoints
    │   ├── video.py     # /api/v1/video/* endpoints
    │   └── health.py    # /api/v1/health/* endpoints
    ├── schemas/         # Pydantic models (request/response shapes)
    │   ├── base.py      # Common models (APIResponse, Error)
    │   ├── documents.py # Document-specific models
    │   └── ...
    └── middleware/      # Request/response processing
        ├── auth.py      # Authentication
        ├── logging.py   # Request logging
        └── ...

=== KEY CONCEPTS ===

1. Routers - Group related endpoints together
2. Schemas - Define the shape of request/response data
3. Dependencies - Inject shared resources (database, clients)
4. Middleware - Process all requests (logging, auth, etc.)

=== RUNNING THE API ===

Development:
    uvicorn api.main:app --reload

Production:
    uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
"""

from api.main import app

__all__ = ["app"]
