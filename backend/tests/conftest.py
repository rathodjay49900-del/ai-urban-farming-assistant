"""Shared pytest fixtures.

The environment is configured *before* any project module is imported so the
FastAPI app uses an isolated throwaway SQLite database and never tries to load
CLIP (keeping the gatekeeper deterministic and offline in CI).
"""

from __future__ import annotations

import io
import os
import sys
import tempfile
from pathlib import Path

import pytest
from PIL import Image

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

_TEST_DB = Path(tempfile.gettempdir()) / "ai_urban_farming_test.db"
if _TEST_DB.exists():
    _TEST_DB.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB.as_posix()}"
os.environ["AI_ENABLE_CLIP"] = "false"
# Pin the model path to a file that never exists so API tests stay hermetic:
# they must exercise the honest no-model fallback even after the user trains
# a real checkpoint into backend/ml/model/.
os.environ["AI_MODEL_PATH"] = str(Path(tempfile.gettempdir()) / "ai_urban_farming_test_missing.pth")


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient

    import main

    with TestClient(main.app) as test_client:
        yield test_client


def make_green_image_bytes(size: int = 96) -> bytes:
    """A clearly plant-like (green) JPEG used to pass the gatekeeper."""
    image = Image.new("RGB", (size, size), (34, 139, 34))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def make_gray_image_bytes(size: int = 96) -> bytes:
    image = Image.new("RGB", (size, size), (128, 128, 128))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.fixture
def green_image() -> bytes:
    return make_green_image_bytes()


@pytest.fixture
def gray_image() -> bytes:
    return make_gray_image_bytes()
