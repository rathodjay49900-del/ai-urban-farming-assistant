from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ----------------------------------------------------------------- Plants
class PlantBase(BaseModel):
    name: str
    type: str
    variety: Optional[str] = None
    planting_date: Optional[str] = None
    location: Optional[str] = None
    sunlight: Optional[str] = None
    growth_stage: Optional[str] = "Vegetative"
    soil_moisture: Optional[float] = None
    watering_interval_days: Optional[int] = None
    image: Optional[str] = None
    notes: Optional[str] = None


class PlantCreate(PlantBase):
    pass


class PlantUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    variety: Optional[str] = None
    planting_date: Optional[str] = None
    location: Optional[str] = None
    sunlight: Optional[str] = None
    growth_stage: Optional[str] = None
    soil_moisture: Optional[float] = None
    watering_interval_days: Optional[int] = None
    health_score: Optional[int] = None
    status: Optional[str] = None
    image: Optional[str] = None
    notes: Optional[str] = None


class PlantResponse(PlantBase):
    id: int
    health_score: int
    status: str
    last_watered: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --------------------------------------------------------------- Scanner
class Prediction(BaseModel):
    label: str
    confidence: float


class ValidationResponse(BaseModel):
    success: bool
    is_plant_related: bool
    category: str
    confidence: float
    message: Optional[str] = None


class PlantInfo(BaseModel):
    name: str
    scientific_name: str
    category: str
    sunlight: str
    water: str
    temperature: str
    soil: str


class ScanResponse(BaseModel):
    success: bool
    is_plant_related: bool
    category: str
    confidence: float
    class_label: Optional[str] = None
    disease: Optional[str] = None
    severity: Optional[str] = None
    symptoms: Optional[List[str]] = None
    treatment: Optional[List[str]] = None
    prevention: Optional[List[str]] = None
    explanation: Optional[str] = None
    plant_info: Optional[PlantInfo] = None
    top_predictions: Optional[List[Prediction]] = None
    low_confidence: bool = False
    needs_expert: bool = False
    message: Optional[str] = None


class ScanHistoryItem(BaseModel):
    id: int
    plant_id: Optional[int] = None
    crop: Optional[str] = None
    class_label: Optional[str] = None
    disease: Optional[str] = None
    confidence: Optional[float] = None
    severity: Optional[str] = None
    low_confidence: bool = False
    needs_expert: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


# -------------------------------------------------------------- Watering
class WateringLogCreate(BaseModel):
    plant_id: int
    soil_moisture: Optional[float] = None
    amount_ml: Optional[float] = None
    note: Optional[str] = None


class WateringLogResponse(WateringLogCreate):
    id: int
    watered_at: datetime

    class Config:
        from_attributes = True


class WateringRecommendation(BaseModel):
    plant_id: Optional[int] = None
    plant_name: str
    water_now: bool
    amount_ml: Optional[float] = None
    next_watering: Optional[str] = None
    soil_moisture: Optional[float] = None
    weather: Optional[str] = None
    temperature_c: Optional[float] = None
    reason: str


# ------------------------------------------------------------------- AI
class ChatMessage(BaseModel):
    text: str
    role: str = "user"


class ChatResponse(BaseModel):
    text: str
    is_valid_topic: bool


# -------------------------------------------------------------- Stats
class DashboardStats(BaseModel):
    total_plants: int
    healthy_plants: int
    needs_attention: int
    water_today: int
    average_health: float
    total_scans: int
    healthy_scans: int
    diseased_scans: int
