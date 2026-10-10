from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

from config import DATABASE_URL

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Additive columns for every table, keyed by table name. SQLite's CREATE TABLE
# (used by SQLAlchemy's create_all) never alters existing tables, so an old
# database file would otherwise be missing columns and every query touching
# them would fail. This lightweight, idempotent migration adds whatever is
# missing. Columns are added nullable (SQLite type affinity makes this safe)
# so the ALTER never fails on tables that already hold rows; fresh tables
# created by create_all still get the full model-defined schema.
_ADDITIVE_COLUMNS = {
    "plants": {
        "name": "VARCHAR",
        "type": "VARCHAR",
        "variety": "VARCHAR",
        "planting_date": "VARCHAR",
        "location": "VARCHAR",
        "sunlight": "VARCHAR",
        "growth_stage": "VARCHAR DEFAULT 'Vegetative'",
        "soil_moisture": "FLOAT",
        "watering_interval_days": "INTEGER",
        "last_watered": "DATETIME",
        "health_score": "INTEGER",
        "status": "VARCHAR",
        "image": "VARCHAR",
        "notes": "VARCHAR",
        "created_at": "DATETIME",
    },
    "disease_scans": {
        "plant_id": "INTEGER",
        "image": "VARCHAR",
        "crop": "VARCHAR",
        "class_label": "VARCHAR",
        "disease": "VARCHAR",
        "confidence": "FLOAT",
        "severity": "VARCHAR",
        "recommendation": "VARCHAR",
        "low_confidence": "BOOLEAN",
        "needs_expert": "BOOLEAN",
        "created_at": "DATETIME",
    },
    "watering_logs": {
        "plant_id": "INTEGER",
        "watered_at": "DATETIME",
        "soil_moisture": "FLOAT",
        "amount_ml": "FLOAT",
        "note": "VARCHAR",
    },
    "health_logs": {
        "plant_id": "INTEGER",
        "health_score": "INTEGER",
        "status": "VARCHAR",
        "note": "VARCHAR",
        "created_at": "DATETIME",
    },
}


def ensure_schema() -> None:
    """Bring an existing SQLite database up to the current schema (idempotent)."""
    if not DATABASE_URL.startswith("sqlite"):
        return
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    # 1) Drop a legacy disease_scans table that has a NOT NULL disease column
    #    (the new code stores NULL for healthy scans). It is recreated by
    #    create_all and only contains disposable scan history.
    if "disease_scans" in tables:
        scan_cols = {c["name"]: c for c in inspector.get_columns("disease_scans")}
        needs_rebuild = (
            ("class_label" not in scan_cols)
            or (scan_cols.get("disease") is not None and not scan_cols["disease"]["nullable"])
        )
        if needs_rebuild:
            with engine.begin() as conn:
                conn.execute(text("DROP TABLE disease_scans"))

    # 2) Add additive columns to existing tables.
    for table, columns in _ADDITIVE_COLUMNS.items():
        if table not in set(inspect(engine).get_table_names()):
            continue
        present = {c["name"] for c in inspect(engine).get_columns(table)}
        missing = {name: ddl for name, ddl in columns.items() if name not in present}
        if missing:
            with engine.begin() as conn:
                for name, ddl in missing.items():
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))
