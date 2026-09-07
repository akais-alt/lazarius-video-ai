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
        finally:
            list_file.unlink(missing_ok=True)
        return {"status": "completed", "path": str(output_path)}

    def mux_audio(self, video_path: Path, voice_path: Path | None, music_path: Path | None, subtitle_path: Path | None, output_path: Path) -> dict:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        input_paths: list[Path] = [video_path]
        if voice_path:
            input_paths.append(voice_path)
        if music_path:
            input_paths.append(music_path)
        if subtitle_path:
            input_paths.append(subtitle_path)

        command = [self.binary, "-y"]
        for path in input_paths:
            command += ["-i", str(path)]

        command += ["-map", "0:v:0"]
        audio_indexes = []
        if voice_path:
            audio_indexes.append(1)
        if music_path:
            audio_indexes.append(2 if voice_path else 1)

        if len(audio_indexes) == 2:
            command += ["-filter_complex", f"[{audio_indexes[0]}:a][{audio_indexes[1]}:a]amix=inputs=2:duration=first:dropout_transition=2[aout]", "-map", "[aout]"]
        elif len(audio_indexes) == 1:
            command += ["-map", f"{audio_indexes[0]}:a:0"]

        if subtitle_path:
            subtitle_index = len(input_paths) - 1
            command += ["-map", f"{subtitle_index}:0", "-c:s", "mov_text"]

        command += ["-c:v", "libx264", "-c:a", "aac", "-movflags", "+faststart"]
        if audio_indexes:
            command += ["-shortest"]
        command += [str(output_path)]

        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except (OSError, subprocess.CalledProcessError) as exc:
            return {"status": "failed", "error": str(exc)}
        return {"status": "completed", "path": str(output_path)}
