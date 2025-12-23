"""
Document Processing Schemas

Pydantic models for document processing endpoints.

=== REQUEST VALIDATION ===

When a client sends a request:
1. FastAPI deserializes JSON to Python dict
2. Pydantic validates against the model
3. If invalid: 422 Unprocessable Entity with details
4. If valid: Your endpoint receives a typed object

Example:
    # Client sends:
    POST /api/v1/documents/ocr
    {"file_base64": "iVBORw0KGgo..."}

    # Your endpoint receives:
    async def ocr(request: DocumentRequest):
        # request.file_base64 is guaranteed to be a string
        # Validation already happened!

=== FIELD CONSTRAINTS ===

Pydantic supports many constraints:
- min_length, max_length for strings
- gt, ge, lt, le for numbers
- pattern for regex matching
- Custom validators for complex logic
"""

from enum import Enum
from typing import Optional, List, Any

from pydantic import BaseModel, Field, field_validator, ConfigDict


class DocumentType(str, Enum):
    """
    Supported document types for classification.

    Using Enum ensures only valid values are accepted.
    In Swagger, this becomes a dropdown!
    """
    INVOICE = "invoice"
    RECEIPT = "receipt"
    CONTRACT = "contract"
    FORM = "form"
    ID_DOCUMENT = "id_document"
    REPORT = "report"
    LETTER = "letter"
    OTHER = "other"


class DocumentRequest(BaseModel):
    """
    Request model for document processing endpoints.

    Clients can provide a document in multiple ways:
    1. file_base64: Base64 encoded file content
    2. file_url: URL to download the file from
    3. file_path: Path on server (for on-premise deployments)

    At least one of these must be provided.
    """
    # Document source (one required)
    file_base64: Optional[str] = Field(
        None,
        description="Base64 encoded document (image or PDF)",
        min_length=10,  # Minimum viable base64
    )
    file_url: Optional[str] = Field(
        None,
        description="URL to download the document from",
        pattern=r"^https?://.*",  # Must start with http:// or https://
    )
    file_path: Optional[str] = Field(
        None,
        description="Server file path (on-premise only)"
    )

    # Processing options
    document_type_hint: Optional[DocumentType] = Field(
        None,
        description="Hint about document type for better extraction"
    )
    extract_tables: bool = Field(
        True,
        description="Whether to extract tables from the document"
    )
    extract_structured: bool = Field(
        True,
        description="Whether to extract structured key-value data"
    )
    pages: Optional[str] = Field(
        None,
        description="Page numbers to process (e.g., '1,2,5' or '1-5')",
        pattern=r"^[\d,\-\s]+$"
    )

    # Validation: At least one source must be provided
    @field_validator('file_path', mode='after')
    @classmethod
    def validate_source_provided(cls, v, info):
        """Ensure at least one document source is provided."""
        # This runs after all fields are set
        # Access other fields via info.data
        values = info.data
        if not v and not values.get('file_base64') and not values.get('file_url'):
            raise ValueError(
                'At least one of file_base64, file_url, or file_path must be provided'
            )
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "file_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
                "extract_tables": True,
                "extract_structured": True,
                "document_type_hint": "invoice"
            }
        }
    )


class OCRResult(BaseModel):
    """
    Result from OCR processing.

    Contains the extracted text and metadata.
    """
    success: bool = Field(..., description="Whether OCR succeeded")
    markdown: str = Field(
        ...,
        description="Extracted text in markdown format"
    )
    page_count: int = Field(
        ...,
        ge=0,
        description="Number of pages processed"
    )
    has_tables: bool = Field(
        False,
        description="Whether tables were detected"
    )
    has_images: bool = Field(
        False,
        description="Whether embedded images were detected"
    )
    confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="OCR confidence score (0-1)"
    )
    model: str = Field(
        "mistral-ocr-2512",
        description="Model used for OCR"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "markdown": "# Invoice\\n\\nInvoice #: 12345\\nDate: 2024-01-15\\n\\n| Item | Price |\\n|------|-------|\\n| Widget | $10.00 |",
                "page_count": 1,
                "has_tables": True,
                "has_images": False,
                "confidence": 0.95,
                "model": "mistral-ocr-2512"
            }
        }
    )


