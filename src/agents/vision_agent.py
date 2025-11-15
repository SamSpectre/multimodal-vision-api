"""
Vision Agent - Specialized agent for image analysis and visual understanding.

Built using LangChain v1.0's create_agent() API (latest, non-deprecated).
Handles:
- Image property analysis
- Color analysis
- Image quality detection
- Visual understanding with GPT-4o

Architecture: Specialist agent in multi-agent system
Pattern: Tool-calling with LangChain create_agent
"""

from langchain.agents import create_agent
from config.settings import settings
from src.tools.basic_vision_tools import (
    get_image_properties,
    analyze_image_colors,
    detect_image_quality_issues
)


def create_vision_agent():
    """
    Create a Vision Analysis specialist agent using the latest LangChain v1.0 API.

    This agent specializes in:
    - Image property analysis (size, format, dimensions)
    - Color analysis and palette extraction
    - Image quality assessment and recommendations
    - Visual understanding using GPT-4o multimodal capabilities

    Returns:
        Compiled agent ready for invocation

    Usage:
        >>> vision_agent = create_vision_agent()
        >>> result = vision_agent.invoke({
        ...     "messages": [{"role": "user", "content": "Analyze image.jpg"}]
        ... })
        >>> print(result["messages"][-1].content)
    """

    # Define vision specialist tools
    vision_tools = [
        get_image_properties,
        analyze_image_colors,
        detect_image_quality_issues
    ]

    # System prompt for vision specialist
    system_prompt = """You are a Vision Analysis Specialist with expertise in image analysis and visual understanding.

Your capabilities:
- Analyze image properties (size, format, dimensions, color mode)
- Perform color analysis and extract dominant color palettes
- Detect image quality issues (blur, contrast, exposure problems)
- Provide actionable recommendations for image improvements

Your tools:
1. get_image_properties: Get basic image metadata and properties
2. analyze_image_colors: Analyze color distribution and dominant colors
3. detect_image_quality_issues: Assess image quality and detect problems

Guidelines:
- Always use your tools to gather data before providing analysis
- Provide detailed, specific insights based on tool results
- Give actionable recommendations when quality issues are detected
- Be precise with measurements (dimensions, file sizes, percentages)
- Explain findings in clear, non-technical language when possible

When analyzing an image:
1. Start with get_image_properties to understand basic characteristics
2. Use analyze_image_colors for color-related queries
3. Use detect_image_quality_issues when asked about quality or problems
4. Synthesize results into comprehensive analysis
"""

    # Create agent using latest LangChain v1.0 API
    agent = create_agent(
        model=settings.default_llm_model,  # GPT-4o for multimodal capabilities
        tools=vision_tools,
        system_prompt=system_prompt,
        checkpointer=None  # Will be handled by supervisor
    )

    return agent


# For standalone testing
if __name__ == "__main__":
    import sys

    print("Creating Vision Agent...")
    agent = create_vision_agent()

    print("\n" + "="*60)
    print("VISION AGENT - Image Analysis Specialist")
    print("="*60)
    print("\nBuilt with: LangChain v1.0 create_agent API")
    print("Model: GPT-4o (multimodal)")
    print("Tools: 3 vision analysis tools")
    print("\nReady for integration with multi-agent supervisor!")
    print("="*60 + "\n")

    # Test with a simple query
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        print(f"Testing with: {image_path}")

        result = agent.invoke({
            "messages": [{"role": "user", "content": f"Analyze the image at {image_path}"}]
        })

        print("\nResponse:")
        print(result["messages"][-1].content)
