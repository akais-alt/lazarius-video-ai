from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/media", tags=["media"])
STORAGE = Path(__import__("os").getenv("STORAGE_DIR", "./storage"))


@router.get("/{filename}")
def get_media(filename: str):
    safe_name = Path(filename).name
    path = STORAGE / safe_name
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Média introuvable")
    return FileResponse(path)
