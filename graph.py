"""
LangChain v1.0 Multi-Agent Multimodal System
Using the NEW create_agent pattern with Tool-Calling Supervisor!

This is the MODERN, RECOMMENDED architecture for multi-agent systems (2025):
- Supervisor agent orchestrates specialist agents
- Specialist agents (Vision, OCR, QA) wrapped as tools
- Tool-calling pattern (official LangChain recommendation)
- Centralized control flow with intelligent delegation

KEY V1.0 CHANGES:
- Use create_agent() (NOT deprecated create_react_agent)
- Multi-agent system with supervisor pattern
- Tool-calling for delegation (NOT manual routing)
- Each specialist is a create_agent instance
- Much simpler than manual StateGraph construction!

Architecture:
    User → Supervisor → [Vision | OCR | QA] Specialist → Response
"""

from src.agents.supervisor import create_supervisor
from config.settings import settings


def build_multiagent_system():
    """
    Build a multi-agent system using the modern LangChain v1.0 pattern.

    Architecture:
    - **Supervisor Agent**: Analyzes requests and delegates to specialists
    - **Vision Specialist**: Image analysis, colors, quality assessment
    - **OCR Specialist**: Text extraction, document processing
    - **QA Specialist**: Question answering based on context

    This uses the TOOL-CALLING PATTERN (recommended by LangChain 2025):
    - Each specialist agent is wrapped as a tool
    - Supervisor intelligently routes to appropriate specialist(s)
    - Can call multiple specialists for complex tasks
    - Maintains conversation context across calls

    Returns:
        Compiled supervisor agent ready to use

    Example usage:
        >>> agent = build_multiagent_system()
        >>> result = agent.invoke({
        ...     "messages": [{"role": "user", "content": "Analyze image.jpg and extract any text"}]
        ... })
        >>> print(result["messages"][-1].content)

    OLD WAY (Deprecated - DON'T USE):
    ```python
    from langgraph.prebuilt import create_react_agent  # DEPRECATED!
    agent = create_react_agent(llm, tools, ...)
    ```

    NEW WAY (Modern v1.0 - USE THIS):
    ```python
    from langchain.agents import create_agent  # CURRENT API
    supervisor = create_agent(
        model="gpt-4o",
        tools=[vision_specialist, ocr_specialist, qa_specialist],
        system_prompt="Route to specialists..."
    )
    ```

    Multi-Agent Benefits:
    - **Specialization**: Each agent focuses on specific domain
    - **Scalability**: Easy to add new specialists
    - **Maintainability**: Clear separation of concerns
    - **Flexibility**: Supervisor handles complex multi-step tasks
    - **Context**: Shared conversation history across specialists
    """

    print("Building multi-agent system...")
    print("  - Creating Vision Specialist (image analysis)")
    print("  - Creating OCR Specialist (text extraction)")
    print("  - Creating QA Specialist (question answering)")
    print("  - Creating Supervisor (orchestration)")

    # Create the supervisor (which initializes all specialists)
    supervisor = create_supervisor()

    print("\n[OK] Multi-agent system ready!")
    print("\nAvailable capabilities:")
    print("  - Image analysis (properties, colors, quality)")
    print("  - Text extraction (OCR, documents, receipts)")
    print("  - Question answering (search, summarize)")
    print("\nArchitecture: Tool-Calling Supervisor Pattern")
    print("API: LangChain v1.0 create_agent (latest, non-deprecated)")

    return supervisor


# Backward compatibility: Keep the old function name but use new system
def build_vision_agent():
    """
    Legacy function name for backward compatibility.

    Now returns the full multi-agent supervisor instead of just vision agent.
    The supervisor includes vision capabilities plus OCR and QA.

    DEPRECATED: Use build_multiagent_system() instead.
    """
    print("[INFO] build_vision_agent() is legacy - now returns multi-agent supervisor")
    return build_multiagent_system()


if __name__ == "__main__":
    print("="*70)
    print("LANGGRAPH MULTI-AGENT SYSTEM TEST")
    print("="*70)
    print()

    # Check Python version
    import sys
    if sys.version_info < (3, 10):
        print("[ERROR] LangChain v1.0 requires Python 3.10+")
        print(f"   Your version: {sys.version}")
        exit(1)

    print("[OK] Python version OK (3.10+)\n")

    # Build the multi-agent system
    print("Building multi-agent system using create_agent()...")
    print()

    try:
        agent = build_multiagent_system()
        print("\n[OK] Multi-agent system created successfully!\n")

        print("System Details:")
        print(f"  - Architecture: Tool-Calling Supervisor Pattern")
        print(f"  - Supervisor Model: {settings.default_llm_model}")
        print(f"  - Specialist Agents: 3 (Vision, OCR, QA)")
        print(f"  - Built on: LangGraph (via create_agent)")
        print(f"  - Memory: Yes (conversation history)")
        print(f"  - Streaming: Yes")
        print(f"  - API: LangChain v1.0 (non-deprecated)")

        # Test with a simple message
        print("\n\n[TEST] Testing multi-agent system...")
        print("Query: 'Hello! What can you help me with?'")

        test_input = {
            "messages": [
                {"role": "user", "content": "Hello! What can you help me with?"}
            ]
        }

        response = agent.invoke(test_input)

        print("\n[OK] Supervisor Response:")
        print("-" * 70)
        print(response['messages'][-1].content)
        print("-" * 70)

        print("\n\n[SUCCESS] Multi-Agent System is working perfectly!")
        print("\nKey Differences from Old Patterns:")
        print("  [OLD] create_react_agent from langgraph.prebuilt - DEPRECATED")
        print("  [NEW] create_agent from langchain.agents - CURRENT")
        print()
        print("  [OLD] Single vision agent")
        print("  [NEW] Multi-agent with Vision + OCR + QA specialists")
        print()
        print("  [OLD] No routing logic")
        print("  [NEW] Intelligent supervisor with tool-calling delegation")
        print()
        print("  [OLD] Manual LangGraph construction")
        print("  [NEW] Automatic via create_agent")
        print()
        print("\nArchitecture Pattern:")
        print("  User -> Supervisor -> [Vision|OCR|QA] -> Response")
        print()
        print("This follows LangChain 2025 best practices!")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        print("\nTroubleshooting:")
        print("1. Check OPENAI_API_KEY is set in .env")
        print("2. Verify internet connection")
        print("3. Ensure langchain>=1.0.0 is installed")
        print("4. Confirm Python 3.10+ is being used")
        print("5. Check all dependencies are installed (see requirements.txt)")
