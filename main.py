"""
Example: Using the Arabic text rendering tool with a LangChain Agent.

This demonstrates two usage modes:
  1. Direct invocation (no LLM required — useful for testing).
  2. Full agent loop with an Ollama-backed LLM.
"""

from arabic_renderer import ArabicTextRenderer
from tools import render_arabic_text
# test

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
    from langchain_ollama import OllamaLLM
    from langchain.agents import initialize_agent, AgentType

    llm = OllamaLLM(model="gpt-oss-safeguard:20b")
    tools = [render_arabic_text]

    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True,
    )

    response = agent.invoke(
        "Render the Arabic phrase 'السلام عليكم' using the Cairo font at size 72."
    )
    print(response)


if __name__ == "__main__":
    # Run the direct test by default (no LLM dependency).
    # Uncomment agent_usage() to test the full agent loop.
    direct_usage()
    # agent_usage()
