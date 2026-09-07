from fastapi import APIRouter
from pydantic import BaseModel, Field
from services.pipeline_service import PipelineService

router = APIRouter(prefix="/generate", tags=["generation"])
pipeline = PipelineService()

class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=3)
    duration: int = Field(default=30, ge=1, le=600)
    aspect_ratio: str = Field(default="9:16")
    language: str = Field(default="fr")
    style: str = Field(default="cinematic")

@router.post("/plan")
async def generate_plan(data: GenerateRequest):
    return await pipeline.plan(**data.model_dump())
