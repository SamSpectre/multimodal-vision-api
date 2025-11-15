"""
Supervisor Agent - Orchestrates specialist agents using tool-calling pattern.

Built using LangChain v1.0's create_agent() API with tool-calling pattern.
This is the OFFICIAL RECOMMENDED APPROACH for multi-agent systems (2025).

Architecture: Supervisor/Router pattern
- Centralized control flow
- Specialist agents wrapped as tools
- Context-aware delegation
- Better than legacy create_react_agent or manual routing

The supervisor analyzes user requests and delegates to appropriate specialists:
- Vision Agent: Image analysis, colors, quality
- OCR Agent: Text extraction, document analysis
- QA Agent: Question answering based on context
"""

from langchain.agents import create_agent
from langchain.tools import tool
from config.settings import settings
from .vision_agent import create_vision_agent
from .ocr_agent import create_ocr_agent
from .qa_agent import create_qa_agent


# Initialize specialist agents (created once, reused)
_vision_agent = None
_ocr_agent = None
_qa_agent = None


def get_vision_agent():
    """Get or create the Vision agent (singleton pattern)."""
    global _vision_agent
    if _vision_agent is None:
        _vision_agent = create_vision_agent()
    return _vision_agent


def get_ocr_agent():
    """Get or create the OCR agent (singleton pattern)."""
    global _ocr_agent
    if _ocr_agent is None:
        _ocr_agent = create_ocr_agent()
    return _ocr_agent


def get_qa_agent():
    """Get or create the QA agent (singleton pattern)."""
    global _qa_agent
    if _qa_agent is None:
        _qa_agent = create_qa_agent()
    return _qa_agent


# Wrap specialist agents as tools for the supervisor
@tool
def use_vision_specialist(query: str) -> str:
    """
    Use the Vision Analysis Specialist for image-related tasks.

    Use this specialist for:
    - Analyzing image properties (size, format, dimensions)
    - Color analysis and palette extraction
    - Image quality assessment
    - Detecting blur, contrast, or exposure issues
    - Visual understanding tasks

    Examples:
    - "Analyze the colors in this image"
    - "Check the quality of this photo"
    - "What are the dimensions of this image?"
    - "Is this image blurry?"

    Args:
        query: The user's vision-related request

    Returns:
        Vision analysis results
    """
    vision_agent = get_vision_agent()

    result = vision_agent.invoke({
        "messages": [{"role": "user", "content": query}]
    })

    return result["messages"][-1].content


@tool
def use_ocr_specialist(query: str) -> str:
    """
    Use the OCR (Optical Character Recognition) Specialist for text extraction tasks.

    Use this specialist for:
    - Extracting text from images
    - Document digitization
    - Receipt and invoice processing
    - Form data extraction
    - Text region detection and localization
    - Document structure analysis

    Examples:
    - "Extract text from this document"
    - "What text is in this image?"
    - "Read the receipt"
    - "Get the text regions from this form"
    - "What type of document is this?"

    Args:
        query: The user's OCR-related request

    Returns:
        Extracted text or analysis results
    """
    ocr_agent = get_ocr_agent()

    result = ocr_agent.invoke({
        "messages": [{"role": "user", "content": query}]
    })

    return result["messages"][-1].content


@tool
def use_qa_specialist(query: str, context: str = "") -> str:
    """
    Use the Question Answering Specialist for context-based questions.

    Use this specialist for:
    - Answering questions about previously extracted text
    - Finding specific information in OCR results
    - Summarizing documents
    - Searching for details in analyzed content

    Examples:
    - "What is the total amount on the receipt?"
    - "Find the phone number in the extracted text"
    - "Summarize this document"
    - "What colors were detected?"

    Args:
        query: The user's question
        context: Optional context from previous agent results

    Returns:
        Answer based on provided context
    """
    qa_agent = get_qa_agent()

    # Build message with context if provided
    if context:
        message_content = f"Context:\n{context}\n\nQuestion: {query}"
    else:
        message_content = query

    result = qa_agent.invoke({
        "messages": [{"role": "user", "content": message_content}]
    })

    return result["messages"][-1].content


