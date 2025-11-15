"""
QA Agent - Specialized agent for question answering based on extracted context.

Built using LangChain v1.0's create_agent() API (latest, non-deprecated).
Handles:
- Answering questions based on OCR-extracted text
- Analyzing vision analysis results
- Synthesizing information from multiple sources
- Providing contextual answers

Architecture: Specialist agent in multi-agent system
Pattern: Tool-calling with LangChain create_agent
"""

from langchain.agents import create_agent
from langchain.tools import tool
from config.settings import settings


# QA-specific tools
@tool
def search_extracted_text(query: str, context: str) -> str:
    """
    Search for specific information in extracted text.

    Args:
        query: What to search for
        context: The extracted text to search in

    Returns:
        Relevant excerpts or answer
    """
    # Simple keyword-based search
    lines = context.split('\n')
    relevant_lines = [line for line in lines if query.lower() in line.lower()]

    if relevant_lines:
        return "\n".join(relevant_lines)
    else:
        return f"No information found for '{query}' in the provided context."


@tool
def summarize_text(text: str, max_length: int = 200) -> str:
    """
    Summarize long text into key points.

    Args:
        text: Text to summarize
        max_length: Maximum length of summary

    Returns:
        Concise summary
    """
    # Simple summarization (first sentences)
    sentences = text.split('. ')
    summary = []
    current_length = 0

    for sentence in sentences:
        if current_length + len(sentence) <= max_length:
            summary.append(sentence)
            current_length += len(sentence)
        else:
            break

    return '. '.join(summary) + ('.' if summary else '')


def create_qa_agent():
    """
    Create a Question Answering specialist agent using the latest LangChain v1.0 API.

    This agent specializes in:
    - Answering questions based on extracted text (from OCR agent)
    - Analyzing vision analysis results
    - Synthesizing information from multiple sources
    - Providing contextual, accurate answers

    The QA agent works with context provided by other agents (Vision, OCR)
    and helps users get specific information from analyzed data.

    Returns:
        Compiled agent ready for invocation

    Usage:
        >>> qa_agent = create_qa_agent()
        >>> result = qa_agent.invoke({
        ...     "messages": [{"role": "user", "content": "What is the total on this receipt?"}]
        ... })
        >>> print(result["messages"][-1].content)
    """

    # Define QA specialist tools
    qa_tools = [
        search_extracted_text,
        summarize_text
    ]

    # System prompt for QA specialist
    system_prompt = """You are a Question Answering Specialist with expertise in analyzing and answering questions based on provided context.

Your capabilities:
- Answer questions based on text extracted by the OCR agent
- Analyze results from the Vision agent
- Search for specific information in context
- Summarize long documents
- Provide accurate, context-based answers

Your tools:
1. search_extracted_text: Search for specific information in extracted text
   - Use when user asks about specific details
   - Helps find relevant portions of long documents

2. summarize_text: Create concise summaries of long text
   - Use when user wants an overview
   - Helps condense verbose documents

Guidelines:
- ALWAYS base answers on the provided context (from Vision/OCR agents)
- Use search_extracted_text to find specific information
- Use summarize_text for overview questions
- Be precise and quote relevant parts of the context
- If information is not in the context, say so clearly
- Don't make assumptions beyond what's in the context

When answering questions:
1. Check if context is available in conversation history
2. Use tools to search or summarize as needed
3. Provide direct, accurate answers based on context
4. Quote relevant parts of the source when helpful
5. Clearly state if information is not available in context

Example interactions:
- "What is the total amount?" → Search for "total" or currency amounts
- "Summarize this document" → Use summarize_text tool
- "What colors are in the image?" → Reference Vision agent's color analysis
- "Extract the phone number" → Search extracted text for phone patterns
"""

    # Create agent using latest LangChain v1.0 API
    agent = create_agent(
        model=settings.default_llm_model,  # GPT-4o for advanced reasoning
        tools=qa_tools,
        system_prompt=system_prompt,
        checkpointer=None  # Handled by supervisor
    )

    return agent


# For standalone testing
if __name__ == "__main__":
    import sys

    print("Creating QA Agent...")
    agent = create_qa_agent()

    print("\n" + "="*60)
    print("QA AGENT - Question Answering Specialist")
    print("="*60)
    print("\nBuilt with: LangChain v1.0 create_agent API")
    print("Model: GPT-4o")
    print("Tools: 2 QA tools (search, summarize)")
    print("\nReady for integration with multi-agent supervisor!")
    print("="*60 + "\n")

    # Test with a simple query
    if len(sys.argv) > 2:
        query = sys.argv[1]
        context = sys.argv[2]
        print(f"Testing with query: {query}")
        print(f"Context: {context[:100]}...")

        result = agent.invoke({
            "messages": [{"role": "user", "content": f"Context: {context}\n\nQuestion: {query}"}]
        })

        print("\nResponse:")
        print(result["messages"][-1].content)
