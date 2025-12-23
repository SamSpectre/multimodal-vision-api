"""
Mistral OCR 3 Tools for Document Processing

This module provides LangChain tools that wrap the Mistral OCR 3 API.

=== LANGCHAIN TOOLS EXPLAINED ===

What is a Tool?
  A tool is a function that an AI agent can call to perform actions.
  Think of it like giving the AI "superpowers" - abilities beyond just text generation.

How @tool decorator works:
  1. It reads your function's docstring for the tool description
  2. It reads type hints for parameter types
  3. It wraps your function so agents can call it
  4. The AI uses the description to decide WHEN to use the tool

Why is the docstring so important?
  The AI READS the docstring to understand what the tool does!
  Write it like you're explaining to a coworker:
  - What does this tool do?
  - When should it be used?
  - What are the inputs/outputs?

=== MISTRAL OCR 3 EXPLAINED ===

What is Mistral OCR 3?
  - OCR = Optical Character Recognition
  - Converts images of text into actual text
  - Mistral's version is the best-in-class (better than Google, Azure, GPT-4o)
  - Handles: forms, invoices, handwriting, tables, scanned documents

How it works:
  1. You send an image (base64 or URL)
  2. Mistral processes it with their vision model
  3. Returns markdown text with structure preserved

Pricing:
  - Standard: $2 per 1,000 pages
  - Batch API: $1 per 1,000 pages (50% discount!)
"""

import os
import base64
import json
from pathlib import Path
from typing import Optional, List, Union
from langchain_core.tools import tool

# Import our singleton client
from src.clients.mistral_client import get_mistral_client, is_mistral_available


# === HELPER FUNCTIONS ===

def encode_image_to_base64(image_path: str) -> str:
    """
    Encode an image file to base64 string.

    Base64 encoding converts binary data (like images) into text.
    This is necessary because APIs typically work with text, not binary.

    How base64 works:
      - Takes 3 bytes of binary data
      - Converts to 4 ASCII characters
      - Results in ~33% larger size but text-compatible

    Args:
        image_path: Path to the image file

    Returns:
        Base64 encoded string of the image
    """
    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    with open(path, "rb") as f:  # "rb" = read binary
        return base64.b64encode(f.read()).decode("utf-8")


def get_mime_type(file_path: str) -> str:
    """
    Get the MIME type based on file extension.

    MIME types tell the server what kind of data you're sending.
    Example: image/jpeg tells the server "this is a JPEG image"

    Common MIME types:
      - image/jpeg - JPEG images
      - image/png - PNG images
      - application/pdf - PDF documents
    """
    extension = Path(file_path).suffix.lower()

    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
        ".tiff": "image/tiff",
        ".tif": "image/tiff",
        ".webp": "image/webp",
        ".pdf": "application/pdf",
    }

    return mime_types.get(extension, "application/octet-stream")


# === MAIN OCR TOOLS ===

@tool
def process_document_ocr(image_path: str) -> str:
    """
    Extract text from a document image using Mistral OCR 3.

    This is the PRIMARY tool for document text extraction. Use it when you need to:
    - Extract text from scanned documents
    - Process receipts or invoices
    - Read text from images
    - Digitize paper documents

    The output is in Markdown format with:
    - Preserved text structure
    - Tables in HTML format (with colspan/rowspan)
    - Embedded images extracted

    Args:
        image_path: Path to the image file (jpg, png, pdf, etc.)

    Returns:
        JSON string with:
        - markdown: The extracted text in markdown format
        - page_count: Number of pages processed
        - has_tables: Whether tables were detected
        - processing_info: Usage statistics

    Example:
        >>> result = process_document_ocr("/path/to/receipt.jpg")
        >>> data = json.loads(result)
        >>> print(data["markdown"])
    """
    try:
        # Validate the file exists
        if not Path(image_path).exists():
            return json.dumps({
                "error": f"File not found: {image_path}",
                "success": False
            })

        # Get the Mistral client (singleton)
        client = get_mistral_client()

        # Encode the image to base64
        image_base64 = encode_image_to_base64(image_path)
        mime_type = get_mime_type(image_path)

        # Create the data URL format
        # Format: data:{mime_type};base64,{base64_data}
        data_url = f"data:{mime_type};base64,{image_base64}"

        # Call Mistral OCR 3 API
        # Model: "mistral-ocr-2512" is the latest OCR 3 model
        result = client.ocr.process(
            model="mistral-ocr-2512",
            document={
                "type": "image_url",
                "image_url": {"url": data_url}
            }
        )

        # Process the response
        # Mistral returns pages[] with markdown content
        pages = result.pages if hasattr(result, 'pages') else []

        # Combine all pages into one markdown document
        full_markdown = ""
        has_tables = False

        for i, page in enumerate(pages):
            if hasattr(page, 'markdown'):
                full_markdown += page.markdown
                # Check for tables (HTML table tags)
                if "<table" in page.markdown.lower():
                    has_tables = True
                if i < len(pages) - 1:
                    full_markdown += "\n\n---\n\n"  # Page separator

        return json.dumps({
            "success": True,
            "markdown": full_markdown,
            "page_count": len(pages),
            "has_tables": has_tables,
            "file_processed": str(image_path),
            "model": "mistral-ocr-2512"
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "error": str(e),
            "success": False,
            "file_attempted": str(image_path)
        })


