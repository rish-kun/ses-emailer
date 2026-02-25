"""
History API router – view email campaigns and statistics.
"""

import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from api.auth import verify_token
from sending.db import Database

router = APIRouter()


@router.get("", dependencies=[Depends(verify_token)])
async def list_campaigns(search: str = ""):
    """List grouped email campaigns."""
    db = Database()
    grouped = db.get_grouped_emails_summary()
    db.close()

    if search:
        search_lower = search.lower()
        grouped = [
            g
            for g in grouped
            if search_lower in g["subject"].lower()
            or search_lower in g["sender"].lower()
        ]

    return {"campaigns": grouped, "total": len(grouped)}


@router.get("/stats", dependencies=[Depends(verify_token)])
async def get_stats():
    """Get overall email statistics."""
    db = Database()
    grouped = db.get_grouped_emails_summary()

    total_campaigns = len(grouped)
    total_sent = sum(g["sent_count"] for g in grouped)
    total_failed = sum(g["failed_count"] for g in grouped)

    # Unique recipients
    db.cursor.execute("SELECT COUNT(DISTINCT sent_to) FROM sent_emails")
    row = db.cursor.fetchone()
    unique_recipients = row[0] if row else 0

    # Today / this week
    today = datetime.date.today()
    db.cursor.execute(
        "SELECT sent_at FROM sent_emails WHERE sent_at IS NOT NULL"
    )
    all_sent_dates = db.cursor.fetchall()

    today_sent = 0
    week_sent = 0
    for (sent_at,) in all_sent_dates:
        try:
            sent_date = datetime.datetime.fromisoformat(
                str(sent_at).replace(" ", "T")
            ).date()
            if sent_date == today:
                today_sent += 1
            if (today - sent_date).days <= 7:
                week_sent += 1
        except (ValueError, TypeError):
            pass

    db.close()

    success_rate = (total_sent / (total_sent + total_failed) * 100) if (total_sent + total_failed) > 0 else 0

    return {
        "total_campaigns": total_campaigns,
        "total_sent": total_sent,
        "total_failed": total_failed,
        "unique_recipients": unique_recipients,
        "today_sent": today_sent,
        "week_sent": week_sent,
        "success_rate": round(success_rate, 1),
    }


@router.get("/{campaign_id}", dependencies=[Depends(verify_token)])
async def get_campaign_detail(campaign_id: str):
    """Get detailed info for a campaign (grouped email)."""
    db = Database()
    grouped = db.get_grouped_emails_summary()

    campaign = None
    for g in grouped:
        if g["id"] == campaign_id:
            campaign = g
            break

    if not campaign:
        db.close()
        raise HTTPException(status_code=404, detail="Campaign not found")

    email_ids = campaign["email_ids"]
    sent_records = db.get_sent_emails_by_email_ids(email_ids)
    failed_records = db.get_failed_emails_by_email_ids(email_ids)

    # Get the email template
    email = db.get_email(campaign_id)
    body = email[2] if email else ""

    db.close()

    sent = [
        {
            "id": r[0],
            "email_id": r[1],
            "recipient": r[2],
            "type": r[3],
            "sent_at": str(r[4]) if len(r) > 4 and r[4] else None,
        }
        for r in sent_records
    ]

    failed = [
        {
            "id": r[0],
            "email_id": r[1],
            "recipient": r[2],
            "error": r[3],
            "failed_at": str(r[4]) if len(r) > 4 and r[4] else None,
            "retried": bool(r[5]) if len(r) > 5 else False,
        }
        for r in failed_records
    ]

    return {
        "campaign": campaign,
        "body": body,
        "sent_records": sent,
        "failed_records": failed,
    }
