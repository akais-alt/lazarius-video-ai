import os
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from pydantic import BaseModel, Field, HttpUrl
from services.pipeline_service import PipelineService
from services.job_service import jobs
from services.runtime_service import RuntimeService

router = APIRouter(prefix="/generate", tags=["generation"])
pipeline = PipelineService()
runtime = RuntimeService()
STORAGE_DIR = Path(os.getenv("STORAGE_DIR", "./storage"))
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
MAX_IMAGE_BYTES = int(os.getenv("MAX_IMAGE_UPLOAD_MB", "10")) * 1024 * 1024
MAX_VIDEO_BYTES = int(os.getenv("MAX_MOTION_VIDEO_UPLOAD_MB", "100")) * 1024 * 1024
ALLOWED_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
ALLOWED_VIDEO_TYPES = {"video/mp4": ".mp4", "video/webm": ".webm", "video/quicktime": ".mov"}


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=3)
    duration: int = Field(default=30, ge=1, le=600)
    aspect_ratio: str = Field(default="9:16")
    language: str = Field(default="fr")
    style: str = Field(default="cinematic")
    mode: str = Field(default="auto", pattern="^(auto|local|cloud)$")
    quality: str = Field(default="720p", pattern="^(480p|720p|1080p)$")
    image_url: HttpUrl | None = None
    motion_video_url: HttpUrl | None = None
    character_description: str | None = Field(default=None, max_length=1000)
    character_engine: str = Field(default="auto", pattern="^(auto|i2v_5b|wan_animate)$")
    chain_scenes: bool = False


@router.get("/runtime")
def runtime_info():
    return runtime.as_dict()


@router.post("/media/upload")
async def upload_image(file: UploadFile = File(...)):
    extension = ALLOWED_TYPES.get(file.content_type or "")
    if not extension:
        raise HTTPException(status_code=415, detail="Format image non supporté. Utilise JPG, PNG ou WebP.")
    data = await file.read(MAX_IMAGE_BYTES + 1)
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail=f"Image trop volumineuse. Maximum: {MAX_IMAGE_BYTES // (1024 * 1024)} Mo.")
    filename = f"upload_{uuid.uuid4().hex}{extension}"
    (STORAGE_DIR / filename).write_bytes(data)
    relative_url = f"/api/media/{filename}"
    url = f"{PUBLIC_BASE_URL}{relative_url}" if PUBLIC_BASE_URL else relative_url
    return {"status": "completed", "filename": filename, "url": url, "public": bool(PUBLIC_BASE_URL)}


@router.post("/media/upload-motion")
async def upload_motion_video(file: UploadFile = File(...)):
    extension = ALLOWED_VIDEO_TYPES.get(file.content_type or "")
    if not extension:
        raise HTTPException(status_code=415, detail="Vidéo non supportée. Utilise MP4, WebM ou MOV.")
    data = await file.read(MAX_VIDEO_BYTES + 1)
    if len(data) > MAX_VIDEO_BYTES:
        raise HTTPException(status_code=413, detail=f"Vidéo trop volumineuse. Maximum: {MAX_VIDEO_BYTES // (1024 * 1024)} Mo.")
    filename = f"motion_{uuid.uuid4().hex}{extension}"
    (STORAGE_DIR / filename).write_bytes(data)
    relative_url = f"/api/media/{filename}"
    url = f"{PUBLIC_BASE_URL}{relative_url}" if PUBLIC_BASE_URL else relative_url
    return {"status": "completed", "filename": filename, "url": url, "public": bool(PUBLIC_BASE_URL)}


@router.post("/plan")
async def generate_plan(data: GenerateRequest):
    return await pipeline.plan(**data.model_dump(exclude={"mode", "quality", "image_url", "motion_video_url", "character_engine", "chain_scenes"}))


@router.post("/video")
async def generate_video(data: GenerateRequest, background_tasks: BackgroundTasks):
    payload = data.model_dump(mode="json")
    requested_mode = payload.pop("mode")
    selected_mode = runtime.detect().mode if requested_mode == "auto" else requested_mode
    if selected_mode == "local_low_vram":
        selected_mode = "local"
    if (payload.get("image_url") or payload.get("motion_video_url")) and selected_mode == "local":
        selected_mode = "cloud"
    if payload.get("motion_video_url") and not payload.get("image_url"):
        raise HTTPException(status_code=400, detail="Wan2.2 Animate nécessite une image de référence.")
    if payload.get("character_engine") == "wan_animate" and not payload.get("motion_video_url"):
        raise HTTPException(status_code=400, detail="Le moteur Wan2.2 Animate nécessite une vidéo de mouvement.")
    if payload.get("chain_scenes") and selected_mode != "cloud":
        raise HTTPException(status_code=400, detail="Le chaînage des scènes est actuellement disponible en mode cloud.")

    job = jobs.create("video", {**payload, "mode": selected_mode})
    if selected_mode == "cloud":
        background_tasks.add_task(_run_full_pipeline, job["id"], payload, selected_mode)
    else:
        background_tasks.add_task(_run_local_placeholder, job["id"], payload)

    engine = payload.get("character_engine", "auto")
    if engine == "auto":
        engine = "wan_animate" if payload.get("motion_video_url") else ("i2v_5b" if payload.get("image_url") else "t2v")
    return {
        "job_id": job["id"],
        "mode": selected_mode,
        "status": job["status"],
        "type": "wan_animate" if engine == "wan_animate" else ("image_to_video" if payload.get("image_url") else "text_to_video"),
        "character_engine": engine,
        "chain_scenes": payload.get("chain_scenes", False),
        "character_consistency": bool(payload.get("character_description") or payload.get("image_url")),
        "message": "Pipeline vidéo lancée",
    }


async def _run_full_pipeline(job_id: str, payload: dict, mode: str):
    try:
        result = await pipeline.execute(**payload, mode=mode, progress=lambda p, stage: jobs.update(job_id, status="running", progress=p, message=stage))
        final_status = "completed" if result.get("status") == "completed" else "waiting_config"
        jobs.update(job_id, status=final_status, progress=100, message=result.get("message", "Pipeline préparée"), result=result)
    except Exception as exc:
        jobs.update(job_id, status="failed", progress=100, message=str(exc), error=str(exc))


async def _run_local_placeholder(job_id: str, payload: dict):
    jobs.update(job_id, status="running", progress=20, message="Mode local sélectionné")
    try:
        plan_payload = {key: payload[key] for key in ("prompt", "duration", "aspect_ratio", "language", "style")}
        plan = await pipeline.plan(**plan_payload)
        jobs.update(job_id, status="waiting_config", progress=100, message="Plan prêt. Configure un moteur vidéo local GPU pour le rendu.", result={"plan": plan, "render": "not_configured"})
    except Exception as exc:
        jobs.update(job_id, status="failed", progress=100, message=str(exc), error=str(exc))


@router.get("/jobs/{job_id}")
def get_job(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job introuvable")
    return job
