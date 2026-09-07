from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any


class JobManager:
    """Lightweight in-memory job store for local development.

    Production deployments should replace this with Redis/PostgreSQL/queue storage.
    """

    def __init__(self) -> None:
        self.jobs: dict[str, dict[str, Any]] = {}

    def create(self, payload: dict[str, Any]) -> str:
        job_id = str(uuid.uuid4())
        self.jobs[job_id] = {
            "id": job_id,
            "status": "queued",
            "progress": 0,
            "stage": "queued",
            "payload": payload,
            "result": None,
            "error": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return job_id

    def update(self, job_id: str, **changes: Any) -> None:
        if job_id in self.jobs:
            self.jobs[job_id].update(changes)

    def get(self, job_id: str) -> dict[str, Any] | None:
        return self.jobs.get(job_id)


job_manager = JobManager()
