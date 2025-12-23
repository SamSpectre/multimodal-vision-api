"""
API Routers Package

Routers group related endpoints together.
Each router handles a specific domain/feature.

=== WHAT IS A ROUTER? ===

A router is like a mini-application within FastAPI.
It groups related endpoints and can have:
- Its own prefix (e.g., /api/v1/documents)
- Its own tags (for Swagger grouping)
- Its own dependencies

Example:
    # In documents.py
    router = APIRouter()

    @router.post("/ocr")
    async def ocr_endpoint():
        ...

    # In main.py
    app.include_router(documents.router, prefix="/api/v1/documents")

    # Result: POST /api/v1/documents/ocr

=== AVAILABLE ROUTERS ===

- health: Health check endpoints (/api/v1/health/*)
- documents: Document processing (/api/v1/documents/*)
- agent: Document Intelligence Agent (/api/v1/agent/*)
- video: Video processing (/api/v1/video/*) - coming soon
"""

from api.routers import health
from api.routers import documents
from api.routers import agent

__all__ = ["health", "documents", "agent"]
