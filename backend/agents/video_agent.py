class VideoAgent:
    """Adapter for local ComfyUI video workflows."""

    def __init__(self, comfyui_url: str = "http://localhost:8188"):
        self.comfyui_url = comfyui_url

    async def generate(self, workflow: dict):
        # ComfyUI integration will be implemented in the next phase.
        return {"status": "queued", "workflow": workflow}
