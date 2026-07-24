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
