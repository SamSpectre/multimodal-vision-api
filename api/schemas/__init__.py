"""
API Schemas Package - Pydantic Models

This package contains Pydantic models that define:
1. Request shapes (what clients send to us)
2. Response shapes (what we send back)
3. Common models (shared across endpoints)

=== PYDANTIC EXPLAINED ===

What is Pydantic?
    A data validation library that uses Python type hints.
    It converts raw data (like JSON) into validated Python objects.

Example:
    class User(BaseModel):
        name: str
        age: int

    # This works:
    user = User(name="Alice", age=30)

    # This raises ValidationError:
    user = User(name="Alice", age="not a number")

=== WHY PYDANTIC FOR APIs? ===

1. Automatic Validation
   - Type checking
   - Required vs optional fields
   - Custom validators

2. Automatic Documentation
   - FastAPI reads your models
   - Generates Swagger/OpenAPI docs
   - Shows exact field types and examples

3. Serialization
   - .model_dump() → Python dict
   - .model_dump_json() → JSON string
   - Automatic conversion from JSON input

=== SCHEMA ORGANIZATION ===

- base.py: Common models used everywhere
- documents.py: Document-specific models
- faces.py: Face analysis models (coming soon)
- video.py: Video processing models (coming soon)
- jobs.py: Async job tracking models (coming soon)
"""

from api.schemas.base import APIResponse, ErrorResponse, ErrorDetail
from api.schemas.documents import (
    DocumentRequest,
    DocumentResponse,
    OCRResult,
    TableExtractionResult,
)

__all__ = [
    # Base
    "APIResponse",
    "ErrorResponse",
    "ErrorDetail",
    # Documents
    "DocumentRequest",
    "DocumentResponse",
    "OCRResult",
    "TableExtractionResult",
]
