from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from database import Base
import datetime


def _utcnow():
    return datetime.datetime.utcnow()


class Plant(Base):
    __tablename__ = "plants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    type = Column(String)
    variety = Column(String, nullable=True)
    planting_date = Column(String, nullable=True)
    location = Column(String, nullable=True)
    sunlight = Column(String, nullable=True)
    growth_stage = Column(String, default="Vegetative")
    soil_moisture = Column(Float, nullable=True)
    watering_interval_days = Column(Integer, nullable=True)
    last_watered = Column(DateTime, nullable=True)
    health_score = Column(Integer, default=100)
    status = Column(String, default="Healthy")
    image = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class DiseaseScan(Base):
    __tablename__ = "disease_scans"

    id = Column(Integer, primary_key=True, index=True)
    plant_id = Column(Integer, ForeignKey("plants.id"), nullable=True)
    image = Column(String, nullable=True)
    crop = Column(String, nullable=True)
    class_label = Column(String, nullable=True)
    disease = Column(String, nullable=True)
    confidence = Column(Float)
    severity = Column(String, nullable=True)
    recommendation = Column(String, nullable=True)
    low_confidence = Column(Boolean, default=False)
    needs_expert = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)


class WateringLog(Base):
    __tablename__ = "watering_logs"

    id = Column(Integer, primary_key=True, index=True)
    plant_id = Column(Integer, ForeignKey("plants.id"), nullable=False)
    watered_at = Column(DateTime, default=_utcnow)
    soil_moisture = Column(Float, nullable=True)
    amount_ml = Column(Float, nullable=True)
    note = Column(String, nullable=True)


class HealthLog(Base):
    __tablename__ = "health_logs"

    id = Column(Integer, primary_key=True, index=True)
    plant_id = Column(Integer, ForeignKey("plants.id"), nullable=False)
    health_score = Column(Integer)
    status = Column(String)
    note = Column(String, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
