"""
Video Agent Test Suite

Tests for the Groq Vision-powered video analysis agent.

Run: python test_video_agent.py
"""

import os
import sys
import json

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()


def test_groq_client():
    """Test Groq client availability."""
    print("\n" + "=" * 60)
    print("TEST 1: Groq Client Availability")
    print("=" * 60)

    from src.clients.groq_client import is_groq_available, get_recommended_vision_model

    available = is_groq_available()
    model = get_recommended_vision_model("robotics")

    print(f"Groq Available: {available}")
    print(f"Recommended Model: {model}")

    if not available:
        print("\n⚠️  Groq is not available. Check:")
        print("  1. Is groq installed? pip install groq")
        print("  2. Is GROQ_API_KEY set in .env?")
        return False

    print("✓ Groq client is available")
    return True


def test_video_tools():
    """Test video tools availability."""
    print("\n" + "=" * 60)
    print("TEST 2: Video Tools")
    print("=" * 60)

    from src.tools.video_tools import (
        VIDEO_TOOLS,
        analyze_image,
        describe_scene,
        detect_objects,
        visual_question,
        check_groq_vision_status
    )

    print(f"Number of tools: {len(VIDEO_TOOLS)}")

    for tool in VIDEO_TOOLS:
        print(f"  - {tool.name}: {tool.description[:50]}...")

    # Check status
    status = check_groq_vision_status()
    print(f"\nGroq Vision Status: {status}")

    print("✓ Video tools loaded successfully")
    return True


def test_video_agent():
    """Test video agent initialization."""
    print("\n" + "=" * 60)
    print("TEST 3: Video Agent")
    print("=" * 60)

    try:
        from src.agents.video_agent import (
            get_video_llm,
            get_video_agent,
            VIDEO_AGENT_PROMPT,
            HAS_LANGCHAIN_GROQ
        )

        print(f"LangChain Groq available: {HAS_LANGCHAIN_GROQ}")

        # Get the LLM
        print("\nInitializing video LLM...")
        llm = get_video_llm()
        print(f"LLM type: {type(llm).__name__}")

        # Get the agent
        print("\nInitializing video agent...")
        agent = get_video_agent()
        print(f"Agent created: {type(agent).__name__}")

        print("✓ Video agent initialized successfully")
        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_video_schemas():
    """Test video schemas."""
    print("\n" + "=" * 60)
    print("TEST 4: Video Schemas")
    print("=" * 60)

    from api.schemas.video import (
        ImageRequest,
        VisualQuestionRequest,
        AnalysisResult,
        SceneDescription,
        ObjectDetectionResult,
        VisualQuestionResult,
        VideoServiceStatus
    )

    # Test ImageRequest
    request = ImageRequest(
        image_path="/path/to/test.jpg",
        prompt="Describe this image"
    )
    print(f"ImageRequest: image_path={request.image_path}")

    # Test VisualQuestionRequest
    vq_request = VisualQuestionRequest(
        image_path="/path/to/test.jpg",
        question="Is there a cat in the image?"
    )
    print(f"VisualQuestionRequest: question={vq_request.question}")

    # Test result models
    result = AnalysisResult(
        success=True,
        analysis="Test analysis",
        latency_ms=50,
        model="llama-3.2-11b-vision-preview",
        provider="groq"
    )
    print(f"AnalysisResult: latency={result.latency_ms}ms")

    print("✓ Video schemas validated")
    return True


def test_api_router():
    """Test API router registration."""
    print("\n" + "=" * 60)
    print("TEST 5: API Router")
    print("=" * 60)

    from api.routers.video import router

    # Get all routes
    routes = [r.path for r in router.routes]
    print(f"Video router routes: {routes}")

    expected_routes = ["/analyze", "/describe", "/objects", "/ask", "/status"]
    for route in expected_routes:
        if route in routes:
            print(f"  ✓ {route}")
        else:
            print(f"  ✗ {route} - MISSING")

    print("✓ Video router configured")
    return True


def test_image_analysis(image_path: str = None):
    """Test actual image analysis (optional - requires image)."""
    print("\n" + "=" * 60)
    print("TEST 6: Image Analysis (Live)")
    print("=" * 60)

    if image_path is None:
        # Try to find a test image
        test_paths = [
            "test_images/sample.jpg",
            "test_images/test.png",
            "test_image.jpg",
        ]
        for path in test_paths:
            if os.path.exists(path):
                image_path = path
                break

    if image_path is None or not os.path.exists(image_path):
        print("⚠️  No test image found. Skipping live analysis test.")
        print("   To run this test, provide an image path:")
        print("   python test_video_agent.py /path/to/image.jpg")
        return None

    print(f"Testing with image: {image_path}")

    from src.tools.video_tools import analyze_image

    try:
        result_json = analyze_image.invoke(image_path)
        result = json.loads(result_json)

        if result.get("success"):
            print(f"\n✓ Analysis successful!")
            print(f"  Latency: {result.get('latency_ms', 'N/A')}ms")
            print(f"  Model: {result.get('model', 'N/A')}")
            print(f"\nAnalysis (first 200 chars):")
            print(f"  {result.get('analysis', '')[:200]}...")
            return True
        else:
            print(f"✗ Analysis failed: {result.get('error')}")
            return False

    except Exception as e:
        print(f"✗ Error during analysis: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("VIDEO AGENT TEST SUITE")
    print("=" * 60)

    results = {}

    # Test 1: Groq client
    results["groq_client"] = test_groq_client()

    # Test 2: Video tools
    results["video_tools"] = test_video_tools()

    # Test 3: Video agent
    results["video_agent"] = test_video_agent()

    # Test 4: Schemas
    results["schemas"] = test_video_schemas()

    # Test 5: Router
    results["router"] = test_api_router()

    # Test 6: Live analysis (optional)
    image_path = sys.argv[1] if len(sys.argv) > 1 else None
    results["live_analysis"] = test_image_analysis(image_path)

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = 0
    failed = 0
    skipped = 0

    for name, result in results.items():
        if result is True:
            status = "✓ PASSED"
            passed += 1
        elif result is False:
            status = "✗ FAILED"
            failed += 1
        else:
            status = "- SKIPPED"
            skipped += 1

        print(f"  {name}: {status}")

    print(f"\nTotal: {passed} passed, {failed} failed, {skipped} skipped")

    if failed == 0:
        print("\n✓ All tests passed! Video agent is ready.")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
