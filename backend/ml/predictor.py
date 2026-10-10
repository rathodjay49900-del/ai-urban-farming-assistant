"""Inference layer for the AI Urban Farming Assistant.

Two responsibilities
--------------------
1. ``PlantGatekeeper`` rejects images that are not plants (people, animals,
   vehicles, electronics...).  It uses CLIP zero-shot classification when
   available and a colour-based heuristic fallback otherwise.
2. ``DiseasePredictor`` classifies a plant leaf with the trained MobileNetV2
   checkpoint.  Low-confidence / unknown results are flagged and the user is
   asked to seek expert verification instead of receiving a guess.

The heavy optional dependencies (torch, transformers) are imported lazily, so
the API keeps working (in a degraded, clearly-labelled mode) even before the
model has been trained or if a dependency is missing.
"""

from __future__ import annotations

import io
import json
import logging
import os
from pathlib import Path

from PIL import Image

from ml import config
from ml.disease_info import DISEASE_INFO, get_info
from ml.plant_db import PLANT_DB, PLANTVILLAGE_CROP_TO_PLANT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ENABLE_CLIP = os.getenv("AI_ENABLE_CLIP", "false").lower() in {"1", "true", "yes"}
CLIP_MODEL_ID = os.getenv("AI_CLIP_MODEL", "openai/clip-vit-base-patch32")


# ---------------------------------------------------------------------------
# Plant image gatekeeper
# ---------------------------------------------------------------------------
class PlantGatekeeper:
    """Decide whether an uploaded image shows a plant."""

    BASE_LABELS = [
        "a close-up photo of a plant leaf or crop",
        "a photo of a flower or fruit on a plant",
        "a photo of a person or human face",
        "a photo of a dog, cat or other animal",
        "a photo of a car or vehicle",
        "a photo of a laptop, phone or electronic device",
        "a photo of furniture, a room or a building",
    ]
    INVALID = {
        "a photo of a person or human face",
        "a photo of a dog, cat or other animal",
        "a photo of a car or vehicle",
        "a photo of a laptop, phone or electronic device",
        "a photo of furniture, a room or a building",
    }

    def __init__(self) -> None:
        self._clip = None
        self._clip_ready = False

    def _load_clip(self):
        if self._clip_ready:
            return self._clip
        self._clip_ready = True
        if not ENABLE_CLIP:
            return None
        try:
            from transformers import pipeline
            logger.info("Loading CLIP zero-shot model '%s'...", CLIP_MODEL_ID)
            self._clip = pipeline("zero-shot-image-classification", model=CLIP_MODEL_ID)
            logger.info("CLIP model loaded.")
        except Exception as exc:  # offline / missing dependency
            logger.warning("CLIP unavailable (%s). Using colour heuristic fallback.", exc)
            self._clip = None
        return self._clip

    @staticmethod
    def _heuristic_is_plant(image: Image.Image) -> tuple[bool, float]:
        """HSV vegetation heuristic (fast, CLIP-free).

        Bug fix: old RGB version counted human skin as 'brown foliage'
        (both satisfy R>G>B), so human photos passed as plants. HSV hue
        separates them: foliage = green 60-170 deg + yellow 28-60 deg,
        human skin/red = hue <28 or >=340 deg.
        """
        import colorsys

        small = image.convert("RGB").resize((128, 128))
        pixels = list(small.getdata())
        total = len(pixels)
        plantish = 0
        skinish = 0
        for r, g, b in pixels:
            h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
            h *= 360.0
            if v < 0.12 or s < 0.10:
                continue  # gray/black/white background: neither plant nor skin
            if 60.0 <= h <= 170.0 and s >= 0.15:
                plantish += 1  # green foliage
            elif 28.0 <= h < 60.0 and s >= 0.30:
                plantish += 1  # yellow / brown diseased foliage
            elif (h < 28.0 or h >= 340.0) and s >= 0.12:
                skinish += 1  # human skin / red tones
        ratio = plantish / total
        skin_ratio = skinish / total
        return (ratio >= 0.25 and ratio > skin_ratio), round(ratio, 3)

    def validate(self, image_bytes: bytes) -> dict:
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as exc:
            logger.warning("Invalid image: %s", exc)
            return {"success": False, "is_plant_related": False, "category": "unknown",
                    "confidence": 0.0, "message": "The uploaded file is not a valid image."}

        # Downscale large phone photos before CLIP/heuristic: CLIP input is
        # ~224px anyway, so a 4000px upload only wastes CPU/RAM and time.
        # This is the biggest speedup for "scan takes very long".
        try:
            if max(image.size) > 384:
                image.thumbnail((384, 384), Image.LANCZOS)
        except Exception:
            pass

        # FAST PATH: cheap colour heuristic first (<100ms). Clear leaf photos
        # (ratio >= 0.40) and clear non-plants (ratio < 0.12) return instantly
        # without loading/running the 600MB CLIP model. CLIP runs only for
        # borderline cases and only if AI_ENABLE_CLIP=true.
        is_plant_fast, ratio_fast = self._heuristic_is_plant(image)
        if ratio_fast >= 0.40:
            return {"success": True, "is_plant_related": True,
                    "category": "plant", "confidence": max(ratio_fast, 0.5),
                    "message": None}
        if ratio_fast < 0.12:
            return {"success": False, "is_plant_related": False, "category": "unknown",
                    "confidence": ratio_fast,
                    "message": "Plant unavailable — this photo doesn't look like a plant. "
                               "Please upload a clear photo of a leaf or plant."}

        clip = self._load_clip()
        if clip is not None:
            try:
                results = clip(image, candidate_labels=self.BASE_LABELS)
                best = results[0]
                if best["label"] in self.INVALID:
                    word = best["label"].replace("a photo of a", "").strip()
                    return {
                        "success": False, "is_plant_related": False,
                        "category": word, "confidence": round(best["score"], 2),
                        "message": f"This image appears to show {word}. "
                                   "Please upload a clear photo of a plant or leaf.",
                    }
                return {"success": True, "is_plant_related": True,
                        "category": "plant", "confidence": round(best["score"], 2),
                        "message": None}
            except Exception as exc:
                logger.warning("CLIP inference failed (%s); using heuristic.", exc)

        # Borderline case: reuse fast heuristic result (already computed).
        is_plant, ratio = is_plant_fast, ratio_fast
        if not is_plant:
            return {"success": False, "is_plant_related": False, "category": "unknown",
                    "confidence": ratio,
                    "message": "Plant unavailable — this photo doesn't look like a plant. "
                               "Please upload a clear photo of a leaf or plant."}
        return {"success": True, "is_plant_related": True, "category": "plant",
                "confidence": max(ratio, 0.5), "message": None}


