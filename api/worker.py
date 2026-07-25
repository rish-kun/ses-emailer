"""
Background send worker + scheduler.

A single in-process async task claims runnable jobs from the ``jobs`` table
(pending, or scheduled and due), runs them through the shared send stream, and
records progress back to the DB. Because the worker runs independently of any
client connection, a queued/scheduled send survives the TUI disconnecting.

Kept deliberately simple: one job at a time (avoids SES rate contention), SQLite
as the only store (no external broker), cooperative cancellation between events.
"""

import asyncio
import json
import logging

from sending.db import Database

logger = logging.getLogger(__name__)

# Job ids requested to cancel; checked cooperatively between send events.
_cancel_requested: set[str] = set()

_POLL_INTERVAL = 2.0  # seconds between queue checks when idle


def request_cancel(job_id: str) -> None:
    """Signal the worker to stop a running job at the next event boundary."""
    _cancel_requested.add(job_id)


async def _run_job(job: dict) -> None:
    """Execute a single send job, updating its progress row as it goes."""
    # Imported here to avoid a circular import at module load time.
    from api.routers.email import send_event_stream

    job_id = job["id"]
    payload = job["payload"]
    db = Database()
    email_id: str | None = None
    total_sent = 0
    total_failed = 0

    try:
        gen = send_event_stream(
            recipients=payload.get("recipients", []),
            subject=payload.get("subject", ""),
            body=payload.get("body", ""),
            email_type=payload.get("email_type", "html"),
            attachments=payload.get("attachments", []),
            skip_already_sent=payload.get("skip_already_sent", False),
            personalize=payload.get("personalize", False),
            recipient_fields=payload.get("recipient_fields", {}),
        )
        async for event in gen:
            data = json.loads(event["data"])
            name = event["event"]
            if name in ("batch_complete", "batch_error"):
                total_sent = data.get("total_sent", total_sent)
                total_failed = data.get("total_failed", total_failed)
                await asyncio.to_thread(
                    db.update_job_progress, job_id, total_sent, total_failed
                )
            elif name == "start":
                await asyncio.to_thread(
                    db.update_job_progress, job_id, 0, 0, data.get("total_recipients", 0)
                )
            elif name == "complete":
                total_sent = data.get("total_sent", total_sent)
                total_failed = data.get("total_failed", total_failed)
                email_id = data.get("email_id") or email_id

            # Cooperative cancellation: stop the generator mid-send.
            if job_id in _cancel_requested:
                await gen.aclose()
                _cancel_requested.discard(job_id)
                await asyncio.to_thread(
                    db.finish_job, job_id, "canceled", "Canceled by user", email_id
                )
                logger.info("Job %s canceled", job_id)
                return

        await asyncio.to_thread(db.finish_job, job_id, "completed", "", email_id)
        logger.info("Job %s completed: %s sent, %s failed", job_id, total_sent, total_failed)
    except Exception as e:
        # The worker must never die on a single bad job.
        logger.exception("Job %s failed", job_id)
        await asyncio.to_thread(db.finish_job, job_id, "failed", str(e), email_id)
    finally:
        db.close()


async def worker_loop(stop_event: asyncio.Event) -> None:
    """Main worker loop. Runs until ``stop_event`` is set."""
    # Recover jobs left 'running' by a previous crash.
    recovery_db = Database()
    try:
        requeued = await asyncio.to_thread(recovery_db.requeue_running_jobs)
        if requeued:
            logger.info("Requeued %s interrupted job(s)", requeued)
    finally:
        recovery_db.close()

    logger.info("Send worker started")
    while not stop_event.is_set():
        db = Database()
        try:
            job = await asyncio.to_thread(db.claim_next_job)
        finally:
            db.close()

        if job is None:
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=_POLL_INTERVAL)
            except asyncio.TimeoutError:
                pass
            continue

        await _run_job(job)

    logger.info("Send worker stopped")
