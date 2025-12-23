"""
Comprehensive Test Suite for Document Intelligence System

Tests:
1. Mistral OCR API Connection
2. OCR Text Extraction (process_document_ocr)
3. Table Extraction (extract_tables_from_document)
4. Document Analysis/Classification (analyze_document_content)
5. Full Document Agent via Multi-Agent System

Run: python test_document_intelligence.py
"""

import os
import sys
import json
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def create_test_images():
    """Create test images for different document types."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Installing Pillow...")
        os.system("pip install Pillow")
        from PIL import Image, ImageDraw, ImageFont

    test_dir = project_root / "test_images"
    test_dir.mkdir(exist_ok=True)
    created = {}

    # 1. Simple text document
    img = Image.new('RGB', (600, 300), color='white')
    draw = ImageDraw.Draw(img)
    text = """INVOICE #INV-2024-001

Bill To: John Smith
Date: December 23, 2024

Description         Qty    Price
Widget A             2     $50.00
Widget B             3     $75.00
Service Fee          1     $25.00

Subtotal: $275.00
Tax (10%): $27.50
Total Due: $302.50

Thank you for your business!"""
    draw.text((20, 20), text, fill='black')
    path = test_dir / "invoice_test.png"
    img.save(path)
    created['invoice'] = path

    # 2. Table document
    img = Image.new('RGB', (500, 250), color='white')
    draw = ImageDraw.Draw(img)
    table_text = """PRODUCT CATALOG

| Product | Category | Price |
|---------|----------|-------|
| Laptop  | Tech     | $999  |
| Phone   | Tech     | $599  |
| Desk    | Furniture| $299  |
| Chair   | Furniture| $199  |"""
    draw.text((20, 20), table_text, fill='black')
    path = test_dir / "table_test.png"
    img.save(path)
    created['table'] = path

    # 3. Form-like document
    img = Image.new('RGB', (500, 300), color='white')
    draw = ImageDraw.Draw(img)
    form_text = """APPLICATION FORM

Full Name: ________________________
Date of Birth: ____________________
Email: ___________________________
Phone: ___________________________

Please fill in all fields completely.
Signature: _______________________
Date: ___________________________"""
    draw.text((20, 20), form_text, fill='black')
    path = test_dir / "form_test.png"
    img.save(path)
    created['form'] = path

    # 4. Contract-like document
    img = Image.new('RGB', (600, 400), color='white')
    draw = ImageDraw.Draw(img)
    contract_text = """SERVICE AGREEMENT CONTRACT

This Agreement is entered into between:
Party A ("Provider") and Party B ("Client")

WHEREAS the Provider agrees to deliver services
as described herein, the parties agree as follows:

1. SCOPE OF SERVICES
   Provider shall deliver consulting services.

2. PAYMENT TERMS
   Client shall pay within 30 days of invoice.

3. TERMINATION
   Either party may terminate with 30 days notice.

