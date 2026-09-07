import os
import platform
import shutil
from dataclasses import asdict, dataclass

@dataclass
class RuntimeProfile:
    mode: str
    cpu_count: int
    ram_gb: float
    gpu: str
    ffmpeg: bool
    recommendation: str

class RuntimeService:
    def detect(self) -> RuntimeProfile:
        cpu_count = os.cpu_count() or 1
        ram_gb = 0.0
        try:
            import psutil
            ram_gb = round(psutil.virtual_memory().total / (1024 ** 3), 1)
        except Exception:
            pass
        gpu = "unknown"
        try:
            import torch
            if torch.cuda.is_available():
                gpu = torch.cuda.get_device_name(0)
            else:
                gpu = "none"
        except Exception:
            gpu = "not-installed"
        configured = os.getenv("RUNTIME_MODE", "auto").lower()
        if configured in {"cloud", "local", "auto"}:
            mode = configured
        else:
            mode = "auto"
        if mode == "auto":
            mode = "local" if gpu not in {"none", "unknown", "not-installed"} else "cloud"
        recommendation = "local GPU available" if mode == "local" else "cloud generation recommended"
        return RuntimeProfile(mode, cpu_count, ram_gb, gpu, shutil.which("ffmpeg") is not None, recommendation)

    def as_dict(self):
        return asdict(self.detect())
