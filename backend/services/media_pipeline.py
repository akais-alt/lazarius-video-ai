from __future__ import annotations

import os
import subprocess
import uuid
from pathlib import Path
from typing import Callable

import httpx

from services.cloud_video_service import CloudVideoService


class MediaPipeline:
    """Cloud-first production pipeline with lightweight local FFmpeg assembly."""

    def __init__(self):
        self.cloud = CloudVideoService()
        self.storage = Path(os.getenv("STORAGE_DIR", "./storage"))
        self.storage.mkdir(parents=True, exist_ok=True)
        self.ffmpeg = os.getenv("FFMPEG_BIN", "ffmpeg")

    async def _download(self, url: str, target: Path) -> Path:
        async with httpx.AsyncClient(timeout=300) as client:
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                with target.open("wb") as file:
                    async for chunk in response.aiter_bytes():
                        file.write(chunk)
        return target

    def _concat(self, clips: list[Path], output: Path) -> Path:
        concat_file = output.with_suffix(".txt")
        concat_file.write_text(
            "".join(f"file '{clip.resolve().as_posix()}'\n" for clip in clips),
            encoding="utf-8",
        )
        try:
            subprocess.run(
                [
                    self.ffmpeg,
                    "-y",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    str(concat_file),
                    "-c",
                    "copy",
                    str(output),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        finally:
            concat_file.unlink(missing_ok=True)
        return output

    async def run(self, plan: dict, payload: dict, progress: Callable[[int, str], None]):
        progress(10, "script")
        scenes = plan.get("storyboard", [])
        if not scenes:
            raise RuntimeError("Aucune scène dans le storyboard")

        progress(25, "video_cloud")
        clips = []
        local_clip_paths: list[Path] = []

        for index, scene in enumerate(scenes):
            visual_prompt = scene.get("visual_prompt") or scene.get("description") or "cinematic scene"
            cloud_job = await self.cloud.submit({
                "type": "video_clip",
                "request_id": str(uuid.uuid4()),
                "prompt": visual_prompt,
                "duration": scene.get("duration", 4),
                "aspect_ratio": payload.get("aspect_ratio", "9:16"),
                "quality": payload.get("quality", "720p"),
            })

            clip_record = {"scene": index + 1, "cloud": cloud_job}
            video_url = cloud_job.get("video_url")
            if video_url:
                clip_path = self.storage / f"clip_{uuid.uuid4().hex}.mp4"
                await self._download(video_url, clip_path)
                local_clip_paths.append(clip_path)
                clip_record["local_file"] = str(clip_path)
            clips.append(clip_record)
            progress(min(55, 25 + int((index + 1) * 30 / max(len(scenes), 1))), "video_cloud")

        if not local_clip_paths:
            return {
                "status": "waiting_config",
                "stages": ["prompt", "script", "scenes", "video_cloud"],
                "clips": clips,
                "message": "Le moteur cloud a été appelé, mais aucun fichier vidéo exploitable n'a été retourné.",
            }

        progress(60, "voice")
        voice = {
            "status": "not_configured",
            "provider": os.getenv("TTS_PROVIDER", "piper"),
            "language": payload.get("language", "fr"),
        }

        progress(68, "music")
        music = {
            "status": "optional",
            "provider": os.getenv("MUSIC_PROVIDER", "local_or_user_upload"),
        }

        progress(76, "subtitles")
        subtitles = {
            "status": "not_configured",
            "provider": os.getenv("STT_PROVIDER", "whisper"),
        }

        progress(84, "editing")
        output = self.storage / f"lazarius_{uuid.uuid4().hex}.mp4"
        self._concat(local_clip_paths, output)

        progress(96, "export")
        return {
            "status": "completed",
            "stages": ["prompt", "script", "scenes", "video_cloud", "voice", "music", "subtitles", "editing", "mp4"],
            "clips": clips,
            "voice": voice,
            "music": music,
            "subtitles": subtitles,
            "render": {
                "status": "completed",
                "engine": "ffmpeg",
                "output_format": "mp4",
                "quality": payload.get("quality", "720p"),
                "filename": output.name,
                "media_url": f"/api/media/{output.name}",
            },
        }