class TableData(BaseModel):
    """
    Extracted table data.

    Tables from Mistral OCR 3 are returned in HTML format
    with proper structure (colspan/rowspan for merged cells).
    """
    html: str = Field(..., description="Table in HTML format")
    row_count: int = Field(..., ge=0, description="Number of rows")
    col_count: int = Field(..., ge=0, description="Number of columns")
    has_header: bool = Field(False, description="Whether table has a header row")
    position: Optional[int] = Field(None, description="Table position in document (1-indexed)")


class TableExtractionResult(BaseModel):
    """
    Result from table extraction.
    """
    success: bool = Field(..., description="Whether extraction succeeded")
    tables: List[TableData] = Field(
        default_factory=list,
        description="Extracted tables"
    )
    table_count: int = Field(..., ge=0, description="Number of tables found")
    raw_markdown: Optional[str] = Field(
        None,
        description="Full document markdown"
    )


class StructuredData(BaseModel):
    """
    Structured data extracted from document.

    Key-value pairs identified in the document.
    """
    document_type: Optional[DocumentType] = Field(
        None,
        description="Detected document type"
    )
    fields: dict = Field(
        default_factory=dict,
        description="Extracted key-value pairs"
    )
    confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Extraction confidence"
    )


class DocumentResponse(BaseModel):
    """
    Complete document processing response.

    Combines OCR, table extraction, and structured data.
    """
    success: bool = Field(..., description="Whether processing succeeded")

    # Core results
    ocr: Optional[OCRResult] = Field(None, description="OCR results")
    tables: Optional[List[TableData]] = Field(None, description="Extracted tables")
    structured_data: Optional[StructuredData] = Field(
        None,
        description="Structured key-value extraction"
    )

    # Metadata
    processing_time_ms: int = Field(
        ...,
        ge=0,
        description="Total processing time in milliseconds"
    )
    file_info: Optional[dict] = Field(
        None,
        description="Information about the processed file"
    )
    warnings: Optional[List[str]] = Field(
        None,
        description="Any warnings during processing"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "ocr": {
                    "success": True,
                    "markdown": "# Invoice 12345...",
                    "page_count": 1,
                    "has_tables": True
                },
                "tables": [
                    {
                        "html": "<table>...</table>",
                        "row_count": 5,
                        "col_count": 3,
                        "has_header": True
                    }
                ],
                "structured_data": {
                    "document_type": "invoice",
                    "fields": {
                        "invoice_number": "12345",
                        "date": "2024-01-15",
                        "total": "$150.00"
                    }
                },
                "processing_time_ms": 2500
            }
        }
    )


class BatchDocumentRequest(BaseModel):
    """
    Request for batch document processing.

    Process multiple documents in one request.
    """
    documents: List[DocumentRequest] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of documents to process"
    )
    use_batch_api: bool = Field(
        True,
        description="Use Mistral batch API (50% discount, async)"
    )
    webhook_url: Optional[str] = Field(
        None,
        description="URL to call when processing completes",
        pattern=r"^https?://.*"
    )


class BatchJobStatus(BaseModel):
    """
    Status of a batch processing job.
    """
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(
        ...,
        description="Job status",
        pattern="^(pending|processing|completed|failed)$"
    )
    total_documents: int = Field(..., ge=0)
    processed_documents: int = Field(..., ge=0)
    failed_documents: int = Field(default=0, ge=0)
    created_at: str = Field(..., description="ISO 8601 timestamp")
    completed_at: Optional[str] = Field(None, description="ISO 8601 timestamp")
    results_url: Optional[str] = Field(
        None,
        description="URL to download results when complete"
    )
