"""Create a workable demo checkpoint so /api/health reports model_loaded=true.

This does NOT fake accuracy:
- weights are ImageNet-pretrained backbone (if cached/offline fallback to random)
  + a randomly-initialized 38-class head,
- val_acc is stored as 0.0 with a clear demo flag,
- at inference the 60% confidence gate will therefore return
  low_confidence/needs_expert (uncertain) instead of inventing a diagnosis.

Run from backend/:
    pip install -r requirements.txt -r requirements-ml.txt
    python create_demo_model.py
    python -c "from ml.predictor import DiseasePredictor; print(DiseasePredictor().classifier.status())"

For a REAL model you still need the PlantVillage dataset:
    train_model.bat --data "D:\\datasets\\plantvillage\\color"
See ML_SETUP.md sections 2-5.
"""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from ml import config
from ml.disease_info import DISEASE_INFO


def main() -> int:
    try:
        import torch
        import torch.nn as nn
        from torchvision import models
    except Exception as exc:
        print(f"ERROR: torch/torchvision not installed ({exc})")
        print("Run: pip install -r requirements-ml.txt  (from backend/)")
        return 1

    class_names = sorted(DISEASE_INFO.keys())
    print(f"Building MobileNetV2 with {len(class_names)} classes...")

    # Try ImageNet weights (better features), fall back to random offline.
    model = None
    pretrained_used = False
    for attempt_pretrained in (True, False):
        try:
            from torchvision.models import MobileNet_V2_Weights
            weights = MobileNet_V2_Weights.IMAGENET1K_V1 if attempt_pretrained else None
            model = models.mobilenet_v2(weights=weights)
            pretrained_used = attempt_pretrained
            break
        except Exception as exc:
            print(f"  pretrained={attempt_pretrained} failed ({exc}), trying next...")
            model = None
    if model is None:
        print("ERROR: could not build MobileNetV2 at all.")
        return 1

    model.classifier[1] = nn.Linear(model.classifier[1].in_features, len(class_names))
    model.eval()

    ckpt = {
        "arch": "mobilenet_v2",
        "state_dict": model.state_dict(),
        "class_names": class_names,
        "num_classes": len(class_names),
        "image_size": config.IMAGE_SIZE,
        "mean": config.MEAN,
        "std": config.STD,
        "threshold": config.CONFIDENCE_THRESHOLD,
        "val_acc": 0.0,
        "val_loss": 0.0,
        "epoch": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "demo_checkpoint": True,
        "note": "Demo/synthetic weights only - real PlantVillage training still required for accurate diagnosis.",
    }

    out_dir = Path(config.MODEL_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    torch.save(ckpt, out_dir / "plant_disease_model.pth")
    (out_dir / "labels.json").write_text(json.dumps(class_names, indent=2), encoding="utf-8")
    (out_dir / "training_history.json").write_text(json.dumps([], indent=2), encoding="utf-8")
    metadata = {
        "arch": "mobilenet_v2",
        "num_classes": len(class_names),
        "class_names": class_names,
        "demo_checkpoint": True,
        "pretrained_backbone": pretrained_used,
        "best_val_acc": 0.0,
        "trained_at": ckpt["created_at"],
        "note": "Demo weights. Train on PlantVillage for real accuracy (see ML_SETUP.md).",
    }
    (out_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"OK wrote {out_dir / 'plant_disease_model.pth'}")
    print(f"   pretrained_backbone={pretrained_used}, classes={len(class_names)}")

    # Self-verify load path identical to predictor.py
    try:
        from ml.predictor import DiseasePredictor
        status = DiseasePredictor().classifier.status()
        print(f"Verify status: loaded={status['loaded']}, num_classes={status['num_classes']}")
        if not status["loaded"]:
            print(f"WARNING: predictor still not loading: {status.get('error')}")
            return 1
    except Exception as exc:
        print(f"WARNING: self-verify failed: {exc}")
    print("Done. Restart backend: uvicorn main:app --reload ; check GET /api/health")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
