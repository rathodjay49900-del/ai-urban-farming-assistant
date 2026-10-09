"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except Exception:  # python-dotenv optional
    pass

BACKEND_DIR = Path(__file__).resolve().parent

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ai_farming.db")
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

MODEL_PATH = Path(os.getenv("AI_MODEL_PATH", str(BACKEND_DIR / "ml" / "model" / "plant_disease_model.pth")))

# Comma separated list of allowed CORS origins; "*" allows everything.
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]

# Optional weather provider settings (placeholder for a real API key).
WEATHER_LAT = os.getenv("WEATHER_LAT")
WEATHER_LON = os.getenv("WEATHER_LON")
