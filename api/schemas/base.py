"""
Base Schemas - Common Pydantic Models

These models are used across all endpoints for consistent responses.

=== PYDANTIC V2 FEATURES ===

Pydantic v2 (which we're using) has some key features:

1. ConfigDict instead of class Config:
    class MyModel(BaseModel):
        model_config = ConfigDict(str_strip_whitespace=True)

2. Field() for constraints:
    name: str = Field(..., min_length=1, max_length=100)

3. model_dump() instead of dict():
    data = my_model.model_dump()

4. Validators with @field_validator:
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email')
        return v

=== RESPONSE PATTERNS ===

Consistent response structure is important for:
1. Client developers know what to expect
2. Error handling becomes predictable
3. Documentation is clearer

Our pattern:
    {
        "success": true/false,
        "data": { ... } or null,
        "error": { ... } or null,
        "meta": { ... } optional metadata
    }
"""

from datetime import datetime
from typing import Optional, Any, Generic, TypeVar

from pydantic import BaseModel, Field, ConfigDict


# Generic type for response data
T = TypeVar('T')


class ErrorDetail(BaseModel):
    """
    Detailed error information.

    Example:
        {
            "code": 400,
            "message": "Validation Error",
            "detail": "file_base64 must be a valid base64 string",
            "path": "/api/v1/documents/ocr"
        }
    """
    code: int = Field(..., description="HTTP status code or custom error code")
    message: str = Field(..., description="Human-readable error message")
    detail: Optional[str] = Field(None, description="Additional error details")
    path: Optional[str] = Field(None, description="Request path that caused the error")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the error occurred"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": 400,
                "message": "Validation Error",
                "detail": "file_base64 is required",
                "path": "/api/v1/documents/ocr"
            }
        }
    )


class ErrorResponse(BaseModel):
    """
    Standard error response format.

    All API errors return this format for consistency.
    """
    success: bool = Field(False, description="Always false for errors")
    error: ErrorDetail = Field(..., description="Error details")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error": {
                    "code": 404,
                    "message": "Document not found",
                    "detail": "No document with ID 'abc123' exists"
                }
            }
        }
    )


class MetaInfo(BaseModel):
    """
    Metadata about the response.

    Useful for pagination, timing, debugging.
    """
    request_id: Optional[str] = Field(None, description="Unique request identifier")
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp"
    )
    version: str = Field("1.0.0", description="API version")


class APIResponse(BaseModel):
    """
    Standard successful response format.

    All successful API responses use this format.

    Example:
        {
            "success": true,
            "data": {
                "markdown": "# Document Title...",
                "page_count": 3
            },
            "meta": {
                "processing_time_ms": 1523,
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
    """
    success: bool = Field(True, description="Whether the request succeeded")
    data: Optional[Any] = Field(None, description="Response data (shape varies by endpoint)")
    meta: Optional[MetaInfo] = Field(None, description="Response metadata")
    message: Optional[str] = Field(None, description="Optional success message")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "data": {"result": "example data"},
                "meta": {
                    "processing_time_ms": 150,
                    "timestamp": "2024-01-15T10:30:00Z"
                }
            }
        }
    )


class HealthStatus(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Health status: healthy, degraded, unhealthy")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    checks: Optional[dict] = Field(None, description="Individual service checks")


class PaginationParams(BaseModel):
    """
    Pagination parameters for list endpoints.

    Usage:
        @router.get("/documents")
        async def list_documents(pagination: PaginationParams = Depends()):
            ...
    """
    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")

    @property
    def offset(self) -> int:
        """Calculate the offset for database queries."""
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel):
    """
    Paginated list response.

    Example:
        {
            "success": true,
            "data": [...],
            "pagination": {
                "page": 1,
                "page_size": 20,
                "total_items": 100,
                "total_pages": 5
            }
        }
    """
    success: bool = True
    data: list = Field(default_factory=list)
    pagination: dict = Field(
        ...,
        description="Pagination info",
        json_schema_extra={
            "example": {
                "page": 1,
                "page_size": 20,
                "total_items": 100,
                "total_pages": 5,
                "has_next": True,
                "has_prev": False
            }
        }
    )
