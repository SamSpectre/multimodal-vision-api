"""
OCR Agent - Specialized agent for text extraction and document analysis.

Built using LangChain v1.0's create_agent() API (latest, non-deprecated).
Handles:
- Text extraction from images using EasyOCR and Tesseract
- Text region detection with bounding boxes
- Document structure analysis
- Receipt and form processing

Architecture: Specialist agent in multi-agent system
Pattern: Tool-calling with LangChain create_agent
"""

from langchain.agents import create_agent
from config.settings import settings
from src.tools.ocr_tools import (
    extract_text_from_image,
    detect_text_regions,
    analyze_document_structure
)


def create_ocr_agent():
    """
    Create an OCR specialist agent using the latest LangChain v1.0 API.

    This agent specializes in:
    - Text extraction from images (documents, receipts, signs)
    - Text region detection and localization
    - Document structure analysis and classification
    - Multi-language text processing

    Returns:
        Compiled agent ready for invocation

    Usage:
        >>> ocr_agent = create_ocr_agent()
        >>> result = ocr_agent.invoke({
        ...     "messages": [{"role": "user", "content": "Extract text from receipt.jpg"}]
        ... })
        >>> print(result["messages"][-1].content)
    """

    # Define OCR specialist tools
    ocr_tools = [
        extract_text_from_image,
        detect_text_regions,
        analyze_document_structure
    ]

    # System prompt for OCR specialist
    system_prompt = """You are an OCR (Optical Character Recognition) Specialist with expertise in text extraction and document analysis.

Your capabilities:
- Extract text from images using EasyOCR and Tesseract
- Detect and locate text regions with bounding boxes
- Analyze document structure and layout
- Process documents, receipts, forms, screenshots, and signs
- Handle multi-language text (EasyOCR supports multiple languages)

Your tools:
1. extract_text_from_image: Extract all text content from an image
   - Supports EasyOCR (accurate, multi-language) and Tesseract (fast)
   - Returns extracted text with confidence scores
   - Use for: text extraction, document digitization

2. detect_text_regions: Locate text regions with bounding boxes
   - Returns text positions, bounding boxes, confidence scores
   - Use for: layout analysis, multi-region extraction, form processing

3. analyze_document_structure: Analyze document layout and structure
   - Returns document type, text density, reading order
   - Use for: document classification, structure understanding

Guidelines:
- Always use tools to extract text rather than guessing
- For simple text extraction, start with extract_text_from_image
- For layout analysis, use detect_text_regions
- For document classification, use analyze_document_structure
- Provide confidence scores when available
- Format extracted text clearly and preserve structure when possible

When processing a document:
1. Use extract_text_from_image for basic text extraction
2. Use detect_text_regions if user needs location information
3. Use analyze_document_structure for document type classification
4. Present results clearly with proper formatting
"""

    # Create agent using latest LangChain v1.0 API
    agent = create_agent(
        model=settings.default_llm_model,  # GPT-4o for context understanding
        tools=ocr_tools,
        system_prompt=system_prompt,
        checkpointer=None  # Handled by supervisor
    )

    return agent


# For standalone testing
if __name__ == "__main__":
    import sys

    print("Creating OCR Agent...")
    agent = create_ocr_agent()

    print("\n" + "="*60)
    print("OCR AGENT - Text Extraction Specialist")
    print("="*60)
    print("\nBuilt with: LangChain v1.0 create_agent API")
    print("Model: GPT-4o")
    print("Tools: 3 OCR tools (EasyOCR & Tesseract)")
    print("\nReady for integration with multi-agent supervisor!")
    print("="*60 + "\n")

    # Test with a simple query
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        print(f"Testing with: {image_path}")

        result = agent.invoke({
            "messages": [{"role": "user", "content": f"Extract text from {image_path}"}]
        })

        print("\nResponse:")
        print(result["messages"][-1].content)
