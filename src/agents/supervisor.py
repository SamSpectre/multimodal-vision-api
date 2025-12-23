"""
Supervisor Agent - Multi-Agent Orchestration

This implements the LangGraph Supervisor pattern for multi-agent systems.
The supervisor analyzes incoming requests and routes them to specialist agents.

Architecture:
    User Request
         ↓
    ┌─────────────┐
    │ Supervisor  │ ← Mistral LLM decides routing
    └─────────────┘
         ↓
    ┌────┴────┐
    ↓         ↓
┌─────────┐ ┌─────────┐
│Document │ │ Video   │  ← Specialist Agents
│ Agent   │ │ Agent   │
└─────────┘ └─────────┘
         ↓
    Response

LangGraph Pattern Used (2025 Latest):
    - Using langgraph-supervisor package for hierarchical multi-agent systems
    - create_supervisor() for high-level orchestration
    - Fallback to manual StateGraph for fine-grained control
    - Supervisor node makes routing decisions via tool calling (handoff pattern)
    - Specialist agents process tasks
    - Results flow back through supervisor
"""

import os
from typing import Literal, List, Callable
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_mistralai import ChatMistralAI
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .base import AgentState, AGENT_NAMES, AGENT_DESCRIPTIONS

# Try to import langgraph-supervisor (latest 2025 pattern)
try:
    from langgraph_supervisor import create_supervisor
    HAS_SUPERVISOR_PACKAGE = True
except ImportError:
    HAS_SUPERVISOR_PACKAGE = False


def get_supervisor_llm():
    """Get the LLM for the supervisor agent."""
    api_key = os.getenv("MISTRAL_API_KEY")
    if api_key and api_key != "your_mistral_api_key_here":
        return ChatMistralAI(
            model="mistral-large-latest",
            temperature=0.1,
            api_key=api_key,
        )

    # Fallback to OpenAI if Mistral not available
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return ChatOpenAI(
            model="gpt-4o",
            temperature=0.1,
            api_key=api_key,
        )

    raise ValueError("No LLM API key configured (MISTRAL_API_KEY or OPENAI_API_KEY)")


SUPERVISOR_SYSTEM_PROMPT = """You are a Supervisor Agent that routes user requests to specialist agents.

Your role is to:
1. Analyze the user's request
2. Determine which specialist agent should handle it
3. Route to the appropriate agent

Available Specialist Agents:

{agent_descriptions}

Routing Rules:
- For document processing, OCR, PDF, text extraction → route to "document_agent"
- For video analysis, face detection, emotion analysis → route to "video_agent"
- If the task is complete or needs no specialist → respond with "FINISH"

IMPORTANT: You must respond with ONLY the agent name to route to:
- "document_agent" - for document/OCR tasks
- "video_agent" - for video/face/emotion tasks
- "FINISH" - if you can answer directly or task is complete

Do not explain your routing decision. Just output the agent name.
"""


def create_supervisor_node(llm):
    """
    Create the supervisor node function.

    The supervisor analyzes messages and decides which agent to route to.
    """
    def supervisor_node(state: AgentState) -> AgentState:
        """Supervisor decides which agent should handle the request."""

        # Build the system prompt with agent descriptions
        agent_desc_text = "\n\n".join([
            f"**{name}**:\n{desc}"
            for name, desc in AGENT_DESCRIPTIONS.items()
        ])

        system_prompt = SUPERVISOR_SYSTEM_PROMPT.format(
            agent_descriptions=agent_desc_text
        )

        # Get the last user message
        messages = state.get("messages", [])
        if not messages:
            return {
                **state,
                "next_agent": "FINISH",
                "current_agent": "supervisor"
            }

        # Ask LLM to route
        routing_messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Route this request: {messages[-1].content}")
        ]

        response = llm.invoke(routing_messages)
        routing_decision = response.content.strip().lower()

        # Parse the routing decision
        if "document" in routing_decision:
            next_agent = "document_agent"
            task_type = "document"
        elif "video" in routing_decision:
            next_agent = "video_agent"
            task_type = "video"
        elif "finish" in routing_decision:
            next_agent = "FINISH"
            task_type = "general"
        else:
            # Default to document agent for unclear requests
            next_agent = "document_agent"
            task_type = "unknown"

        return {
            **state,
            "next_agent": next_agent,
            "current_agent": "supervisor",
            "task_type": task_type,
        }

    return supervisor_node


