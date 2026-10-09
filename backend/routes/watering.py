"""Weather-aware watering recommendations."""

from __future__ import annotations

import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

import models
import schemas
from database import get_db
from weather import get_current_weather
from ml.plant_db import PLANT_DB

router = APIRouter(prefix="/api/watering", tags=["Watering"])

# Watering interval (days) by growth stage - a sensible default per stage.
STAGE_FACTOR = {
    "seedling": 0.6,
    "vegetative": 1.0,
    "flowering": 1.2,
    "fruiting": 1.2,
    "mature": 1.0,
}


def _base_interval_days(plant_type: str) -> int:
    key = (plant_type or "").lower()
    ref = next((v for k, v in PLANT_DB.items() if k in key), None)
    water = (ref or {}).get("water", "").lower()
    if "very low" in water or "low" in water:
        return 7
    if "high" in water:
        return 2
    return 3


def _recommend(plant: models.Plant, weather: dict) -> dict:
    interval = plant.watering_interval_days or _base_interval_days(plant.type)
    stage = (plant.growth_stage or "vegetative").lower()
    interval = max(1, round(interval * STAGE_FACTOR.get(stage, 1.0)))

    moisture = plant.soil_moisture
    rain = bool(weather.get("rain_expected"))
    temp = weather.get("temperature_c") or 25

    reasons: list[str] = []
    water_now = False

    if moisture is not None:
        if moisture < 30:
            water_now = True
            reasons.append(f"soil moisture is low ({moisture:.0f}%)")
        elif moisture <= 45:
            reasons.append(f"soil moisture is moderate ({moisture:.0f}%)")

    last = plant.last_watered
    days_since = (datetime.datetime.utcnow() - last).days if last else None
    if days_since is None or days_since >= interval:
        water_now = True
        reasons.append(
            f"it has been {days_since} day(s) since the last watering (target {interval})"
            if days_since is not None else "no watering history is recorded yet"
        )

    if rain:
        water_now = False
        reasons.append("rain is expected, so the plant can be left for now")

    if temp >= 32 and water_now:
        reasons.append("high temperature increases evaporation - water deeply")

    amount = 250.0
    if water_now:
        amount = 400.0 if temp >= 32 else (150.0 if moisture and moisture > 45 else 250.0)

    next_watering = None
    if not water_now:
        next_watering = (datetime.datetime.utcnow() + datetime.timedelta(days=interval)).strftime("%Y-%m-%d")

    return {
        "plant_id": plant.id,
        "plant_name": plant.name,
        "water_now": water_now,
        "amount_ml": amount if water_now else None,
        "next_watering": next_watering,
        "soil_moisture": moisture,
        "weather": weather.get("summary"),
        "temperature_c": temp,
        "reason": "; ".join(reasons) or "Conditions are normal for the current schedule",
    }


@router.get("/recommendations", response_model=List[schemas.WateringRecommendation])
def recommendations(db: Session = Depends(get_db)):
    weather = get_current_weather()
    plants = db.query(models.Plant).all()
    return [_recommend(p, weather) for p in plants]


@router.get("/recommendation/{plant_id}", response_model=schemas.WateringRecommendation)
def recommendation(plant_id: int, db: Session = Depends(get_db)):
    plant = db.query(models.Plant).filter(models.Plant.id == plant_id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    return _recommend(plant, get_current_weather())


@router.post("/log", response_model=schemas.WateringLogResponse)
def log_watering(payload: schemas.WateringLogCreate, db: Session = Depends(get_db)):
    plant = db.query(models.Plant).filter(models.Plant.id == payload.plant_id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    log = models.WateringLog(**payload.model_dump())
    db.add(log)
    plant.last_watered = datetime.datetime.utcnow()
    if payload.soil_moisture is not None:
        plant.soil_moisture = payload.soil_moisture
    db.commit()
    db.refresh(log)
    return log


@router.get("/history/{plant_id}", response_model=List[schemas.WateringLogResponse])
def watering_history(plant_id: int, db: Session = Depends(get_db)):
    return (db.query(models.WateringLog)
            .filter(models.WateringLog.plant_id == plant_id)
            .order_by(models.WateringLog.watered_at.desc())
            .limit(100).all())


@router.get("/logs", response_model=List[schemas.WateringLogResponse])
def all_watering_logs(plant_id: Optional[int] = None, limit: int = 100,
                      db: Session = Depends(get_db)):
    """Return watering activity across all plants (optionally filtered by plant)."""
    query = db.query(models.WateringLog)
    if plant_id is not None:
        query = query.filter(models.WateringLog.plant_id == plant_id)
    return query.order_by(models.WateringLog.watered_at.desc()).limit(limit).all()
