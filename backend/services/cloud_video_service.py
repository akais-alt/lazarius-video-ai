import copy
import json
import os
import random
from typing import Any

import httpx


class CloudVideoService:
    """Cloud video adapter for ComfyUI/Vast-style serverless generation."""

    def __init__(self):
        self.base_url = os.getenv("CLOUD_VIDEO_API_URL", "").rstrip("/")
        self.api_key = os.getenv("CLOUD_VIDEO_API_KEY", "")
        self.provider = os.getenv("CLOUD_VIDEO_PROVIDER", "generic").lower()
        self.workflow_path = os.getenv("CLOUD_VIDEO_WORKFLOW", "workflows/text_to_video.json")
        self.i2v_workflow_path = os.getenv("CLOUD_VIDEO_I2V_WORKFLOW", "workflows/image_to_video_5b.json")
        self.animate_workflow_path = os.getenv("CLOUD_VIDEO_ANIMATE_WORKFLOW", "workflows/wan2_2_14B_animate.json")
        self.timeout = float(os.getenv("CLOUD_VIDEO_TIMEOUT", "900"))

    @property
    def configured(self) -> bool:
        return bool(self.base_url)

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    @staticmethod
    def _load_json(path: str) -> dict[str, Any] | None:
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    @staticmethod
    def _dimensions(aspect_ratio: str, quality: str) -> tuple[int, int]:
        presets = {
            "480p": {"9:16": (480, 864), "16:9": (864, 480), "1:1": (640, 640)},
            "720p": {"9:16": (720, 1280), "16:9": (1280, 720), "1:1": (720, 720)},
            "1080p": {"9:16": (1080, 1920), "16:9": (1920, 1080), "1:1": (1080, 1080)},
        }
        return presets.get(quality, presets["720p"]).get(aspect_ratio, (720, 1280))

    @staticmethod
    def _replace(value: Any, replacements: dict[str, Any]):
        if isinstance(value, str):
            return replacements.get(value, value)
        if isinstance(value, dict):
            return {k: CloudVideoService._replace(v, replacements) for k, v in value.items()}
        if isinstance(value, list):
            return [CloudVideoService._replace(v, replacements) for v in value]
        return value

    def _prepare_workflow(self, payload: dict) -> dict[str, Any]:
        engine = payload.get("character_engine", "auto")
        if engine == "auto":
            engine = "wan_animate" if payload.get("motion_video_url") else ("i2v_5b" if payload.get("image_url") else "t2v")
        is_animate = engine == "wan_animate"
        is_i2v = bool(payload.get("image_url"))
        if is_animate:
            workflow_path = self.animate_workflow_path
        else:
            workflow_path = self.i2v_workflow_path if is_i2v else self.workflow_path

        workflow = copy.deepcopy(self._load_json(workflow_path) or {})
        if not workflow:
            raise RuntimeError(f"Workflow introuvable ou vide: {workflow_path}")

        width, height = self._dimensions(payload.get("aspect_ratio", "9:16"), payload.get("quality", "720p"))
        fps = 24
        frames = max(17, min(121, ((max(1, int(payload.get("duration", 5))) * fps - 1) // 4) * 4 + 1))
        seed = random.randint(0, 2**63 - 1)
        replacements = {
            "__PROMPT__": payload.get("prompt", "cinematic scene"),
            "__IMAGE_URL__": payload.get("image_url", ""),
            "__MOTION_VIDEO_URL__": payload.get("motion_video_url", ""),
            "__WIDTH__": width,
            "__HEIGHT__": height,
            "__FRAMES__": frames,
            "__RANDOM_INT__": seed,
        }
        return self._replace(workflow, replacements)

    @staticmethod
    def _find_video_url(value: Any) -> str | None:
        if isinstance(value, str) and (value.startswith("http://") or value.startswith("https://")):
            if any(ext in value.lower() for ext in (".mp4", ".webm", ".mov", ".mkv")) or "video" in value.lower():
                return value
        if isinstance(value, dict):
            for key in ("video_url", "presigned_url", "url", "video", "output"):
                if key in value:
                    found = CloudVideoService._find_video_url(value[key])
                    if found:
                        return found
            for child in value.values():
                found = CloudVideoService._find_video_url(child)
                if found:
                    return found
        elif isinstance(value, list):
            for child in value:
                found = CloudVideoService._find_video_url(child)
                if found:
                    return found
        return None

    async def submit(self, payload: dict) -> dict:
        if not self.configured:
            return {"mode": "cloud", "provider": self.provider, "status": "not_configured", "message": "Aucun moteur cloud configuré. Renseigne CLOUD_VIDEO_API_URL et, si nécessaire, CLOUD_VIDEO_API_KEY."}

        engine = payload.get("character_engine", "auto")
        if engine == "auto":
            engine = "wan_animate" if payload.get("motion_video_url") else ("i2v_5b" if payload.get("image_url") else "t2v")

        if engine == "wan_animate" and (not payload.get("image_url") or not payload.get("motion_video_url")):
            raise ValueError("Wan2.2 Animate exige image_url + motion_video_url.")

        if self.provider in {"vast", "vast_ai", "comfyui_sync"}:
            workflow = self._prepare_workflow(payload)
            request = {"input": {"request_id": payload.get("request_id"), "workflow_json": workflow}}
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/generate/sync", json=request, headers=self._headers())
                response.raise_for_status()
                data = response.json()
            video_url = self._find_video_url(data)
            return {"mode": "cloud", "provider": self.provider, "type": engine, "status": "completed" if video_url else "completed_no_url", "video_url": video_url, "response": data}

        generic_payload = dict(payload)
        generic_payload["type"] = engine
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/jobs", json=generic_payload, headers=self._headers())
            response.raise_for_status()
            data = response.json()
        return {"mode": "cloud", "provider": self.provider, "status": data.get("status", "queued"), "response": data}
