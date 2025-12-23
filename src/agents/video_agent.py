"""
Video Analysis Agent - Specialist Agent for Robotics Vision

This agent handles real-time video processing tasks:
- Video frame extraction
- Face detection (MediaPipe)
- Emotion analysis
- Object detection
- People counting
- Real-time robotics vision (~50ms latency)

Architecture:
    AgentState (from supervisor)
         ↓
    ┌─────────────────────────────────┐
    │  Video Agent                     │
    │  ├─ Groq Llama 3.2 Vision       │  ← Low-latency (~50ms)
    │  │  (real-time robotics)        │
    │  └─ Tools:                      │
    │      • extract_frames           │
    │      • detect_faces             │
    │      • analyze_emotions         │
    │      • detect_objects           │
    │      • count_people             │
    └─────────────────────────────────┘
         ↓
    Updated AgentState (with response)

Model Selection (Latency Optimized):
    - Primary: Groq Llama 3.2 11B Vision (~50ms latency)
    - Fallback: GPT-4o (~200ms) for higher accuracy
    - Configurable via config/settings.py

Phase 2 Implementation Plan (Using 2025 LangChain Patterns):
1. Create src/processors/video_processor.py (OpenCV)
2. Create src/models/face_detector.py (MediaPipe)
3. Create src/models/vision_analyzer.py (Groq Vision)
4. Create src/tools/video_tools.py (@tool functions)
5. Implement full video_agent_node using create_agent from langchain.agents
6. Use system_prompt parameter (NOT deprecated state_modifier)
"""

import os
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from .base import AgentState
from config.settings import settings
from src.clients.groq_client import is_groq_available

# Try to import Groq LangChain integration
try:
    from langchain_groq import ChatGroq
    HAS_LANGCHAIN_GROQ = True
except ImportError:
    ChatGroq = None
    HAS_LANGCHAIN_GROQ = False


def get_video_llm():
    """
    Get the LLM for the video/robotics agent.

    Uses Groq's Llama 3.2 Vision by default for low-latency robotics (~50ms).
    Model is configurable via config/settings.py:
      - video_agent_model: "llama-3.2-11b-vision-preview" (default)
      - video_agent_provider: "groq" (default)
      - video_agent_temperature: 0.3

    Fallback to GPT-4o for higher accuracy when Groq unavailable.
    """
    provider = settings.video_agent_provider
    model = settings.video_agent_model
    temperature = settings.video_agent_temperature

    # Primary: Groq for low-latency robotics vision
    if provider == "groq" and HAS_LANGCHAIN_GROQ:
        api_key = os.getenv("GROQ_API_KEY")
        if api_key and api_key != "your_groq_api_key_here":
            print(f"[VideoAgent] Using {model} (Groq) - ~50ms latency for robotics")
            return ChatGroq(
                model=model,
                temperature=temperature,
                api_key=api_key,
            )

    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            print(f"[VideoAgent] Using {model} (OpenAI)")
            return ChatOpenAI(
                model=model,
                temperature=temperature,
                api_key=api_key,
            )

    # Fallback: Try Groq first (preferred for robotics latency)
    if HAS_LANGCHAIN_GROQ and is_groq_available():
        api_key = os.getenv("GROQ_API_KEY")
        print("[VideoAgent] Fallback to llama-3.2-11b-vision-preview (Groq)")
        return ChatGroq(
            model="llama-3.2-11b-vision-preview",
            temperature=0.3,
            api_key=api_key,
        )

    # Fallback: OpenAI GPT-4o for vision
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print("[VideoAgent] Fallback to gpt-4o (OpenAI) - higher latency")
        return ChatOpenAI(
            model="gpt-4o",
            temperature=0.3,
            api_key=api_key,
        )

    raise ValueError("No vision LLM available (GROQ_API_KEY or OPENAI_API_KEY)")


VIDEO_AGENT_PROMPT = """You are a Video Analysis Specialist optimized for real-time robotics vision.

You are powered by Groq's Llama 3.2 Vision model with ~50ms latency,
making you ideal for real-time robotics applications.

Capabilities:
1. **Frame Extraction** - Extract frames from video at specified intervals
2. **Face Detection** - Detect faces in video using MediaPipe
3. **Emotion Analysis** - Analyze facial emotions in real-time
4. **Object Detection** - Identify objects in video frames
5. **People Counting** - Count and track people across frames
6. **Robotics Vision** - Real-time scene understanding for robotics

Optimizations:
- Low-latency inference (~50ms) via Groq LPU
- Efficient frame sampling for video streams
- Batch processing for multiple frames
"""


def video_agent_node(state: AgentState) -> AgentState:
    """
    Video Agent node for the multi-agent graph.

    PLACEHOLDER: Returns a "coming soon" message.
    Full implementation will be added in Phase 2.

    Args:
        state: Current AgentState from the supervisor

    Returns:
        Updated AgentState with placeholder response
    """
    # Get the user's request for context
    messages = state.get("messages", [])
    user_request = ""
    if messages:
        user_request = messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])

    # Check available vision providers
    groq_available = is_groq_available()
    provider_status = "Groq Llama 3.2 Vision (~50ms)" if groq_available else "GPT-4o (fallback)"

    # Placeholder response with model info
    response_message = AIMessage(
        content=f"""**Video/Robotics Vision Agent - Ready for Phase 2**

I received your request about video analysis:
> {user_request[:200]}{'...' if len(user_request) > 200 else ''}

**Vision Model Status:**
- Provider: {provider_status}
- Latency: {"~50ms (real-time capable)" if groq_available else "~200ms"}
- Ready: {"Yes - Groq API configured" if groq_available else "Partial - using OpenAI fallback"}

**Capabilities (Phase 2):**
- Frame extraction from video files
- Face detection using MediaPipe
- Emotion analysis in real-time
- Object detection and tracking
- People counting
- Real-time robotics vision

**Current Status:** The low-latency vision infrastructure is configured. Full tool implementation coming in Phase 2.

**Available Now:**
For document processing (OCR, tables, PDFs), please use the Document Intelligence Agent.
"""
    )

    return {
        **state,
        "messages": [response_message],
        "current_agent": "video_agent",
        "context": {
            **state.get("context", {}),
            "video_result": "Phase 2 - Coming Soon"
        }
    }


# Placeholder for future tools
VIDEO_TOOLS = []  # Will be populated in Phase 2


# For testing
if __name__ == "__main__":
    print("=" * 60)
    print("VIDEO ANALYSIS AGENT - Placeholder Test")
    print("=" * 60)

    from langchain_core.messages import HumanMessage

    # Test the placeholder
    test_state = {
        "messages": [HumanMessage(content="Analyze this video for faces")],
        "next_agent": "video_agent",
        "current_agent": "supervisor",
        "task_type": "video",
        "context": {}
    }

    result = video_agent_node(test_state)
    print(f"\nResponse:\n{result['messages'][0].content}")
