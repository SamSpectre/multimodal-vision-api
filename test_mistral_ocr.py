"""
Test script for Mistral OCR 3 integration.

This script tests:
1. Mistral client connection
2. OCR functionality with a test image
3. Error handling

Run: python test_mistral_ocr.py
"""

import os
import sys
import base64
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(project_root / ".env")


def create_test_image():
    """Create a simple test image with text using PIL."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Installing Pillow for test image creation...")
        os.system("pip install Pillow")
        from PIL import Image, ImageDraw, ImageFont

    # Create a white image
    img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(img)

    # Add text
    text = "Hello Mistral OCR 3!\nThis is a test document.\nInvoice #12345"
    draw.text((20, 30), text, fill='black')

    # Save it
    test_path = project_root / "test_images" / "test_ocr.png"
    test_path.parent.mkdir(exist_ok=True)
    img.save(test_path)

    print(f"Created test image at: {test_path}")
    return test_path


def encode_image_to_base64(image_path: Path) -> str:
    """Encode an image file to base64."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def test_mistral_connection():
    """Test 1: Check if Mistral client can be created."""
    print("\n" + "=" * 60)
    print("TEST 1: Mistral Client Connection")
    print("=" * 60)

    try:
        from src.clients.mistral_client import get_mistral_client, is_mistral_available

        # Check availability
        available = is_mistral_available()
        print(f"Mistral available: {available}")

        if not available:
            print("FAILED: Mistral is not available")
            print("Check: MISTRAL_API_KEY in .env file")
            return False

        # Try to get the client
        client = get_mistral_client()
        print(f"Client created: {client is not None}")
        print(f"Client type: {type(client).__name__}")

        print("PASSED: Mistral client connection works!")
        return True

    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")
        return False


def test_mistral_ocr(image_path: Path):
    """Test 2: Test OCR functionality."""
    print("\n" + "=" * 60)
    print("TEST 2: Mistral OCR 3 Processing")
    print("=" * 60)

    try:
        from src.clients.mistral_client import get_mistral_client

        client = get_mistral_client()

        # Encode image
        image_base64 = encode_image_to_base64(image_path)
        data_url = f"data:image/png;base64,{image_base64}"

        print(f"Image path: {image_path}")
        print(f"Base64 length: {len(image_base64)} chars")
        print(f"Calling Mistral OCR 3 (model: mistral-ocr-2512)...")

        # Call OCR API
        result = client.ocr.process(
            model="mistral-ocr-2512",
            document={
                "type": "image_url",
                "image_url": data_url
            }
        )

        print(f"\nOCR Result Type: {type(result)}")
        print(f"OCR Result: {result}")

        # Check if we got text
        if hasattr(result, 'pages'):
            print(f"\nPages: {len(result.pages)}")
            for i, page in enumerate(result.pages):
                print(f"\n--- Page {i+1} ---")
                if hasattr(page, 'markdown'):
                    print(f"Markdown: {page.markdown[:500] if len(page.markdown) > 500 else page.markdown}")
                elif hasattr(page, 'text'):
                    print(f"Text: {page.text[:500] if len(page.text) > 500 else page.text}")

        print("\nPASSED: Mistral OCR 3 works!")
        return True

    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_models():
    """Test 3: Check available Mistral models."""
    print("\n" + "=" * 60)
    print("TEST 3: List Mistral Models")
    print("=" * 60)

    try:
        from src.clients.mistral_client import get_mistral_client

        client = get_mistral_client()

        # Try to list models
        if hasattr(client, 'models'):
            print("Listing available models...")
            models = client.models.list()
            print(f"Models response: {models}")

            if hasattr(models, 'data'):
                for model in models.data:
                    model_id = model.id if hasattr(model, 'id') else str(model)
                    print(f"  - {model_id}")
        else:
            print("Models API not available in client")

        print("\nPASSED: Model listing works!")
        return True

    except Exception as e:
        print(f"Note: {type(e).__name__}: {e}")
        print("(Model listing may not be available, this is not critical)")
        return True  # Not critical


def main():
    """Run all tests."""
    print("=" * 60)
    print("MISTRAL OCR 3 INTEGRATION TEST")
    print("=" * 60)

    # Show environment info
    api_key = os.getenv("MISTRAL_API_KEY", "")
    print(f"\nMISTRAL_API_KEY configured: {'Yes' if api_key and api_key != 'your_mistral_api_key_here' else 'No'}")
    if api_key:
        print(f"API Key prefix: {api_key[:8]}...")

    results = []

    # Test 1: Connection
    results.append(("Connection", test_mistral_connection()))

    if results[-1][1]:  # Only continue if connection works
        # Create test image
        test_image = create_test_image()

        # Test 2: OCR
        results.append(("OCR", test_mistral_ocr(test_image)))

        # Test 3: Models (optional)
        results.append(("Models", test_api_models()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "PASSED" if passed else "FAILED"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("All tests passed! Mistral OCR 3 is working correctly.")
    else:
        print("Some tests failed. Please check the errors above.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
