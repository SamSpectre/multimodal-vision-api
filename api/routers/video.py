"""
Video Analysis Router

API endpoints for image/video analysis powered by Groq Vision.
Optimized for robotics applications with ~50ms latency.

=== ENDPOINT DESIGN ===

1. Single Responsibility
   - /analyze → Full image analysis
   - /describe → Scene description for robotics
   - /objects → Object detection
   - /ask → Visual question answering

2. Consistent Response Format
   All endpoints return:
   - success: bool
   - data: {...}
   - meta: {latency_ms, model, provider}

3. Low Latency Focus
   - Groq Vision: ~50ms
   - Optimized for real-time robotics
"""

import json
import time
import base64
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse

# Import authentication
from src.auth.dependencies import require_auth
from src.auth.models import User

# Import our schemas
from api.schemas.video import (
    ImageRequest,
    VisualQuestionRequest,
    AnalysisResult,
    SceneDescription,
    ObjectDetectionResult,
    VisualQuestionResult,
    VideoServiceStatus,
)

# Import our tools
from src.tools.video_tools import (
    analyze_image,
    describe_scene,
    detect_objects,
    visual_question,
    check_groq_vision_status,
)

# Import client check
from src.clients.groq_client import is_groq_available, get_recommended_vision_model


# Create the router
router = APIRouter()


# === HELPER FUNCTIONS ===

def decode_base64_to_temp_file(base64_string: str, suffix: str = ".jpg") -> str:
    """
    Decode base64 string and save to a temporary file.

    Args:
        base64_string: Base64 encoded file content
        suffix: File extension to use

    Returns:
        Path to the temporary file
    """
    file_bytes = base64.b64decode(base64_string)

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
        f.write(file_bytes)
        return f.name


def cleanup_temp_file(file_path: str):
    """Remove a temporary file (for background cleanup)."""
    try:
        Path(file_path).unlink(missing_ok=True)
    except Exception:
        pass


def detect_image_type(base64_string: str) -> str:
    """
    Detect image type from base64 magic bytes.
    """
    try:
        header = base64.b64decode(base64_string[:100])

        if header[:3] == b'\xff\xd8\xff':
            return ".jpg"
        elif header[:8] == b'\x89PNG\r\n\x1a\n':
            return ".png"
        elif header[:4] == b'GIF8':
            return ".gif"
        elif header[:4] == b'RIFF' and header[8:12] == b'WEBP':
            return ".webp"
        else:
            return ".jpg"
    except Exception:
        return ".jpg"


def get_file_to_process(request, background_tasks) -> tuple[str, Optional[str]]:
    """
    Extract file path from request, handling base64/path options.

    Returns:
        tuple of (file_path, temp_file_or_none)
    """
    temp_file = None

    if hasattr(request, 'image_base64') and request.image_base64:
        suffix = detect_image_type(request.image_base64)
        temp_file = decode_base64_to_temp_file(request.image_base64, suffix)
        file_to_process = temp_file
    elif hasattr(request, 'image_url') and request.image_url:
        raise HTTPException(
            status_code=501,
            detail="URL processing not yet implemented. Use image_base64 or image_path."
        )
    elif hasattr(request, 'image_path') and request.image_path:
        if not Path(request.image_path).exists():
            raise HTTPException(
                status_code=404,
                detail=f"Image not found: {request.image_path}"
            )
        file_to_process = request.image_path
    else:
        raise HTTPException(
            status_code=400,
            detail="No image source provided. Use image_base64 or image_path."
        )

    return file_to_process, temp_file


# === ENDPOINTS ===

