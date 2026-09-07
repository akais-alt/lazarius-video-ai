from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
from services.pipeline_service import PipelineService
from services.job_service import jobs
from services.runtime_service import RuntimeService
from services.cloud_video_service import CloudVideoService

router = APIRouter(prefix="/generate", tags=["generation"])
pipeline = PipelineService()
runtime = RuntimeService()
cloud = CloudVideoService()

class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=3)
    duration: int = Field(default=30, ge=1, le=600)
    aspect_ratio: str = Field(default="9:16")
    language: str = Field(default="fr")
    style: str = Field(default="cinematic")
    mode: str = Field(default="auto", pattern="^(auto|local|cloud)$")

@router.get("/runtime")
def runtime_info():
    return runtime.as_dict()

@router.post("/plan")
async def generate_plan(data: GenerateRequest):
    return await pipeline.plan(**data.model_dump(exclude={"mode"}))

@router.post("/video")
async def generate_video(data: GenerateRequest, background_tasks: BackgroundTasks):
    payload = data.model_dump()
    requested_mode = payload.pop("mode")
    selected_mode = runtime.detect().mode if requested_mode == "auto" else requested_mode
    job = jobs.create("video", {**payload, "mode": selected_mode})
    if selected_mode == "cloud":
        background_tasks.add_task(_run_cloud, job["id"], payload)
    else:
        background_tasks.add_task(_run_local_placeholder, job["id"], payload)
    return {"job_id": job["id"], "mode": selected_mode, "status": job["status"], "message": "Génération lancée"}

async def _run_cloud(job_id: str, payload: dict):
    jobs.update(job_id, status="running", progress=15, message="Préparation du scénario")
    try:
        plan = await pipeline.plan(**payload)
        jobs.update(job_id, progress=45, message="Envoi au moteur cloud")
        result = await cloud.submit({"project": payload, "plan": plan})
        jobs.update(job_id, status="completed" if result.get("status") != "not_configured" else "waiting_config", progress=100, message=result.get("message", "Job cloud créé"), result={"plan": plan, "cloud": result})
    except Exception as exc:
        jobs.update(job_id, status="failed", progress=100, message=str(exc), error=str(exc))

async def _run_local_placeholder(job_id: str, payload: dict):
    jobs.update(job_id, status="running", progress=20, message="Mode local sélectionné")
    try:
        plan = await pipeline.plan(**payload)
        jobs.update(job_id, status="completed", progress=100, message="Plan prêt. Un moteur vidéo local GPU doit être configuré pour le rendu.", result={"plan": plan, "render": "not_configured"})
    except Exception as exc:
        jobs.update(job_id, status="failed", progress=100, message=str(exc), error=str(exc))

@router.get("/jobs/{job_id}")
def get_job(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job introuvable")
    return job
