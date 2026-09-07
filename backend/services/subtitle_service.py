from __future__ import annotations

import os
from pathlib import Path


class SubtitleService:
    """faster-whisper subtitle adapter with CPU/GPU selection."""

    def __init__(self):
        self.model_name = os.getenv("WHISPER_MODEL", "small")
        self.device = os.getenv("WHISPER_DEVICE", "auto")

    def generate_srt(self, audio_path: Path, output_path: Path, language: str = "fr") -> dict:
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            return {"status": "not_installed", "provider": "faster-whisper", "path": None}

        device = self.device
        compute_type = "int8"
        if device == "auto":
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                device = "cpu"
        if device == "cuda":
            compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "float16")

        model = WhisperModel(self.model_name, device=device, compute_type=compute_type)
        segments, _ = model.transcribe(str(audio_path), language=language, vad_filter=True)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        def timestamp(seconds: float) -> str:
            total_ms = max(0, int(round(seconds * 1000)))
            h, rem = divmod(total_ms, 3_600_000)
            m, rem = divmod(rem, 60_000)
            s, ms = divmod(rem, 1000)
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

        with output_path.open("w", encoding="utf-8") as file:
            for index, segment in enumerate(segments, start=1):
                text = segment.text.strip()
                if not text:
                    continue
                file.write(f"{index}\n{timestamp(segment.start)} --> {timestamp(segment.end)}\n{text}\n\n")

        return {"status": "completed", "provider": "faster-whisper", "path": str(output_path)}