@router.post("/analyze", response_model=None)
async def analyze_image_endpoint(
    request: ImageRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_auth)
):
    """
    Analyze an image using Groq Vision (~50ms latency).

    **Requires Authentication:** JWT token or API key

    This endpoint:
    1. Accepts an image (base64 or path)
    2. Analyzes it with Groq Llama 3.2 Vision
    3. Returns a detailed analysis

    **Features:**
    - Scene understanding
    - Object identification
    - Custom prompts supported
    - Optimized for robotics (~50ms)

    **Use Cases:**
    - General image understanding
    - Custom analysis with specific prompts
    - Robotics scene awareness
    """
    start_time = time.time()
    temp_file = None

    try:
        # Check if Groq is available
        if not is_groq_available():
            raise HTTPException(
                status_code=503,
                detail="Groq Vision service is not available. Check GROQ_API_KEY."
            )

        # Get file to process
        file_to_process, temp_file = get_file_to_process(request, background_tasks)

        # Call the analysis tool
        result_json = analyze_image.invoke({
            "image_path": file_to_process,
            "prompt": request.prompt
        })
        result = json.loads(result_json)

        # Schedule cleanup
        if temp_file:
            background_tasks.add_task(cleanup_temp_file, temp_file)

        processing_time_ms = int((time.time() - start_time) * 1000)

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Image analysis failed")
            )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "analysis": result.get("analysis", ""),
                },
                "meta": {
                    "latency_ms": result.get("latency_ms", processing_time_ms),
                    "model": result.get("model", "llama-3.2-11b-vision-preview"),
                    "provider": "groq",
                    "total_time_ms": processing_time_ms
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        if temp_file:
            cleanup_temp_file(temp_file)
        raise HTTPException(
            status_code=500,
            detail=f"Image analysis failed: {str(e)}"
        )


@router.post("/describe", response_model=None)
async def describe_scene_endpoint(
    request: ImageRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_auth)
):
    """
    Get a detailed scene description optimized for robotics.

    **Requires Authentication:** JWT token or API key

    Returns:
    - Scene overview
    - Object locations (left, center, right, etc.)
    - Spatial relationships
    - Navigation information
    - Interactable objects

    **Best for:** Robotics navigation, spatial awareness, scene understanding.
    """
    start_time = time.time()
    temp_file = None

    try:
        if not is_groq_available():
            raise HTTPException(
                status_code=503,
                detail="Groq Vision service is not available"
            )

        file_to_process, temp_file = get_file_to_process(request, background_tasks)

        result_json = describe_scene.invoke(file_to_process)
        result = json.loads(result_json)

        if temp_file:
            background_tasks.add_task(cleanup_temp_file, temp_file)

        processing_time_ms = int((time.time() - start_time) * 1000)

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Scene description failed")
            )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "scene_description": result.get("scene_description", ""),
                },
                "meta": {
                    "latency_ms": result.get("latency_ms", processing_time_ms),
                    "model": result.get("model", "llama-3.2-11b-vision-preview"),
                    "provider": "groq"
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        if temp_file:
            cleanup_temp_file(temp_file)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/objects", response_model=None)
async def detect_objects_endpoint(
    request: ImageRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_auth)
):
    """
    Detect and list objects in an image.

    **Requires Authentication:** JWT token or API key

    Returns a list of detected objects with:
    - Object name/type
    - Location (left, center, right, etc.)
    - Size estimate
    - Notable characteristics

    **Best for:** Object identification, inventory, robotics manipulation tasks.
    """
    start_time = time.time()
    temp_file = None

    try:
        if not is_groq_available():
            raise HTTPException(
                status_code=503,
                detail="Groq Vision service is not available"
            )

        file_to_process, temp_file = get_file_to_process(request, background_tasks)

        result_json = detect_objects.invoke(file_to_process)
        result = json.loads(result_json)

        if temp_file:
            background_tasks.add_task(cleanup_temp_file, temp_file)

        processing_time_ms = int((time.time() - start_time) * 1000)

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Object detection failed")
            )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "objects_description": result.get("objects_description", ""),
                },
                "meta": {
                    "latency_ms": result.get("latency_ms", processing_time_ms),
                    "model": result.get("model", "llama-3.2-11b-vision-preview"),
                    "provider": "groq"
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        if temp_file:
            cleanup_temp_file(temp_file)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ask", response_model=None)
async def visual_question_endpoint(
    request: VisualQuestionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_auth)
):
    """
    Answer a specific question about an image (Visual Q&A).

    **Requires Authentication:** JWT token or API key

    Provide an image and a question, get a direct answer.

    **Examples:**
    - "Is there a red cup on the table?"
    - "How many people are in the image?"
    - "Is the door open or closed?"

    **Best for:** Targeted queries, yes/no questions, specific information extraction.
    """
    start_time = time.time()
    temp_file = None

    try:
        if not is_groq_available():
            raise HTTPException(
                status_code=503,
                detail="Groq Vision service is not available"
            )

        file_to_process, temp_file = get_file_to_process(request, background_tasks)

        result_json = visual_question.invoke({
            "image_path": file_to_process,
            "question": request.question
        })
        result = json.loads(result_json)

        if temp_file:
            background_tasks.add_task(cleanup_temp_file, temp_file)

        processing_time_ms = int((time.time() - start_time) * 1000)

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Visual Q&A failed")
            )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "question": result.get("question", request.question),
                    "answer": result.get("answer", ""),
                },
                "meta": {
                    "latency_ms": result.get("latency_ms", processing_time_ms),
                    "model": result.get("model", "llama-3.2-11b-vision-preview"),
                    "provider": "groq"
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
    Check video analysis service status.

    Returns availability of Groq Vision services.
    No authentication required.
    """
    status = check_groq_vision_status()

    return {
        "service": "Video Analysis",
        "status": "available" if status["available"] else "unavailable",
        "provider": "groq",
        "model": status.get("model", "llama-3.2-11b-vision-preview"),
        "expected_latency": status.get("expected_latency", "~50ms"),
        "available": status["available"]
    }
