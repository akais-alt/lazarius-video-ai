import asyncio
import uuid
from datetime import datetime, timezone

class JobService:
    def __init__(self):
        self.jobs = {}

    def create(self, kind: str, payload: dict):
        job_id = str(uuid.uuid4())
        self.jobs[job_id] = {
            "id": job_id,
            "kind": kind,
            "status": "queued",
            "progress": 0,
            "message": "Job en attente",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }
        return self.jobs[job_id]

    def update(self, job_id: str, **changes):
        if job_id in self.jobs:
            self.jobs[job_id].update(changes)
        return self.jobs.get(job_id)

    def get(self, job_id: str):
        return self.jobs.get(job_id)

    async def run_plan(self, job_id: str, pipeline, payload: dict):
        try:
            self.update(job_id, status="running", progress=10, message="Analyse de l'idée")
            result = await pipeline.plan(**payload)
            self.update(job_id, status="completed", progress=100, message="Plan prêt", result=result)
        except Exception as exc:
            self.update(job_id, status="failed", progress=100, message=str(exc), error=str(exc))

jobs = JobService()
