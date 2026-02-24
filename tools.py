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
    font_name: str = "Alyamama",
    size: int = 48,
    image_path: str | None = None,
    x: int | None = None,
    y: int | None = None,
    text_color: str = "0,0,0",
    bg_color: str = "255,255,255",
    padding: int = 40,
    outline_color: str = "255,255,255",
    outline_width: int = 0,
    max_width: int = 0,
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
                   project's ``fonts/`` directory (e.g. 'Alyamama', 'Amiri', 'Cairo').
        size: Font size in pixels (default 48).
        image_path: Optional absolute path to a background image. When provided,
                    the text is drawn on top of this image instead of a blank
                    canvas.
        x: Horizontal pixel position for the text on the image (from the left
           edge). Defaults to horizontally centered if not specified.
        y: Vertical pixel position for the text on the image (from the top
           edge). Defaults to vertically centered if not specified.
        text_color: Text fill color as comma-separated RGB values, e.g.
                    '255,0,0' for red. Default is '0,0,0' (black).
        bg_color: Background color as comma-separated RGB values, e.g.
                  '30,30,30' for dark gray. Only used when rendering on a
                  blank canvas (no image_path). Default is '255,255,255' (white).
        padding: Padding around the text in pixels when rendering on a blank
                 canvas. Default is 40.
        outline_color: Outline/stroke color as comma-separated RGB values. Used
                       together with outline_width for a text stroke effect.
                       Default is '255,255,255' (white).
        outline_width: Outline/stroke thickness in pixels. Set to 0 to disable
                       (default). Values of 2-4 work well for most sizes.
        max_width: Maximum width in pixels before text wraps to the next line.
                   Set to 0 to disable wrapping (default). Useful for long
                   sentences that should fit within a specific width.

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
        text_color=text_color,
        bg_color=bg_color,
        padding=padding,
        outline_color=outline_color,
        outline_width=outline_width,
        max_width=max_width,
    )