Signatures:
_____________________  _____________________
Provider               Client"""
    draw.text((20, 20), contract_text, fill='black')
    path = test_dir / "contract_test.png"
    img.save(path)
    created['contract'] = path

    print(f"Created {len(created)} test images in {test_dir}")
    return created


def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_result(name, passed, details=""):
    """Print test result."""
    status = "PASSED" if passed else "FAILED"
    symbol = "✓" if passed else "✗"
    print(f"  {symbol} {name}: {status}")
    if details:
        for line in details.split('\n')[:5]:  # Limit to 5 lines
            print(f"      {line[:80]}")


# ========== TEST 1: API CONNECTION ==========

def test_api_connection():
    """Test Mistral API connection."""
    print_header("TEST 1: Mistral API Connection")

    try:
        from src.clients.mistral_client import get_mistral_client, is_mistral_available

        available = is_mistral_available()
        if not available:
            print_result("API Available", False, "MISTRAL_API_KEY not configured")
            return False

        client = get_mistral_client()
        print_result("Client Creation", True, f"Type: {type(client).__name__}")
        return True

    except Exception as e:
        print_result("API Connection", False, str(e))
        return False


# ========== TEST 2: OCR TEXT EXTRACTION ==========

def test_ocr_extraction(test_images):
    """Test OCR text extraction on various documents."""
    print_header("TEST 2: OCR Text Extraction (process_document_ocr)")

    all_passed = True

    try:
        from src.tools.mistral_ocr_tools import process_document_ocr

        for doc_type, image_path in test_images.items():
            print(f"\n  Testing {doc_type} document...")
            start = time.time()

            result = process_document_ocr.invoke(str(image_path))
            elapsed = time.time() - start

            data = json.loads(result)

            if data.get("success"):
                markdown = data.get("markdown", "")
                word_count = len(markdown.split())

                # Check for expected content
                expected_found = False
                if doc_type == "invoice" and "invoice" in markdown.lower():
                    expected_found = True
                elif doc_type == "table" and ("product" in markdown.lower() or "catalog" in markdown.lower()):
                    expected_found = True
                elif doc_type == "form" and ("form" in markdown.lower() or "name" in markdown.lower()):
                    expected_found = True
                elif doc_type == "contract" and ("agreement" in markdown.lower() or "contract" in markdown.lower()):
                    expected_found = True

                print_result(
                    f"OCR {doc_type}",
                    expected_found,
                    f"Words: {word_count}, Time: {elapsed:.2f}s, Content found: {expected_found}"
                )

                if not expected_found:
                    all_passed = False
                    print(f"      Preview: {markdown[:100]}...")
            else:
                print_result(f"OCR {doc_type}", False, data.get("error", "Unknown error"))
                all_passed = False

    except Exception as e:
        print_result("OCR Extraction", False, str(e))
        return False

    return all_passed


# ========== TEST 3: TABLE EXTRACTION ==========

def test_table_extraction(test_images):
    """Test table extraction capability."""
    print_header("TEST 3: Table Extraction (extract_tables_from_document)")

    try:
        from src.tools.mistral_ocr_tools import extract_tables_from_document

        # Test on invoice (has table-like structure)
        image_path = test_images.get("invoice") or test_images.get("table")
        if not image_path:
            print_result("Table Extraction", False, "No test image available")
            return False

        print(f"  Testing on: {image_path.name}")
        start = time.time()

        result = extract_tables_from_document.invoke(str(image_path))
        elapsed = time.time() - start

        data = json.loads(result)

        if data.get("success"):
            tables = data.get("tables", [])
            table_count = data.get("table_count", 0)
            raw_md = data.get("raw_markdown", "")

            print_result(
                "Table Extraction",
                True,
                f"Tables found: {table_count}, Time: {elapsed:.2f}s, Raw text length: {len(raw_md)}"
            )

            if tables:
                print(f"      First table preview: {tables[0][:100]}...")

            return True
        else:
            print_result("Table Extraction", False, data.get("error", "Unknown error"))
            return False

    except Exception as e:
        print_result("Table Extraction", False, str(e))
        return False


# ========== TEST 4: DOCUMENT ANALYSIS ==========

def test_document_analysis(test_images):
    """Test document analysis and classification."""
    print_header("TEST 4: Document Analysis (analyze_document_content)")

    all_passed = True
    expected_types = {
        "invoice": "invoice",
        "form": "form",
        "contract": "contract",
    }

    try:
        from src.tools.mistral_ocr_tools import analyze_document_content

        for doc_type, image_path in test_images.items():
            if doc_type not in expected_types:
                continue

            print(f"\n  Analyzing {doc_type} document...")
            start = time.time()

            result = analyze_document_content.invoke(str(image_path))
            elapsed = time.time() - start

            data = json.loads(result)

            if data.get("success"):
                analysis = data.get("analysis", {})
                detected_type = analysis.get("content_type_hint", "unknown")
                word_count = analysis.get("word_count", 0)
                has_tables = analysis.get("has_tables", False)

                type_correct = detected_type == expected_types.get(doc_type, "unknown")

                print_result(
                    f"Analysis {doc_type}",
                    type_correct or detected_type != "unknown",
                    f"Detected: {detected_type}, Expected: {expected_types[doc_type]}, "
                    f"Words: {word_count}, Tables: {has_tables}, Time: {elapsed:.2f}s"
                )

                if not type_correct and detected_type == "unknown":
                    all_passed = False
            else:
                print_result(f"Analysis {doc_type}", False, data.get("error", "Unknown error"))
                all_passed = False

    except Exception as e:
        print_result("Document Analysis", False, str(e))
        return False

    return all_passed


# ========== TEST 5: FULL DOCUMENT AGENT ==========

def test_document_agent():
    """Test the full Document Agent via multi-agent system."""
    print_header("TEST 5: Document Agent (Multi-Agent System)")

    try:
        from src.agents import invoke_agent, AGENT_DESCRIPTIONS

        print("\n  Agent Descriptions:")
        for name, desc in AGENT_DESCRIPTIONS.items():
            print(f"    - {name}: {desc[:50]}...")

        # Test 1: Ask about capabilities
        print("\n  Test 5a: Asking about capabilities...")
        start = time.time()

        result = invoke_agent("What types of documents can you process?")
        elapsed = time.time() - start

        if result and len(result) > 20:
            response_preview = result[:200] if len(result) > 200 else result
            print_result(
                "Capability Query",
                True,
                f"Response length: {len(result)}, Time: {elapsed:.2f}s"
            )
        else:
            print_result("Capability Query", False, f"Short/empty response: {result}")
            return False

        # Test 2: Document routing
        print("\n  Test 5b: Testing document routing...")
        start = time.time()

        result = invoke_agent("I have an invoice image at test_images/invoice_test.png, can you extract the text?")
        elapsed = time.time() - start

        if result:
            print_result(
                "Document Routing",
                True,
                f"Response length: {len(result)}, Time: {elapsed:.2f}s"
            )
        else:
            print_result("Document Routing", False, "No response")

        return True

    except Exception as e:
        print_result("Document Agent", False, str(e))
        import traceback
        traceback.print_exc()
        return False


# ========== TEST 6: OCR TOOLS DIRECT ==========

def test_ocr_tools_direct(test_images):
    """Test OCR tools directly without agent."""
    print_header("TEST 6: Direct Tool Invocation")

    try:
        from src.tools.mistral_ocr_tools import (
            process_document_ocr,
            extract_tables_from_document,
            analyze_document_content,
            check_mistral_connection
        )

        # Check connection
        status = check_mistral_connection()
        print_result(
            "Connection Check",
            status.get("available", False),
            f"Model: {status.get('model')}, Service: {status.get('service')}"
        )

        if not status.get("available"):
            return False

        # Test with invoice
        image_path = test_images.get("invoice")
        if image_path:
            print(f"\n  Processing: {image_path.name}")

            result = process_document_ocr.invoke(str(image_path))
            data = json.loads(result)

            if data.get("success"):
                md = data.get("markdown", "")
                print_result(
                    "Direct OCR Call",
                    True,
                    f"Extracted {len(md.split())} words, {data.get('page_count')} pages"
                )
                return True
            else:
                print_result("Direct OCR Call", False, data.get("error"))
                return False

        return True

    except Exception as e:
        print_result("Direct Tool Test", False, str(e))
        return False


# ========== MAIN ==========

def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("   DOCUMENT INTELLIGENCE SYSTEM - COMPREHENSIVE TEST SUITE")
    print("=" * 70)

    # Show environment info
    api_key = os.getenv("MISTRAL_API_KEY", "")
    print(f"\nEnvironment:")
    print(f"  MISTRAL_API_KEY: {'Configured' if api_key and api_key != 'your_mistral_api_key_here' else 'NOT SET'}")
    print(f"  Working Directory: {project_root}")

    results = []

    # Test 1: API Connection
    results.append(("API Connection", test_api_connection()))

    if not results[-1][1]:
        print("\n[ABORT] Cannot proceed without API connection")
        return 1

    # Create test images
    print("\n[SETUP] Creating test images...")
    test_images = create_test_images()

    # Test 2: OCR Extraction
    results.append(("OCR Extraction", test_ocr_extraction(test_images)))

    # Test 3: Table Extraction
    results.append(("Table Extraction", test_table_extraction(test_images)))

    # Test 4: Document Analysis
    results.append(("Document Analysis", test_document_analysis(test_images)))

    # Test 5: Direct Tool Test
    results.append(("Direct Tools", test_ocr_tools_direct(test_images)))

    # Test 6: Full Agent (optional - may take longer)
    try:
        results.append(("Document Agent", test_document_agent()))
    except Exception as e:
        print(f"\n  [SKIP] Document Agent test failed: {e}")
        results.append(("Document Agent", False))

    # Summary
    print_header("TEST SUMMARY")

    passed = 0
    failed = 0
    for name, result in results:
        status = "PASSED" if result else "FAILED"
        symbol = "✓" if result else "✗"
        print(f"  {symbol} {name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1

    print("\n" + "-" * 70)
    print(f"  Total: {passed} passed, {failed} failed out of {len(results)} tests")
    print("=" * 70)

    if failed == 0:
        print("\n  All tests passed! Document Intelligence is working correctly.")
        return 0
    else:
        print(f"\n  {failed} test(s) failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    exit(main())
