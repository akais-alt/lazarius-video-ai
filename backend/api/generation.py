import os
from pathlib import Path
import uuid

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
ALLOWED_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=3)
    duration: int = Field(default=30, ge=1, le=600)
    aspect_ratio: str = Field(default="9:16")
    language: str = Field(default="fr")
    style: str = Field(default="cinematic")
    mode: str = Field(default="auto", pattern="^(auto|local|cloud)$")
    quality: str = Field(default="720p", pattern="^(480p|720p|1080p)$")
    image_url: HttpUrl | None = None
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


@router.post("/plan")
async def generate_plan(data: GenerateRequest):
    return await pipeline.plan(**data.model_dump(exclude={"mode", "quality", "image_url", "chain_scenes"}))


@router.post("/video")
async def generate_video(data: GenerateRequest, background_tasks: BackgroundTasks):
    payload = data.model_dump(mode="json")
    requested_mode = payload.pop("mode")
    selected_mode = runtime.detect().mode if requested_mode == "auto" else requested_mode
    if selected_mode == "local_low_vram":
        selected_mode = "local"

    if payload.get("image_url") and selected_mode == "local":
        selected_mode = "cloud"

    job = jobs.create("video", {**payload, "mode": selected_mode})
    if selected_mode == "cloud":
        background_tasks.add_task(_run_full_pipeline, job["id"], payload, selected_mode)
    else:
        background_tasks.add_task(_run_local_placeholder, job["id"], payload)

    return {
        "job_id": job["id"],
        "mode": selected_mode,
        "status": job["status"],
        "type": "image_to_video" if payload.get("image_url") else "text_to_video",
        "chain_scenes": payload.get("chain_scenes", False),
        "message": "Pipeline vidéo lancée",
    }


async def _run_full_pipeline(job_id: str, payload: dict, mode: str):
    try:
        result = await pipeline.execute(
            **payload,
            mode=mode,
            progress=lambda p, stage: jobs.update(
                job_id, status="running", progress=p, message=stage
            ),
        )
        final_status = "completed" if result.get("status") == "completed" else "waiting_config"
        jobs.update(
            job_id,
            status=final_status,
            progress=100,
            message=result.get("message", "Pipeline préparée"),
            result=result,
        )
    except Exception as exc:
        jobs.update(job_id, status="failed", progress=100, message=str(exc), error=str(exc))


async def _run_local_placeholder(job_id: str, payload: dict):
    jobs.update(job_id, status="running", progress=20, message="Mode local sélectionné")
    try:
        plan_payload = {key: payload[key] for key in ("prompt", "duration", "aspect_ratio", "language", "style")}
        plan = await pipeline.plan(**plan_payload)
        jobs.update(
            job_id,
            status="waiting_config",
            progress=100,
            message="Plan prêt. Configure un moteur vidéo local GPU pour le rendu.",
            result={"plan": plan, "render": "not_configured"},
        )
    except Exception as exc:
        jobs.update(job_id, status="failed", progress=100, message=str(exc), error=str(exc))


@router.get("/jobs/{job_id}")
def get_job(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job introuvable")
    return job
