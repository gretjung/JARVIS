import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

MEMORY_DIR = BASE_DIR / "memory"
MEDIA_DIR = BASE_DIR / "media"

IMAGE_DIR = MEDIA_DIR / "images"
VIDEO_DIR = MEDIA_DIR / "videos"

SKILLS_DIR = BASE_DIR / "skills"


for folder in [
    MEMORY_DIR,
    MEDIA_DIR,
    IMAGE_DIR,
    VIDEO_DIR,
    SKILLS_DIR
]:
    folder.mkdir(parents=True, exist_ok=True)


# =========================
# AI
# =========================

MODEL = os.getenv(
    "JARVIS_MODEL",
    "qwen3:8b"
)

OLLAMA_HOST = os.getenv(
    "OLLAMA_HOST",
    "http://127.0.0.1:11434"
)


# =========================
# WEB
# =========================

TAVILY_API_KEY = os.getenv(
    "TAVILY_API_KEY",
    ""
)


# =========================
# IMAGE / VIDEO
# =========================

COMFYUI_URL = os.getenv(
    "COMFYUI_URL",
    "http://127.0.0.1:8188"
)

FFMPEG = os.getenv(
    "JARVIS_FFMPEG",
    "ffmpeg"
)