"""Aggregated statistics powering the dashboard."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from routes.watering import _recommend
from weather import get_current_weather

router = APIRouter(prefix="/api/stats", tags=["Stats"])


@router.get("/dashboard", response_model=schemas.DashboardStats)
def dashboard_stats(db: Session = Depends(get_db)):
    plants = db.query(models.Plant).all()
    total = len(plants)
    healthy = sum(1 for p in plants if (p.status or "").lower() == "healthy")
    attention = total - healthy
    avg_health = round(sum(p.health_score or 0 for p in plants) / total, 1) if total else 0.0

    weather = get_current_weather()
    water_today = sum(1 for p in plants if _recommend(p, weather)["water_now"])

    total_scans = db.query(func.count(models.DiseaseScan.id)).scalar() or 0
    diseased_scans = (db.query(func.count(models.DiseaseScan.id))
                      .filter(models.DiseaseScan.disease.isnot(None)).scalar() or 0)
    healthy_scans = total_scans - diseased_scans

    return {
        "total_plants": total,
        "healthy_plants": healthy,
        "needs_attention": attention,
        "water_today": water_today,
        "average_health": avg_health,
        "total_scans": total_scans,
        "healthy_scans": healthy_scans,
        "diseased_scans": diseased_scans,
    }


@router.get("/weather")
def weather():
    return get_current_weather()
