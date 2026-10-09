"""Central configuration for the ML pipeline.

Values can be overridden with environment variables so the same code works on
a laptop and on a training server. Every path/constant used by
``preprocess.py``, ``train.py``, ``evaluate.py`` and ``predictor.py`` lives here
so training and inference can never disagree silently.
"""

from __future__ import annotations

import os
from pathlib import Path

# Project directory layout -------------------------------------------------
ML_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ML_DIR.parent
MODEL_DIR = Path(os.getenv("AI_MODEL_DIR", ML_DIR / "model"))

# ------------------------------------------------------------------ Files
MODEL_PATH = Path(os.getenv("AI_MODEL_PATH", MODEL_DIR / "plant_disease_model.pth"))
LABELS_PATH = Path(os.getenv("AI_LABELS_PATH", MODEL_DIR / "labels.json"))
METADATA_PATH = Path(os.getenv("AI_METADATA_PATH", MODEL_DIR / "metadata.json"))
TRAINING_HISTORY_PATH = Path(os.getenv("AI_HISTORY_PATH", MODEL_DIR / "training_history.json"))
EVAL_DIR = Path(os.getenv("AI_EVAL_DIR", ML_DIR / "evaluation"))

# -------------------------------------------------------------- Dataset
# Root folder that contains one sub-folder per class (ImageFolder layout).
DATASET_DIR = Path(os.getenv("AI_DATASET_DIR", ML_DIR / "data" / "plantvillage" / "color"))
SPLIT_DIR = Path(os.getenv("AI_SPLIT_DIR", ML_DIR / "data" / "splits"))
MANIFEST_PATH = SPLIT_DIR / "manifest.json"
VERIFICATION_PATH = SPLIT_DIR / "verification_report.json"

# 70 / 15 / 15 reproducible split
TRAIN_RATIO = float(os.getenv("AI_TRAIN_RATIO", "0.70"))
VAL_RATIO = float(os.getenv("AI_VAL_RATIO", "0.15"))
TEST_RATIO = float(os.getenv("AI_TEST_RATIO", "0.15"))
SPLIT_SEED = int(os.getenv("AI_SPLIT_SEED", "42"))

# Dataset validation guards
MIN_SAMPLES_PER_CLASS = int(os.getenv("AI_MIN_SAMPLES_PER_CLASS", "10"))
REQUIRE_ALL_CLASSES = os.getenv("AI_REQUIRE_ALL_CLASSES", "true").lower() in {"1", "true", "yes"}
# Perceptual-hash (dHash) Hamming distance used to drop *near* duplicates.
# 0 disables the extra pass (exact MD5 de-duplication still always runs).
NEAR_DUP_THRESHOLD = int(os.getenv("AI_NEAR_DUP_THRESHOLD", "0"))

# ---------------------------------------------------------- Training
IMAGE_SIZE = int(os.getenv("AI_IMAGE_SIZE", "224"))
BATCH_SIZE = int(os.getenv("AI_BATCH_SIZE", "32"))
EPOCHS = int(os.getenv("AI_EPOCHS", "20"))
LEARNING_RATE = float(os.getenv("AI_LEARNING_RATE", "0.0001"))
WEIGHT_DECAY = float(os.getenv("AI_WEIGHT_DECAY", "0.0001"))
NUM_WORKERS = int(os.getenv("AI_NUM_WORKERS", "2"))
SEED = int(os.getenv("AI_SEED", "42"))
EARLY_STOP_PATIENCE = int(os.getenv("AI_EARLY_STOP", "5"))
LR_SCHEDULER_PATIENCE = int(os.getenv("AI_LR_PATIENCE", "2"))

# ImageNet statistics - correct for MobileNetV2 pretrained weights.
MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]

# -------------------------------------------------------- Inference
# Predictions below this confidence are reported as "uncertain" and the user
# is asked to consult an expert instead of receiving a diagnosis.
# NOTE: softmax confidence is not a calibrated probability - tune this on the
# held-out validation split (see ML_SETUP.md).
CONFIDENCE_THRESHOLD = float(os.getenv("AI_CONFIDENCE_THRESHOLD", "0.60"))

# -------------------------------------------------------- Upload limits
MAX_UPLOAD_MB = int(os.getenv("AI_MAX_UPLOAD_MB", "10"))
# "application/octet-stream" is allowed because some browsers/clients do not set
# a meaningful MIME type; Pillow still validates the actual bytes afterwards.
ALLOWED_CONTENT_TYPES = {
    "image/jpeg", "image/jpg", "image/png", "image/bmp", "image/webp",
    "application/octet-stream",
}
