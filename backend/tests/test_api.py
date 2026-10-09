"""End-to-end API tests against an isolated SQLite database."""

import importlib

import pytest


@pytest.fixture
def created_plant(client):
    response = client.post("/api/plants/", json={"name": "Test Tomato", "type": "Tomato"})
    assert response.status_code == 200, response.text
    return response.json()


def test_health_endpoint_reports_model_status(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "model_loaded" in body
    assert "model" in body
    # The full filesystem path must never be exposed.
    assert "model_path" not in body
    assert "model_path" not in body["model"]
    assert "model_file" in body["model"]


def test_root_endpoint(client):
    assert client.get("/").status_code == 200


def test_plant_crud_and_health_history(client, created_plant):
    plant_id = created_plant["id"]
    assert created_plant["health_score"] >= 0

    listing = client.get("/api/plants/")
    assert listing.status_code == 200
    assert any(p["id"] == plant_id for p in listing.json())

    history = client.get(f"/api/plants/{plant_id}/health-history")
    assert history.status_code == 200
    assert isinstance(history.json(), list)
    assert len(history.json()) >= 1  # initial "Plant registered" entry


def test_watering_log_flow(client, created_plant):
    plant_id = created_plant["id"]
    log = client.post("/api/watering/log", json={"plant_id": plant_id, "amount_ml": 250})
    assert log.status_code == 200, log.text
    assert log.json()["plant_id"] == plant_id

    logs = client.get("/api/watering/logs")
    assert logs.status_code == 200
    assert any(item["plant_id"] == plant_id for item in logs.json())


def test_watering_log_unknown_plant_returns_404(client):
    response = client.post("/api/watering/log", json={"plant_id": 999999, "amount_ml": 100})
    assert response.status_code == 404


def test_dashboard_stats(client):
    response = client.get("/api/stats/dashboard")
    assert response.status_code == 200
    body = response.json()
    for key in ("total_plants", "healthy_plants", "total_scans", "average_health"):
        assert key in body


def test_analyze_green_image_returns_no_fake_diagnosis(client, green_image):
    response = client.post(
        "/api/scanner/analyze",
        files={"file": ("leaf.jpg", green_image, "image/jpeg")},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True
    assert body["is_plant_related"] is True
    # No trained model in the test environment -> must not invent a disease.
    assert body["disease"] is None
    assert body["low_confidence"] is True
    assert body["needs_expert"] is True


def test_analyze_rejects_non_image(client):
    response = client.post(
        "/api/scanner/analyze",
        files={"file": ("notes.jpg", b"just some text, not an image", "image/jpeg")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["is_plant_related"] is False


def test_analyze_rejects_unsupported_content_type(client, green_image):
    response = client.post(
        "/api/scanner/analyze",
        files={"file": ("leaf.txt", green_image, "text/plain")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert "Unsupported file type" in (body["message"] or "")


def test_analyze_rejects_oversized_upload(client, green_image, monkeypatch):
    disease_module = importlib.import_module("routes.disease")
    monkeypatch.setattr(disease_module, "MAX_UPLOAD_BYTES", 10)
    response = client.post(
        "/api/scanner/analyze",
        files={"file": ("leaf.jpg", green_image, "image/jpeg")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert "too large" in (body["message"] or "").lower()


def test_scanner_history_returns_list(client):
    response = client.get("/api/scanner/history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
