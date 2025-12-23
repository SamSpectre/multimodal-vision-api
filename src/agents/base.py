"""
Base Agent Definitions and Shared State

This module defines the shared state and base utilities for the multi-agent system.

LangGraph Multi-Agent Architecture (2025 Latest Patterns):
    - Shared state passes between all agents via TypedDict
    - Each agent can read/write to the state
    - Supervisor controls routing decisions
    - Uses add_messages annotation for automatic message merging
    - Compatible with langgraph-supervisor package

Agent Creation (2025):
    - Use create_agent from langchain.agents (NOT create_react_agent from langgraph.prebuilt)
    - Use system_prompt parameter (NOT deprecated state_modifier)
"""

from typing import Annotated, Sequence, TypedDict, Literal
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    Shared state for the multi-agent system.

    This state is passed between the supervisor and all specialist agents.
    Using TypedDict ensures type safety and clear documentation.

    Attributes:
        messages: Conversation history (automatically merged via add_messages)
        next_agent: Which agent should handle the next step
        current_agent: Which agent is currently processing
        task_type: Classification of the current task
        context: Additional context accumulated during processing
    """
    # Messages with automatic merging (LangGraph pattern)
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # Routing information
    next_agent: str  # "document", "video", "supervisor", "FINISH"
    current_agent: str

    # Task context
    task_type: Literal["document", "video", "general", "unknown"]
    context: dict  # Accumulated results from agents


# Agent names for routing
AGENT_NAMES = Literal["document_agent", "video_agent", "FINISH"]

# Agent descriptions for the supervisor
AGENT_DESCRIPTIONS = {
    "document_agent": """Document Intelligence Specialist - Handles:
        - OCR text extraction from images and PDFs
        - Table detection and extraction
        - Document classification (invoice, receipt, contract, etc.)
        - Multi-page PDF processing
        - Document content analysis
        Use for: "extract text", "read document", "OCR", "what's in this PDF", "classify document"
    """,

    "video_agent": """Video Analysis Specialist - Handles:
        - Video frame extraction and analysis
        - Face detection in video streams
        - Emotion analysis from facial expressions
        - Object detection and tracking
        - People counting
        - Scene understanding
        Use for: "analyze video", "detect faces", "count people", "what's in this video"
    """,
}
