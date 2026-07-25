"""Tests for the scheduling / background job queue."""

import datetime
import time


def _poll_until(client, auth, job_id, statuses, timeout=15.0):
    """Poll a job until it reaches one of `statuses` or times out; return the job."""
    deadline = time.time() + timeout
    job = None
    while time.time() < deadline:
        job = client.get(f"/api/jobs/{job_id}", headers=auth).json()
        if job["status"] in statuses:
            return job
        time.sleep(0.3)
    return job


# ── Enqueue / validation (no worker needed) ───────────────────────────


def test_enqueue_requires_valid_recipients(client, auth):
    resp = client.post(
        "/api/jobs",
        headers=auth,
        json={"recipients": ["not-an-email"], "subject": "s", "body": "b"},
    )
    assert resp.status_code == 400


def test_enqueue_returns_pending_job(client, auth):
    resp = client.post(
        "/api/jobs",
        headers=auth,
        json={"recipients": ["a@x.com"], "subject": "Hello", "body": "b"},
    )
    assert resp.status_code == 200
    job = resp.json()
    assert job["status"] == "pending"
    assert job["total"] == 1
    assert job["name"] == "Hello"


def test_scheduled_job_is_scheduled(client, auth):
    future = (datetime.datetime.now() + datetime.timedelta(hours=1)).isoformat()
    resp = client.post(
        "/api/jobs",
        headers=auth,
        json={"recipients": ["a@x.com"], "subject": "s", "body": "b", "scheduled_at": future},
    )
    assert resp.json()["status"] == "scheduled"


def test_get_unknown_job_404(client, auth):
    assert client.get("/api/jobs/nope", headers=auth).status_code == 404


def test_cancel_scheduled_job(client, auth):
    future = (datetime.datetime.now() + datetime.timedelta(hours=2)).isoformat()
    job = client.post(
        "/api/jobs",
        headers=auth,
        json={"recipients": ["a@x.com"], "subject": "s", "body": "b", "scheduled_at": future},
    ).json()
    resp = client.post(f"/api/jobs/{job['id']}/cancel", headers=auth)
    assert resp.status_code == 200
    assert resp.json()["status"] == "canceled"


# ── End-to-end run through the worker ─────────────────────────────────


def test_worker_runs_queued_job_to_completion(worker_client, auth):
    job = worker_client.post(
        "/api/jobs",
        headers=auth,
        json={"recipients": ["a@x.com", "b@y.io"], "subject": "Campaign", "body": "Hi"},
    ).json()

    done = _poll_until(worker_client, auth, job["id"], {"completed", "failed"})
    assert done["status"] == "completed"
    assert done["sent"] == 2
    assert done["email_id"]
    # SES was actually invoked by the worker.
    assert worker_client.fake_ses.send_email.call_count >= 1

    # The completed job produced a campaign visible in history.
    campaigns = worker_client.get("/api/history", headers=auth).json()["campaigns"]
    assert any(c["subject"] == "Campaign" for c in campaigns)
