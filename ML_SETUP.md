# ML Setup — Plant Disease Classifier

This project ships a **complete, reproducible** plant-disease pipeline
(MobileNetV2, 38 PlantVillage classes) and a **graceful fallback** so the app is
fully usable before the model is trained. Nothing is faked: until you train a
checkpoint the API honestly reports "model not trained" instead of inventing a
diagnosis.

> TL;DR
> ```bat
> cd backend
> pip install -r requirements.txt -r requirements-ml.txt
> python -m ml.preprocess --dataset-dir ml\data\plantvillage\color
> python -m ml.train --epochs 20
> python -m ml.evaluate
> python seed.py
> uvicorn main:app --reload
> ```

---

## 1. Prerequisites

* **Python 3.10+** (tested on 3.13).
* Backend deps: `pip install -r backend/requirements.txt`
* ML deps: `pip install -r backend/requirements-ml.txt`
  (torch, torchvision, transformers, scikit-learn, matplotlib, pytest, httpx)
* Optional **CUDA GPU** for faster training. CPU works but is slow.
  For a CUDA torch build see <https://pytorch.org/get-started/locally/>.

All commands below are run from the **`backend/`** directory.

---

## 2. Dataset

We use the **New Plant Diseases Dataset (PlantVillage)** with 38 classes:
<https://www.kaggle.com/datasets/vipoooool/new-plant-diseases-dataset>

* Use the **colour** images, `color/` folder.
* Point `AI_DATASET_DIR` at the folder that **directly contains the 38 class
  sub-folders** (an ImageFolder layout), e.g. `backend/ml/data/plantvillage/color`.
* Prefer the **original** images over the pre-augmented set — augmented copies
  create near-duplicate leakage between train and test.
* The loader also auto-detects a one-level-deeper nesting and supports
  `.jpg/.jpeg/.png/.bmp/.webp`.

Set the location with an environment variable or copy `.env.example` to `.env`:

```bat
set AI_DATASET_DIR=D:\datasets\plantvillage\color
```

You can also just drop the folder at the default `backend/ml/data/plantvillage/color`.

---

## 3. Preprocess + verify

```bat
python -m ml.preprocess --dataset-dir ml\data\plantvillage\color
```

This will:

1. **Verify** every image opens (corrupt files are reported and skipped).
2. Report **unknown** class folders and **missing** of the 38 supported classes.
3. Fail clearly if any class has fewer than `AI_MIN_SAMPLES_PER_CLASS` images
   (default 10) so a split can never end up empty.
4. Remove **exact duplicates** (MD5) and optionally **near duplicates**
   (perceptual dHash) so the same photo cannot leak across splits.
5. Produce a **stratified 70/15/15** split with a fixed seed and an
   **inverse-frequency class-weight** map for imbalance.
6. Write `ml/data/splits/manifest.json` and `.../verification_report.json`.

Useful flags:

| Flag | Meaning |
|------|---------|
| `--allow-missing` | train on a subset instead of all 38 classes |
| `--near-dup-threshold N` | dHash Hamming distance for near-duplicate removal (`0` = off) |
| `--min-samples N` | override the per-class minimum |
| `--no-verify` | skip opening every image (faster, less safe) |

The manifest stores **relative paths only** — the dataset is never modified.

---

## 4. Train

```bat
python -m ml.train --epochs 20
```

Details:

* 224×224 RGB, ImageNet normalisation (matches the pretrained weights).
* Augmentation: random resized crop, horizontal flip, ±15° rotation, colour jitter.
* Weighted cross-entropy, **AdamW-style** Adam optimiser, default **LR = 1e-4**.
* `ReduceLROnPlateau` + early stopping (`AI_EARLY_STOP`, default 5).
* Saves the **best validation** checkpoint, never the last epoch.
* Aborts on NaN/inf loss, empty splits or labels outside the class map.

Progressive fine-tuning (freeze backbone, then unfreeze):

```bat
python -m ml.train --freeze-backbone --unfreeze-epoch 3
```

Offline / no download of ImageNet weights:

```bat
python -m ml.train --no-pretrained
```

Outputs in `backend/ml/model/`:

| File | Contents |
|------|----------|
| `plant_disease_model.pth` | architecture, weights, class names, preprocessing, metrics |
| `labels.json` | ordered class names |
| `training_history.json` | per-epoch loss/acc/LR/time |
| `metadata.json` | full training config + manifest hash + timestamp |

