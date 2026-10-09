from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import schemas
import models
from database import get_db

router = APIRouter(prefix="/api/assistant", tags=["Assistant"])

PLANT_KEYWORDS = [
    "plant", "farm", "garden", "crop", "water", "watering", "soil", "sun", "sunlight",
    "leaf", "leaves", "disease", "pest", "grow", "growth", "harvest", "seed", "fertil",
    "tomato", "chilli", "chili", "potato", "rose", "basil", "mint", "compost", "prune",
    "blight", "mildew", "rust", "spot", "fungus", "fungal", "aphid", "mite", "yellow",
]

KNOWLEDGE = [
    (["water", "watering", "dry", "moist"], "Water at the base of the plant, early in the morning. "
     "Let the top 2-3 cm of soil dry out between waterings to prevent root rot."),
    (["yellow", "yellowing"], "Yellowing can come from overwatering, nutrient deficiency or disease. "
     "Check soil moisture first, then inspect the leaf undersides for pests."),
    (["blight"], "Blight spreads fast in cool, wet conditions. Remove and destroy infected leaves, "
     "improve airflow and avoid overhead watering."),
    (["mildew"], "Powdery mildew thrives in humid air with dry soil. Improve ventilation, "
     "remove affected leaves and apply a potassium-bicarbonate or sulfur spray."),
    (["pest", "aphid", "mite", "bug"], "Inspect leaf undersides. A jet of water, insecticidal soap "
     "or neem oil handles most soft-bodied pests. Introduce beneficial insects when possible."),
    (["fertil", "nutrient"], "Feed with a balanced fertiliser during active growth, and switch to a "
     "lower-nitrogen blend once flowering begins."),
    (["soil"], "Most vegetables prefer loose, well-draining soil rich in organic matter. "
     "Add compost and check that water does not pool around the roots."),
    (["sun", "sunlight", "light"], "Most fruiting crops need 6-8 hours of direct sun. "
     "Leafy greens tolerate partial shade."),
]


@router.post("/chat", response_model=schemas.ChatResponse)
def chat_assistant(message: schemas.ChatMessage, db: Session = Depends(get_db)):
    text_lower = message.text.lower()
    is_valid = any(kw in text_lower for kw in PLANT_KEYWORDS)

    if not is_valid:
        return {
            "text": "I'm PlantAI, your urban farming assistant. I can help with plant health, "
                    "diseases, watering, soil, and crop care. Please ask a plant or farming question.",
            "is_valid_topic": False,
        }

    for keywords, advice in KNOWLEDGE:
        if any(kw in text_lower for kw in keywords):
            return {"text": advice, "is_valid_topic": True}

    # Personalise with real plant data when available.
    count = db.query(models.Plant).count()
    if count:
        needs_water = db.query(models.Plant).filter(models.Plant.soil_moisture < 30).count()
        return {
            "text": f"You currently track {count} plant(s). "
                    + (f"{needs_water} have low soil moisture - check the Watering tab. " if needs_water else
                       "Soil moisture looks fine across your garden. ")
                    + "Scan a leaf with the Disease Scanner for a detailed diagnosis.",
            "is_valid_topic": True,
        }

    return {
        "text": "Here is a general tip: consistency matters more than intensity. Water deeply and less "
                "often, feed during active growth, and inspect leaves weekly for early signs of disease.",
        "is_valid_topic": True,
    }
