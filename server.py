"""
FastAPI server for the Arabic Text AI Chat Agent.

Serves a ChatGPT/Gemini-style web UI and proxies chat messages
to the LangChain agent backed by Ollama + Arabic text tools.
"""

from __future__ import annotations

import logging
import re
import uuid
from pathlib import Path

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("arabic-ai")

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from langchain.agents import create_agent
from langchain_ollama import ChatOllama

from tools import render_arabic_text, render_arabic_texts, get_image_info

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
UPLOAD_DIR = BASE_DIR / "uploads"
STATIC_DIR = BASE_DIR / "static"

OUTPUT_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# LangChain Agent (same pattern as main.py)
# ---------------------------------------------------------------------------
llm = ChatOllama(model="gpt-oss-safeguard:20b")
tools = [render_arabic_text, render_arabic_texts, get_image_info]

SYSTEM_PROMPT = (
    "You are a helpful AI assistant. You can have normal conversations, answer "
    "questions, and help with a wide variety of tasks. Always respond in the "
    "same language the user uses.\n\n"
    "You also have specialized tools for rendering Arabic text onto images. "
    "ONLY use these tools when the user explicitly asks you to write or render "
    "text on an image, or when the user uploads an image and asks you to add "
    "text to it. If the user is just chatting or asking questions, respond "
    "normally with text — do NOT call any tools.\n\n"
    "When you DO need to render text on an image, always call get_image_info "
    "first to learn the image dimensions before placing text."
)

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=SYSTEM_PROMPT,
)

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(title="Arabic AI Chat")

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/output/{filename}")
async def serve_output(filename: str):
    file_path = OUTPUT_DIR / filename
    if file_path.is_file():
        return FileResponse(file_path, media_type="image/png")
    return JSONResponse({"error": "File not found"}, status_code=404)


@app.post("/chat")
async def chat(
    message: str = Form(...),
    image: UploadFile | None = File(None),
):
    """Accept a user message (+ optional image) and return the agent response."""
    log.info("━" * 60)
    log.info("NEW REQUEST")
    log.info("  Message : %s", message[:200])
    log.info("  Image   : %s", image.filename if image and image.filename else "(none)")

    image_path: str | None = None

    # Save uploaded image -------------------------------------------------
    if image and image.filename:
        ext = Path(image.filename).suffix or ".png"
        saved_name = f"upload_{uuid.uuid4().hex[:8]}{ext}"
        saved_path = UPLOAD_DIR / saved_name
        contents = await image.read()
        saved_path.write_bytes(contents)
        image_path = str(saved_path)
        log.info("  Saved to: %s  (%d bytes)", image_path, len(contents))

    # Build the prompt for the agent --------------------------------------
    user_input = message
    if image_path:
        user_input += (
            f"\n\nThe user uploaded an image. If they want you to write or "
            f"render text on it, use this exact path as the image_path "
            f"argument when calling render_arabic_text or render_arabic_texts: "
            f"{image_path}\n"
            f"If the user's message is about the image (e.g. writing text on it), "
            f"use the tools. Otherwise, just respond normally."
        )

    log.debug("PROMPT TO AGENT:\n%s", user_input)

    # Invoke agent --------------------------------------------------------
    log.info("Invoking agent…")
    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": user_input}]}
        )
        # Log all messages for debugging
        for i, msg in enumerate(result.get("messages", [])):
            role = getattr(msg, "type", "?")
            content = getattr(msg, "content", "")
            preview = (str(content)[:300] + "…") if len(str(content)) > 300 else str(content)
            log.debug("  msg[%d] role=%s: %s", i, role, preview)

        # Extract the final AI message text
        messages = result.get("messages", [])
        agent_text = ""
        for msg in reversed(messages):
            if hasattr(msg, "content") and msg.type == "ai" and msg.content:
                agent_text = msg.content
                break
        if not agent_text:
            agent_text = str(result)

        log.info("Agent reply: %s", agent_text[:300])
    except Exception as exc:
        log.exception("Agent error")
        agent_text = f"Sorry, an error occurred: {exc}"

    # Find any output image paths in the response -------------------------
    output_images: list[str] = []
    # Search in the agent text and also in all message contents
    search_text = agent_text
    for msg in result.get("messages", []):
        if hasattr(msg, "content") and isinstance(msg.content, str):
            search_text += " " + msg.content

    for match in re.finditer(r"(?:/[^\s\"']+)?output/render_\w+\.png", search_text):
        full_path = match.group(0)
        fname = Path(full_path).name
        if (OUTPUT_DIR / fname).is_file():
            url = f"/output/{fname}"
            if url not in output_images:
                output_images.append(url)

    log.info("Output images: %s", output_images)
    log.info("━" * 60)

    return JSONResponse({
        "reply": agent_text,
        "images": output_images,
    })
