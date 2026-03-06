"""
Video Analysis Schemas

Pydantic models for video/image analysis endpoints.

=== VIDEO ANALYSIS API ===

These endpoints provide image analysis capabilities optimized for
robotics applications with ~50ms latency via Groq Vision.

Endpoints:
- /analyze: Full image analysis
- /describe: Scene description for robotics
- /objects: Object detection
- /ask: Visual question answering
"""

from typing import Optional, List, Any

from pydantic import BaseModel, Field, field_validator, ConfigDict


class ImageRequest(BaseModel):
    """
    Request model for image analysis endpoints.

    Clients can provide an image in multiple ways:
    1. image_base64: Base64 encoded image content
    2. image_url: URL to download the image from
    3. image_path: Path on server (for on-premise deployments)

    At least one of these must be provided.
    """
    # Image source (one required)
    image_base64: Optional[str] = Field(
        None,
        description="Base64 encoded image (jpg, png, webp)",
        min_length=10,
    )
    image_url: Optional[str] = Field(
        None,
        description="URL to download the image from",
        pattern=r"^https?://.*",
    )
    image_path: Optional[str] = Field(
        None,
        description="Server file path (on-premise only)"
    )

    # Optional analysis parameters
    prompt: Optional[str] = Field(
        None,
        description="Custom prompt for analysis (for /analyze endpoint)",
        max_length=2000
    )

    # Validation: At least one source must be provided
    @field_validator('image_path', mode='after')
    @classmethod
    def validate_source_provided(cls, v, info):
        """Ensure at least one image source is provided."""
        values = info.data
        if not v and not values.get('image_base64') and not values.get('image_url'):
            raise ValueError(
                'At least one of image_base64, image_url, or image_path must be provided'
            )
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
                "prompt": "Describe what objects a robot could interact with"
            }
        }
    )


class VisualQuestionRequest(BaseModel):
    """
    Request model for visual question answering endpoint.

    Requires an image source and a specific question.
    """
    # Image source (one required)
    image_base64: Optional[str] = Field(
        None,
        description="Base64 encoded image",
        min_length=10,
    )
    image_url: Optional[str] = Field(
        None,
        description="URL to download the image from",
        pattern=r"^https?://.*",
    )
    image_path: Optional[str] = Field(
        None,
        description="Server file path"
    )

    # Question (required)
    question: str = Field(
        ...,
        description="The question to answer about the image",
        min_length=3,
        max_length=500
    )

    @field_validator('image_path', mode='after')
    @classmethod
    def validate_source_provided(cls, v, info):
        """Ensure at least one image source is provided."""
        values = info.data
        if not v and not values.get('image_base64') and not values.get('image_url'):
            raise ValueError(
                'At least one of image_base64, image_url, or image_path must be provided'
            )
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "image_path": "/path/to/scene.jpg",
                "question": "Is there a red cup on the table?"
            }
        }
    )


class AnalysisResult(BaseModel):
    """
    Result from image analysis.
    """
    success: bool = Field(..., description="Whether analysis succeeded")
    analysis: str = Field(
        ...,
        description="The analysis/description from the vision model"
    )
    latency_ms: int = Field(
        ...,
        ge=0,
        description="Response time in milliseconds"
    )
    model: str = Field(
        "llama-3.2-11b-vision-preview",
        description="Vision model used"
    )
    provider: str = Field(
        "groq",
        description="API provider (groq or openai)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "analysis": "The image shows a warehouse environment with shelving units on the left and right sides. In the center, there is a clear pathway...",
                "latency_ms": 52,
                "model": "llama-3.2-11b-vision-preview",
                "provider": "groq"
            }
        }
    )


class SceneDescription(BaseModel):
    """
    Scene description optimized for robotics.
    """
    success: bool = Field(..., description="Whether description succeeded")
    scene_description: str = Field(
        ...,
        description="Detailed scene description with spatial information"
    )
    latency_ms: int = Field(..., ge=0, description="Response time in ms")
    model: str = Field(..., description="Vision model used")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "scene_description": "**Scene Overview**: Indoor warehouse environment\n\n**Objects Detected**:\n- Shelving unit (left, large)\n- Boxes (center, medium, stacked)\n- Forklift (right, large)\n\n**Spatial Layout**: Clear central pathway...",
                "latency_ms": 48,
                "model": "llama-3.2-11b-vision-preview"
            }
        }
    )


class ObjectDetectionResult(BaseModel):
    """
    Result from object detection.
    """
    success: bool = Field(..., description="Whether detection succeeded")
    objects_description: str = Field(
        ...,
        description="Detected objects with locations and characteristics"
    )
    latency_ms: int = Field(..., ge=0, description="Response time in ms")
    model: str = Field(..., description="Vision model used")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "objects_description": "1. Table (center, large) - wooden, rectangular\n2. Red cup (left on table, small)\n3. Laptop (center on table, medium)\n4. Chair (foreground, medium) - office chair, black",
                "latency_ms": 45,
                "model": "llama-3.2-11b-vision-preview"
            }
        }
    )


class VisualQuestionResult(BaseModel):
    """
    Result from visual question answering.
    """
    success: bool = Field(..., description="Whether Q&A succeeded")
    question: str = Field(..., description="The original question")
    answer: str = Field(..., description="The model's answer")
    latency_ms: int = Field(..., ge=0, description="Response time in ms")
    model: str = Field(..., description="Vision model used")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "question": "Is there a red cup on the table?",
                "answer": "Yes, there is a red cup on the left side of the table, next to the laptop.",
                "latency_ms": 41,
                "model": "llama-3.2-11b-vision-preview"
            }
        }
    )


class VideoAnalysisResponse(BaseModel):
    """
    Standard response wrapper for video/image analysis endpoints.
    """
    success: bool = Field(..., description="Whether the request succeeded")
    data: dict = Field(..., description="Analysis results")
    meta: dict = Field(
        ...,
        description="Metadata including latency, model, provider"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if success is False"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "data": {
                    "analysis": "The image shows...",
                },
                "meta": {
                    "latency_ms": 52,
                    "model": "llama-3.2-11b-vision-preview",
                    "provider": "groq"
                },
                "error": None
            }
        }
    )


class VideoServiceStatus(BaseModel):
    """
    Status of the video analysis service.
    """
    service: str = Field("Video Analysis", description="Service name")
    status: str = Field(..., description="Service status")
    provider: str = Field(..., description="Current vision provider")
    model: str = Field(..., description="Current vision model")
    expected_latency: str = Field(..., description="Expected response latency")
    available: bool = Field(..., description="Whether service is available")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "service": "Video Analysis",
                "status": "available",
                "provider": "groq",
                "model": "llama-3.2-11b-vision-preview",
                "expected_latency": "~50ms",
                "available": True
            }
        }
    )
