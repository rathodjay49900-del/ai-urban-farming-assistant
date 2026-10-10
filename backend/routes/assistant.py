from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import schemas
import models
from database import get_db

router = APIRouter(prefix="/api/assistant", tags=["Assistant"])

# English keywords + Hinglish/Hindi equivalents so "paani", "mitti",
# "dhoop", "patta" jaise messages ka bhi jawab aaye.
PLANT_KEYWORDS = [
    "plant", "farm", "garden", "crop", "water", "watering", "soil", "sun", "sunlight",
    "leaf", "leaves", "disease", "pest", "grow", "growth", "harvest", "seed", "fertil",
    "tomato", "chilli", "chili", "potato", "rose", "basil", "mint", "compost", "prune",
    "blight", "mildew", "rust", "spot", "fungus", "fungal", "aphid", "mite", "yellow",
    "flower", "fruit", "stem", "root", "pot", "balcony", "indoor", "rain", "heat",
    # Hinglish / Hindi (roman)
    "paudha", "podha", "paudhe", "pani", "paani", "mitti", "matti", "dhoop",
    "patta", "patte", "beej", "khad", "keeda", "keede", "peela", "peele",
    "dhaniya", "palak", "tulsi", "genda", "gulab", "nimbu", "tamatar",
]

# Hindi -> English helper so the same knowledge base answers both.
HINDI_MAP = {
    "paudha": "plant", "podha": "plant", "paudhe": "plant", "podhe": "plant",
    "pani": "water", "paani": "water",
    "mitti": "soil", "matti": "soil",
    "dhoop": "sunlight", "suraj": "sun",
    "patta": "leaf", "patte": "leaves",
    "beej": "seed", "khad": "fertilizer",
    "keeda": "pest", "keede": "pest",
    "peela": "yellow", "peele": "yellow", "peeli": "yellow",
}

GREETINGS = ["hello", "hi", "hey", "namaste", "namaskar", "ram ram",
             "good morning", "good evening", "salaam", "sat sri"]

KNOWLEDGE = [
    (["water", "watering", "dry", "moist", "pani"], "Water at the base of the plant, early in the morning. "
     "Let the top 2-3 cm of soil dry out between waterings to prevent root rot. "
     "Most indoor plants need water every 2-3 days in summer, less in winter."),
    (["yellow", "yellowing", "peela"], "Yellowing can come from overwatering, nutrient deficiency or disease. "
     "Check soil moisture first (don't water if the top soil is still wet), then inspect the leaf undersides for pests. "
     "Remove fully yellow leaves so the plant saves energy."),
    (["blight"], "Blight spreads fast in cool, wet conditions. Remove and destroy infected leaves, "
     "improve airflow and avoid overhead watering."),
    (["mildew"], "Powdery mildew thrives in humid air with dry soil. Improve ventilation, "
     "remove affected leaves and apply a potassium-bicarbonate or sulfur spray."),
    (["rust"], "Rust shows as orange-brown pustules under leaves. Remove affected leaves, avoid wetting foliage, "
     "and improve air circulation. A copper or sulfur spray helps in early stages."),
    (["spot"], "Leaf spots are usually fungal/bacterial. Remove spotted leaves, avoid overhead watering, "
     "mulch to stop soil splash, and run a Disease Scanner check for the exact cause."),
    (["pest", "aphid", "mite", "bug", "keeda"], "Inspect leaf undersides. A jet of water, insecticidal soap "
     "or neem oil handles most soft-bodied pests. Repeat every 5-7 days for 2-3 rounds and introduce beneficial insects when possible."),
    (["fertil", "nutrient", "khad"], "Feed with a balanced fertiliser during active growth, and switch to a "
     "lower-nitrogen blend once flowering begins. Compost every 3-4 weeks is enough for most balcony plants — overfeeding burns roots."),
    (["soil", "mitti", "compost"], "Most vegetables prefer loose, well-draining soil rich in organic matter. "
     "Mix garden soil + compost + sand/cocopeat roughly 40:30:30. Add compost and check that water does not pool around the roots."),
    (["sun", "sunlight", "light", "dhoop"], "Most fruiting crops (tomato, chilli) need 6-8 hours of direct sun. "
     "Leafy greens and mint tolerate partial shade. Balcony east-facing is ideal — harsh afternoon sun burns leaves."),
    (["seed", "beej", "germin"], "Sow seeds 2x as deep as their size, keep soil moist (not soggy), and give warmth (20-28°C). "
     "Most veggie seeds sprout in 5-12 days. Don't bury tiny seeds like basil too deep."),
    (["harvest"], "Harvest in the morning when leaves/fruits are crisp. Pick regularly — the more you pick herbs like basil and mint, "
     "the bushier they grow. Never remove more than one-third of the plant at once."),
    (["prune", "cutting", "trim"], "Prune dead/yellow leaves first, cut just above a leaf node, and always use clean scissors. "
     "Pinch basil/mint tips to make them bushy."),
    (["pot", "container", "balcony", "indoor"], "Use pots with drainage holes, slightly bigger than the root ball. "
     "Balcony plants dry faster — check soil daily in summer. Rotate indoor pots weekly so all sides get light."),
    (["rain", "barish"], "Rain is good but waterlogging kills roots. Move pots where excess water drains out, "
     "skip manual watering on rainy days, and watch for fungal spots after continuous rain."),
    (["heat", "hot", "garmi", "temperature"], "Above 35°C plants stress: move pots to morning-sun only, mulch the topsoil, "
     "and water early morning. Wilting in afternoon heat is normal if leaves recover by evening."),
    (["disease", "fungus", "fungal", "sick", "bimar"], "For any sick plant: 1) isolate it, 2) remove worst leaves, "
     "3) run the Disease Scanner with a clear single-leaf close-up for the exact diagnosis + treatment. "
     "Don't guess medicine before diagnosis."),
    (["scan"], "Open the Disease Scanner, upload a clear close-up of ONE leaf in good light, and you'll get "
     "crop, disease, severity and treatment steps. Human/animal photos are rejected with a 'Plant unavailable' message."),
    (["tomato", "tamatar"], "Tomato needs 6-8 hrs sun, support stick, and base watering (never on leaves). "
     "Yellow lower leaves + brown rings = early blight usually. Mulch helps a lot."),
    (["chilli", "chili", "mirch"], "Chilli loves sun and hates soggy roots. Water only when topsoil is dry. "
     "Curled leaves often mean mites/aphids — check leaf undersides and spray neem oil."),
    (["mint", "pudina"], "Mint is thirsty and spreads fast — keep it in its own pot, soil always slightly moist, "
     "partial shade is fine. Pinch regularly."),
    (["basil", "tulsi"], "Basil needs sun + daily light watering. Pinch flower buds to keep leaves tasty. "
     "Black spots usually mean too much water on leaves."),
    (["rose", "gulab"], "Rose needs full sun, airy spot and regular deadheading (remove spent flowers). "
     "Black spot on leaves = remove them, avoid wetting foliage."),
    (["flower", "fruit"], "No flowers/fruits usually means less sun or excess nitrogen. Give 6+ hrs sun, "
     "switch to a low-nitrogen (flowering) feed, and don't overwater."),
    (["root", "stem"], "Mushy stem/base = overwatering or root rot. Let soil dry fully, improve drainage, "
     "and trim rotted roots before repotting in fresh mix."),
    (["grow", "growth"], "Healthy growth = right light + right water + monthly feeding. Track health score in the app, "
     "scan leaves every 1-2 weeks, and log watering so the schedule stays correct."),
]


