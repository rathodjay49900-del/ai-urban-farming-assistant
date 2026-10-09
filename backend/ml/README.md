# Plant Disease Model — Training & Integration

MobileNetV2 transfer-learning classifier for the AI Urban Farming Assistant.
It classifies a leaf image into one of the **38 PlantVillage classes** (crops
include tomato, potato, pepper, apple, grape, corn, cherry, peach, orange,
strawberry, squash, soybean, blueberry and raspberry) and the API attaches
disease-specific treatment, prevention and care advice.

> The application runs **without** a trained model. Until you train one,
> `ml/predictor.py` reports plant identification via the CLIP/heuristic
> gatekeeper and returns a clearly-labelled "model not trained" fallback instead
> of a false diagnosis.

## 1. Dataset sources & licenses

| Dataset | Images | Classes | License | Link |
|---|---|---|---|---|
| New Plant Diseases Dataset (default) | ~87k | 38 | CC BY-SA 4.0 — check page | https://www.kaggle.com/datasets/vipoooool/new-plant-diseases-dataset |
| PlantVillage (original) | ~54k | 38 | CC0 1.0 (public domain) | https://www.kaggle.com/datasets/abdallahalidev/plantvillage-dataset |
| PlantVillage paper | — | — | arXiv preprint | https://arxiv.org/abs/1511.08060 |

Always re-verify the license on the dataset page before redistribution. The
class names are defined in `ml/disease_info.py` and match the Kaggle folders.

### Getting the data

```bash
# Option A - manual (no credentials): download + unzip, then point at the
# folder that directly contains the 38 class sub-folders.
set AI_DATASET_DIR=C:\data\plantvillage

# Option B - automatic (needs ~/.kaggle/kaggle.json)
python -m ml.download_dataset --download --dataset-dir ml/data/plantvillage

# Verify layout
python -m ml.download_dataset --verify --dataset-dir ml/data/plantvillage
```

## 2. Install ML dependencies

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-ml.txt        # torch, torchvision, transformers, ...
```

For a CUDA build of PyTorch follow https://pytorch.org/get-started/locally/.

## 3. Preprocess (dedup, leakage check, 70/15/15 split)

```bash
python -m ml.preprocess --dataset-dir ml/data/plantvillage
```

This writes `ml/data/splits/manifest.json` containing:

* a stratified **70% train / 15% validation / 15% test** split (fixed seed 42),
* **exact-duplicate removal** by MD5 so the same image cannot leak across splits,
* a **cross-split leakage check** (must report `0`),
* inverse-frequency **class weights** for class balancing.

It also reports, per class, how many images went into each split.

## 4. Train (transfer learning, augmentation, callbacks)

```bash
python -m ml.train --epochs 20 --batch-size 32 --lr 0.001
```

| Hyperparameter | Default | Env var |
|---|---|---|
| Image size | 224×224 | `AI_IMAGE_SIZE` |
| Batch size | 32 | `AI_BATCH_SIZE` |
| Epochs | 20 | `AI_EPOCHS` |
| Learning rate | 1e-3 | `AI_LEARNING_RATE` |
| Weight decay | 1e-4 | `AI_WEIGHT_DECAY` |
| Early-stop patience | 5 | `AI_EARLY_STOP` |
| LR scheduler patience | 2 | `AI_LR_PATIENCE` |

What the trainer does:

* MobileNetV2 pretrained on ImageNet, classifier head replaced (38 outputs).
* Augmentation: random resized crop, horizontal/vertical flip, rotation ±20°,
  colour jitter; validation uses resize + normalise only (ImageNet stats).
* **Adam** optimiser + weighted **CrossEntropyLoss** (class balancing).
* `ReduceLROnPlateau` learning-rate scheduling.
* **Early stopping** and **best-model checkpointing** on validation loss.
* Writes `ml/model/plant_disease_model.pth`, `ml/model/labels.json` and
  `ml/model/training_history.json`.

`--freeze-backbone` trains only the classifier head (faster, useful for small
datasets or CPU-only machines).

## 5. Evaluate

```bash
python -m ml.evaluate --checkpoint ml/model/plant_disease_model.pth
```

Outputs to `ml/evaluation/`:

* `report.json` — accuracy, macro/weighted precision, recall and F1, plus
  per-class metrics and the full confusion matrix,
* `classification_report.txt` (scikit-learn) ,
* `confusion_matrix.png` (matplotlib).

## 6. Model export / integration

The checkpoint is a self-contained PyTorch file; `ml/predictor.py` reconstructs
the architecture from the stored `class_names` and loads `state_dict`. The
FastAPI backend loads it automatically at first request:

* path from `AI_MODEL_PATH` (default `ml/model/plant_disease_model.pth`),
* `GET /api/health` reports `model_loaded: true/false`,
* predictions below `AI_CONFIDENCE_THRESHOLD` (default 0.60) are returned with
  `low_confidence: true` / `needs_expert: true` and **no** disease name, so the
  UI recommends expert verification instead of guessing.

To move to TensorFlow/Keras instead, keep `labels.json` as the contract and
export to `.keras`/SavedModel; only `DiseaseClassifier._load`/`predict` need to
change.

## 7. Plant-image validation (reject non-plant uploads)

`PlantGatekeeper` in `ml/predictor.py` accepts only plant/leaf images:

* **CLIP** zero-shot classification (`openai/clip-vit-base-patch32`) when
  `AI_ENABLE_CLIP=true`, otherwise
* a colour-based vegetation heuristic fallback (green/brown pixel ratio,
  skin-tone rejection) that works fully offline.

## 8. Testing instructions

```bash
# Backend unit-level smoke tests (no dataset required if model is untrained)
python -m ml.preprocess --dataset-dir ml/data/plantvillage --help
python -m ml.train --help
python -m ml.evaluate --help

# API smoke test
uvicorn main:app --reload
# then, in another shell:
curl http://localhost:8000/api/health
curl -F "file=@leaf.jpg" http://localhost:8000/api/scanner/analyze
curl -F "file=@cat.jpg"  http://localhost:8000/api/scanner/analyze   # must be rejected
```

## 9. Reproducibility

* Fixed seeds for the split (`AI_SPLIT_SEED`) and training (`AI_SEED`).
* The split is materialised once into `manifest.json` and reused by training and
  evaluation, so results are comparable across runs.
* Duplicate removal + leakage check guarantee no image overlap between splits.
