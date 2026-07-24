"""
Email API router – sending, file uploads, recipient comparison.
"""

import asyncio
import json
import logging
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from api.auth import verify_token
from config.settings import format_source_email, get_config, get_email_address
from sending.db import Database
from sending.validation import partition_valid

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Request models ────────────────────────────────────────────────────


class SendRequest(BaseModel):
    recipients: list[str]
    subject: str
    body: str
    email_type: str = "html"
    attachments: list[str] = []
    # When true, addresses already sent this subject are skipped (dedup).
    skip_already_sent: bool = False


class CompareRequest(BaseModel):
    recipients: list[str]
    email_id: str | None = None
    email_ids: list[str] | None = None


class ExcelUploadRequest(BaseModel):
    column_index: int = 0


# ── Shared send stream ────────────────────────────────────────────────


def _sse(event: str, **data) -> dict:
    return {"event": event, "data": json.dumps(data)}


def _send_batch_sync(ses_client, msg_bytes: bytes, from_address, to_address, batch, use_bcc):
    """Blocking SES send for a single batch. Run via asyncio.to_thread."""
    return ses_client.send_email(
        FromEmailAddress=from_address,
        Destination={
            "BccAddresses": batch if use_bcc else [],
            "ToAddresses": [to_address] if use_bcc else batch,
        },
        Content={"Raw": {"Data": msg_bytes}},
    )


async def send_event_stream(
    *,
    recipients: list[str],
    subject: str,
    body: str,
    email_type: str,
    attachments: list[str],
    skip_already_sent: bool = False,
    existing_email_id: Optional[str] = None,
    mark_retried: Optional[dict[str, int]] = None,
):
    """
    Async generator yielding SSE event dicts for a batch send.

    Shared by the /emails/send endpoint and the campaign retry endpoint. All
    blocking SES/SQLite calls are dispatched to worker threads so the event loop
    (and other API requests) stay responsive during a send.

    Args:
        existing_email_id: reuse this email template id (retry) instead of
            creating a new one on the first successful batch.
        mark_retried: map of recipient -> failed_email row id to mark as retried
            once that recipient is successfully re-sent (retry flow).
    """
    config_mgr = get_config()
    config_mgr.apply_env_vars()
    cfg = config_mgr.config

    batch_size = cfg.batch.batch_size
    delay = cfg.batch.delay_seconds
    use_bcc = cfg.batch.use_bcc

    db = Database()

    # Validate + optionally dedup before touching SES.
    valid, invalid = partition_valid(recipients)
    skipped: list[str] = []
    if skip_already_sent and valid:
        comparison = await asyncio.to_thread(
            db.compare_recipients, valid, None, None
        )
        already = set(comparison["already_sent_list"])
        skipped = [r for r in valid if r in already]
        valid = [r for r in valid if r not in already]

    recipients = valid
    total_batches = (len(recipients) + batch_size - 1) // batch_size if recipients else 0
    total_sent = 0
    total_failed = 0
    current_email_id: Optional[str] = existing_email_id

    yield _sse(
        "start",
        total_recipients=len(recipients),
        total_batches=total_batches,
        batch_size=batch_size,
        delay=delay,
        invalid=len(invalid),
        invalid_list=invalid[:50],
        skipped=len(skipped),
    )

    if not recipients:
        yield _sse("complete", total_sent=0, total_failed=0)
        db.close()
        return

    try:
        import boto3
        from botocore.exceptions import ClientError

        ses_client = await asyncio.to_thread(
            boto3.client,
            "sesv2",
            region_name=cfg.aws.region,
            aws_access_key_id=cfg.aws.access_key_id,
            aws_secret_access_key=cfg.aws.secret_access_key,
        )

        def _ensure_email_id() -> str:
            """Create the email template row on first use; reused thereafter."""
            nonlocal current_email_id
            if current_email_id is None:
                from sending.emails import Email

                email_obj = Email(
                    body=body,
                    subject=subject,
                    sender=cfg.sender.sender_name,
                    recipient=cfg.aws.source_email,
                    files=attachments,
                )
                current_email_id = email_obj.id
                try:
                    db.add_email(email_obj)
                except Exception as e:
                    logger.warning("Failed to persist email template: %s", e)
            return current_email_id

        for batch_num, i in enumerate(range(0, len(recipients), batch_size), start=1):
            batch = recipients[i : i + batch_size]

            yield _sse(
                "batch_start",
                batch=batch_num,
                total_batches=total_batches,
                batch_size=len(batch),
            )

            try:
                msg = _create_message(
                    subject=subject,
                    body=body,
                    email_type=email_type,
                    attachments=attachments,
                    config=cfg,
                )
                source_email = cfg.aws.source_email
                from_address = format_source_email(source_email, cfg.sender.sender_name)
                to_address = cfg.sender.default_to or get_email_address(source_email)

                response = await asyncio.to_thread(
                    _send_batch_sync,
                    ses_client,
                    msg.as_bytes(),
                    from_address,
                    to_address,
                    batch,
                    use_bcc,
                )

                total_sent += len(batch)
                email_id = _ensure_email_id()

                for recipient in batch:
                    await asyncio.to_thread(db.add_sent, email_id, recipient, "bcc")
                    if mark_retried and recipient in mark_retried:
                        await asyncio.to_thread(
                            db.mark_failed_email_retried, mark_retried[recipient]
                        )

                yield _sse(
                    "batch_complete",
                    batch=batch_num,
                    sent=len(batch),
                    total_sent=total_sent,
                    total_failed=total_failed,
                    message_id=response.get("MessageId", "")[:16],
                )

            except ClientError as e:
                error_msg = e.response["Error"]["Message"]
                total_failed += len(batch)
                email_id = _ensure_email_id()
                for recipient in batch:
                    await asyncio.to_thread(
                        db.add_failed_email, email_id, recipient, error_msg
                    )
                yield _sse(
                    "batch_error",
                    batch=batch_num,
                    failed=len(batch),
                    total_sent=total_sent,
                    total_failed=total_failed,
                    error=error_msg,
                )

            except Exception as e:
                error_msg = str(e)
                total_failed += len(batch)
                # Record generic failures too (previously only counted, not logged).
                email_id = _ensure_email_id()
                for recipient in batch:
                    await asyncio.to_thread(
                        db.add_failed_email, email_id, recipient, error_msg
                    )
                yield _sse(
                    "batch_error",
                    batch=batch_num,
                    failed=len(batch),
                    total_sent=total_sent,
                    total_failed=total_failed,
                    error=error_msg,
                )

            # Delay between batches
            if batch_num < total_batches:
                for remaining in range(int(delay), 0, -1):
                    yield _sse("waiting", seconds_remaining=remaining)
                    await asyncio.sleep(1)

    except Exception as e:
        logger.exception("Send stream failed")
        yield _sse("error", error=str(e))

    finally:
        db.close()

    yield _sse("complete", total_sent=total_sent, total_failed=total_failed)


