from sending.db import Database
from sending.emails import Email


def _db(db_path):
    return Database()


def test_db_honors_env_path(db_path):
    db = Database()
    assert db.path == db_path
    db.close()


def test_sent_and_compare(db_path):
    db = Database()
    email = Email(body="b", subject="s", sender="me", recipient="from@x.com")
    db.add_email(email)
    db.add_sent(email.id, "a@x.com", "bcc")

    result = db.compare_recipients(["a@x.com", "b@y.io"])
    assert result["already_sent"] == 1
    assert result["new_recipients"] == 1
    assert "b@y.io" in result["new_recipients_list"]
    db.close()


def test_failed_email_lifecycle(db_path):
    db = Database()
    email = Email(body="b", subject="s", sender="me", recipient="from@x.com")
    db.add_email(email)
    fid = db.add_failed_email(email.id, "bad@x.com", "Throttled")

    unretried = db.get_unretried_failed_emails(email.id)
    assert len(unretried) == 1
    assert unretried[0][2] == "bad@x.com"

    assert db.mark_failed_email_retried(fid) is True
    assert db.get_unretried_failed_emails(email.id) == []
    db.close()


def test_job_lifecycle(db_path):
    import datetime

    db = Database()
    db.add_job("j1", {"recipients": ["a@x.com", "b@y.io"], "subject": "s"}, name="Test")
    job = db.get_job("j1")
    assert job["status"] == "pending"
    assert job["total"] == 2

    claimed = db.claim_next_job()
    assert claimed["id"] == "j1"
    assert claimed["status"] == "running"
    assert db.claim_next_job() is None  # nothing else runnable

    db.update_job_progress("j1", 2, 0)
    db.finish_job("j1", "completed", email_id="e1")
    done = db.get_job("j1")
    assert done["status"] == "completed"
    assert done["sent"] == 2
    assert done["email_id"] == "e1"

    # A future-scheduled job is not claimed until due.
    future = datetime.datetime.now() + datetime.timedelta(hours=1)
    db.add_job("j2", {"recipients": ["c@z.com"]}, scheduled_at=future)
    assert db.get_job("j2")["status"] == "scheduled"
    assert db.claim_next_job() is None
    db.close()


def test_job_cancel_and_requeue(db_path):
    db = Database()
    db.add_job("j1", {"recipients": ["a@x.com"]})
    assert db.cancel_job("j1") is True
    assert db.get_job("j1")["status"] == "canceled"
    assert db.cancel_job("j1") is False  # already terminal

    # Requeue recovers interrupted (running) jobs.
    db.add_job("j2", {"recipients": ["b@y.io"]})
    db.claim_next_job()  # marks j2 running
    assert db.get_job("j2")["status"] == "running"
    assert db.requeue_running_jobs() == 1
    assert db.get_job("j2")["status"] == "pending"
    db.close()


def test_draft_crud(db_path):
    db = Database()
    did = db.add_draft(name="Draft 1", subject="Hi", body="Body", recipients=["a@x.com"])
    draft = db.get_draft(did)
    assert draft["name"] == "Draft 1"
    assert draft["recipients"] == ["a@x.com"]

    assert db.update_draft(did, subject="Updated") is True
    assert db.get_draft(did)["subject"] == "Updated"

    assert db.delete_draft(did) is True
    assert db.get_draft(did) is None
    db.close()
