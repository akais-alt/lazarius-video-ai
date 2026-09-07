from __future__ import annotations

import os
import subprocess
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
        self.ffmpeg_bin = os.getenv("FFMPEG_BIN", "ffmpeg")
        self.public_base_url = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")

    async def _download(self, url: str, target: Path) -> Path:
        async with httpx.AsyncClient(timeout=300, follow_redirects=True) as client:
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                with target.open("wb") as file:
                    async for chunk in response.aiter_bytes():
                        file.write(chunk)
        return target

    def _extract_last_frame(self, clip_path: Path) -> Path:
        frame_path = self.storage / f"last_frame_{uuid.uuid4().hex}.jpg"
        command = [self.ffmpeg_bin, "-y", "-sseof", "-0.1", "-i", str(clip_path), "-frames:v", "1", "-q:v", "2", str(frame_path)]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0 or not frame_path.exists():
            raise RuntimeError(f"Impossible d'extraire la dernière image: {result.stderr[-500:]}")
        return frame_path

    def _public_media_url(self, path: Path) -> str:
        if not self.public_base_url:
            raise RuntimeError("PUBLIC_BASE_URL est requis pour le chaînage des scènes en mode cloud.")
        return f"{self.public_base_url}/api/media/{path.name}"

    async def run(self, plan: dict, payload: dict, progress: Callable[[int, str], None]):
        scenes = plan.get("storyboard", [])
        if not scenes:
            raise RuntimeError("Aucune scène dans le storyboard")

        progress(10, "script")
        clips = []
        local_clip_paths: list[Path] = []
        current_image_url = payload.get("image_url")
        chain_scenes = bool(payload.get("chain_scenes"))

        if chain_scenes and len(scenes) > 1 and not self.public_base_url:
            raise RuntimeError("Le chaînage des scènes nécessite PUBLIC_BASE_URL pour rendre les dernières images accessibles au moteur cloud.")

        for index, scene in enumerate(scenes):
            progress(20 + int(index * 35 / max(len(scenes), 1)), "video_cloud")
            visual_prompt = scene.get("visual_prompt") or scene.get("description") or "cinematic scene"
            cloud_job = await self.cloud.submit({
                "type": "image_to_video" if current_image_url else "video_clip",
                "request_id": str(uuid.uuid4()),
                "prompt": visual_prompt,
                "image_url": current_image_url,
                "duration": scene.get("duration", 4),
                "aspect_ratio": payload.get("aspect_ratio", "9:16"),
                "quality": payload.get("quality", "720p"),
            })
            record = {"scene": index + 1, "cloud": cloud_job, "input_image_url": current_image_url}
            if cloud_job.get("video_url"):
                clip_path = self.storage / f"clip_{uuid.uuid4().hex}.mp4"
                await self._download(cloud_job["video_url"], clip_path)
                local_clip_paths.append(clip_path)
                record["local_file"] = str(clip_path)
                if chain_scenes and index < len(scenes) - 1:
                    last_frame = self._extract_last_frame(clip_path)
                    record["last_frame"] = str(last_frame)
                    current_image_url = self._public_media_url(last_frame)
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
            "type": "image_to_video" if payload.get("image_url") else "text_to_video",
            "chain_scenes": chain_scenes,
            "stages": ["prompt", "script", "scenes", "video_cloud", "voice", "subtitles", "editing", "mp4"],
            "clips": clips,
            "voice": voice,
            "subtitles": {"status": "completed" if subtitle_path else "not_configured", "path": str(subtitle_path) if subtitle_path else None},
            "render": {"status": "completed", "engine": "ffmpeg", "filename": final_path.name, "media_url": f"/api/media/{final_path.name}"},
        }