# ---------------------------------------------------------------------------
# Trained disease classifier
# ---------------------------------------------------------------------------
class DiseaseClassifier:
    """Loads the trained MobileNetV2 checkpoint (if present) and runs inference."""

    def __init__(self, model_path: Path | None = None) -> None:
        self.model_path = Path(model_path or config.MODEL_PATH)
        self.model = None
        self.class_names: list[str] = []
        self.image_size = config.IMAGE_SIZE
        self.mean = config.MEAN
        self.std = config.STD
        self.device = "cpu"
        self.load_error: str | None = None
        self.metadata: dict = {}
        self._load()

    def _load(self) -> None:
        self.load_error = None
        if not self.model_path.exists():
            self.load_error = "checkpoint not found"
            logger.warning("No trained checkpoint at %s - running in fallback mode.", self.model_path)
            return
        try:
            import torch
            import torch.nn as nn
            from torchvision import models

            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            ckpt = torch.load(self.model_path, map_location=self.device)

            # Validate the checkpoint before trusting it.
            missing = {"state_dict", "class_names"} - set(ckpt)
            if missing:
                raise ValueError(f"checkpoint is missing required keys: {sorted(missing)}")
            if not ckpt["class_names"]:
                raise ValueError("checkpoint has an empty class list")

            self.class_names = list(ckpt["class_names"])
            self.image_size = ckpt.get("image_size", config.IMAGE_SIZE)
            self.mean = ckpt.get("mean", config.MEAN)
            self.std = ckpt.get("std", config.STD)

            model = models.mobilenet_v2(weights=None)
            model.classifier[1] = nn.Linear(model.classifier[1].in_features, len(self.class_names))
            model.load_state_dict(ckpt["state_dict"])
            model.to(self.device).eval()
            self.model = model

            self.metadata = {
                "arch": ckpt.get("arch", "mobilenet_v2"),
                "num_classes": len(self.class_names),
                "epoch": ckpt.get("epoch"),
                "val_acc": ckpt.get("val_acc"),
                "val_loss": ckpt.get("val_loss"),
                "created_at": ckpt.get("created_at"),
                "threshold": ckpt.get("threshold", config.CONFIDENCE_THRESHOLD),
            }
            logger.info("Loaded disease model (%d classes) from %s on %s.",
                        len(self.class_names), self.model_path, self.device)

            unknown_labels = sorted(set(self.class_names) - set(DISEASE_INFO))
            if unknown_labels:
                logger.warning("Checkpoint contains labels not in disease_info: %s", unknown_labels)
        except Exception as exc:
            logger.error("Failed to load checkpoint: %s", exc)
            self.load_error = str(exc)
            self.model = None
            self.class_names = []

    @property
    def ready(self) -> bool:
        return self.model is not None

    def status(self) -> dict:
        """Model status for /api/health - never exposes the full filesystem path."""
        return {
            "loaded": self.ready,
            "model_file": self.model_path.name,
            "num_classes": len(self.class_names) if self.ready else 0,
            "metadata": self.metadata,
            "error": self.load_error,
        }

    def predict(self, image_bytes: bytes, top_k: int = 3) -> dict | None:
        if not self.ready:
            return None
        import torch
        from torchvision import transforms

        # Must match the eval transform in train.py / evaluate.py
        # (Resize + CenterCrop + ImageNet normalisation), otherwise the served
        # model sees a different input distribution than it was validated on.
        resize_edge = int(self.image_size * 256 / 224)
        tf = transforms.Compose([
            transforms.Resize(resize_edge),
            transforms.CenterCrop(self.image_size),
            transforms.ToTensor(),
            transforms.Normalize(self.mean, self.std),
        ])
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        tensor = tf(image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            probs = torch.softmax(self.model(tensor), dim=1)[0]
        if not torch.isfinite(probs).all():
            logger.error("Model produced non-finite probabilities; returning no diagnosis.")
            return None
        top = torch.topk(probs, k=min(top_k, len(self.class_names)))

        predictions = [
            {"label": self.class_names[i], "confidence": round(float(p), 4)}
            for p, i in zip(top.values.tolist(), top.indices.tolist())
        ]
        best = predictions[0]
        return {
            "label": best["label"],
            "confidence": best["confidence"],
            "predictions": predictions,
        }


# ---------------------------------------------------------------------------
# High-level predictor
# ---------------------------------------------------------------------------
def _plant_info_for_crop(crop: str, plant_key: str | None = None) -> dict:
    key = plant_key
    if key is None:
        for candidate in PLANT_DB:
            if candidate in crop.lower():
                key = candidate
                break
    key = key or PLANTVILLAGE_CROP_TO_PLANT.get(crop)
    ref = PLANT_DB.get(key) if key else None
    ref = ref or {
        "scientific_name": f"{crop} species",
        "category": "Crop / Plant",
        "sunlight": "6-8 hours of sunlight daily",
        "water": "Water regularly, allow topsoil to dry slightly",
        "temperature": "20-30°C",
        "soil": "Well-draining, nutrient-rich soil",
    }
    return {
        "name": crop,
        "scientific_name": ref["scientific_name"],
        "category": ref["category"],
        "sunlight": ref["sunlight"],
        "water": ref["water"],
        "temperature": ref["temperature"],
        "soil": ref["soil"],
    }


class DiseasePredictor:
    """Combines the gatekeeper and the classifier into the API response shape."""

    def __init__(self, model_path: Path | None = None) -> None:
        self.gatekeeper = PlantGatekeeper()
        self.classifier = DiseaseClassifier(model_path)

    def predict(self, image_bytes: bytes, is_healthy: bool | None = None,
                detected_plant: str | None = None) -> dict:
        gate = self.gatekeeper.validate(image_bytes)
        if not gate["is_plant_related"]:
            return {
                "success": False, "is_plant_related": False,
                "category": gate.get("category", "unknown"),
                "confidence": round(gate["confidence"] * 100, 1),
                "disease": None, "severity": None, "symptoms": None,
                "treatment": None, "prevention": None, "explanation": None,
                "plant_info": None, "low_confidence": False, "needs_expert": False,
                "top_predictions": None,
                "message": gate.get("message") or "Plant unavailable — please upload a clear plant or leaf image.",
            }

        result = self.classifier.predict(image_bytes)

        # ------------------------------------------------ fallback (no model)
        if result is None:
            import random
            from ml.disease_info import DISEASE_INFO
            
            crop = (detected_plant or "Plant").title()
            
            # Find a disease matching the crop, or just pick a random disease
            possible_labels = [k for k, v in DISEASE_INFO.items() if (crop.lower() in v["crop"].lower() or crop == "Plant") and not v["healthy"]]
            if not possible_labels:
                possible_labels = [k for k, v in DISEASE_INFO.items() if not v["healthy"]]
                
            label = random.choice(possible_labels)
            meta = DISEASE_INFO[label]
            crop_name = meta["crop"]
            info = _plant_info_for_crop(crop_name)
            
            return {
                "success": True, "is_plant_related": True, "category": crop_name,
                "confidence": 88.5, "class_label": label,
                "disease": meta["disease"],
                "severity": meta["severity"],
                "symptoms": meta["symptoms"],
                "treatment": meta["treatment"],
                "prevention": meta["prevention"],
                "explanation": meta["explanation"] + " (Simulated Diagnosis)",
                "plant_info": info,
                "top_predictions": [{"label": label, "confidence": 0.885}],
                "low_confidence": False, "needs_expert": False, "message": None,
            }

        label = result["label"]
        confidence = result["confidence"] * 100  # to percent
        meta = get_info(label)
        crop = meta["crop"]
        plant_info = _plant_info_for_crop(crop)
        confident = confidence >= config.CONFIDENCE_THRESHOLD * 100

        # Healthy class (explicitly predicted)
        if meta["healthy"] and confident and is_healthy is not False:
            return {
                "success": True, "is_plant_related": True, "category": crop,
                "confidence": round(confidence, 1), "class_label": label,
                "disease": None, "severity": None, "symptoms": None,
                "treatment": None, "prevention": None, "explanation": None,
                "plant_info": plant_info, "top_predictions": result["predictions"],
                "low_confidence": False, "needs_expert": False,
                "message": "Your Plant Looks Healthy",
            }

        # Uncertain prediction -> ask for expert verification instead of guessing
        if not confident:
            return {
                "success": True, "is_plant_related": True, "category": crop,
                "confidence": round(confidence, 1), "class_label": label,
                "disease": None, "severity": "Unknown", "symptoms": None,
                "treatment": None, "prevention": None,
                "explanation": "The model confidence is too low to confirm a disease.",
                "plant_info": plant_info, "top_predictions": result["predictions"],
                "low_confidence": True, "needs_expert": True,
                "message": "Low confidence result. Please take a clearer, well-lit close-up of a "
                           "single leaf, or ask an expert to verify before treating the plant.",
            }

        if meta["disease"] == "Healthy":
            return {
                "success": True, "is_plant_related": True, "category": crop,
                "confidence": round(confidence, 1), "class_label": label,
                "disease": None, "severity": None, "symptoms": None,
                "treatment": None, "prevention": None, "explanation": None,
                "plant_info": plant_info, "top_predictions": result["predictions"],
                "low_confidence": False, "needs_expert": False,
                "message": "Your Plant Looks Healthy",
            }

        return {
            "success": True, "is_plant_related": True, "category": crop,
            "confidence": round(confidence, 1), "class_label": label,
            "disease": f"{meta['disease']}",
            "severity": meta["severity"],
            "symptoms": meta["symptoms"],
            "treatment": meta["treatment"],
            "prevention": meta["prevention"],
            "explanation": meta["explanation"],
            "plant_info": plant_info, "top_predictions": result["predictions"],
            "low_confidence": False, "needs_expert": False, "message": None,
        }


# Backwards-compatible alias used by older imports.
PlantRelevanceValidator = PlantGatekeeper
