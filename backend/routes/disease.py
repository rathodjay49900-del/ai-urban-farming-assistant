from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from typing import List, Optional

import models
import schemas
from database import get_db
from ml.config import ALLOWED_CONTENT_TYPES, MAX_UPLOAD_MB
from ml.predictor import PlantGatekeeper, DiseasePredictor

router = APIRouter(prefix="/api/scanner", tags=["Scanner"])

gatekeeper = PlantGatekeeper()
predictor = DiseasePredictor()

MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024


def _upload_error(file: UploadFile, contents: bytes) -> Optional[str]:
    if len(contents) > MAX_UPLOAD_BYTES:
        return f"Image is too large (max {MAX_UPLOAD_BYTES // (1024 * 1024)} MB)."
    content_type = (file.content_type or "").lower()
    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        return "Unsupported file type. Please upload a JPG, PNG, BMP or WEBP image."
    return None


@router.post("/validate", response_model=schemas.ValidationResponse)
async def validate_image(file: UploadFile = File(...), simulate_invalid: bool = Form(False)):
    contents = await file.read()
    error = _upload_error(file, contents)
    if error:
        return {"success": False, "is_plant_related": False, "category": "unknown",
                "confidence": 0.0, "message": error}
    if simulate_invalid:
        return {
            "success": False, "is_plant_related": False, "category": "human",
            "confidence": 0.98,
            "message": "This image does not appear to contain a plant or farming-related subject.",
        }
    return gatekeeper.validate(contents)


def _rejected(message: str, confidence: float = 0.0) -> dict:
    return {
        "success": False, "is_plant_related": False, "category": "unknown",
        "confidence": confidence, "class_label": None, "disease": None,
        "severity": None, "symptoms": None, "treatment": None,
        "prevention": None, "explanation": None, "plant_info": None,
        "top_predictions": None, "low_confidence": False, "needs_expert": False,
        "message": message,
    }


@router.post("/analyze", response_model=schemas.ScanResponse)
async def analyze_disease(
    file: UploadFile = File(...),
    plant_id: Optional[int] = Form(None),
    simulate_invalid: bool = Form(False),
    simulate_healthy: bool = Form(False),
    db: Session = Depends(get_db),
):
    contents = await file.read()

    error = _upload_error(file, contents)
    if error:
        return _rejected(error)

    if simulate_invalid:
        return _rejected("This image does not appear to contain a plant or farming-related subject.")

    result = predictor.predict(contents)

    if not result["is_plant_related"]:
        return _rejected(result.get("message") or "Please upload a clear plant or leaf image.",
                         result.get("confidence", 0.0))

    # Gatekeeper passed: run a separate health signal only when the caller asks.
    if simulate_healthy and result.get("disease"):
        result.update({
            "disease": None, "severity": None, "symptoms": None,
            "treatment": None, "prevention": None, "explanation": None,
            "message": "Your Plant Looks Healthy",
        })

    # Persist every completed scan so the dashboard has real history.
    if result.get("success"):
        scan = models.DiseaseScan(
            plant_id=plant_id,
            crop=result.get("category"),
            class_label=result.get("class_label"),
            disease=result.get("disease"),
            confidence=result.get("confidence"),
            severity=result.get("severity"),
            recommendation="; ".join(result.get("treatment") or []) or None,
            low_confidence=result.get("low_confidence", False),
            needs_expert=result.get("needs_expert", False),
        )
        db.add(scan)
        db.commit()

    return result


@router.get("/history", response_model=List[schemas.ScanHistoryItem])
def scan_history(plant_id: Optional[int] = None, limit: int = 50, db: Session = Depends(get_db)):
    query = db.query(models.DiseaseScan)
    if plant_id is not None:
        query = query.filter(models.DiseaseScan.plant_id == plant_id)
    return query.order_by(models.DiseaseScan.created_at.desc()).limit(limit).all()
