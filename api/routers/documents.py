"""
Document Processing Router

API endpoints for document OCR, classification, and data extraction.
Powered by Mistral OCR 3.

=== ENDPOINT DESIGN PATTERNS ===

1. Single Responsibility
   Each endpoint does ONE thing well.
   - /ocr → Extract text
   - /classify → Classify document type
   - /tables → Extract tables
   - /analyze → Full pipeline

2. Consistent Response Format
   All endpoints return:
   - success: bool
   - data: {...} or null
   - error: {...} or null

3. Proper HTTP Status Codes
   - 200: Success
   - 400: Bad request (validation error)
   - 422: Unprocessable entity (Pydantic validation)
   - 500: Server error

4. Clear Documentation
   - Docstrings become Swagger descriptions
   - Examples help clients understand usage

=== FASTAPI FEATURES USED ===

1. Path Operations (@router.post, @router.get)
2. Request Models (Pydantic automatic validation)
3. Response Models (Pydantic serialization)
4. Dependency Injection (shared resources)
5. Background Tasks (async processing)
"""

import json
import time
import base64
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse

# Import our schemas
from api.schemas.documents import (
    DocumentRequest,
    DocumentResponse,
    OCRResult,
    TableExtractionResult,
    TableData,
    StructuredData,
    DocumentType,
)

# Import our tools
from src.tools.mistral_ocr_tools import (
    process_document_ocr,
    extract_tables_from_document,
    process_pdf_document,
    analyze_document_content,
    check_mistral_connection,
)

# Import client check
from src.clients.mistral_client import is_mistral_available


# Create the router
router = APIRouter()


# === HELPER FUNCTIONS ===

def decode_base64_to_temp_file(base64_string: str, suffix: str = ".jpg") -> str:
    """
    Decode base64 string and save to a temporary file.

    FastAPI tools work with file paths, so we need to save
    base64 data to a temp file first.

    Args:
        base64_string: Base64 encoded file content
        suffix: File extension to use

    Returns:
        Path to the temporary file
    """
    # Decode base64 to bytes
    file_bytes = base64.b64decode(base64_string)

    # Create temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
        f.write(file_bytes)
        return f.name


def cleanup_temp_file(file_path: str):
    """Remove a temporary file (for background cleanup)."""
    try:
        Path(file_path).unlink(missing_ok=True)
    except Exception:
        pass  # Best effort cleanup


def detect_file_type(base64_string: str) -> str:
    """
    Detect file type from base64 magic bytes.

    Different file types have different starting bytes:
    - JPEG: FFD8FF
    - PNG: 89504E47
    - PDF: 25504446
    """
    # Decode first few bytes
    try:
        header = base64.b64decode(base64_string[:100])

        if header[:3] == b'\xff\xd8\xff':
            return ".jpg"
        elif header[:8] == b'\x89PNG\r\n\x1a\n':
            return ".png"
        elif header[:4] == b'%PDF':
            return ".pdf"
        elif header[:4] == b'GIF8':
            return ".gif"
        else:
            return ".jpg"  # Default
    except Exception:
        return ".jpg"


# === ENDPOINTS ===

