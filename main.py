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
        {"messages": [{"role": "user", "content": "design a bussiness card that has more than one text for a doctor with the name 'عبد الرحمن بن خالد' use 'image.png' as background add the phone number '0500000000' you can place the text on the middle of the image. and place the job title in arabic, style all text with a an outline"}]}
    )

    print(response)


if __name__ == "__main__":
    # Run the direct test by default (no LLM dependency).
    # Uncomment agent_usage() to test the full agent loop.
    # direct_usage()
    agent_usage()
