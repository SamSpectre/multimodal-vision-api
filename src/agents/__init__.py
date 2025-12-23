"""
Multi-Agent System for Document and Video Intelligence

This package implements the LangGraph multi-agent architecture:
- Supervisor Agent: Routes tasks to specialists
- Document Agent: OCR, tables, classification (Mistral)
- Video Agent: Face detection, emotions (Phase 2)

2025 LangChain/LangGraph Patterns:
- Uses create_agent from langchain.agents (NOT deprecated create_react_agent)
- Uses system_prompt parameter (NOT deprecated state_modifier)
- Supports langgraph-supervisor package for high-level orchestration

Usage:
    from src.agents import get_multi_agent_system, invoke_agent

    # Get the full system
    agent = get_multi_agent_system()

    # Or use the convenience function
    result = invoke_agent("Extract text from invoice.pdf")
"""

from .orchestrator import (
    get_multi_agent_system,
    create_multi_agent_system,
    reset_multi_agent_system,
    invoke_agent,
)

from .document_agent import (
    document_agent_node,
    create_standalone_document_agent,
    get_document_agent,  # New: returns the internal agent
)

from .video_agent import (
    video_agent_node,
)

from .supervisor import (
    build_supervisor_graph,
    build_supervisor_with_package,  # New: uses langgraph-supervisor package
)

from .base import (
    AgentState,
    AGENT_NAMES,
    AGENT_DESCRIPTIONS,
)

__all__ = [
    # Main orchestrator
    "get_multi_agent_system",
    "create_multi_agent_system",
    "reset_multi_agent_system",
    "invoke_agent",

    # Agent nodes
    "document_agent_node",
    "video_agent_node",

    # Standalone agents
    "create_standalone_document_agent",
    "get_document_agent",

    # Supervisor building
    "build_supervisor_graph",
    "build_supervisor_with_package",

    # State and types
    "AgentState",
    "AGENT_NAMES",
    "AGENT_DESCRIPTIONS",
]
