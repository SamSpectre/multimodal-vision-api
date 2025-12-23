"""
Document Intelligence Agent - Specialist Agent

This agent handles all document processing tasks:
- OCR text extraction (Mistral OCR 3)
- Table extraction
- Document classification
- PDF processing

Architecture:
    AgentState (from supervisor)
         ↓
    ┌─────────────────────────────────┐
    │  Document Agent                  │
    │  ├─ Mistral Large (reasoning)   │
    │  └─ Tools:                      │
    │      • process_document_ocr     │
    │      • extract_tables           │
    │      • process_pdf              │
    │      • analyze_document         │
    └─────────────────────────────────┘
         ↓
    Updated AgentState (with response)

This agent uses LangChain's create_agent (latest 2025 API) for tool calling,
wrapped to work within the multi-agent supervisor system.

NOTE: create_react_agent from langgraph.prebuilt is DEPRECATED.
      Use create_agent from langchain.agents instead.
"""

import os
from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_mistralai import ChatMistralAI
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent

from .base import AgentState
from src.tools.mistral_ocr_tools import MISTRAL_OCR_TOOLS


DOCUMENT_AGENT_PROMPT = """You are a Document Intelligence Specialist powered by Mistral OCR 3.

Your expertise:
1. **OCR Text Extraction** - Extract text from images, scanned documents, PDFs
2. **Table Extraction** - Identify and extract tabular data with structure
3. **Document Classification** - Classify documents (invoice, receipt, contract, form, report)
4. **Content Analysis** - Analyze document structure, word count, page count

Available Tools:
- `process_document_ocr`: Extract text from any document image (PRIMARY tool)
- `extract_tables_from_document`: Extract tables specifically (for invoices, spreadsheets)
- `process_pdf_document`: Process multi-page PDFs with page-by-page results
- `analyze_document_content`: Full analysis with classification and metrics

Guidelines:
- For general text extraction → use `process_document_ocr`
- For table-heavy documents → use `extract_tables_from_document`
- For multi-page PDFs → use `process_pdf_document`
- For classification/analysis → use `analyze_document_content`

When you receive a file path, use the appropriate tool to process it.
Provide clear, structured summaries of extracted content.
If no file path is provided, ask the user to provide one.
"""


def get_document_llm():
    """Get the LLM for the document agent."""
    api_key = os.getenv("MISTRAL_API_KEY")
    if api_key and api_key != "your_mistral_api_key_here":
        return ChatMistralAI(
            model="mistral-large-latest",
            temperature=0.1,
            api_key=api_key,
        )

    # Fallback to OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return ChatOpenAI(
            model="gpt-4o",
            temperature=0.1,
            api_key=api_key,
        )

    raise ValueError("No LLM API key configured")


# Singleton for the internal document agent
_document_agent = None


def get_document_agent():
    """
    Get or create the internal agent for document processing.

    Uses the latest LangChain create_agent API (2025):
    - model: The LLM to use for reasoning
    - tools: List of tools the agent can invoke
    - system_prompt: System message (replaces deprecated state_modifier)
    """
    global _document_agent

    if _document_agent is None:
        llm = get_document_llm()
        _document_agent = create_agent(
            model=llm,
            tools=MISTRAL_OCR_TOOLS,
            system_prompt=DOCUMENT_AGENT_PROMPT,
        )

    return _document_agent


def document_agent_node(state: AgentState) -> AgentState:
    """
    Document Agent node for the multi-agent graph.

    This wraps the agent to work within the supervisor system.

    Args:
        state: Current AgentState from the supervisor

    Returns:
        Updated AgentState with the document agent's response
    """
    # Get the internal agent (using latest create_agent API)
    agent = get_document_agent()

    # Get messages from state
    messages = state.get("messages", [])

    if not messages:
        # No messages to process
        response_message = AIMessage(
            content="I'm the Document Intelligence Agent. Please provide a document to process or ask about my capabilities."
        )
        return {
            **state,
            "messages": [response_message],
            "current_agent": "document_agent",
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
            final_response = AIMessage(content="Document processing completed.")

        return {
            **state,
            "messages": [final_response],
            "current_agent": "document_agent",
            "context": {
                **state.get("context", {}),
                "document_result": final_response.content
            }
        }

    except Exception as e:
        error_message = AIMessage(
            content=f"Document processing error: {str(e)}. Please ensure the file path is correct and the file exists."
        )
        return {
            **state,
            "messages": [error_message],
            "current_agent": "document_agent",
        }


# Standalone agent for direct use (without supervisor)
def create_standalone_document_agent(use_memory: bool = True):
    """
    Create a standalone Document Agent for direct use.

    This can be used without the supervisor for simple document tasks.
    Uses the latest LangChain create_agent API (2025).

    Returns:
        Compiled LangGraph agent
    """
    from langgraph.checkpoint.memory import MemorySaver

    llm = get_document_llm()
    checkpointer = MemorySaver() if use_memory else None

    return create_agent(
        model=llm,
        tools=MISTRAL_OCR_TOOLS,
        system_prompt=DOCUMENT_AGENT_PROMPT,
        checkpointer=checkpointer,
    )


# For testing
if __name__ == "__main__":
    print("=" * 60)
    print("DOCUMENT INTELLIGENCE AGENT - Standalone Test")
    print("=" * 60)

    agent = create_standalone_document_agent()

    test_query = "What types of documents can you process?"
    print(f"\nUser: {test_query}")

    result = agent.invoke(
        {"messages": [HumanMessage(content=test_query)]},
        config={"configurable": {"thread_id": "test"}}
    )

    print(f"\nAgent: {result['messages'][-1].content}")
