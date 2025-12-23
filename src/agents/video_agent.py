"""
Video Analysis Agent - Specialist Agent (Phase 2)

This agent will handle video processing tasks:
- Video frame extraction
- Face detection (MediaPipe)
- Emotion analysis (GPT-4o Vision)
- Object detection
- People counting

STATUS: PLACEHOLDER - Full implementation in Phase 2

Architecture (Planned):
    AgentState (from supervisor)
         ↓
    ┌─────────────────────────────────┐
    │  Video Agent                     │
    │  ├─ GPT-4o Vision (analysis)    │
    │  └─ Tools:                      │
    │      • extract_frames           │
    │      • detect_faces             │
    │      • analyze_emotions         │
    │      • detect_objects           │
    │      • count_people             │
    └─────────────────────────────────┘
         ↓
    Updated AgentState (with response)

Phase 2 Implementation Plan (Using 2025 LangChain Patterns):
1. Create src/processors/video_processor.py (OpenCV)
2. Create src/models/face_detector.py (MediaPipe)
3. Create src/models/vision_analyzer.py (GPT-4o)
4. Create src/tools/video_tools.py (@tool functions)
5. Implement full video_agent_node using create_agent from langchain.agents
   (NOT deprecated create_react_agent from langgraph.prebuilt)
6. Use system_prompt parameter (NOT deprecated state_modifier)
"""

from langchain_core.messages import AIMessage
from .base import AgentState


VIDEO_AGENT_PROMPT = """You are a Video Analysis Specialist (Coming in Phase 2).

Planned capabilities:
1. **Frame Extraction** - Extract frames from video at specified intervals
2. **Face Detection** - Detect faces in video using MediaPipe
3. **Emotion Analysis** - Analyze facial emotions using GPT-4o Vision
4. **Object Detection** - Identify objects in video frames
5. **People Counting** - Count and track people across frames

Current Status: PLACEHOLDER - Full implementation coming soon.
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

    # Placeholder response
    response_message = AIMessage(
        content=f"""**Video Analysis Agent - Coming Soon (Phase 2)**

I received your request about video analysis:
> {user_request[:200]}{'...' if len(user_request) > 200 else ''}

**Planned Capabilities:**
- Frame extraction from video files
- Face detection using MediaPipe
- Emotion analysis using GPT-4o Vision
- Object detection and tracking
- People counting

**Current Status:** This feature is under development. The multi-agent architecture is in place and ready for Phase 2 implementation.

**Available Now:**
For document processing (OCR, tables, PDFs), please use the Document Intelligence Agent by asking about documents instead.

Stay tuned for video analysis capabilities!
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
