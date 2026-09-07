from uuid import uuid4
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/projects", tags=["projects"])

class ProjectCreate(BaseModel):
    prompt: str = Field(min_length=1)
    duration: int = Field(default=30, ge=1, le=600)
    aspect_ratio: str = Field(default="9:16")
    language: str = Field(default="fr")
    style: str = Field(default="cinematic")

@router.post("")
def create_project(data: ProjectCreate):
    return {
        "id": str(uuid4()),
        "status": "created",
        "config": data.model_dump(),
    }
