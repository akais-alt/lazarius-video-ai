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
    vram_gb: float | None
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
        vram_gb = None
        try:
            import torch
            if torch.cuda.is_available():
                gpu = torch.cuda.get_device_name(0)
                vram_gb = round(torch.cuda.get_device_properties(0).total_memory / (1024 ** 3), 1)
            else:
                gpu = "none"
        except Exception:
            gpu = "not-installed"
        configured = os.getenv("RUNTIME_MODE", "auto").lower()
        if configured not in {"cloud", "local", "auto"}:
            configured = "auto"
        if configured == "cloud":
            mode = "cloud"
        elif configured == "local":
            mode = "local"
        elif vram_gb is not None and vram_gb >= 12:
            mode = "local"
        elif vram_gb is not None and vram_gb >= 6 and ram_gb >= 16:
            mode = "local_low_vram"
        else:
            mode = "cloud"
        recommendation = {
            "local": "GPU local suffisante pour le rendu vidéo.",
            "local_low_vram": "GPU utilisable en mode économie de VRAM.",
            "cloud": "PC léger détecté : génération vidéo Cloud recommandée.",
        }[mode]
        return RuntimeProfile(mode, cpu_count, ram_gb, gpu, vram_gb, shutil.which("ffmpeg") is not None, recommendation)

    def as_dict(self):
        profile = asdict(self.detect())
        profile["os"] = platform.system()
        return profile
