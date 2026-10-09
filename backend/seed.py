"""Seed the database with demo plants so the dashboard has data on first run.

    python seed.py
"""

from __future__ import annotations

import datetime

import models
from database import Base, SessionLocal, engine, ensure_schema

DEMO_PLANTS = [
    {"name": "Balcony Tomato", "type": "Tomato", "variety": "Cherry", "location": "Balcony (East)",
     "sunlight": "Full Sun", "growth_stage": "Fruiting", "soil_moisture": 62,
     "watering_interval_days": 3, "health_score": 92, "status": "Healthy"},
    {"name": "Chilli Plant", "type": "Chilli", "variety": "Bird's Eye", "location": "Kitchen Window",
     "sunlight": "Full Sun", "growth_stage": "Flowering", "soil_moisture": 30,
     "watering_interval_days": 3, "health_score": 76, "status": "Needs Attention"},
    {"name": "Spearmint", "type": "Mint", "variety": "Spearmint", "location": "Garden",
     "sunlight": "Partial Sun", "growth_stage": "Vegetative", "soil_moisture": 50,
     "watering_interval_days": 2, "health_score": 95, "status": "Healthy"},
    {"name": "Genovese Basil", "type": "Basil", "variety": "Genovese", "location": "Living Room",
     "sunlight": "Full Sun", "growth_stage": "Vegetative", "soil_moisture": 45,
     "watering_interval_days": 2, "health_score": 88, "status": "Healthy"},
]


def main() -> None:
    ensure_schema()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(models.Plant).count() > 0:
            print("Database already contains plants - skipping seed.")
            return
        now = datetime.datetime.utcnow()
        for data in DEMO_PLANTS:
            plant = models.Plant(last_watered=now - datetime.timedelta(days=2), **data)
            db.add(plant)
            db.flush()
            db.add(models.HealthLog(plant_id=plant.id, health_score=plant.health_score,
                                    status=plant.status, note="Seed data"))
        db.commit()
        print(f"Seeded {len(DEMO_PLANTS)} demo plants.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
