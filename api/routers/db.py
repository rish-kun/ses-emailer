"""
Database management API router – migrations, stats, health checks.
"""

import os
from pathlib import Path

from fastapi import APIRouter, Depends

from api.auth import verify_token
from sending.db import Database

router = APIRouter()


@router.post("/migrate", dependencies=[Depends(verify_token)])
async def run_migration(consolidate: bool = True):
    """Run database migration (consolidate duplicate templates)."""
    if not consolidate:
        return {"message": "No migration specified. Set consolidate=true."}

    db = Database()

    # Check for duplicates
    db.cursor.execute(
        """
        SELECT subject, sender, COUNT(*) as cnt, GROUP_CONCAT(id) as ids
        FROM emails
        GROUP BY subject, sender, body
        HAVING cnt > 1
        ORDER BY cnt DESC
        """
    )
    duplicates = db.cursor.fetchall()

    if not duplicates:
        db.close()
        return {"message": "No duplicates found. Database is already clean."}

    stats = db.migrate_consolidate_duplicate_emails()
    db.close()
    return {"message": "Migration completed", "stats": stats}


@router.get("/stats", dependencies=[Depends(verify_token)])
async def get_db_stats():
    """Get database statistics."""
    db = Database()

    db.cursor.execute("SELECT COUNT(*) FROM emails")
    email_count = db.cursor.fetchone()[0]

    grouped = db.get_grouped_emails_summary()

    db.cursor.execute("SELECT COUNT(*) FROM sent_emails")
    sent_count = db.cursor.fetchone()[0]

    db.cursor.execute("SELECT COUNT(DISTINCT sent_to) FROM sent_emails")
    unique_recipients = db.cursor.fetchone()[0]

    db.cursor.execute("SELECT COUNT(*) FROM failed_emails")
    failed_count = db.cursor.fetchone()[0]

    draft_count = 0
    if db.check_drafts_table_exists():
        db.cursor.execute("SELECT COUNT(*) FROM drafts")
        draft_count = db.cursor.fetchone()[0]

    db.close()

    return {
        "email_templates": email_count,
        "unique_campaigns": len(grouped),
        "total_sent": sent_count,
        "unique_recipients": unique_recipients,
        "failed": failed_count,
        "drafts": draft_count,
    }


@router.get("/check", dependencies=[Depends(verify_token)])
async def check_credentials():
    """Check configuration and system health."""
    from config.settings import get_config

    cm = get_config()
    checks = {}

    # Config
    checks["config_file"] = cm.config_path.exists()
    checks["is_configured"] = cm.is_configured()

    # AWS vars
    checks["aws_access_key_set"] = bool(cm.config.aws.access_key_id)
    checks["aws_secret_key_set"] = bool(cm.config.aws.secret_access_key)
    checks["aws_region"] = cm.config.aws.region
    checks["source_email_set"] = bool(cm.config.aws.source_email)

    # Database
    checks["database_exists"] = Path("emails.db").exists()

    # Directories
    for d in ["data", "files", "config"]:
        checks[f"dir_{d}"] = Path(d).exists()

    return checks
