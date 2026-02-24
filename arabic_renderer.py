"""
ArabicTextRenderer — Core rendering engine for the LangChain Arabic text tool.

Processes Arabic text (reshape + BiDi), then delegates the actual p5.py drawing
to a subprocess worker (_p5_render_worker.py) so the caller thread is never
blocked by the OpenGL window on macOS.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from glob import glob
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display


class ArabicTextRenderer:
    """Render Arabic text to PNG images via p5.py (subprocess-isolated).

    Parameters
    ----------
    fonts_dir : str | Path | None
        Directory containing font sub-folders. Defaults to ``<project>/fonts``.
    output_dir : str | Path | None
        Directory where output PNGs are written. Defaults to ``<project>/output``.
    """

    # ── Construction ─────────────────────────────────────────────────────
    def __init__(
        self,
        fonts_dir: str | Path | None = None,
        output_dir: str | Path | None = None,
    ) -> None:
        project_root = Path(__file__).resolve().parent

        self.fonts_dir = Path(fonts_dir) if fonts_dir else project_root / "fonts"
        self.output_dir = Path(output_dir) if output_dir else project_root / "output"
        self._worker_script = project_root / "_p5_render_worker.py"

    # ── Public API ───────────────────────────────────────────────────────
    def render_text_as_image(
        self,
        text: str,
        font_name: str = "Amiri",
        size: int = 48,
        image_path: str | None = None,
        x: int | None = None,
        y: int | None = None,
    ) -> str:
        """Render *text* in Arabic to a PNG file and return its path.

        Parameters
        ----------
        text : str
            Raw Arabic text (the method handles reshaping + BiDi internally).
        font_name : str
            Name of a font family folder inside ``fonts_dir`` (e.g. ``'Amiri'``).
        size : int
            Font size in pixels.
        image_path : str | None
            Optional path to a background image. If provided, the Arabic text
            is drawn on top of this image instead of a blank canvas.
        x : int | None
            Horizontal position for the text on the image (pixels from the
            left). Defaults to center if not specified.
        y : int | None
            Vertical position for the text on the image (pixels from the top).
            Defaults to center if not specified.

        Returns
        -------
        str
            Absolute path to the saved PNG on success, or a human-readable
            error description starting with ``"Error:"`` on failure.
        """
        # 1. Validate image_path if provided
        if image_path is not None:
            img_p = Path(image_path)
            if not img_p.is_file():
                return f"Error: Image file not found at '{image_path}'."

        # 2. Validate font
        font_path = self._resolve_font(font_name)
        if font_path is None:
            available = self._list_available_fonts()
            return (
                f"Error: Font '{font_name}' not found in {self.fonts_dir}. "
                f"Available fonts: {available or 'none — add .ttf/.otf files to fonts/<FamilyName>/'}."
            )

        # 3. Process Arabic text (reshape + BiDi)
        try:
            processed_text = self._process_arabic(text)
        except Exception as exc:
            return f"Error: Arabic text processing failed — {exc}"

        # 4. Prepare output path
        self.output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = int(time.time() * 1000)
        output_path = self.output_dir / f"render_{timestamp}.png"

        # 5. Invoke the worker in a subprocess
        try:
            result = self._run_worker(
                processed_text=processed_text,
                font_path=str(font_path),
                size=size,
                output_path=str(output_path),
                image_path=image_path,
                x=x,
                y=y,
            )
        except Exception as exc:
            return f"Error: Subprocess execution failed — {exc}"

        if result is not None:
            return result  # error string from worker

        # 6. Verify the output file was created
        if not output_path.exists():
            return (
                "Error: Rendering completed but the output file was not created. "
                "Check that Pillow is correctly installed and that the font file is valid."
            )

        return str(output_path)

    # ── Private helpers ──────────────────────────────────────────────────
    @staticmethod
    def _process_arabic(text: str) -> str:
        """Reshape Arabic glyphs and apply the BiDi algorithm."""
        reshaped = arabic_reshaper.reshape(text)
        bidi_text = get_display(reshaped)
        return bidi_text

    def _resolve_font(self, font_name: str) -> Path | None:
        """Return the first .ttf/.otf file inside ``fonts_dir/font_name/``."""
        family_dir = self.fonts_dir / font_name
        if not family_dir.is_dir():
            # Try case-insensitive search
            for d in self.fonts_dir.iterdir():
                if d.is_dir() and d.name.lower() == font_name.lower():
                    family_dir = d
                    break
            else:
                return None

        patterns = ("*.ttf", "*.otf", "*.TTF", "*.OTF")
        for pat in patterns:
            matches = sorted(family_dir.glob(pat))
            if matches:
                # Prefer "Regular" variant if present
                for m in matches:
                    if "regular" in m.stem.lower():
                        return m
                return matches[0]

        return None

    def _list_available_fonts(self) -> list[str]:
        """List font family names that are available in the fonts directory."""
        if not self.fonts_dir.is_dir():
            return []
        families: list[str] = []
        for d in sorted(self.fonts_dir.iterdir()):
            if d.is_dir() and not d.name.startswith("."):
                has_fonts = any(d.glob("*.ttf")) or any(d.glob("*.otf"))
                if has_fonts:
                    families.append(d.name)
        return families

    def _run_worker(
        self,
        processed_text: str,
        font_path: str,
        size: int,
        output_path: str,
        image_path: str | None = None,
        x: int | None = None,
        y: int | None = None,
    ) -> str | None:
        """Run the rendering worker script in a subprocess.

        Returns ``None`` on success, or an error string on failure.
        """
        cmd = [
            sys.executable,
            str(self._worker_script),
            "--text", processed_text,
            "--font", font_path,
            "--size", str(size),
            "--output", output_path,
        ]

        if image_path is not None:
            cmd.extend(["--image", image_path])
        if x is not None:
            cmd.extend(["--x", str(x)])
        if y is not None:
            cmd.extend(["--y", str(y)])

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            return "Error: Rendering timed out after 30 seconds."

        # Check stderr for RENDER_ERROR markers
        if proc.returncode != 0:
            stderr = proc.stderr.strip()
            # Extract our custom error messages
            for line in stderr.splitlines():
                if line.startswith("RENDER_ERROR:"):
                    return f"Error: {line}"
            return f"Error: Worker exited with code {proc.returncode}. stderr: {stderr[:500]}"

        return None
