"""Database schema, migration-safety and persistence tests.

All tests run against the isolated throwaway SQLite database configured in
``conftest.py`` — never the real ``ai_farming.db``.
"""

import pytest


def test_empty_database_creates_all_expected_tables():
    from sqlalchemy import create_engine, inspect

    import models

    engine = create_engine("sqlite:///:memory:")
    models.Base.metadata.create_all(bind=engine)
    tables = set(inspect(engine).get_table_names())
    assert {"plants", "disease_scans", "watering_logs", "health_logs"} <= tables


def test_migration_map_covers_every_model_column():
    """Every non-PK column must have an upgrade entry so old DB files migrate."""
    import models
    from database import _ADDITIVE_COLUMNS

    for table_name, table in models.Base.metadata.tables.items():
        assert table_name in _ADDITIVE_COLUMNS, f"no migration entry for table {table_name}"
        for column in table.columns:
            if column.primary_key:
                continue
            assert column.name in _ADDITIVE_COLUMNS[table_name], (
                f"column {table_name}.{column.name} has no migration entry - "
                "old databases would fail on it"
            )


def test_ensure_schema_is_idempotent(client):
    from database import ensure_schema

    ensure_schema()
    ensure_schema()  # must not raise on an up-to-date database
    response = client.get("/api/plants/")
    assert response.status_code == 200


def test_invalid_plant_is_rejected(client):
    # "name" is required — FastAPI/Pydantic must answer 422, not store garbage.
    response = client.post("/api/plants/", json={"type": "Tomato"})
    assert response.status_code == 422


def test_delete_plant_cascades_watering_logs(client):
    plant = client.post(
        "/api/plants/", json={"name": "Cascade Test Plant", "type": "Mint"}
    ).json()
    plant_id = plant["id"]

    log = client.post("/api/watering/log", json={"plant_id": plant_id, "amount_ml": 100})
    assert log.status_code == 200
    before = client.get("/api/watering/logs", params={"plant_id": plant_id})
    assert len(before.json()) >= 1

    assert client.delete(f"/api/plants/{plant_id}").status_code == 200
    after = client.get("/api/watering/logs", params={"plant_id": plant_id})
    assert after.json() == []
    assert client.get(f"/api/plants/{plant_id}").status_code == 404
