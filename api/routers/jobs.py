"""
Jobs API router – enqueue, schedule, monitor, and cancel background send jobs.

Enqueued sends run in the in-process worker (see api/worker.py), so progress is
durable and survives the TUI disconnecting. Clients can poll GET /api/jobs/{id}
or subscribe to the SSE progress stream.
"""

import asyncio
import datetime
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from api.auth import verify_token
from api.worker import request_cancel
from sending.db import Database
from sending.validation import partition_valid

router = APIRouter()

_TERMINAL = {"completed", "failed", "canceled"}


class JobCreate(BaseModel):
    recipients: list[str]
    subject: str
    body: str
    email_type: str = "html"
    attachments: list[str] = []
    skip_already_sent: bool = False
    personalize: bool = False
    recipient_fields: dict[str, dict] = {}
    # ISO-8601 datetime to run at; null/absent = run as soon as possible.
    scheduled_at: str | None = None
    name: str = ""


@router.post("", dependencies=[Depends(verify_token)])
async def enqueue_job(body: JobCreate):
    """Enqueue (or schedule) a send job. Returns the job id and status."""
    valid, _invalid = partition_valid(body.recipients)
    if not valid:
        raise HTTPException(status_code=400, detail="No valid recipients")

    scheduled_at = None
    if body.scheduled_at:
        try:
            scheduled_at = datetime.datetime.fromisoformat(body.scheduled_at)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid scheduled_at (use ISO-8601)")

    payload = {
        "recipients": body.recipients,
        "subject": body.subject,
        "body": body.body,
        "email_type": body.email_type,
        "attachments": body.attachments,
        "skip_already_sent": body.skip_already_sent,
        "personalize": body.personalize,
        "recipient_fields": body.recipient_fields,
    }
    job_id = uuid.uuid4().hex
    name = body.name or body.subject or "Untitled send"

    db = Database()
    db.add_job(job_id, payload, name=name, scheduled_at=scheduled_at)
    job = db.get_job(job_id)
    db.close()
    return job


@router.get("", dependencies=[Depends(verify_token)])
async def list_jobs(limit: int = 100):
    """List jobs, newest first."""
    db = Database()
    jobs = db.list_jobs(limit=limit)
    db.close()
    return {"jobs": jobs, "total": len(jobs)}


@router.get("/{job_id}", dependencies=[Depends(verify_token)])
async def get_job(job_id: str):
    """Get a single job's status and progress."""
    db = Database()
    job = db.get_job(job_id)
    db.close()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/{job_id}/cancel", dependencies=[Depends(verify_token)])
async def cancel_job(job_id: str):
    """Cancel a pending/scheduled/running job."""
    db = Database()
    job = db.get_job(job_id)
    if not job:
        db.close()
        raise HTTPException(status_code=404, detail="Job not found")
    # Signal the worker (for running jobs) and flip the DB status.
    request_cancel(job_id)
    canceled = db.cancel_job(job_id)
    result = db.get_job(job_id)
    db.close()
    if not canceled:
        raise HTTPException(status_code=409, detail=f"Job is {job['status']}, cannot cancel")
    return result


@router.get("/{job_id}/stream", dependencies=[Depends(verify_token)])
async def stream_job(job_id: str):
    """
    SSE stream of a job's progress by polling its row until it reaches a terminal
    state. Reconnect-safe: it reads current DB state, so a dropped/reopened TUI
    simply resumes from wherever the job is.
    """

    async def gen():
        db = Database()
        try:
            last = None
            while True:
                job = await asyncio.to_thread(db.get_job, job_id)
                if not job:
                    yield {"event": "error", "data": json.dumps({"error": "not found"})}
                    return
                snapshot = json.dumps(
                    {
                        "status": job["status"],
                        "total": job["total"],
                        "sent": job["sent"],
                        "failed": job["failed"],
                        "error": job["error"],
                    }
                )
                if snapshot != last:
                    yield {"event": "progress", "data": snapshot}
                    last = snapshot
                if job["status"] in _TERMINAL:
                    yield {"event": "done", "data": snapshot}
                    return
                await asyncio.sleep(1)
        finally:
            db.close()

    return EventSourceResponse(gen())
