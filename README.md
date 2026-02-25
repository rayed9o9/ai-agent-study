# Arabic AI Agent 🖋️

An AI-powered tool that renders Arabic text onto images using **LangChain**, **Ollama**, and a custom Arabic text rendering engine. Comes with a ChatGPT-style web interface for interactive use.

## Features

- ✨ **Arabic text rendering** — proper reshaping, BiDi, and RTL support
- 🤖 **LangChain agent** — uses `gpt-oss-safeguard:20b` via Ollama
- 🌐 **Web chat UI** — dark-themed, Gemini/ChatGPT-inspired interface
- 🖼️ **Image upload** — attach an image and the AI writes Arabic text on it
- 🔤 **Multiple fonts** — supports Alyamama, Amiri, and custom fonts
- 🎨 **Customizable** — text color, outline, position, size, and wrapping

## Quick Start

### Prerequisites

- [Ollama](https://ollama.ai) installed and running
- [uv](https://docs.astral.sh/uv/) package manager
- The model pulled: `ollama pull gpt-oss-safeguard:20b`

### Install & Run

```bash
# Install dependencies
uv sync

# Start the web server
uv run uvicorn server:app --reload --port 8000
```

Then open **http://localhost:8000** in your browser.

### CLI Usage

```bash
# Run the agent directly
uv run python main.py
```

## How It Works

1. User sends a message + image through the chat UI
2. FastAPI server passes the request to the LangChain agent
3. Agent calls `get_image_info` to read image dimensions
4. Agent calls `render_arabic_text` / `render_arabic_texts` to draw text
5. The rendered image is returned and displayed inline

## Output Example

![Arabic text rendered on image](output_example.png)

## Project Structure

```
├── server.py              # FastAPI web server
├── main.py                # CLI entry point
├── tools.py               # LangChain tool wrappers
├── arabic_renderer.py     # Core Arabic rendering engine
├── _p5_render_worker.py   # Subprocess rendering worker
├── static/
│   ├── index.html         # Chat UI
│   ├── style.css          # Dark theme styles
│   └── app.js             # Client-side logic
├── fonts/
│   ├── Alyamama/          # Default Arabic font
│   └── Amiri/             # Alternative Arabic font
├── output/                # Rendered images
└── uploads/               # User-uploaded images
```

## Adding Fonts

Place `.ttf` or `.otf` files in a subfolder under `fonts/`:

```
fonts/
├── Cairo/
│   └── Cairo-Regular.ttf
└── Tajawal/
    └── Tajawal-Regular.ttf
```

Download Arabic fonts from [Google Fonts](https://fonts.google.com/?subset=arabic).
