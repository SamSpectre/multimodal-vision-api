"""
Graph State for this multimodal Agentic Project
This defines the structure of data that flows through our LangGraph.
"""
from langchain_core.messages import BaseMessage
from typing import TypedDict, List, Annotated,Sequence
from langgraph.graph.message import add_messages
from config.settings import Settings

class GraphState(TypedDict):
    """
    State for the LangGraph. This state is passed between nodes (agents) in the graph.
    Each node can read from and write to this state.
    
    Attributes:
        messages: Conversation history (text + images)
                  Uses add_messages reducer to append new messages

    The 'add_messages' reducer automatically:
    - Appends new messages to the list
    - Handles both text and multimodal (text + image) messages
    - Maintains conversation history for memory              
    """
    messages: Annotated[List[BaseMessage], add_messages]

State=GraphState


