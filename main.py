"""
Example: Using the Arabic text rendering tool with a LangChain Agent.

This demonstrates two usage modes:
  1. Direct invocation (no LLM required — useful for testing).
  2. Full agent loop with an Ollama-backed LLM.
"""

from arabic_renderer import ArabicTextRenderer
from tools import render_arabic_text, render_arabic_texts, get_image_info


def direct_usage() -> None:
    """Call the renderer directly, bypassing the LLM."""
    renderer = ArabicTextRenderer()
    result = renderer.render_text_as_image(
        text="بسم الله الرحمن الرحيم",
        font_name="Alyamama",
        image_path="image.png",
        size=64,
    )
    print(f"Direct render result: {result}")


def agent_usage() -> None:
    """Bind the tool to a LangChain Agent powered by Ollama."""
    from langchain_ollama import ChatOllama
    from langchain.agents import create_agent

    llm = ChatOllama(model="gpt-oss-safeguard:20b")
    tools = [render_arabic_text, render_arabic_texts, get_image_info]

    agent = create_agent(
        model=llm,
        tools=tools,
    )

    response = agent.invoke(
        {"messages": [{"role": "user", "content": "design a card with this arabic poem 'نَعاهُ الشّيبُ والرّأسُ الخَضِيبُ , عريتُ منَ الشّبابِ وكنتُ غضاً	, فيَا لَيتَ الشّبابَ يَعُودُ يَوْماً, أحنّ إلى خبز أمي ' the path of the image is 'image.png' "}]}
    )
    print(response)


if __name__ == "__main__":
    # Run the direct test by default (no LLM dependency).
    # Uncomment agent_usage() to test the full agent loop.
    # direct_usage()
    agent_usage()