def create_supervisor():
    """
    Create the Supervisor agent that orchestrates specialist agents.

    The supervisor uses the tool-calling pattern (recommended by LangChain 2025):
    - Specialist agents (Vision, OCR, QA) are wrapped as tools
    - Supervisor intelligently delegates to appropriate specialist
    - Can call multiple specialists for complex tasks
    - Maintains conversation context

    This is the MODERN, RECOMMENDED approach for multi-agent systems,
    replacing legacy patterns like create_react_agent or manual routing.

    Returns:
        Compiled supervisor agent ready for invocation

    Usage:
        >>> supervisor = create_supervisor()
        >>> result = supervisor.invoke({
        ...     "messages": [{"role": "user", "content": "Analyze this image and extract any text"}]
        ... })
        >>> print(result["messages"][-1].content)
    """

    # Define supervisor tools (specialist agents)
    supervisor_tools = [
        use_vision_specialist,
        use_ocr_specialist,
        use_qa_specialist
    ]

    # System prompt for supervisor
    system_prompt = """You are the Supervisor of a multimodal AI system with three specialist agents.

Your role is to analyze user requests and delegate tasks to the appropriate specialist(s).

Available specialists:
1. **Vision Specialist** (use_vision_specialist)
   - Image analysis, properties, dimensions
   - Color analysis and palette extraction
   - Image quality assessment (blur, contrast, exposure)
   - Use for: "analyze image", "check quality", "what colors", "image properties"

2. **OCR Specialist** (use_ocr_specialist)
   - Text extraction from images
   - Document processing (receipts, forms, invoices)
   - Text region detection and localization
   - Document structure analysis
   - Use for: "extract text", "read document", "OCR", "get text from image"

3. **QA Specialist** (use_qa_specialist)
   - Answer questions based on context
   - Search extracted text
   - Summarize documents
   - Use for: "what is the total", "find phone number", "summarize", specific questions

Delegation guidelines:
- For image analysis → use_vision_specialist
- For text extraction → use_ocr_specialist
- For questions about extracted data → use_qa_specialist
- For complex tasks, you can call MULTIPLE specialists in sequence
  Example: "Extract text and tell me the total" → OCR specialist, then QA specialist

Important:
- Always delegate to specialists rather than answering directly
- You can call multiple specialists for complex multi-step tasks
- Pass user's full request to specialists
- Synthesize specialist responses into coherent answer for user
- Maintain conversation context across specialist calls

Workflow examples:
1. "Analyze this image" → use_vision_specialist
2. "Extract text from receipt.jpg" → use_ocr_specialist
3. "What's the total on this receipt?" → use_ocr_specialist (extract), then use_qa_specialist (find total)
4. "Check image quality and extract any text" → use_vision_specialist, then use_ocr_specialist
"""

    # Create supervisor using latest LangChain v1.0 API
    supervisor = create_agent(
        model=settings.default_llm_model,  # GPT-4o for intelligent routing
        tools=supervisor_tools,
        system_prompt=system_prompt,
        checkpointer=None  # Add checkpointer here for conversation persistence
    )

    return supervisor


# For standalone testing
if __name__ == "__main__":
    import sys

    print("Creating Multi-Agent Supervisor...")
    supervisor = create_supervisor()

    print("\n" + "="*70)
    print("MULTI-AGENT SUPERVISOR - Multimodal Vision System")
    print("="*70)
    print("\nArchitecture: Tool-Calling Pattern (LangChain v1.0 Recommended)")
    print("\nSpecialist Agents:")
    print("  1. Vision Specialist - Image analysis, colors, quality")
    print("  2. OCR Specialist - Text extraction, document processing")
    print("  3. QA Specialist - Question answering, search, summarization")
    print("\nModel: GPT-4o (multimodal)")
    print("Pattern: Centralized supervisor with tool-calling delegation")
    print("="*70 + "\n")

    # Interactive test
    if len(sys.argv) > 1:
        user_query = " ".join(sys.argv[1:])
        print(f"User Query: {user_query}\n")
        print("Processing...")

        result = supervisor.invoke({
            "messages": [{"role": "user", "content": user_query}]
        })

        print("\nSupervisor Response:")
        print("="*70)
        print(result["messages"][-1].content)
        print("="*70)
    else:
        print("Usage: python supervisor.py <your query>")
        print("Example: python supervisor.py 'Analyze image.jpg and extract any text'")
