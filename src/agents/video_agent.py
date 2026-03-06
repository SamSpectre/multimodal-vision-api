"""
Video Analysis Agent - Specialist Agent for Robotics Vision

This agent handles real-time video and image processing tasks:
- Image analysis and scene understanding
- Object detection and identification
- Visual question answering
- Scene description for robotics

Architecture:
    AgentState (from supervisor)
         ↓
    ┌─────────────────────────────────┐
    │  Video Agent                     │
    │  ├─ Groq Llama 3.2 Vision       │  ← Low-latency (~50ms)
    │  │  (real-time robotics)        │
    │  └─ Tools:                      │
    │      • analyze_image            │
    │      • describe_scene           │
    │      • detect_objects           │
    │      • visual_question          │
    └─────────────────────────────────┘
         ↓
    Updated AgentState (with response)

Model Selection (Latency Optimized):
    - Primary: Groq Llama 3.2 11B Vision (~50ms latency)
    - Fallback: GPT-4o (~200ms) for higher accuracy
    - Configurable via config/settings.py

This agent uses LangChain's create_agent (latest 2025 API) for tool calling,
wrapped to work within the multi-agent supervisor system.
"""

import os
from typing import Optional

from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent

from .base import AgentState
from src.tools.video_tools import VIDEO_TOOLS
from config.settings import settings
from src.clients.groq_client import is_groq_available

# Try to import Groq LangChain integration
try:
    from langchain_groq import ChatGroq
    HAS_LANGCHAIN_GROQ = True
except ImportError:
    ChatGroq = None
    HAS_LANGCHAIN_GROQ = False


VIDEO_AGENT_PROMPT = """You are a Video Analysis Specialist optimized for real-time robotics vision.

You are powered by Groq's Llama 3.2 Vision model with ~50ms latency,
making you ideal for real-time robotics applications.

Your expertise:
1. **Image Analysis** - Analyze images for scene understanding and content
2. **Scene Description** - Provide detailed spatial descriptions for robotics
3. **Object Detection** - Identify and locate objects in images
4. **Visual Q&A** - Answer specific questions about visual content

Available Tools:
- `analyze_image`: Primary tool for image analysis (custom prompts supported)
- `describe_scene`: Get robotics-optimized scene descriptions with spatial info
- `detect_objects`: List all objects with locations and characteristics
- `visual_question`: Answer specific yes/no or factual questions about images

Guidelines:
- For general understanding → use `analyze_image`
- For spatial/navigation info → use `describe_scene`
- For object identification → use `detect_objects`
- For specific questions → use `visual_question`

When you receive an image path, use the appropriate tool to analyze it.
Provide clear, actionable insights for robotic systems.
If no image path is provided, ask the user to provide one.

Note: All responses are optimized for low latency (~50ms) to support real-time robotics.
"""


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
    # Note: Llama 4 models now support native vision (multimodal)
    if provider == "groq" and HAS_LANGCHAIN_GROQ:
        api_key = os.getenv("GROQ_API_KEY")
        if api_key and api_key != "your_groq_api_key_here":
            # Use Llama 4 Scout for fast multimodal (vision) tasks
            groq_model = "meta-llama/llama-4-scout-17b-16e-instruct"
            print(f"[VideoAgent] Using {groq_model} (Groq) - fast multimodal")
            return ChatGroq(
                model=groq_model,
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
        print("[VideoAgent] Fallback to Llama 4 Scout (Groq)")
        return ChatGroq(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
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


# Singleton for the internal video agent
_video_agent = None


def get_video_agent():
    """
    Get or create the internal agent for video processing.

    Uses the latest LangChain create_agent API (2025):
    - model: The LLM to use for reasoning
    - tools: List of tools the agent can invoke
    - system_prompt: System message (replaces deprecated state_modifier)
    """
    global _video_agent

    if _video_agent is None:
        llm = get_video_llm()
        _video_agent = create_agent(
            model=llm,
            tools=VIDEO_TOOLS,
            system_prompt=VIDEO_AGENT_PROMPT,
        )

    return _video_agent


def reset_video_agent():
    """Reset the singleton video agent (for testing or config changes)."""
    global _video_agent
    _video_agent = None


def video_agent_node(state: AgentState) -> AgentState:
    """
    Video Agent node for the multi-agent graph.

    This wraps the agent to work within the supervisor system.

    Args:
        state: Current AgentState from the supervisor

    Returns:
        Updated AgentState with the video agent's response
    """
    # Get the internal agent
    agent = get_video_agent()

    # Get messages from state
    messages = state.get("messages", [])

    if not messages:
        # No messages to process
        response_message = AIMessage(
            content="I'm the Video Analysis Agent optimized for robotics (~50ms latency). Please provide an image path to analyze or ask about my capabilities."
        )
        return {
            **state,
            "messages": [response_message],
            "current_agent": "video_agent",
        }

    # Invoke the agent with the messages
    try:
        result = agent.invoke({
            "messages": messages
        })

        # Extract the response messages
        response_messages = result.get("messages", [])

        # Get the last AI message as the response
        ai_messages = [m for m in response_messages if isinstance(m, AIMessage)]
        if ai_messages:
            final_response = ai_messages[-1]
        else:
            final_response = AIMessage(content="Image analysis completed.")

        return {
            **state,
            "messages": [final_response],
            "current_agent": "video_agent",
            "context": {
                **state.get("context", {}),
                "video_result": final_response.content
            }
        }

    except Exception as e:
        error_message = AIMessage(
            content=f"Video analysis error: {str(e)}. Please ensure the image path is correct and the file exists."
        )
        return {
            **state,
            "messages": [error_message],
            "current_agent": "video_agent",
        }


# Standalone agent for direct use (without supervisor)
def create_standalone_video_agent(use_memory: bool = True):
    """
    Create a standalone Video Agent for direct use.

    This can be used without the supervisor for simple video/image tasks.
    Uses the latest LangChain create_agent API (2025).

    Returns:
        Compiled LangGraph agent
    """
    from langgraph.checkpoint.memory import MemorySaver

    llm = get_video_llm()
    checkpointer = MemorySaver() if use_memory else None

    return create_agent(
        model=llm,
        tools=VIDEO_TOOLS,
        system_prompt=VIDEO_AGENT_PROMPT,
        checkpointer=checkpointer,
    )


# For testing
if __name__ == "__main__":
    print("=" * 60)
    print("VIDEO ANALYSIS AGENT - Standalone Test")
    print("=" * 60)

    # Check Groq availability
    print(f"\nGroq Available: {is_groq_available()}")
    print(f"LangChain Groq: {HAS_LANGCHAIN_GROQ}")

    if not is_groq_available():
        print("\nGroq is not available. Check:")
        print("  1. Is groq installed? pip install groq langchain-groq")
        print("  2. Is GROQ_API_KEY set in .env?")
        print("\nFalling back to OpenAI if available...")

    try:
        agent = create_standalone_video_agent()

        test_query = "What types of images can you analyze?"
        print(f"\nUser: {test_query}")

        result = agent.invoke(
            {"messages": [HumanMessage(content=test_query)]},
            config={"configurable": {"thread_id": "test"}}
        )

        print(f"\nAgent: {result['messages'][-1].content}")

    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure GROQ_API_KEY or OPENAI_API_KEY is set in your .env file")