@tool
def extract_tables_from_document(image_path: str) -> str:
    """
    Extract tables from a document image using Mistral OCR 3.

    Use this tool specifically when you need to:
    - Extract tabular data from images
    - Process spreadsheet-like content in documents
    - Get structured table data from invoices or forms

    Tables are returned in HTML format with proper structure
    (colspan, rowspan preserved for merged cells).

    Args:
        image_path: Path to the image file containing tables

    Returns:
        JSON string with:
        - tables: List of tables found (in HTML format)
        - table_count: Number of tables extracted
        - raw_markdown: Full document markdown

    Example:
        >>> result = extract_tables_from_document("/path/to/invoice.jpg")
        >>> data = json.loads(result)
        >>> for table in data["tables"]:
        ...     print(table)
    """
    try:
        # First, get the full OCR result
        ocr_result = process_document_ocr.invoke(image_path)
        ocr_data = json.loads(ocr_result)

        if not ocr_data.get("success"):
            return json.dumps({
                "error": ocr_data.get("error", "OCR failed"),
                "success": False
            })

        markdown = ocr_data.get("markdown", "")

        # Extract tables from the markdown
        # Tables in Mistral OCR 3 output are in HTML format
        import re

        # Find all table blocks (from <table> to </table>)
        table_pattern = r'<table.*?>.*?</table>'
        tables = re.findall(table_pattern, markdown, re.DOTALL | re.IGNORECASE)

        return json.dumps({
            "success": True,
            "tables": tables,
            "table_count": len(tables),
            "raw_markdown": markdown,
            "file_processed": str(image_path)
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "error": str(e),
            "success": False
        })


@tool
def process_pdf_document(pdf_path: str, page_numbers: Optional[str] = None) -> str:
    """
    Process a multi-page PDF document using Mistral OCR 3.

    Use this tool for:
    - Multi-page PDF documents
    - When you need page-by-page results
    - Processing specific pages of a PDF

    Args:
        pdf_path: Path to the PDF file
        page_numbers: Optional comma-separated page numbers (e.g., "1,2,5")
                     If not provided, all pages are processed

    Returns:
        JSON string with:
        - pages: List of page results with markdown content
        - total_pages: Total pages in document
        - pages_processed: Which pages were processed

    Example:
        >>> result = process_pdf_document("/path/to/doc.pdf", "1,2,3")
        >>> data = json.loads(result)
        >>> for page in data["pages"]:
        ...     print(f"Page {page['number']}: {page['markdown'][:100]}...")
    """
    try:
        # Validate the file
        if not Path(pdf_path).exists():
            return json.dumps({
                "error": f"PDF not found: {pdf_path}",
                "success": False
            })

        if not pdf_path.lower().endswith('.pdf'):
            return json.dumps({
                "error": "File must be a PDF",
                "success": False
            })

        # Get the Mistral client
        client = get_mistral_client()

        # Encode PDF to base64
        pdf_base64 = encode_image_to_base64(pdf_path)
        data_url = f"data:application/pdf;base64,{pdf_base64}"

        # Call Mistral OCR 3
        result = client.ocr.process(
            model="mistral-ocr-2512",
            document={
                "type": "image_url",
                "image_url": {"url": data_url}
            }
        )

        # Process pages
        pages = result.pages if hasattr(result, 'pages') else []

        # Filter to specific pages if requested
        pages_to_process = None
        if page_numbers:
            try:
                pages_to_process = [int(p.strip()) for p in page_numbers.split(",")]
            except ValueError:
                pass

        processed_pages = []
        for i, page in enumerate(pages, start=1):
            if pages_to_process is None or i in pages_to_process:
                processed_pages.append({
                    "number": i,
                    "markdown": page.markdown if hasattr(page, 'markdown') else "",
                    "has_tables": "<table" in (page.markdown or "").lower()
                })

        return json.dumps({
            "success": True,
            "pages": processed_pages,
            "total_pages": len(pages),
            "pages_processed": [p["number"] for p in processed_pages],
            "file_processed": str(pdf_path)
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "error": str(e),
            "success": False
        })


