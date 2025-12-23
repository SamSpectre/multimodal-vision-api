"""
Multi-Agent System Router - FastAPI Endpoints

Provides endpoints for interacting with the LangGraph multi-agent system.
The supervisor automatically routes requests to the appropriate specialist agent.

Architecture:
    POST /chat → Supervisor → [Document Agent | Video Agent] → Response

Endpoints:
    POST /chat      - Chat with the multi-agent system
    POST /stream    - Stream responses (SSE)
    GET  /status    - Check system status
    POST /reset     - Reset agent memory
"""

import json
import uuid
from typing import Optional, List
from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from langchain_core.messages import HumanMessage, AIMessage

from src.agents import (
    get_multi_agent_system,
    reset_multi_agent_system,
    AGENT_DESCRIPTIONS,
)
from src.clients.mistral_client import is_mistral_available
from src.clients.groq_client import is_groq_available
from config.settings import settings


router = APIRouter()


# === SCHEMAS ===

class AgentChatRequest(BaseModel):
    """Request to chat with the multi-agent system."""
    message: str = Field(..., description="User message")
    thread_id: Optional[str] = Field(
        default=None,
        description="Conversation thread ID. Auto-generated if not provided."
    )


class AgentChatResponse(BaseModel):
    """Response from the multi-agent system."""
    response: str = Field(..., description="Agent's response")
    thread_id: str = Field(..., description="Conversation thread ID")
    routed_to: str = Field(..., description="Which specialist agent handled the request")
    task_type: str = Field(..., description="Classified task type")


class AgentStatusResponse(BaseModel):
    """Multi-agent system status."""
    status: str
    supervisor: dict
    agents: dict


# === ENDPOINTS ===

@router.post("/chat", response_model=AgentChatResponse)
async def chat_with_agent(request: AgentChatRequest):
    """
    Chat with the Multi-Agent System.

    The supervisor analyzes your request and routes it to the appropriate
    specialist agent:

    - **Document tasks** → Document Intelligence Agent (Mistral OCR 3)
      - "Extract text from invoice.pdf"
      - "What's in this document?"
      - "Get tables from spreadsheet.png"

    - **Video tasks** → Video Analysis Agent (Coming in Phase 2)
      - "Analyze this video for faces"
      - "Count people in video.mp4"
      - "Detect emotions in the video"

    The system maintains conversation memory per thread_id.
    """
    try:
        # Check if Mistral is available
        if not is_mistral_available():
            raise HTTPException(
                status_code=503,
                detail="Mistral API not available. Check MISTRAL_API_KEY."
            )

        # Get the multi-agent system
        agent = get_multi_agent_system()

        # Generate thread ID if not provided
        thread_id = request.thread_id or str(uuid.uuid4())

        # Build initial state
        initial_state = {
            "messages": [HumanMessage(content=request.message)],
            "next_agent": "",
            "current_agent": "",
            "task_type": "unknown",
            "context": {},
        }

        # Invoke the multi-agent system
        result = agent.invoke(
            initial_state,
            config={"configurable": {"thread_id": thread_id}}
        )

        # Extract response
        messages = result.get("messages", [])
        if not messages:
            raise HTTPException(status_code=500, detail="No response from agent")

        # Get the last message
        last_message = messages[-1]
        response_content = (
            last_message.content
            if hasattr(last_message, 'content')
            else str(last_message)
        )

        return AgentChatResponse(
            response=response_content,
            thread_id=thread_id,
            routed_to=result.get("current_agent", "unknown"),
            task_type=result.get("task_type", "unknown"),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {str(e)}"
        )


@router.post("/stream")
async def stream_agent_response(request: AgentChatRequest):
    """
    Stream responses from the Multi-Agent System.

    Uses Server-Sent Events (SSE) to stream the agent's response
    in real-time. Useful for long-running document processing.

    Events:
    - `{"type": "routing", "agent": "..."}` - Routing decision
    - `{"type": "message", "content": "..."}` - Response content
    - `{"type": "done", "thread_id": "..."}` - Completion
    - `{"type": "error", "message": "..."}` - Error
    """
    try:
        if not is_mistral_available():
            raise HTTPException(
                status_code=503,
                detail="Mistral API not available"
            )

        agent = get_multi_agent_system()
        thread_id = request.thread_id or str(uuid.uuid4())

        async def generate():
            try:
                initial_state = {
                    "messages": [HumanMessage(content=request.message)],
                    "next_agent": "",
                    "current_agent": "",
                    "task_type": "unknown",
                    "context": {},
                }

                # Stream the agent response
                for event in agent.stream(
                    initial_state,
                    config={"configurable": {"thread_id": thread_id}},
                    stream_mode="values"
                ):
                    # Send routing info
                    current_agent = event.get("current_agent")
                    if current_agent:
                        yield f"data: {json.dumps({'type': 'routing', 'agent': current_agent})}\n\n"

                    # Send messages
                    messages = event.get("messages", [])
                    for msg in messages:
                        if hasattr(msg, 'content') and msg.content:
                            yield f"data: {json.dumps({'type': 'message', 'content': msg.content})}\n\n"

                # Completion
                yield f"data: {json.dumps({'type': 'done', 'thread_id': thread_id})}\n\n"

            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=AgentStatusResponse)
async def get_agent_status():
    """
    Get Multi-Agent System status.

    Returns information about:
    - System availability
    - Supervisor configuration (model, provider, latency)
    - Available specialist agents and their capabilities
    - Model selection optimized for cost/latency
    """
    # Determine overall availability
    mistral_ok = is_mistral_available()
    groq_ok = is_groq_available()

    return AgentStatusResponse(
        status="available" if mistral_ok else "partial",
        supervisor={
            "model": settings.supervisor_model,
            "provider": settings.supervisor_provider,
            "role": "Routes requests to specialist agents",
            "cost": "$0.15/1M tokens (cost optimized)",
        },
        agents={
            "document_agent": {
                "status": "active" if mistral_ok else "fallback",
                "model": settings.document_agent_model,
                "provider": settings.document_agent_provider,
                "description": AGENT_DESCRIPTIONS.get("document_agent", ""),
                "capabilities": [
                    "OCR text extraction",
                    "Table extraction",
                    "Document classification",
                    "PDF processing",
                ],
            },
            "video_agent": {
                "status": "ready" if groq_ok else "fallback",
                "model": settings.video_agent_model,
                "provider": settings.video_agent_provider,
                "latency": "~50ms" if groq_ok else "~200ms",
                "description": AGENT_DESCRIPTIONS.get("video_agent", ""),
                "capabilities": [
                    "Real-time robotics vision",
                    "Face detection",
                    "Emotion analysis",
                    "Object detection",
                    "People counting",
                ],
            },
        }
    )


@router.post("/reset")
async def reset_agent_memory():
    """
    Reset the Multi-Agent System.

    Clears all conversation memory and resets the agent state.
    Use this to start fresh.
    """
    try:
        reset_multi_agent_system()
        return {
            "success": True,
            "message": "Multi-agent system has been reset"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset: {str(e)}"
        )
