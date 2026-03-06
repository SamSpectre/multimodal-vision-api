"""
Video Analysis Tools for Robotics Vision

This module provides LangChain tools that wrap the Groq Vision API.

=== WHY GROQ FOR ROBOTICS VISION? ===

Latency Comparison:
  - Groq Llama 3.2 Vision: ~50ms (real-time capable)
  - OpenAI GPT-4o: ~200ms (2.6x slower)
  - Claude: ~300ms (not ideal for robotics)

For robotics applications:
  - Sub-100ms response is critical for real-time decisions
  - Groq's LPU architecture provides consistent latency
  - Cloud inference matching edge computing performance

=== TOOL PATTERN ===

Following the same pattern as mistral_ocr_tools.py:
  1. @tool decorator from langchain_core.tools
  2. Detailed docstrings for AI agent understanding
  3. JSON string returns with success/error fields
  4. Export list: VIDEO_TOOLS = [...]
"""

import os
import base64
import json
import time
from pathlib import Path
from typing import Optional
from langchain_core.tools import tool

# Import our singleton client
from src.clients.groq_client import get_groq_client, is_groq_available, get_recommended_vision_model


# === HELPER FUNCTIONS ===

def encode_image_to_base64(image_path: str) -> str:
    """
    Encode an image file to base64 string.

    Args:
        image_path: Path to the image file

    Returns:
        Base64 encoded string of the image
    """
    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def get_mime_type(file_path: str) -> str:
    """
    Get the MIME type based on file extension.
    """
    extension = Path(file_path).suffix.lower()

    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
        ".webp": "image/webp",
    }

    return mime_types.get(extension, "image/jpeg")


def call_groq_vision(image_path: str, prompt: str, model: str = None) -> dict:
    """
    Call Groq Vision API with an image and prompt.

    Args:
        image_path: Path to the image file
        prompt: The prompt/question for the vision model
        model: Vision model to use (default: llama-4-scout for speed)

    Returns:
        dict with response and metadata
    """
    start_time = time.time()

    # Get the Groq client
    client = get_groq_client()

    # Encode image
    image_base64 = encode_image_to_base64(image_path)
    mime_type = get_mime_type(image_path)

    # Create data URL
    data_url = f"data:{mime_type};base64,{image_base64}"

    # Select model - Llama 4 models support native vision
    # Scout: faster (~460 tok/s), Maverick: more capable
    if model is None:
        model = "meta-llama/llama-4-scout-17b-16e-instruct"  # Fast multimodal

    # Call Groq Vision API
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": data_url
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ],
        max_tokens=1024,
        temperature=0.3
    )

    latency_ms = int((time.time() - start_time) * 1000)

    return {
        "response": response.choices[0].message.content,
        "model": model,
        "latency_ms": latency_ms,
        "usage": {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }
    }


# === VISION TOOLS ===

@tool
def analyze_image(image_path: str, prompt: Optional[str] = None) -> str:
    """
    Analyze an image using Groq Vision with ~50ms latency.

    This is the PRIMARY tool for image analysis. Use it when you need to:
    - Understand what's in an image
    - Get a general description of a scene
    - Analyze visual content for robotics applications
    - Perform custom analysis with a specific prompt

    The tool uses Groq's Llama 3.2 Vision model optimized for
    real-time robotics with sub-100ms response times.

    Args:
        image_path: Path to the image file (jpg, png, webp, etc.)
        prompt: Optional custom prompt for analysis. If not provided,
                a general analysis is performed.

    Returns:
        JSON string with:
        - success: Whether the analysis succeeded
        - analysis: The vision model's analysis/description
        - latency_ms: Response time in milliseconds
        - model: The model used for analysis

    Example:
        >>> result = analyze_image("/path/to/scene.jpg")
        >>> data = json.loads(result)
        >>> print(data["analysis"])

        >>> result = analyze_image("/path/to/robot.jpg", "What objects can the robot interact with?")
    """
    try:
        # Validate file exists
        if not Path(image_path).exists():
            return json.dumps({
                "success": False,
                "error": f"Image not found: {image_path}"
            })

        # Default prompt for general analysis
        if prompt is None:
            prompt = """Analyze this image in detail. Describe:
1. The main subjects/objects visible
2. The setting/environment
3. Any notable details or features
4. Relevant context for a robotics application (objects that could be manipulated, obstacles, etc.)

Be concise but thorough."""

        # Call Groq Vision
        result = call_groq_vision(image_path, prompt)

        return json.dumps({
            "success": True,
            "analysis": result["response"],
            "latency_ms": result["latency_ms"],
            "model": result["model"],
            "file_processed": str(image_path),
            "usage": result["usage"]
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "file_attempted": str(image_path)
        })


