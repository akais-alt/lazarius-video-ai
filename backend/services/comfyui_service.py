import httpx

class ComfyUIService:
    def __init__(self, base_url: str = "http://localhost:8188"):
        self.base_url = base_url.rstrip("/")

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/system_stats")
                return response.is_success
        except httpx.HTTPError:
            return False
