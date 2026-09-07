from __future__ import annotations

import os
import subprocess
from pathlib import Path


class FFmpegService:
    def __init__(self):
        self.binary = os.getenv("FFMPEG_BIN", "ffmpeg")

    def concat_videos(self, video_paths: list[Path], output_path: Path) -> dict:
        if not video_paths:
            return {"status": "failed", "error": "Aucune vidéo à assembler"}
        output_path.parent.mkdir(parents=True, exist_ok=True)
        list_file = output_path.with_suffix(".concat.txt")
        list_file.write_text("\n".join(f"file '{p.resolve().as_posix()}'" for p in video_paths), encoding="utf-8")
        command = [self.binary, "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(output_path)]
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except (OSError, subprocess.CalledProcessError) as exc:
            return {"status": "failed", "error": str(exc)}
        return {"status": "completed", "path": str(output_path)}

    def mux_audio(self, video_path: Path, voice_path: Path | None, music_path: Path | None, subtitle_path: Path | None, output_path: Path) -> dict:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        inputs = ["-i", str(video_path)]
        if voice_path:
            inputs += ["-i", str(voice_path)]
        if music_path:
            inputs += ["-i", str(music_path)]
        command = [self.binary, "-y", *inputs]
        maps = ["-map", "0:v:0"]
        audio_count = int(bool(voice_path)) + int(bool(music_path))
        if audio_count:
            if voice_path and music_path:
                command += ["-filter_complex", "[1:a][2:a]amix=inputs=2:duration=first:dropout_transition=2[aout]", *maps, "-map", "[aout]"]
            else:
                command += [*maps, "-map", "1:a:0"]
            command += ["-shortest"]
        else:
            command += maps
        command += ["-c:v", "libx264", "-c:a", "aac", "-movflags", "+faststart", str(output_path)]
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except (OSError, subprocess.CalledProcessError) as exc:
            return {"status": "failed", "error": str(exc)}
        return {"status": "completed", "path": str(output_path)}
