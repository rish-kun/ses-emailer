"""API smoke tests via FastAPI TestClient with SES mocked (see conftest)."""

import json
from pathlib import Path

import pandas as pd

from sending.db import Database
from sending.emails import Email


def parse_sse(text: str) -> list[tuple[str, dict]]:
    """Parse an SSE response body into a list of (event, data-dict) tuples."""
    events = []
    event_name = None
    for line in text.splitlines():
        if line.startswith("event:"):
            event_name = line.split(":", 1)[1].strip()
        elif line.startswith("data:") and event_name:
            events.append((event_name, json.loads(line.split(":", 1)[1].strip())))
            event_name = None
    return events


def events_of(events, name):
    return [d for e, d in events if e == name]


# ── Auth / health ─────────────────────────────────────────────────────


def test_health_needs_no_auth(client):
    assert client.get("/health").status_code == 200


def test_config_requires_token(client):
    # Missing credentials → 401/403 depending on FastAPI version; wrong token → 401.
    assert client.get("/api/config").status_code in (401, 403)
    assert (
        client.get("/api/config", headers={"Authorization": "Bearer wrong"}).status_code
        == 401
    )


# ── Sending ───────────────────────────────────────────────────────────


def test_send_happy_path(client, auth):
    resp = client.post(
        "/api/emails/send",
        headers=auth,
        json={
            "recipients": ["a@x.com", "b@y.io", "c@z.org"],
            "subject": "Hello",
            "body": "<p>Hi</p>",
        },
    )
    assert resp.status_code == 200
    events = parse_sse(resp.text)
    complete = events_of(events, "complete")[-1]
    assert complete["total_sent"] == 3
    assert complete["total_failed"] == 0
    assert client.fake_ses.send_email.call_count == 1  # single batch


def test_send_filters_invalid_recipients(client, auth):
    resp = client.post(
        "/api/emails/send",
        headers=auth,
        json={"recipients": ["not-an-email", "ok@test.com"], "subject": "s", "body": "b"},
    )
    events = parse_sse(resp.text)
    start = events_of(events, "start")[0]
    assert start["total_recipients"] == 1
    assert start["invalid"] == 1
    assert events_of(events, "complete")[-1]["total_sent"] == 1


def test_personalized_send_renders_per_recipient(client, auth):
    resp = client.post(
        "/api/emails/send",
        headers=auth,
        json={
            "recipients": ["a@x.com", "b@y.io"],
            "subject": "Hi {{name}}",
            "body": "Hello {{name}}, welcome!",
            "personalize": True,
            "recipient_fields": {
                "a@x.com": {"name": "Alice"},
                "b@y.io": {"name": "Bob"},
            },
        },
    )
    events = parse_sse(resp.text)
    start = events_of(events, "start")[0]
    assert start["personalized"] is True
    assert start["fields"] == ["name"]
    assert events_of(events, "complete")[-1]["total_sent"] == 2

    # One SES call per recipient (To:, not BCC), each rendered with its own name.
    assert client.fake_ses.send_email.call_count == 2
    raw_payloads = b" ".join(
        call.kwargs["Content"]["Raw"]["Data"]
        for call in client.fake_ses.send_email.call_args_list
    )
    assert b"Hello Alice" in raw_payloads
    assert b"Hello Bob" in raw_payloads
    destinations = [
        call.kwargs["Destination"]["ToAddresses"]
        for call in client.fake_ses.send_email.call_args_list
    ]
    assert ["a@x.com"] in destinations and ["b@y.io"] in destinations


def test_personalize_ignored_without_tokens(client, auth):
    """personalize=True but no {{tokens}} → single BCC batch, not per-recipient."""
    resp = client.post(
        "/api/emails/send",
        headers=auth,
        json={
            "recipients": ["a@x.com", "b@y.io"],
            "subject": "Plain subject",
            "body": "No tokens here",
            "personalize": True,
        },
    )
    start = events_of(parse_sse(resp.text), "start")[0]
    assert start["personalized"] is False
    assert client.fake_ses.send_email.call_count == 1  # single BCC batch


def test_send_skips_already_sent_when_requested(client, auth):
    # Seed a prior send of a@x.com.
    db = Database()
    email = Email(body="b", subject="s", sender="me", recipient="from@x.com")
    db.add_email(email)
    db.add_sent(email.id, "a@x.com", "bcc")
    db.close()

    resp = client.post(
        "/api/emails/send",
        headers=auth,
        json={
            "recipients": ["a@x.com", "new@y.io"],
            "subject": "s",
            "body": "b",
            "skip_already_sent": True,
        },
    )
    events = parse_sse(resp.text)
    start = events_of(events, "start")[0]
    assert start["skipped"] == 1
    assert start["total_recipients"] == 1  # only the new address


# ── Excel rows upload ─────────────────────────────────────────────────


def test_upload_excel_rows_endpoint(client, auth, tmp_path):
    xlsx = tmp_path / "people.xlsx"
    pd.DataFrame({"email": ["a@x.com", "b@y.io"], "name": ["Alice", "Bob"]}).to_excel(
        xlsx, index=False
    )
    dest = Path("data") / "people.xlsx"
    try:
        with open(xlsx, "rb") as f:
            resp = client.post(
                "/api/emails/upload-excel-rows",
                headers=auth,
                files={"file": ("people.xlsx", f, "application/octet-stream")},
                data={"email_column": "0"},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 2
        assert body["headers"] == ["email", "name"]
        assert body["rows"][0]["fields"]["name"] == "Alice"
    finally:
        dest.unlink(missing_ok=True)


# ── Retry ─────────────────────────────────────────────────────────────


def test_retry_resends_failed_and_marks_retried(client, auth):
    db = Database()
    email = Email(body="b", subject="Campaign X", sender="me", recipient="from@x.com")
    db.add_email(email)
    fid = db.add_failed_email(email.id, "bounce@x.com", "Throttled")
    db.close()

    resp = client.post(f"/api/history/{email.id}/retry", headers=auth)
    assert resp.status_code == 200
    complete = events_of(parse_sse(resp.text), "complete")[-1]
    assert complete["total_sent"] == 1

    # The failed record should now be marked retried.
    db = Database()
    assert db.get_unretried_failed_emails(email.id) == []
    db.close()
    assert fid is not None
