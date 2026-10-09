from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
from database import get_db

router = APIRouter(prefix="/api/plants", tags=["Plants"])


@router.post("/", response_model=schemas.PlantResponse)
def create_plant(plant: schemas.PlantCreate, db: Session = Depends(get_db)):
    db_plant = models.Plant(**plant.model_dump())
    db.add(db_plant)
    db.commit()
    db.refresh(db_plant)
    # Record the initial health entry so a timeline exists from day one.
    db.add(models.HealthLog(plant_id=db_plant.id, health_score=db_plant.health_score,
                            status=db_plant.status, note="Plant registered"))
    db.commit()
    return db_plant


@router.get("/", response_model=List[schemas.PlantResponse])
def get_plants(db: Session = Depends(get_db)):
    return db.query(models.Plant).order_by(models.Plant.created_at.desc()).all()


@router.get("/{plant_id}", response_model=schemas.PlantResponse)
def get_plant(plant_id: int, db: Session = Depends(get_db)):
    plant = db.query(models.Plant).filter(models.Plant.id == plant_id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    return plant


@router.put("/{plant_id}", response_model=schemas.PlantResponse)
def update_plant(plant_id: int, payload: schemas.PlantUpdate, db: Session = Depends(get_db)):
    plant = db.query(models.Plant).filter(models.Plant.id == plant_id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(plant, key, value)
    db.commit()
    db.refresh(plant)
    if "health_score" in data or "status" in data:
        db.add(models.HealthLog(plant_id=plant.id, health_score=plant.health_score,
                                status=plant.status, note="Health updated"))
        db.commit()
    return plant


@router.delete("/{plant_id}")
def delete_plant(plant_id: int, db: Session = Depends(get_db)):
    plant = db.query(models.Plant).filter(models.Plant.id == plant_id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    db.query(models.DiseaseScan).filter(models.DiseaseScan.plant_id == plant_id).delete()
    db.query(models.WateringLog).filter(models.WateringLog.plant_id == plant_id).delete()
    db.query(models.HealthLog).filter(models.HealthLog.plant_id == plant_id).delete()
    db.delete(plant)
    db.commit()
    return {"success": True, "message": f"Plant {plant_id} removed"}


@router.get("/{plant_id}/health-history")
def health_history(plant_id: int, db: Session = Depends(get_db)):
    rows = (db.query(models.HealthLog)
            .filter(models.HealthLog.plant_id == plant_id)
            .order_by(models.HealthLog.created_at.desc())
            .limit(100).all())
    return [
        {"id": r.id, "health_score": r.health_score, "status": r.status,
         "note": r.note, "created_at": r.created_at}
        for r in rows
    ]
