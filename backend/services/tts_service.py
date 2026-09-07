from __future__ import annotations

import os
import subprocess
from pathlib import Path


class TTSService:
    """Optional local Piper TTS adapter. It never pretends audio exists when Piper is unavailable."""

    def __init__(self):
        self.binary = os.getenv("PIPER_BIN", "piper")
        self.model = os.getenv("PIPER_MODEL_PATH", "")

    @property
    def configured(self) -> bool:
        return bool(self.model)

    def synthesize(self, text: str, output_path: Path) -> dict:
        if not self.configured:
            return {"status": "not_configured", "provider": "piper", "path": None}
        output_path.parent.mkdir(parents=True, exist_ok=True)
        command = [self.binary, "--model", self.model, "--output_file", str(output_path)]
        try:
            subprocess.run(command, input=text, text=True, check=True, capture_output=True)
        except (OSError, subprocess.CalledProcessError) as exc:
            return {"status": "failed", "provider": "piper", "path": None, "error": str(exc)}
        return {"status": "completed", "provider": "piper", "path": str(output_path)}
