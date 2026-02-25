"""
Email API router – sending, file uploads, recipient comparison.
"""

import asyncio
import datetime
import json
import os
import shutil
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

router = APIRouter()


# ── Request models ────────────────────────────────────────────────────


class SendRequest(BaseModel):
    recipients: list[str]
    subject: str
    body: str
    email_type: str = "html"
    attachments: list[str] = []


class CompareRequest(BaseModel):
    recipients: list[str]
    email_id: str | None = None
    email_ids: list[str] | None = None


class ExcelUploadRequest(BaseModel):
    column_index: int = 0


# ── Email sending (SSE stream) ────────────────────────────────────────


@router.post("/emails/send", dependencies=[Depends(verify_token)])
async def send_emails(req: SendRequest):
    """Start batch email sending. Returns an SSE stream with progress events."""

    async def event_generator():
        config_mgr = get_config()
        config_mgr.apply_env_vars()
        cfg = config_mgr.config

        batch_size = cfg.batch.batch_size
        delay = cfg.batch.delay_seconds
        use_bcc = cfg.batch.use_bcc
        recipients = req.recipients
        total_batches = (len(recipients) + batch_size - 1) // batch_size
        total_sent = 0
        total_failed = 0
        current_email_id: Optional[str] = None

        yield {
            "event": "start",
            "data": json.dumps(
                {
                    "total_recipients": len(recipients),
                    "total_batches": total_batches,
                    "batch_size": batch_size,
                    "delay": delay,
                }
            ),
        }

        try:
            import boto3
            from botocore.exceptions import ClientError

            ses_client = boto3.client(
                "sesv2",
                region_name=cfg.aws.region,
                aws_access_key_id=cfg.aws.access_key_id,
                aws_secret_access_key=cfg.aws.secret_access_key,
            )

            db = Database()

            for batch_num, i in enumerate(
                range(0, len(recipients), batch_size), start=1
            ):
                batch = recipients[i : i + batch_size]

                yield {
                    "event": "batch_start",
                    "data": json.dumps(
                        {
                            "batch": batch_num,
                            "total_batches": total_batches,
                            "batch_size": len(batch),
                        }
                    ),
                }

                try:
                    msg = _create_message(
                        subject=req.subject,
                        body=req.body,
                        email_type=req.email_type,
                        attachments=req.attachments,
                        config=cfg,
                    )

                    source_email = cfg.aws.source_email
                    from_address = format_source_email(
                        source_email, cfg.sender.sender_name
                    )
                    to_address = cfg.sender.default_to or get_email_address(
                        source_email
                    )

                    response = ses_client.send_email(
                        FromEmailAddress=from_address,
                        Destination={
                            "BccAddresses": batch if use_bcc else [],
                            "ToAddresses": [to_address] if use_bcc else batch,
                        },
                        Content={"Raw": {"Data": msg.as_bytes()}},
                    )

                    total_sent += len(batch)

                    # Save to database
                    if current_email_id is None:
                        from sending.emails import Email

                        email_obj = Email(
                            body=req.body,
                            subject=req.subject,
                            sender=cfg.sender.sender_name,
                            recipient=cfg.aws.source_email,
                            files=req.attachments,
                        )
                        current_email_id = email_obj.id
                        try:
                            db.add_email(email_obj)
                        except Exception:
                            pass

                    for recipient in batch:
                        db.add_sent(current_email_id, recipient, "bcc")

                    yield {
                        "event": "batch_complete",
                        "data": json.dumps(
                            {
                                "batch": batch_num,
                                "sent": len(batch),
                                "total_sent": total_sent,
                                "total_failed": total_failed,
                                "message_id": response.get("MessageId", "")[:16],
                            }
                        ),
                    }

                except ClientError as e:
                    error_msg = e.response["Error"]["Message"]
                    total_failed += len(batch)

                    # Save failed to database
                    if current_email_id is None:
                        from sending.emails import Email

                        email_obj = Email(
                            body=req.body,
                            subject=req.subject,
                            sender=cfg.sender.sender_name,
                            recipient=cfg.aws.source_email,
                            files=req.attachments,
                        )
                        current_email_id = email_obj.id
                        try:
                            db.add_email(email_obj)
                        except Exception:
                            pass

                    for recipient in batch:
                        db.add_failed_email(current_email_id, recipient, error_msg)

                    yield {
                        "event": "batch_error",
                        "data": json.dumps(
                            {
                                "batch": batch_num,
                                "failed": len(batch),
                                "total_sent": total_sent,
                                "total_failed": total_failed,
                                "error": error_msg,
                            }
                        ),
                    }

                except Exception as e:
                    error_msg = str(e)
                    total_failed += len(batch)

                    yield {
                        "event": "batch_error",
                        "data": json.dumps(
                            {
                                "batch": batch_num,
                                "failed": len(batch),
                                "total_sent": total_sent,
                                "total_failed": total_failed,
                                "error": error_msg,
                            }
                        ),
                    }

                # Delay between batches
                if batch_num < total_batches:
                    for remaining in range(int(delay), 0, -1):
                        yield {
                            "event": "waiting",
                            "data": json.dumps({"seconds_remaining": remaining}),
                        }
                        await asyncio.sleep(1)

            db.close()

        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)}),
            }

        yield {
            "event": "complete",
            "data": json.dumps(
                {
                    "total_sent": total_sent,
                    "total_failed": total_failed,
                }
            ),
        }

    return EventSourceResponse(event_generator())


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
        return {"file": file.filename, "column_index": column_index, "recipients": emails, "count": len(emails)}
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
                part.add_header(
                    "Content-Disposition", "attachment", filename=path.name
                )
                msg.attach(part)
        except Exception:
            pass

    return msg