@router.post("/ocr", response_model=None)
async def ocr_endpoint(
    request: DocumentRequest,
    background_tasks: BackgroundTasks
):
    """
    Extract text from a document using Mistral OCR 3.

    This endpoint:
    1. Accepts a document (base64, URL, or path)
    2. Processes it with Mistral OCR 3
    3. Returns markdown text with preserved structure

    **Features:**
    - Tables preserved in HTML format
    - Multi-page PDF support
    - Handwriting recognition
    - Multiple languages

    **Pricing:** $2 per 1,000 pages
    """
    start_time = time.time()
    temp_file = None

    try:
        # Check if Mistral is available
        if not is_mistral_available():
            raise HTTPException(
                status_code=503,
                detail="Mistral OCR service is not available. Check MISTRAL_API_KEY."
            )

        # Get the file to process
        if request.file_base64:
            # Decode and save to temp file
            suffix = detect_file_type(request.file_base64)
            temp_file = decode_base64_to_temp_file(request.file_base64, suffix)
            file_to_process = temp_file
        elif request.file_url:
            # TODO: Download from URL
            raise HTTPException(
                status_code=501,
                detail="URL processing not yet implemented. Use file_base64."
            )
        elif request.file_path:
            # Use server path directly
            if not Path(request.file_path).exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"File not found: {request.file_path}"
                )
            file_to_process = request.file_path
        else:
            raise HTTPException(
                status_code=400,
                detail="No document source provided"
            )

        # Call the OCR tool
        result_json = process_document_ocr.invoke(file_to_process)
        result = json.loads(result_json)

        # Schedule cleanup of temp file
        if temp_file:
            background_tasks.add_task(cleanup_temp_file, temp_file)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "OCR processing failed")
            )

        # Build response
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "markdown": result.get("markdown", ""),
                    "page_count": result.get("page_count", 1),
                    "has_tables": result.get("has_tables", False),
                    "model": "mistral-ocr-2512"
                },
                "meta": {
                    "processing_time_ms": processing_time_ms
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        # Cleanup on error
        if temp_file:
            cleanup_temp_file(temp_file)
        raise HTTPException(
            status_code=500,
            detail=f"OCR processing failed: {str(e)}"
        )


@router.post("/tables")
async def extract_tables_endpoint(
    request: DocumentRequest,
    background_tasks: BackgroundTasks
):
    """
    Extract tables from a document.

    Returns tables in HTML format with:
    - Row and column structure
    - Merged cells (colspan/rowspan)
    - Header detection

    Best for: Invoices, financial documents, forms with tabular data.
    """
    start_time = time.time()
    temp_file = None

    try:
        if not is_mistral_available():
            raise HTTPException(
                status_code=503,
                detail="Mistral OCR service is not available"
            )

        # Get file to process
        if request.file_base64:
            suffix = detect_file_type(request.file_base64)
            temp_file = decode_base64_to_temp_file(request.file_base64, suffix)
            file_to_process = temp_file
        elif request.file_path:
            file_to_process = request.file_path
        else:
            raise HTTPException(status_code=400, detail="No document provided")

        # Extract tables
        result_json = extract_tables_from_document.invoke(file_to_process)
        result = json.loads(result_json)

        if temp_file:
            background_tasks.add_task(cleanup_temp_file, temp_file)

        processing_time_ms = int((time.time() - start_time) * 1000)

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Table extraction failed")
            )

        # Build table data
        tables = []
        for i, html in enumerate(result.get("tables", [])):
            tables.append({
                "html": html,
                "position": i + 1,
                "row_count": html.count("<tr"),
                "col_count": max(row.count("<td") + row.count("<th") for row in html.split("<tr")) if "<tr" in html else 0
            })

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "tables": tables,
                    "table_count": len(tables)
                },
                "meta": {
                    "processing_time_ms": processing_time_ms
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        if temp_file:
            cleanup_temp_file(temp_file)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/classify")
async def classify_document_endpoint(
    request: DocumentRequest,
    background_tasks: BackgroundTasks
):
    """
    Classify a document's type.

    Uses OCR + heuristic analysis to determine document type:
    - invoice
    - receipt
    - contract
    - form
    - report
    - other

    Returns the detected type with confidence.
    """
    start_time = time.time()
    temp_file = None

    try:
        if not is_mistral_available():
            raise HTTPException(
                status_code=503,
                detail="Mistral OCR service is not available"
            )

        # Get file
        if request.file_base64:
            suffix = detect_file_type(request.file_base64)
            temp_file = decode_base64_to_temp_file(request.file_base64, suffix)
            file_to_process = temp_file
        elif request.file_path:
            file_to_process = request.file_path
        else:
            raise HTTPException(status_code=400, detail="No document provided")

        # Analyze content
        result_json = analyze_document_content.invoke(file_to_process)
        result = json.loads(result_json)

        if temp_file:
            background_tasks.add_task(cleanup_temp_file, temp_file)

        processing_time_ms = int((time.time() - start_time) * 1000)

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Classification failed")
            )

        analysis = result.get("analysis", {})

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "document_type": analysis.get("content_type_hint", "unknown"),
                    "confidence": 0.8 if analysis.get("content_type_hint") != "unknown" else 0.3,
                    "analysis": {
                        "word_count": analysis.get("word_count", 0),
                        "has_tables": analysis.get("has_tables", False),
                        "page_count": analysis.get("page_count", 1)
                    }
                },
                "meta": {
                    "processing_time_ms": processing_time_ms,
                    "method": "heuristic"
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        if temp_file:
            cleanup_temp_file(temp_file)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze_document_endpoint(
    request: DocumentRequest,
    background_tasks: BackgroundTasks
):
    """
    Complete document analysis pipeline.

    Performs:
    1. OCR text extraction (Mistral OCR 3)
    2. Table extraction
    3. Document classification
    4. Structured data extraction (if requested)

    This is the most comprehensive endpoint - use when you need everything.
    """
    start_time = time.time()
    temp_file = None

    try:
        if not is_mistral_available():
            raise HTTPException(
                status_code=503,
                detail="Mistral OCR service is not available"
            )

        # Get file
        if request.file_base64:
            suffix = detect_file_type(request.file_base64)
            temp_file = decode_base64_to_temp_file(request.file_base64, suffix)
            file_to_process = temp_file
        elif request.file_path:
            file_to_process = request.file_path
        else:
            raise HTTPException(status_code=400, detail="No document provided")

        # Run full analysis
        result_json = analyze_document_content.invoke(file_to_process)
        result = json.loads(result_json)

        if temp_file:
            background_tasks.add_task(cleanup_temp_file, temp_file)

        processing_time_ms = int((time.time() - start_time) * 1000)

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Analysis failed")
            )

        analysis = result.get("analysis", {})
        raw_text = result.get("raw_text", "")

        # Extract tables if requested
        tables = []
        if request.extract_tables and "<table" in raw_text.lower():
            import re
            table_pattern = r'<table.*?>.*?</table>'
            found_tables = re.findall(table_pattern, raw_text, re.DOTALL | re.IGNORECASE)
            tables = [{"html": t, "position": i+1} for i, t in enumerate(found_tables)]

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "ocr": {
                        "markdown": raw_text,
                        "page_count": analysis.get("page_count", 1),
                        "word_count": analysis.get("word_count", 0),
                        "has_tables": analysis.get("has_tables", False)
                    },
                    "classification": {
                        "document_type": analysis.get("content_type_hint", "unknown"),
                        "confidence": 0.8 if analysis.get("content_type_hint") != "unknown" else 0.3
                    },
                    "tables": tables if request.extract_tables else None,
                    "structured_data": None  # TODO: Implement with GPT-4o
                },
                "meta": {
                    "processing_time_ms": processing_time_ms,
                    "model": "mistral-ocr-2512"
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        if temp_file:
            cleanup_temp_file(temp_file)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pdf")
async def process_pdf_endpoint(
    request: DocumentRequest,
    background_tasks: BackgroundTasks
):
    """
    Process a multi-page PDF document.

    Returns page-by-page OCR results.

    Use the `pages` parameter to process specific pages:
    - "1,2,5" - Process pages 1, 2, and 5
    - "1-5" - Process pages 1 through 5 (coming soon)
    """
    start_time = time.time()
    temp_file = None

    try:
        if not is_mistral_available():
            raise HTTPException(
                status_code=503,
                detail="Mistral OCR service is not available"
            )

        # Get file
        if request.file_base64:
            temp_file = decode_base64_to_temp_file(request.file_base64, ".pdf")
            file_to_process = temp_file
        elif request.file_path:
            file_to_process = request.file_path
        else:
            raise HTTPException(status_code=400, detail="No PDF provided")

        # Process PDF
        result_json = process_pdf_document.invoke(file_to_process)
        result = json.loads(result_json)

        if temp_file:
            background_tasks.add_task(cleanup_temp_file, temp_file)

        processing_time_ms = int((time.time() - start_time) * 1000)

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "PDF processing failed")
            )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "pages": result.get("pages", []),
                    "total_pages": result.get("total_pages", 0),
                    "pages_processed": result.get("pages_processed", [])
                },
                "meta": {
                    "processing_time_ms": processing_time_ms,
                    "model": "mistral-ocr-2512"
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        if temp_file:
            cleanup_temp_file(temp_file)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_service_status():
    """
    Check document processing service status.

    Returns availability of OCR services.
    """
    status = check_mistral_connection()

    return {
        "service": "Document Processing",
        "status": "available" if status["available"] else "unavailable",
        "providers": {
            "mistral_ocr": {
                "available": status["available"],
                "model": status["model"]
            }
        }
    }


# === FILE UPLOAD ENDPOINT ===
# Alternative to base64 - direct file upload

@router.post("/upload")
async def upload_and_process(
    file: UploadFile = File(..., description="Document file to process"),
    extract_tables: bool = Form(True),
    background_tasks: BackgroundTasks = None
):
    """
    Upload and process a document file.

    Alternative to base64 encoding - just upload the file directly.

    Accepts: JPEG, PNG, PDF, GIF, BMP, TIFF, WebP
    """
    start_time = time.time()

    try:
        if not is_mistral_available():
            raise HTTPException(
                status_code=503,
                detail="Mistral OCR service is not available"
            )

        # Validate file type
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.pdf', '.gif', '.bmp', '.tiff', '.webp'}
        suffix = Path(file.filename).suffix.lower()

        if suffix not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {suffix}. Allowed: {allowed_extensions}"
            )

        # Save uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
            content = await file.read()
            f.write(content)
            temp_file = f.name

        # Process
        result_json = process_document_ocr.invoke(temp_file)
        result = json.loads(result_json)

        # Cleanup
        background_tasks.add_task(cleanup_temp_file, temp_file)

        processing_time_ms = int((time.time() - start_time) * 1000)

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Processing failed")
            )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "markdown": result.get("markdown", ""),
                    "page_count": result.get("page_count", 1),
                    "has_tables": result.get("has_tables", False),
                    "filename": file.filename
                },
                "meta": {
                    "processing_time_ms": processing_time_ms
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