def route_to_agent(state: AgentState) -> str:
    """
    Conditional routing function for the graph.

    Returns the name of the next node to execute.
    """
    next_agent = state.get("next_agent", "FINISH")

    if next_agent == "FINISH":
        return END
    elif next_agent == "document_agent":
        return "document_agent"
    elif next_agent == "video_agent":
        return "video_agent"
    else:
        return END


def build_supervisor_with_package(
    agents: List,
    use_memory: bool = True,
):
    """
    Build supervisor using langgraph-supervisor package (2025 recommended approach).

    This uses the high-level create_supervisor() API which:
    - Automatically handles handoff between agents via tool calling
    - Manages agent state and message flow
    - Provides cleaner abstraction for multi-agent systems

    Args:
        agents: List of agent graphs/runnables to coordinate
        use_memory: Whether to enable conversation memory

    Returns:
        Compiled supervisor workflow
    """
    if not HAS_SUPERVISOR_PACKAGE:
        raise ImportError(
            "langgraph-supervisor package not installed. "
            "Install with: pip install langgraph-supervisor"
        )

    llm = get_supervisor_llm()
    checkpointer = MemorySaver() if use_memory else None

    # Build agent descriptions for supervisor prompt
    agent_desc = "\n".join([
        f"- {name}: {desc.strip()}"
        for name, desc in AGENT_DESCRIPTIONS.items()
    ])

    supervisor_prompt = f"""You are a supervisor coordinating specialist agents.

Available Agents:
{agent_desc}

Route requests to the appropriate agent based on the task type.
- Document/OCR/PDF tasks → document_agent
- Video/face/emotion tasks → video_agent
"""

    # Create supervisor using the package
    workflow = create_supervisor(
        agents=agents,
        model=llm,
        prompt=supervisor_prompt,
    )

    return workflow.compile(checkpointer=checkpointer)


def build_supervisor_graph(
    document_agent_node,
    video_agent_node=None,
    use_memory: bool = True,
):
    """
    Build the multi-agent supervisor graph.

    This creates a LangGraph StateGraph with:
    - Supervisor node for routing decisions
    - Document agent node for document processing
    - Video agent node for video analysis (optional)

    NOTE: This is the manual approach. For simpler setups, consider using
    build_supervisor_with_package() with the langgraph-supervisor package.

    Args:
        document_agent_node: Function that processes document tasks
        video_agent_node: Function that processes video tasks (optional)
        use_memory: Whether to enable conversation memory

    Returns:
        Compiled LangGraph
    """
    # Get the supervisor LLM
    llm = get_supervisor_llm()

    # Create the supervisor node
    supervisor = create_supervisor_node(llm)

    # Build the graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("supervisor", supervisor)
    workflow.add_node("document_agent", document_agent_node)

    if video_agent_node:
        workflow.add_node("video_agent", video_agent_node)

    # Set entry point
    workflow.set_entry_point("supervisor")

    # Add conditional routing from supervisor
    if video_agent_node:
        workflow.add_conditional_edges(
            "supervisor",
            route_to_agent,
            {
                "document_agent": "document_agent",
                "video_agent": "video_agent",
                END: END,
            }
        )
    else:
        workflow.add_conditional_edges(
            "supervisor",
            route_to_agent,
            {
                "document_agent": "document_agent",
                END: END,
            }
        )

    # After specialist agents, route back to supervisor or end
    workflow.add_edge("document_agent", END)

    if video_agent_node:
        workflow.add_edge("video_agent", END)

    # Set up memory
    checkpointer = MemorySaver() if use_memory else None

    # Compile the graph
    return workflow.compile(checkpointer=checkpointer)
