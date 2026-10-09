# 🌱 AI Urban Farming Assistant

**"Grow Smarter. Detect Faster. Harvest Better."**

An AI-powered urban gardening assistant: identify plant species, detect leaf
diseases from photos, get treatment/prevention advice, track plant health and
receive weather-aware watering recommendations.

## Tech stack

| Layer | Stack |
|---|---|
| Frontend | React 18, Vite, TypeScript, Tailwind CSS, Framer Motion, React Router, Recharts, axios |
| Backend | Python 3, FastAPI, SQLAlchemy, Pydantic, Uvicorn |
| Database | SQLite (SQLAlchemy ORM) |
| ML | PyTorch + torchvision (MobileNetV2 transfer learning), CLIP (image validation) |

## Architecture

```
Image Upload -> Plant gatekeeper (accept/reject) -> MobileNetV2 classifier
             -> Disease + confidence + treatment/prevention
             -> saved to SQLite -> Dashboard / Plants / Watering / Insights
```

Frontend talks to the backend only through `/api/*` (Vite dev proxy), and the
backend is the single writer to the SQLite database.

## Prerequisites

* Node.js 18+ and npm
* Python 3.10+ (3.13 tested)

## Quick start

### 1. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python seed.py                 # optional: adds demo plants
uvicorn main:app --reload
```

API: http://localhost:8000  ·  Docs: http://localhost:8000/docs

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173

The Vite dev server proxies `/api` to `http://localhost:8000`, so both sides
connect automatically once started. No CORS configuration is needed in dev.

> Optional: copy `.env.example` to `.env` (backend) / set `VITE_API_URL`
> (frontend) if you want to point at a different API host.

### 3. ML model (optional but recommended)

The app works immediately without a trained model (clearly-labelled fallback).
To train the real disease classifier see **[backend/ml/README.md](backend/ml/README.md)**:

```bash
cd backend
pip install -r requirements-ml.txt
python -m ml.preprocess --dataset-dir ml/data/plantvillage
python -m ml.train --epochs 20
python -m ml.evaluate
```

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Health check + whether the ML model is loaded |
| POST | `/api/scanner/validate` | Reject non-plant images |
| POST | `/api/scanner/analyze` | Full disease analysis (saved to DB) |
| GET | `/api/scanner/history` | Recent scans |
| GET/POST | `/api/plants/` | List / register plants |
| GET/PUT/DELETE | `/api/plants/{id}` | Read / update / remove a plant |
| GET | `/api/plants/{id}/health-history` | Health timeline |
| GET | `/api/watering/recommendations` | Weather-aware watering plan |
| GET | `/api/watering/recommendation/{id}` | One plant's recommendation |
| POST | `/api/watering/log` | Record a watering event |
| GET | `/api/stats/dashboard` | Dashboard aggregates |
| GET | `/api/stats/weather` | Current weather (Open-Meteo or mock) |
| POST | `/api/assistant/chat` | Plant-care chat assistant |

## How the layers connect

* **Database:** `backend/models.py` defines `Plant`, `DiseaseScan`,
  `WateringLog`, `HealthLog`. Tables are created on startup
  (`Base.metadata.create_all`). `seed.py` populates demo data.
* **Frontend → Backend:** a single axios instance in
  `frontend/src/services/api.ts`. Pages (`Scanner`, `AddPlant`, `Plants`,
  `Dashboard`, `Watering`, `Assistant`) call it and render live data instead of
  mocks.
* **ML → Backend:** `ml/predictor.py` loads the checkpoint from `AI_MODEL_PATH`
  and returns a `ScanResponse`; the route persists each scan.

## Safety behaviour

* Only plant/leaf images are accepted (CLIP gatekeeper, offline heuristic
  fallback).
* Low-confidence predictions or unknown classes are shown as **uncertain** with
  a recommendation to seek expert verification — the app never invents a
  diagnosis from an unsupported class.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Frontend shows "Failed to connect" | Ensure the backend is running on port 8000 |
| `model_loaded: false` in `/api/health` | Train the model (see `backend/ml/README.md`) or ignore — fallback mode still works |
| CLIP download fails / slow first scan | Set `AI_ENABLE_CLIP=false` to use the offline heuristic gatekeeper |
| No plants on dashboard | Run `python seed.py` or add a plant in the UI |

## License

MIT
