from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

from services.cloud_video_service import CloudVideoService


class MediaPipeline:
    """Orchestrates the complete production lifecycle without requiring a local GPU."""

    def __init__(self):
        self.cloud = CloudVideoService()
        self.storage = Path(os.getenv("STORAGE_DIR", "./storage"))
        self.storage.mkdir(parents=True, exist_ok=True)

    async def run(self, plan: dict, payload: dict, progress: Callable[[int, str], None]):
        progress(10, "script")
        scenes = plan.get("storyboard", [])

        progress(25, "video_cloud")
        clips = []
        for index, scene in enumerate(scenes):
            visual_prompt = scene.get("visual_prompt") or scene.get("description") or "cinematic scene"
            cloud_job = await self.cloud.submit({
                "type": "video_clip",
                "prompt": visual_prompt,
                "duration": scene.get("duration", 4),
                "aspect_ratio": payload.get("aspect_ratio", "9:16"),
                "quality": payload.get("quality", "720p"),
            })
            clips.append({"scene": index + 1, "cloud": cloud_job})
            progress(min(55, 25 + int((index + 1) * 30 / max(len(scenes), 1))), "video_cloud")

        progress(60, "voice")
        voice = {
            "status": "queued",
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
            "status": "queued",
            "provider": os.getenv("STT_PROVIDER", "whisper"),
        }

        progress(84, "editing")
        render = {
            "status": "queued",
            "engine": "ffmpeg",
            "output_format": "mp4",
            "quality": payload.get("quality", "720p"),
        }

        progress(92, "export")
        return {
            "status": "pipeline_ready",
            "stages": ["prompt", "script", "scenes", "video_cloud", "voice", "music", "subtitles", "editing", "mp4"],
            "clips": clips,
            "voice": voice,
            "music": music,
            "subtitles": subtitles,
            "render": render,
            "note": "Les étapes voix/musique/sous-titres/montage sont préparées pour les adaptateurs réels; aucun fichier MP4 n'est simulé.",
        }
