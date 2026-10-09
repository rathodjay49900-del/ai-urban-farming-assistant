from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import models
from config import API_HOST, API_PORT, CORS_ORIGINS
from database import engine, ensure_schema
from routes import plants, disease, assistant, watering, stats

ensure_schema()
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Urban Farming Assistant API",
    version="2.0.0",
    description="Plant species identification, disease detection and care recommendations.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(plants.router)
app.include_router(disease.router)
app.include_router(watering.router)
app.include_router(stats.router)
app.include_router(assistant.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to AI Urban Farming Assistant API", "version": "2.0.0"}


@app.get("/api/health")
def health_check():
    from routes.disease import predictor

    model = predictor.classifier.status()
    return {
        "status": "ok",
        "model_loaded": model["loaded"],
        "model": model,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=API_HOST, port=API_PORT, reload=True)
