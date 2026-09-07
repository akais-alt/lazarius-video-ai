import json
import os
from typing import Any

import httpx


class CloudVideoService:
    """Cloud video adapter compatible with a ComfyUI-style HTTP endpoint.

    It supports a generic /jobs API and a ComfyUI/Vast-style /generate/sync API.
    No cloud provider is assumed or advertised as permanently free.
    """

    def __init__(self):
        self.base_url = os.getenv("CLOUD_VIDEO_API_URL", "").rstrip("/")
        self.api_key = os.getenv("CLOUD_VIDEO_API_KEY", "")
        self.provider = os.getenv("CLOUD_VIDEO_PROVIDER", "generic").lower()
        self.workflow_path = os.getenv("CLOUD_VIDEO_WORKFLOW", "workflows/text_to_video.json")
        self.timeout = float(os.getenv("CLOUD_VIDEO_TIMEOUT", "900"))

    @property
    def configured(self) -> bool:
        return bool(self.base_url)

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _load_workflow(self) -> dict[str, Any] | None:
        if not os.path.exists(self.workflow_path):
            return None
        with open(self.workflow_path, "r", encoding="utf-8") as file:
            return json.load(file)

    async def submit(self, payload: dict) -> dict:
        if not self.configured:
            return {
                "mode": "cloud",
                "provider": self.provider,
                "status": "not_configured",
                "message": "Aucun moteur cloud configuré. Renseigne CLOUD_VIDEO_API_URL et, si nécessaire, CLOUD_VIDEO_API_KEY.",
            }

        if self.provider in {"vast", "vast_ai", "comfyui_sync"}:
            workflow = self._load_workflow()
            if workflow is None:
                return {
                    "mode": "cloud",
                    "provider": self.provider,
                    "status": "workflow_missing",
                    "message": f"Workflow introuvable: {self.workflow_path}",
                }

            request = {
                "input": {
                    "request_id": payload.get("request_id"),
                    "workflow_json": workflow,
                }
            }
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/generate/sync",
                    json=request,
                    headers=self._headers(),
                )
                response.raise_for_status()
                data = response.json()

            return {
                "mode": "cloud",
                "provider": self.provider,
                "status": "completed",
                "response": data,
            }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/jobs",
                json=payload,
                headers=self._headers(),
            )
            response.raise_for_status()
            data = response.json()

        return {
            "mode": "cloud",
            "provider": self.provider,
            "status": data.get("status", "queued"),
            "response": data,
        }
