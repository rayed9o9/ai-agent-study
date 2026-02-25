"""
LangChain tool wrappers for the Arabic text renderer.

Import this module to get a ready-to-use ``render_arabic_text`` tool
that can be bound to any LangChain Agent.
"""

from langchain_core.tools import tool

from arabic_renderer import ArabicTextRenderer
from pathlib import Path

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

    **Multiple text layers:** To place several text elements on the same image
    at different positions, sizes, or fonts, call this tool multiple times.
    Use the output file path from the first call as the ``image_path`` for the
    next call. Each call adds one text layer on top of the previous result.
    Example workflow:
      1. Call with image_path='background.png', text='Title', size=64 → returns path_A
      2. Call with image_path=path_A, text='Subtitle', size=32 → returns path_B
      3. Call with image_path=path_B, text='Phone', size=24 → returns path_C (final)

    Args:
        text: The Arabic text to render (raw Arabic — reshaping is handled
              automatically).
        font_name: Name of the font family to use. The font must exist in the
                   project's ``fonts/`` directory (e.g. 'Alyamama', 'Amiri', 'Cairo').
        size: Font size in pixels (default 48).
        image_path: Optional absolute path to a background image. When provided,
                    the text is drawn on top of this image instead of a blank
                    canvas. Can also be the output from a previous call to
                    layer multiple text elements.
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


@tool
def render_arabic_texts(
    items: list[dict],
    image_path: str | None = None,
    bg_color: str = "255,255,255",
    canvas_width: int = 800,
    canvas_height: int = 600,
) -> str:
    """Render multiple Arabic text elements onto a single image in one call.

    Use this tool when you need to place several text elements on the same
    image at different positions, sizes, fonts, or colors. This is ideal
    for business cards, posters, certificates, or any design with multiple
    text blocks.

    IMPORTANT: When providing an image_path, call ``get_image_info`` first to
    learn the image dimensions. All x/y positions must be within the image
    bounds (0 to width-1 for x, 0 to height-1 for y). Text placed outside
    these bounds will not be visible.

    Args:
        items: A JSON list of text items. Each item is a dict with these keys:
            - text (str, required): The Arabic text to render.
            - font_name (str): Font family name (default 'Alyamama').
              Available: 'Alyamama', 'Amiri', or any font in the fonts/ directory.
            - size (int): Font size in pixels (default 48).
            - x (int or null): X position in pixels from left edge. Null = centered.
            - y (int or null): Y position in pixels from top edge. Null = centered.
            - text_color (str): Text color as 'R,G,B' (default '0,0,0' black).
            - outline_color (str): Outline color as 'R,G,B' (default '255,255,255').
            - outline_width (int): Outline thickness in pixels (default 0, off).
            - max_width (int): Max width before wrapping (default 0, no wrap).

            Example items list for a 626x352 image:
            [
                {"text": "عبد الرحمن", "size": 48, "x": 20, "y": 200, "text_color": "255,255,255"},
                {"text": "طبيب", "size": 30, "x": 20, "y": 260, "text_color": "200,200,200"},
                {"text": "0500000000", "size": 24, "x": 20, "y": 300, "text_color": "180,180,180"}
            ]
        image_path: Optional path to a background image. If provided, text is
                    drawn on top of this image. If null, a blank canvas is
                    created using bg_color, canvas_width, and canvas_height.
        bg_color: Background color as 'R,G,B' for the blank canvas
                  (only used when image_path is null). Default '255,255,255'.
        canvas_width: Canvas width in pixels (only for blank canvas). Default 800.
        canvas_height: Canvas height in pixels (only for blank canvas). Default 600.

    Returns:
        The absolute file path to the generated PNG image on success,
        or a descriptive error message starting with "Error:" on failure.
    """
    return _renderer.render_multi_text(
        items=items,
        image_path=image_path,
        bg_color=bg_color,
        canvas_width=canvas_width,
        canvas_height=canvas_height,
    )


@tool
def get_image_info(image_path: str) -> str:
    """Get the dimensions (width x height) of an image file.

    Call this BEFORE placing text on an image with render_arabic_text or
    render_arabic_texts so you know the valid coordinate range for x and y.

    Args:
        image_path: Path to the image file.

    Returns:
        A string like 'Width: 626, Height: 352' on success,
        or an error message starting with 'Error:' on failure.
    """
    from PIL import Image

    p = Path(image_path)
    if not p.is_file():
        return f"Error: Image file not found at '{image_path}'."
    try:
        img = Image.open(p)
        w, h = img.size
        return f"Width: {w}, Height: {h}"
    except Exception as exc:
        return f"Error: Could not open image — {exc}"