# ── Email sending (SSE stream) ────────────────────────────────────────


@router.post("/emails/send", dependencies=[Depends(verify_token)])
async def send_emails(req: SendRequest):
    """Start batch email sending. Returns an SSE stream with progress events."""
    return EventSourceResponse(
        send_event_stream(
            recipients=req.recipients,
            subject=req.subject,
            body=req.body,
            email_type=req.email_type,
            attachments=req.attachments,
            skip_already_sent=req.skip_already_sent,
        )
    )


# ── File / Excel uploads ──────────────────────────────────────────────


@router.post("/emails/upload-excel", dependencies=[Depends(verify_token)])
async def upload_excel(file: UploadFile = File(...), column_index: int = 0):
    """Upload an Excel file and return parsed recipient emails."""
    if not file.filename or not file.filename.endswith((".xlsx", ".xls", ".csv")):
        raise HTTPException(status_code=400, detail="File must be .xlsx, .xls, or .csv")

    # Save to temp location
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    dest = data_dir / file.filename
    with open(dest, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        from sending.email_list import scrape_excel_column

        emails = scrape_excel_column(str(dest), column_index)
        return {
            "file": file.filename,
            "column_index": column_index,
            "recipients": emails,
            "count": len(emails),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing Excel: {e}")


@router.post("/emails/compare", dependencies=[Depends(verify_token)])
async def compare_recipients(body: CompareRequest):
    """Compare recipients against previously sent emails."""
    db = Database()
    result = db.compare_recipients(
        body.recipients, email_id=body.email_id, email_ids=body.email_ids
    )
    db.close()
    return result


@router.post("/files/upload", dependencies=[Depends(verify_token)])
async def upload_file(file: UploadFile = File(...)):
    """Upload an attachment file."""
    files_dir = Path(get_config().config.files_directory)
    files_dir.mkdir(exist_ok=True)
    dest = files_dir / (file.filename or "attachment")
    with open(dest, "wb") as f:
        content = await file.read()
        f.write(content)
    return {"filename": file.filename, "path": str(dest)}


@router.get("/files", dependencies=[Depends(verify_token)])
async def list_files():
    """List files in the attachments directory."""
    files_dir = Path(get_config().config.files_directory)
    if not files_dir.exists():
        return {"files": []}
    files = [
        {"name": f.name, "size": f.stat().st_size, "path": str(f)}
        for f in files_dir.iterdir()
        if f.is_file()
    ]
    return {"files": files}


# ── Helpers ───────────────────────────────────────────────────────────


def _create_message(
    subject: str,
    body: str,
    email_type: str,
    attachments: list[str],
    config,
) -> MIMEMultipart:
    """Create the email MIME message."""
    msg = MIMEMultipart()
    msg["Subject"] = subject
    source_email = config.aws.source_email
    msg["From"] = format_source_email(source_email, config.sender.sender_name)
    msg["To"] = config.sender.default_to or get_email_address(source_email)
    msg["Reply-To"] = config.sender.reply_to or get_email_address(source_email)

    body_part = MIMEMultipart("alternative")
    mime_type = "html" if email_type == "html" else "plain"
    body_part.attach(MIMEText(body, mime_type))
    msg.attach(body_part)

    for attachment_path in attachments:
        try:
            path = Path(attachment_path)
            with open(path, "rb") as f:
                part = MIMEApplication(f.read(), Name=path.name)
                part.add_header("Content-Disposition", "attachment", filename=path.name)
                msg.attach(part)
        except Exception as e:
            logger.warning("Skipping unreadable attachment %s: %s", attachment_path, e)

    return msg