@tool
def describe_scene(image_path: str) -> str:
    """
    Get a detailed scene description optimized for robotics context awareness.

    Use this tool when you need:
    - Spatial understanding of an environment
    - Object locations and relationships
    - Navigation-relevant information
    - Scene layout for robot planning

    The description is structured for robotic systems to understand:
    - What objects are present and where
    - Spatial relationships (left, right, in front, behind)
    - Potential obstacles or hazards
    - Interactable objects

    Args:
        image_path: Path to the image file

    Returns:
        JSON string with:
        - success: Whether the description succeeded
        - scene_description: Detailed scene description
        - objects_detected: List of main objects identified
        - spatial_info: Spatial relationship information
        - latency_ms: Response time

    Example:
        >>> result = describe_scene("/path/to/warehouse.jpg")
        >>> data = json.loads(result)
        >>> print(data["scene_description"])
    """
    try:
        if not Path(image_path).exists():
            return json.dumps({
                "success": False,
                "error": f"Image not found: {image_path}"
            })

        prompt = """You are a vision system for a robot. Analyze this scene and provide:

1. **Scene Overview**: Brief description of the environment type
2. **Objects Detected**: List all visible objects with approximate locations (left, center, right, foreground, background)
3. **Spatial Layout**: Describe the spatial arrangement and relationships between objects
4. **Navigation Info**: Note any obstacles, pathways, or clear areas
5. **Interactable Objects**: Identify objects a robot could potentially manipulate

Format your response in a structured way that's easy for a robotic system to parse."""

        result = call_groq_vision(image_path, prompt)

        return json.dumps({
            "success": True,
            "scene_description": result["response"],
            "latency_ms": result["latency_ms"],
            "model": result["model"],
            "file_processed": str(image_path)
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@tool
def detect_objects(image_path: str) -> str:
    """
    Identify and list objects in an image with descriptions.

    Use this tool when you need:
    - A list of all objects in an image
    - Object identification for robotics tasks
    - Inventory or counting applications
    - Object-specific information

    The tool provides structured object detection results
    optimized for downstream robotic processing.

    Args:
        image_path: Path to the image file

    Returns:
        JSON string with:
        - success: Whether detection succeeded
        - objects: List of detected objects with details
        - object_count: Total number of objects found
        - latency_ms: Response time

    Example:
        >>> result = detect_objects("/path/to/table.jpg")
        >>> data = json.loads(result)
        >>> for obj in data["objects"]:
        ...     print(f"Found: {obj}")
    """
    try:
        if not Path(image_path).exists():
            return json.dumps({
                "success": False,
                "error": f"Image not found: {image_path}"
            })

        prompt = """Identify all objects visible in this image. For each object provide:
- Object name/type
- Approximate location (left, center, right, top, bottom)
- Size estimate (small, medium, large relative to image)
- Any notable characteristics

List the objects in a numbered format. Be thorough but focus on distinct, identifiable objects."""

        result = call_groq_vision(image_path, prompt)

        # Parse the response to extract object list
        response_text = result["response"]

        return json.dumps({
            "success": True,
            "objects_description": response_text,
            "latency_ms": result["latency_ms"],
            "model": result["model"],
            "file_processed": str(image_path)
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@tool
def visual_question(image_path: str, question: str) -> str:
    """
    Answer a specific question about an image (Visual Q&A).

    Use this tool when you need:
    - Answers to specific questions about an image
    - Targeted information extraction
    - Yes/no or factual answers about visual content
    - Clarification about specific aspects of an image

    This is ideal for interactive robotics applications where
    specific information is needed rather than general analysis.

    Args:
        image_path: Path to the image file
        question: The specific question to answer about the image

    Returns:
        JSON string with:
        - success: Whether the Q&A succeeded
        - question: The original question
        - answer: The model's answer
        - latency_ms: Response time

    Example:
        >>> result = visual_question("/path/to/kitchen.jpg", "Is there a red cup on the table?")
        >>> data = json.loads(result)
        >>> print(data["answer"])  # "Yes, there is a red cup on the left side of the table."

        >>> result = visual_question("/path/to/door.jpg", "Is the door open or closed?")
    """
    try:
        if not Path(image_path).exists():
            return json.dumps({
                "success": False,
                "error": f"Image not found: {image_path}"
            })

        if not question or not question.strip():
            return json.dumps({
                "success": False,
                "error": "Question is required"
            })

        prompt = f"""Answer the following question about this image:

Question: {question}

Provide a clear, concise answer. If the question is yes/no, start with Yes or No, then explain briefly."""

        result = call_groq_vision(image_path, prompt)

        return json.dumps({
            "success": True,
            "question": question,
            "answer": result["response"],
            "latency_ms": result["latency_ms"],
            "model": result["model"],
            "file_processed": str(image_path)
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "question": question
        })


# === UTILITY FUNCTIONS ===

def check_groq_vision_status() -> dict:
    """
    Check if Groq Vision API is accessible.
    Use this for health checks.
    """
    return {
        "available": is_groq_available(),
        "model": get_recommended_vision_model("robotics"),
        "service": "Groq Vision",
        "expected_latency": "~50ms"
    }


# === LIST OF ALL TOOLS ===

VIDEO_TOOLS = [
    analyze_image,
    describe_scene,
    detect_objects,
    visual_question,
]


# === TEST ===

if __name__ == "__main__":
    """
    Test the video tools.
    Run: python src/tools/video_tools.py
    """
    print("Groq Vision Tools Test")
    print("=" * 50)

    # Check connection
    status = check_groq_vision_status()
    print(f"\nGroq Vision Available: {status['available']}")
    print(f"Model: {status['model']}")
    print(f"Expected Latency: {status['expected_latency']}")

    if not status['available']:
        print("\nGroq Vision is not available. Please:")
        print("1. Install: pip install groq")
        print("2. Set GROQ_API_KEY in .env")
        exit(1)

    # List available tools
    print("\nAvailable Tools:")
    for tool in VIDEO_TOOLS:
        print(f"  - {tool.name}: {tool.description[:60]}...")
