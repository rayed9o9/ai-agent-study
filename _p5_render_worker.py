"""
Subprocess worker: renders pre-processed Arabic text to a PNG image using Pillow.

This script is invoked by ArabicTextRenderer via subprocess to keep the
rendering isolated from the main LangChain agent thread.

Usage:
    python _p5_render_worker.py \
        --text "reshapedBidiText" \
        --font /absolute/path/to/font.ttf \
        --size 48 \
        --output /absolute/path/to/output.png \
        [--image /path/to/background.png] \
        [--x 100] [--y 50] \
        [--bg-color 255,255,255] \
        [--text-color 0,0,0] \
        [--padding 40] \
        [--outline-color 255,255,255] \
        [--outline-width 0] \
        [--max-width 0]
"""

import argparse
import sys


def parse_color(s: str) -> tuple[int, int, int]:
    """Parse an 'R,G,B' string into a tuple."""
    parts = [int(x.strip()) for x in s.split(",")]
    if len(parts) != 3:
        raise ValueError(f"Expected 3 color components, got {len(parts)}")
    return tuple(parts)  # type: ignore[return-value]


def wrap_text(
    text: str,
    font,
    max_width: int,
    direction: str | None = None,
) -> list[str]:
    """Word-wrap *text* so that each line fits within *max_width* pixels.

    Arabic text uses spaces as word separators just like Latin scripts, so
    simple split-on-space works well here.  If a single word exceeds
    *max_width* it is placed on its own line (never broken mid-word).
    """
    words = text.split()
    if not words:
        return [text]

    lines: list[str] = []
    current_line = words[0]

    length_kwargs: dict = {}
    if direction:
        length_kwargs["direction"] = direction
        length_kwargs["language"] = "ar"

    for word in words[1:]:
        test_line = f"{current_line} {word}"
        line_w = font.getlength(test_line, **length_kwargs)
        if line_w <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    lines.append(current_line)
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description="Arabic text renderer worker (Pillow)")
    parser.add_argument("--text", required=True, help="Pre-processed (reshaped + bidi) text")
    parser.add_argument("--font", required=True, help="Absolute path to .ttf/.otf font file")
    parser.add_argument("--size", type=int, default=48, help="Font size in pixels")
    parser.add_argument("--output", required=True, help="Output PNG file path")
    parser.add_argument("--bg-color", default="255,255,255", help="Background color as R,G,B")
    parser.add_argument("--text-color", default="0,0,0", help="Text color as R,G,B")
    parser.add_argument("--padding", type=int, default=40, help="Padding around text in pixels")
    parser.add_argument("--image", default=None, help="Optional background image path to write text onto")
    parser.add_argument("--x", type=int, default=None, help="Text X position (default: center)")
    parser.add_argument("--y", type=int, default=None, help="Text Y position (default: center)")
    parser.add_argument("--outline-color", default="255,255,255", help="Outline/stroke color as R,G,B")
    parser.add_argument("--outline-width", type=int, default=0, help="Outline/stroke width in px (0 = off)")
    parser.add_argument("--max-width", type=int, default=0, help="Max text width in px before wrapping (0 = no wrap)")
    parser.add_argument("--direction", default=None, help="Text direction for raqm layout, e.g. 'rtl'")
    parser.add_argument("--language", default=None, help="Text language for raqm shaping, e.g. 'ar'")
    args = parser.parse_args()

    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        print(f"RENDER_ERROR: Failed to import Pillow — {exc}", file=sys.stderr)
        sys.exit(1)

    # ── Parse colors ────────────────────────────────────────────────────
    try:
        bg_color = parse_color(args.bg_color)
        text_color = parse_color(args.text_color)
        outline_color = parse_color(args.outline_color)
    except ValueError as exc:
        print(f"RENDER_ERROR: Invalid color — {exc}", file=sys.stderr)
        sys.exit(1)

    # ── Load font ───────────────────────────────────────────────────────
    try:
        font = ImageFont.truetype(args.font, args.size)
    except Exception as exc:
        print(f"RENDER_ERROR: Could not load font '{args.font}' — {exc}", file=sys.stderr)
        sys.exit(2)

    # ── Prepare text lines (multi-line wrapping) ────────────────────────
    if args.max_width > 0:
        lines = wrap_text(args.text, font, args.max_width, direction=args.direction)
    else:
        lines = [args.text]

    # ── Measure each line and compute total block size ──────────────────
    dummy = Image.new("RGB", (1, 1))
    draw_dummy = ImageDraw.Draw(dummy)

    line_metrics: list[tuple[int, int, tuple[int, int, int, int]]] = []  # (w, h, bbox)
    bbox_kwargs: dict = {"font": font, "stroke_width": args.outline_width}
    if args.direction:
        bbox_kwargs["direction"] = args.direction
    if args.language:
        bbox_kwargs["language"] = args.language
    for line in lines:
        bbox = draw_dummy.textbbox((0, 0), line, **bbox_kwargs)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        line_metrics.append((w, h, bbox))

    line_spacing = int(args.size * 0.3)  # 30% of font size
    total_text_w = max(m[0] for m in line_metrics)
    total_text_h = sum(m[1] for m in line_metrics) + line_spacing * (len(lines) - 1)

    # ── Shared draw kwargs (outline) ────────────────────────────────────
    draw_kwargs: dict = {
        "font": font,
        "fill": text_color,
    }
    if args.outline_width > 0:
        draw_kwargs["stroke_width"] = args.outline_width
        draw_kwargs["stroke_fill"] = outline_color
    if args.direction:
        draw_kwargs["direction"] = args.direction
    if args.language:
        draw_kwargs["language"] = args.language

    # ── Create or load canvas ───────────────────────────────────────────
    if args.image:
        try:
            img = Image.open(args.image).convert("RGBA")
        except Exception as exc:
            print(f"RENDER_ERROR: Could not open image '{args.image}' — {exc}", file=sys.stderr)
            sys.exit(2)

        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        canvas_w, canvas_h = img.size

        # Starting position for the text block
        if args.x is not None:
            block_x = args.x
        else:
            block_x = (canvas_w - total_text_w) // 2

        if args.y is not None:
            block_y = args.y
        else:
            block_y = (canvas_h - total_text_h) // 2

        # Draw each line
        cur_y = block_y
        for i, line in enumerate(lines):
            lw, lh, lbbox = line_metrics[i]
            # Center each line within the block width
            lx = block_x + (total_text_w - lw) // 2 - lbbox[0]
            ly = cur_y - lbbox[1]
            draw.text((lx, ly), line, **draw_kwargs)
            cur_y += lh + line_spacing

        img = Image.alpha_composite(img, overlay)
        img = img.convert("RGB")
    else:
        # Blank canvas mode
        canvas_w = total_text_w + args.padding * 2
        canvas_h = total_text_h + args.padding * 2
        canvas_w = max(canvas_w, 100)
        canvas_h = max(canvas_h, 60)

        img = Image.new("RGB", (canvas_w, canvas_h), color=bg_color)
        draw = ImageDraw.Draw(img)

        block_x = args.padding
        block_y = args.padding

        cur_y = block_y
        for i, line in enumerate(lines):
            lw, lh, lbbox = line_metrics[i]
            # Center each line within the canvas
            lx = (canvas_w - lw) // 2 - lbbox[0]
            ly = cur_y - lbbox[1]
            draw.text((lx, ly), line, **draw_kwargs)
            cur_y += lh + line_spacing

    # ── Save ────────────────────────────────────────────────────────────
    try:
        img.save(args.output, "PNG")
    except Exception as exc:
        print(f"RENDER_ERROR: Failed to save image — {exc}", file=sys.stderr)
        sys.exit(3)

    print(f"RENDER_OK: {args.output}")


if __name__ == "__main__":
    main()