@router.post("/chat", response_model=schemas.ChatResponse)
def chat_assistant(message: schemas.ChatMessage, db: Session = Depends(get_db)):
    raw = (message.text or "").strip()
    if not raw:
        return {"text": "Please type your plant question — for example: 'mere tomato ke patte peele ho rahe hain, kya karu?'", "is_valid_topic": True}
    text_lower = raw.lower()
    # Map Hindi words to English so one knowledge base answers both.
    for hindi, eng in HINDI_MAP.items():
        if hindi in text_lower and eng not in text_lower:
            text_lower = f"{text_lower} {eng}"

    # Greetings / thanks / bye always get a warm reply.
    if any(g == text_lower or text_lower.startswith(g + " ") or g in text_lower for g in GREETINGS) and len(text_lower.split()) <= 4:
        return {"text": "Namaste! 🌱 Main aapka PlantAI hoon. Paudhe, pani, mitti, dhoop, keede ya bimari — kuch bhi poochho, jaise 'tulsi me kitna pani du?'", "is_valid_topic": True}
    if "thank" in text_lower or "shukriya" in text_lower or "dhanyavad" in text_lower:
        return {"text": "You're welcome! 🌱 Paudhon ko roz thoda observe karo — wahi sabse achhi care hai. Aur koi sawal ho to poochho.", "is_valid_topic": True}
    if text_lower in {"bye", "alvida", "phir milenge"} or text_lower.startswith("bye "):
        return {"text": "Bye! Happy farming! 🌱 Paudhon me pani subah dena, shaam ko leaves check karna.", "is_valid_topic": True}

    # Best knowledge match (longest keyword wins).
    best = None
    best_len = 0
    for keywords, advice in KNOWLEDGE:
        hit = next((kw for kw in keywords if kw in text_lower), None)
        if hit and len(hit) > best_len:
            best, best_len = advice, len(hit)
    if best:
        return {"text": best, "is_valid_topic": True}

    is_valid = any(kw in text_lower for kw in PLANT_KEYWORDS)

    # Personalise with real plant data when available.
    try:
        count = db.query(models.Plant).count()
    except Exception:
        count = 0
    if count:
        try:
            needs_water = db.query(models.Plant).filter(models.Plant.soil_moisture < 30).count()
        except Exception:
            needs_water = 0
        if is_valid:
            return {
                "text": f"You currently track {count} plant(s). "
                        + (f"{needs_water} have low soil moisture - check the Watering tab. " if needs_water else
                           "Soil moisture looks fine across your garden. ")
                        + "Scan a leaf with the Disease Scanner for a detailed diagnosis.",
                "is_valid_topic": True,
            }
        # Off-topic but user has plants: still answer helpfully + guide.
        short = raw[:80]
        return {
            "text": f"Aapne poochha: '{short}'. Main paudhon ka assistant hoon — paani, mitti, dhoop, khad, keede ya patte ki bimari par turant jawab dunga. "
                    f"Aapke paas {count} plant(s) hain. Koi plant sawal try karo, jaise 'mint me kitna pani du?'",
            "is_valid_topic": True,
        }

    # No plants yet + no topic match: still reply, never silence.
    if is_valid:
        return {
            "text": "Here is a general tip: consistency matters more than intensity. Water deeply and less "
                    "often, feed during active growth, and inspect leaves weekly for early signs of disease. "
                    "Apna pehla paudha Plants page se add karo taaki main exact salah de saku.",
            "is_valid_topic": True,
        }
    short = raw[:80]
    return {
        "text": f"Aapne poochha: '{short}'. Main PlantAI hoon — paudhe, pani, mitti, dhoop, beej, khad ya patte ki bimari ke baare me kuch bhi poochho, "
                "main turant jawab dunga. Jaise: 'tomato me kitna pani du?' ya 'patte peele kyun ho rahe hain?'",
        "is_valid_topic": True,
    }
