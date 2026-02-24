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
        [--padding 40]
"""

import argparse
import sys


def parse_color(s: str) -> tuple[int, int, int]:
    """Parse an 'R,G,B' string into a tuple."""
    parts = [int(x.strip()) for x in s.split(",")]
    if len(parts) != 3:
        raise ValueError(f"Expected 3 color components, got {len(parts)}")
    return tuple(parts)  # type: ignore[return-value]


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
    except ValueError as exc:
        print(f"RENDER_ERROR: Invalid color — {exc}", file=sys.stderr)
        sys.exit(1)

    # ── Load font ───────────────────────────────────────────────────────
    try:
        font = ImageFont.truetype(args.font, args.size)
    except Exception as exc:
        print(f"RENDER_ERROR: Could not load font '{args.font}' — {exc}", file=sys.stderr)
        sys.exit(2)

    # ── Measure text ────────────────────────────────────────────────────
    dummy = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(dummy)
    bbox = draw.textbbox((0, 0), args.text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # ── Create or load canvas ───────────────────────────────────────────
    if args.image:
        try:
            img = Image.open(args.image).convert("RGBA")
        except Exception as exc:
            print(f"RENDER_ERROR: Could not open image '{args.image}' — {exc}", file=sys.stderr)
            sys.exit(2)

        # Create a transparent overlay for the text so it composites cleanly
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        canvas_w, canvas_h = img.size

        # Position: use provided coords or center
        if args.x is not None:
            x = args.x
        else:
            x = (canvas_w - text_w) // 2 - bbox[0]

        if args.y is not None:
            y = args.y
        else:
            y = (canvas_h - text_h) // 2 - bbox[1]

        draw.text((x, y), args.text, font=font, fill=text_color)

        # Composite overlay onto the original image
        img = Image.alpha_composite(img, overlay)
        img = img.convert("RGB")
    else:
        # Blank canvas mode (original behaviour)
        canvas_w = text_w + args.padding * 2
        canvas_h = text_h + args.padding * 2
        canvas_w = max(canvas_w, 100)
        canvas_h = max(canvas_h, 60)

        img = Image.new("RGB", (canvas_w, canvas_h), color=bg_color)
        draw = ImageDraw.Draw(img)

        x = (canvas_w - text_w) // 2 - bbox[0]
        y = (canvas_h - text_h) // 2 - bbox[1]
        draw.text((x, y), args.text, font=font, fill=text_color)

    # ── Save ────────────────────────────────────────────────────────────
    try:
        img.save(args.output, "PNG")
    except Exception as exc:
        print(f"RENDER_ERROR: Failed to save image — {exc}", file=sys.stderr)
        sys.exit(3)

    print(f"RENDER_OK: {args.output}")


if __name__ == "__main__":
    main()
