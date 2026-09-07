from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.health import router as health_router
from api.projects import router as projects_router
from api.generation import router as generation_router

STORAGE_DIR = Path(__import__("os").getenv("STORAGE_DIR", "./storage"))
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Lazarius Video AI", version="0.4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/api/media", StaticFiles(directory=str(STORAGE_DIR)), name="media")
app.include_router(health_router, prefix="/api")
app.include_router(projects_router, prefix="/api")
app.include_router(generation_router, prefix="/api")


@app.get("/")
def root():
    return {
        "name": "Lazarius Video AI",
        "status": "running",
        "version": "0.4.0",
        "architecture": "low-pc-cloud-first",
    }