@tool
def analyze_document_content(image_path: str) -> str:
    """
    Analyze document content and provide structured insights.

    This is a HIGHER-LEVEL tool that:
    1. Extracts text using Mistral OCR 3
    2. Analyzes the content structure
    3. Identifies key information

    Use this when you need more than just raw text extraction.

    Args:
        image_path: Path to the document image

    Returns:
        JSON string with:
        - raw_text: Extracted markdown text
        - analysis: Content analysis including:
          - word_count: Total words
          - line_count: Total lines
          - has_tables: Whether tables exist
          - has_signatures: Potential signature areas
          - content_type_hint: Guessed document type

    Example:
        >>> result = analyze_document_content("/path/to/contract.jpg")
        >>> data = json.loads(result)
        >>> print(f"Document type: {data['analysis']['content_type_hint']}")
    """
    try:
        # Get OCR result first
        ocr_result = process_document_ocr.invoke(image_path)
        ocr_data = json.loads(ocr_result)

        if not ocr_data.get("success"):
            return ocr_result

        markdown = ocr_data.get("markdown", "")

        # Basic analysis
        lines = markdown.split("\n")
        words = markdown.split()

        # Content type detection heuristics
        content_type = "unknown"
        lower_text = markdown.lower()

        if any(kw in lower_text for kw in ["invoice", "total", "amount due", "bill to"]):
            content_type = "invoice"
        elif any(kw in lower_text for kw in ["contract", "agreement", "parties", "whereas"]):
            content_type = "contract"
        elif any(kw in lower_text for kw in ["receipt", "thank you", "transaction"]):
            content_type = "receipt"
        elif any(kw in lower_text for kw in ["form", "please fill", "signature", "date of birth"]):
            content_type = "form"
        elif any(kw in lower_text for kw in ["report", "summary", "conclusion", "analysis"]):
            content_type = "report"

        return json.dumps({
            "success": True,
            "raw_text": markdown,
            "analysis": {
                "word_count": len(words),
                "line_count": len(lines),
                "character_count": len(markdown),
                "has_tables": ocr_data.get("has_tables", False),
                "page_count": ocr_data.get("page_count", 1),
                "content_type_hint": content_type,
                "confidence": "heuristic"  # Not ML-based, just keyword matching
            },
            "file_processed": str(image_path)
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "error": str(e),
            "success": False
        })


# === UTILITY FUNCTIONS (not tools, but helpful) ===

def check_mistral_connection() -> dict:
    """
    Check if Mistral API is accessible.
    Use this for health checks.
    """
    return {
        "available": is_mistral_available(),
        "model": "mistral-ocr-2512",
        "service": "Mistral OCR 3"
    }


# === LIST OF ALL TOOLS (for easy import) ===

MISTRAL_OCR_TOOLS = [
    process_document_ocr,
    extract_tables_from_document,
    process_pdf_document,
    analyze_document_content,
]


# === TEST ===

if __name__ == "__main__":
    """
    Test the OCR tools.
    Run: python src/tools/mistral_ocr_tools.py
    """
    print("Mistral OCR Tools Test")
    print("=" * 50)

    # Check connection
    status = check_mistral_connection()
    print(f"\nMistral Available: {status['available']}")

    if not status['available']:
        print("\nMistral is not available. Please:")
        print("1. Install: pip install mistralai")
        print("2. Set MISTRAL_API_KEY in .env")
        exit(1)

    # List available tools
    print("\nAvailable Tools:")
    for tool in MISTRAL_OCR_TOOLS:
        print(f"  - {tool.name}: {tool.description[:60]}...")
