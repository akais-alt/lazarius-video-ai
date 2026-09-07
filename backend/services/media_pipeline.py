from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Callable

import httpx

from services.cloud_video_service import CloudVideoService
from services.ffmpeg_service import FFmpegService
from services.subtitle_service import SubtitleService
from services.tts_service import TTSService


class MediaPipeline:
    """Cloud-first pipeline: video clips -> Piper voice -> Whisper subtitles -> MP4."""

    def __init__(self):
        self.cloud = CloudVideoService()
        self.tts = TTSService()
        self.subtitles = SubtitleService()
        self.ffmpeg = FFmpegService()
        self.storage = Path(os.getenv("STORAGE_DIR", "./storage"))
        self.storage.mkdir(parents=True, exist_ok=True)

    async def _download(self, url: str, target: Path) -> Path:
        async with httpx.AsyncClient(timeout=300, follow_redirects=True) as client:
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                with target.open("wb") as file:
                    async for chunk in response.aiter_bytes():
                        file.write(chunk)
        return target

    async def run(self, plan: dict, payload: dict, progress: Callable[[int, str], None]):
        scenes = plan.get("storyboard", [])
        if not scenes:
            raise RuntimeError("Aucune scène dans le storyboard")

        progress(10, "script")
        clips = []
        local_clip_paths: list[Path] = []
        image_url = payload.get("image_url")

        for index, scene in enumerate(scenes):
            progress(20 + int(index * 35 / max(len(scenes), 1)), "video_cloud")
            visual_prompt = scene.get("visual_prompt") or scene.get("description") or "cinematic scene"
            cloud_job = await self.cloud.submit({
                "type": "image_to_video" if image_url else "video_clip",
                "request_id": str(uuid.uuid4()),
                "prompt": visual_prompt,
                "image_url": image_url,
                "duration": scene.get("duration", 4),
                "aspect_ratio": payload.get("aspect_ratio", "9:16"),
                "quality": payload.get("quality", "720p"),
            })
            record = {"scene": index + 1, "cloud": cloud_job}
            if cloud_job.get("video_url"):
                clip_path = self.storage / f"clip_{uuid.uuid4().hex}.mp4"
                await self._download(cloud_job["video_url"], clip_path)
                local_clip_paths.append(clip_path)
                record["local_file"] = str(clip_path)
            clips.append(record)

        if not local_clip_paths:
            return {
                "status": "waiting_config",
                "stages": ["prompt", "script", "scenes", "video_cloud"],
                "clips": clips,
                "message": "Le moteur cloud n'a retourné aucune vidéo exploitable.",
            }

        progress(60, "voice")
        script_text = plan.get("script", "")
        voice_path = self.storage / f"voice_{uuid.uuid4().hex}.wav"
        voice = self.tts.synthesize(str(script_text), voice_path)
        if voice.get("status") != "completed":
            voice_path = None

        progress(72, "subtitles")
        subtitle_path = None
        if voice_path:
            candidate = self.storage / f"subtitles_{uuid.uuid4().hex}.srt"
            subtitle = self.subtitles.generate_srt(voice_path, candidate, payload.get("language", "fr"))
            if subtitle.get("status") == "completed":
                subtitle_path = candidate

        progress(84, "editing")
        assembled = self.storage / f"assembled_{uuid.uuid4().hex}.mp4"
        concat = self.ffmpeg.concat_videos(local_clip_paths, assembled)
        if concat.get("status") != "completed":
            raise RuntimeError(concat.get("error", "Erreur FFmpeg pendant l'assemblage"))

        progress(94, "export")
        final_path = self.storage / f"lazarius_{uuid.uuid4().hex}.mp4"
        render = self.ffmpeg.mux_audio(assembled, voice_path, None, subtitle_path, final_path)
        if render.get("status") != "completed":
            raise RuntimeError(render.get("error", "Erreur FFmpeg pendant le rendu final"))

        progress(100, "done")
        return {
            "status": "completed",
            "type": "image_to_video" if image_url else "text_to_video",
            "stages": ["prompt", "script", "scenes", "video_cloud", "voice", "subtitles", "editing", "mp4"],
            "clips": clips,
            "voice": voice,
            "subtitles": {"status": "completed" if subtitle_path else "not_configured", "path": str(subtitle_path) if subtitle_path else None},
            "render": {"status": "completed", "engine": "ffmpeg", "filename": final_path.name, "media_url": f"/api/media/{final_path.name}"},
        }
