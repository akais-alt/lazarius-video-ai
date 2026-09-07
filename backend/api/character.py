from fastapi import APIRouter

router = APIRouter(prefix="/character", tags=["character"])

@router.get("/status")
def character_status():
    return {"enabled": True, "mode": "identity-lock"}
