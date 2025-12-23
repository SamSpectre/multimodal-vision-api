"""
Multi-Agent Orchestrator - Main Entry Point

This module creates and manages the complete multi-agent system.
It ties together the supervisor and all specialist agents.

Architecture:
    ┌─────────────────────────────────────────────────────┐
    │                   User Request                       │
    └─────────────────────────────────────────────────────┘
                            ↓
    ┌─────────────────────────────────────────────────────┐
    │                 SUPERVISOR AGENT                     │
    │           (Mistral Large - Routing)                  │
    │                                                      │
    │   Analyzes request → Decides routing → Delegates     │
    └─────────────────────────────────────────────────────┘
                            ↓
         ┌──────────────────┴──────────────────┐
         ↓                                     ↓
    ┌─────────────┐                     ┌─────────────┐
    │  DOCUMENT   │                     │   VIDEO     │
    │   AGENT     │                     │   AGENT     │
    │             │                     │             │
    │ Mistral LLM │                     │ GPT-4o      │
    │ + OCR Tools │                     │ + CV Tools  │
    │             │                     │ (Phase 2)   │
    └─────────────┘                     └─────────────┘
         ↓                                     ↓
    ┌─────────────────────────────────────────────────────┐
    │                    Response                          │
    └─────────────────────────────────────────────────────┘

Latest LangChain/LangGraph Patterns (2025):
    - Uses create_agent from langchain.agents (not deprecated create_react_agent)
    - Supports langgraph-supervisor package for high-level orchestration
    - Tool-calling based handoff between agents
    - system_prompt parameter (replaces deprecated state_modifier)

Usage:
    from src.agents.orchestrator import get_multi_agent_system

    # Get the compiled graph
    agent = get_multi_agent_system()

    # Invoke
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "Extract text from invoice.pdf"}]},
        config={"configurable": {"thread_id": "session-1"}}
    )
"""

from typing import Optional
from langchain_core.messages import HumanMessage

from .supervisor import build_supervisor_graph
from .document_agent import document_agent_node
from .video_agent import video_agent_node
from .base import AgentState


# Singleton for the multi-agent system
_multi_agent_system = None


def create_multi_agent_system(use_memory: bool = True):
    """
    Create the complete multi-agent system.

    This builds a LangGraph with:
    - Supervisor agent for routing
    - Document agent for OCR tasks (using create_agent - latest 2025 API)
    - Video agent for video analysis (placeholder)

    Latest Patterns Used:
    - create_agent from langchain.agents (not deprecated create_react_agent)
    - system_prompt parameter (not deprecated state_modifier)
    - langgraph-supervisor package support (optional)

    Args:
        use_memory: Whether to enable conversation memory

    Returns:
        Compiled LangGraph multi-agent system
    """
    print("[Orchestrator] Building multi-agent system (2025 patterns)...")
    print("  - Supervisor Agent (routing)")
    print("  - Document Agent (Mistral OCR 3 + create_agent)")
    print("  - Video Agent (Phase 2 placeholder)")

    graph = build_supervisor_graph(
        document_agent_node=document_agent_node,
        video_agent_node=video_agent_node,
        use_memory=use_memory,
    )

    print("[Orchestrator] Multi-agent system ready!")
    return graph


def get_multi_agent_system(use_memory: bool = True):
    """
    Get or create the singleton multi-agent system.

    Args:
        use_memory: Whether to enable conversation memory

    Returns:
        Compiled LangGraph multi-agent system
    """
    global _multi_agent_system

    if _multi_agent_system is None:
        _multi_agent_system = create_multi_agent_system(use_memory)

    return _multi_agent_system


def reset_multi_agent_system():
    """Reset the singleton multi-agent system."""
    global _multi_agent_system
    _multi_agent_system = None
    print("[Orchestrator] Multi-agent system reset")


def invoke_agent(
    message: str,
    thread_id: str = "default",
    return_full_state: bool = False,
) -> str:
    """
    Convenience function to invoke the multi-agent system.

    Args:
        message: User message
        thread_id: Conversation thread ID for memory
        return_full_state: If True, return full state dict; if False, return response string

    Returns:
        Agent response string (or full state dict if return_full_state=True)
    """
    agent = get_multi_agent_system()

    # Build initial state
    initial_state = {
        "messages": [HumanMessage(content=message)],
        "next_agent": "",
        "current_agent": "",
        "task_type": "unknown",
        "context": {},
    }

    # Invoke the agent
    result = agent.invoke(
        initial_state,
        config={"configurable": {"thread_id": thread_id}}
    )

    if return_full_state:
        return result

    # Extract response string from the result
    messages = result.get("messages", [])
    if messages:
        last_message = messages[-1]
        if hasattr(last_message, 'content'):
            return last_message.content
        return str(last_message)

    return "No response from agent"


# For testing
if __name__ == "__main__":
    import sys

    print("=" * 70)
    print("MULTI-AGENT ORCHESTRATOR - Test")
    print("=" * 70)
    print()

    # Test queries
    test_queries = [
        "What can you help me with?",
        "Extract text from invoice.pdf",
        "Analyze video.mp4 for faces",
    ]

    agent = get_multi_agent_system()

    for query in test_queries:
        print(f"\n{'='*70}")
        print(f"USER: {query}")
        print("-" * 70)

        result = invoke_agent(query, thread_id="test")

        # Get the final response
        messages = result.get("messages", [])
        if messages:
            response = messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])
            print(f"AGENT: {response[:500]}...")
        else:
            print("AGENT: No response")

        print(f"Routed to: {result.get('current_agent', 'unknown')}")
        print(f"Task type: {result.get('task_type', 'unknown')}")

    print("\n" + "=" * 70)
    print("[SUCCESS] Multi-agent system is working!")
    print("=" * 70)
