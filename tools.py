"""
LangChain tool wrappers for the Arabic text renderer.

Import this module to get a ready-to-use ``render_arabic_text`` tool
that can be bound to any LangChain Agent.
"""

from langchain_core.tools import tool

from arabic_renderer import ArabicTextRenderer

# Shared renderer instance (stateless — safe for concurrent use).
_renderer = ArabicTextRenderer()


@tool
def render_arabic_text(
    text: str,
    font_name: str = "Amiri",
    size: int = 48,
    image_path: str | None = None,
    x: int | None = None,
    y: int | None = None,
) -> str:
    """Render Arabic text as a PNG image and return the file path.

    Use this tool when you need to create a visual representation of Arabic
    text. The text will be properly reshaped and rendered right-to-left.

    You can either render onto a blank canvas or write text onto an existing
    image by providing its path.

    Args:
        text: The Arabic text to render (raw Arabic — reshaping is handled
              automatically).
        font_name: Name of the font family to use. The font must exist in the
                   project's ``fonts/`` directory (e.g. 'Amiri', 'Cairo').
        size: Font size in pixels (default 48).
        image_path: Optional absolute path to a background image. When provided,
                    the text is drawn on top of this image instead of a blank
                    canvas.
        x: Horizontal pixel position for the text on the image (from the left
           edge). Defaults to horizontally centered if not specified.
        y: Vertical pixel position for the text on the image (from the top
           edge). Defaults to vertically centered if not specified.

    Returns:
        The absolute file path to the generated PNG image on success,
        or a descriptive error message starting with "Error:" on failure.
    """
    return _renderer.render_text_as_image(
        text=text,
        font_name=font_name,
        size=size,
        image_path=image_path,
        x=x,
        y=y,
    )