Key environment overrides: `AI_EPOCHS`, `AI_BATCH_SIZE`, `AI_LEARNING_RATE`,
`AI_IMAGE_SIZE`, `AI_NUM_WORKERS`, `AI_SEED`.

---

## 5. Evaluate

```bat
python -m ml.evaluate
```

Runs on the **held-out test split only** and writes to `backend/ml/evaluation/`:

| File | Contents |
|------|----------|
| `report.json` / `report.txt` | overall accuracy, macro & weighted P/R/F1, per-class table |
| `confusion_matrix.json` / `.png` | raw + normalised confusion matrix |
| `classification_report.json` | sklearn per-class precision/recall/F1/support |
| `training_history.png` | loss / accuracy / LR curves |
| `experiment.json` | checkpoint + manifest metadata (reproducibility) |

> **Important limitation:** PlantVillage photos are **controlled-background lab
> images**. Accuracy on real phone photos will be lower. Always validate on your
> own images before trusting a diagnosis.

---

## 6. Backend integration

* `backend/routes/disease.py` builds **one** `DiseasePredictor` at import time.
  The checkpoint is loaded **once** — never per request.
* `POST /api/scanner/analyze` keeps its existing response schema and now returns
  real `crop`, `disease`, `confidence`, `severity`, `treatment`, etc.
* Healthy vs diseased classes are handled distinctly; low-confidence results are
  flagged (`low_confidence`, `needs_expert`) and no disease is invented.
* The `PlantGatekeeper` (CLIP zero-shot, with a colour heuristic fallback) rejects
  non-plant images **before** the classifier runs. Disable CLIP with
  `AI_ENABLE_CLIP=false`.
* Upload guard: reject files over `AI_MAX_UPLOAD_MB` (default 10 MB) and
  unsupported content types.
* `GET /api/health` reports whether the model is loaded plus safe metadata
  (class count, epoch, val accuracy) — **without exposing filesystem paths**.

At startup you will see either:

* `Loaded disease model (38 classes) ...` — real inference, or
* `No trained checkpoint ... fallback mode` — the API still works and returns a
  clear "model not trained" message.

---

## 7. Run the app

```bat
cd backend
python seed.py            :: optional demo plants
uvicorn main:app --reload :: http://localhost:8000  (docs at /docs)

cd ..\frontend
npm install
npm run dev               :: http://localhost:5173
```

Vite proxies `/api` to `http://localhost:8000`.

---

## 8. Tests

```bat
cd backend
pytest -q
pytest tests\test_preprocess.py -q
```

Coverage:

* `test_disease_info.py` — the 38 classes are canonical and complete.
* `test_preprocess.py` — dedup, corrupt detection, min-samples, missing classes,
  leakage = 0, near-dup + dHash behaviour.
* `test_predictor.py` — gatekeeper accepts leaves / rejects non-plants, invalid
  or missing checkpoints degrade safely, **no fake tomato diagnosis**.
* `test_api.py` — health metadata (no path leak), plant CRUD + health history,
  watering logs, dashboard stats, scanner analyze/reject + upload limits.

Frontend: run `npm run build` (tsc type-check) and `npm run lint`. There is no
JS unit-test runner configured (see "Remaining work").

---

## 9. Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Dataset directory not found` | Set `AI_DATASET_DIR` to the folder with the class sub-folders |
| `fewer than 10 usable images` | Lower `AI_MIN_SAMPLES_PER_CLASS` / `--min-samples`, or use the full dataset |
| `Missing ... supported class folder(s)` | Use `--allow-missing` for a subset, or supply the full 38 classes |
| `Could not obtain ... pretrained weights` | Offline: `--no-pretrained`, or pre-populate the torch hub cache |
| `Non-finite loss` | Check the manifest/labels; lower the learning rate |
| `CLIP unavailable` | Expected offline; the colour heuristic is used. Set `AI_CLIP_MODEL` to a local path if desired |
| Very slow on CPU | Train overnight or use a GPU / Colab, then copy the `.pth` here |

---

## 10. Reproducibility checklist

* Same seed (`AI_SEED`, `AI_SPLIT_SEED`) → same split and same init.
* `metadata.json` stores the manifest SHA-256 and full training config.
* `labels.json` is always `sorted(DISEASE_INFO)` — class indices never change.
* Model + `labels.json` + `metadata.json` must be kept together.

### Honest status

The training pipeline, evaluation, integration and tests are complete and
reproducible, but **no checkpoint is committed** in this environment (no dataset
/ GPU here). The app therefore runs in the clearly-labelled fallback mode until
you follow sections 2–5 above.
