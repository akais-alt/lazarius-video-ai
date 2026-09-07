import os
import httpx

class CloudVideoService:
    """Provider-neutral cloud adapter. It does not require a local GPU."""
    def __init__(self):
        self.base_url = os.getenv("CLOUD_VIDEO_API_URL", "").rstrip("/")
        self.api_key = os.getenv("CLOUD_VIDEO_API_KEY", "")
        self.provider = os.getenv("CLOUD_VIDEO_PROVIDER", "generic")

    @property
    def configured(self):
        return bool(self.base_url and self.api_key)

    async def submit(self, payload: dict):
        if not self.configured:
            return {
                "mode": "cloud",
                "provider": self.provider,
                "status": "not_configured",
                "message": "Aucun fournisseur cloud configuré. Le plan a été préparé sans lancer de génération payante."
            }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(f"{self.base_url}/jobs", json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
