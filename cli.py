#!/usr/bin/env python3
"""
CLI for SES Email application.
Provides commands for database management and migrations.
"""

import argparse
import sys


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="SES Email CLI - Database management and utilities"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Migrate command
    migrate_parser = subparsers.add_parser(
        "migrate",
        help="Run database migrations",
    )
    migrate_parser.add_argument(
        "--consolidate",
        action="store_true",
        help="Consolidate duplicate email templates (same subject, sender, body)",
    )
    migrate_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    # Stats command
    subparsers.add_parser(
        "stats",
        help="Show database statistics",
    )

    # Check command
    subparsers.add_parser(
        "check",
        help="Check configuration and credentials",
    )

    args = parser.parse_args()

    if args.command == "migrate":
        run_migrate(args)
    elif args.command == "stats":
        show_stats()
    elif args.command == "check":
        check_credentials()
    else:
        parser.print_help()


def run_migrate(args):
    """Run database migrations."""
    from sending.db import Database

    db = Database()

    if args.consolidate:
        print("=" * 60)
        print("Consolidating Duplicate Email Templates")
        print("=" * 60)
        print()

        # First, show what will be done
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
            print("No duplicate email templates found. Database is already clean.")
            db.close()
            return

        print(f"Found {len(duplicates)} groups of duplicate templates:\n")
        total_duplicates = 0
        for subject, sender, count, ids in duplicates:
            print(f"  Subject: {subject[:50]}...")
            print(f"  Sender:  {sender}")
            print(f"  Count:   {count} duplicate templates")
            print()
            total_duplicates += count - 1  # -1 because we keep one

        print(f"Total templates to be removed: {total_duplicates}")
        print()

        if args.dry_run:
            print("[DRY RUN] No changes were made.")
            db.close()
            return

        # Ask for confirmation
        confirm = input("Do you want to proceed with consolidation? (yes/no): ")
        if confirm.lower() not in ("yes", "y"):
            print("Aborted.")
            db.close()
            return

        print("\nRunning migration...")
        stats = db.migrate_consolidate_duplicate_emails()

        print("\nMigration completed!")
        print(f"  Groups processed:      {stats['groups_found']}")
        print(f"  Templates removed:     {stats['templates_removed']}")
        print(f"  Sent emails updated:   {stats['sent_emails_updated']}")
        print(f"  Failed emails updated: {stats['failed_emails_updated']}")
    else:
        print("No migration specified. Use --consolidate to consolidate duplicates.")
        print("Run 'python cli.py migrate --help' for more options.")

    db.close()


def show_stats():
    """Show database statistics."""
    from sending.db import Database

    db = Database()

    print("=" * 60)
    print("Database Statistics")
    print("=" * 60)
    print()

    # Email templates
    db.cursor.execute("SELECT COUNT(*) FROM emails")
    email_count = db.cursor.fetchone()[0]
    print(f"Email Templates:     {email_count}")

    # Unique campaigns (grouped)
    grouped = db.get_grouped_emails_summary()
    print(f"Unique Campaigns:    {len(grouped)}")

    # Sent emails
    db.cursor.execute("SELECT COUNT(*) FROM sent_emails")
    sent_count = db.cursor.fetchone()[0]
    print(f"Total Sent Records:  {sent_count}")

    # Unique recipients
    db.cursor.execute("SELECT COUNT(DISTINCT sent_to) FROM sent_emails")
    unique_recipients = db.cursor.fetchone()[0]
    print(f"Unique Recipients:   {unique_recipients}")

    # Failed emails
    db.cursor.execute("SELECT COUNT(*) FROM failed_emails")
    failed_count = db.cursor.fetchone()[0]
    print(f"Failed Records:      {failed_count}")

    # Drafts
    if db.check_drafts_table_exists():
        db.cursor.execute("SELECT COUNT(*) FROM drafts")
        draft_count = db.cursor.fetchone()[0]
        print(f"Drafts:              {draft_count}")

    print()
    print("-" * 60)
    print("Campaigns Summary:")
    print("-" * 60)
    for g in grouped[:10]:
        subject = g["subject"][:40] + "..." if len(g["subject"]) > 40 else g["subject"]
        print(f"  {subject}")
        print(
            f"    Sender: {g['sender']} | Sent: {g['sent_count']} | Templates: {g['template_count']}"
        )

    if len(grouped) > 10:
        print(f"\n  ... and {len(grouped) - 10} more campaigns")

    db.close()


def check_credentials():
    """Check configuration and credentials."""
    import os
    from pathlib import Path

    print("=" * 60)
    print("Configuration Check")
    print("=" * 60)
    print()

    # Check .env file
    env_path = Path(".env")
    if env_path.exists():
        print("[OK] .env file found")

        # Check for AWS credentials
        with open(env_path) as f:
            env_content = f.read()

        required_vars = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"]
        for var in required_vars:
            if var in env_content:
                print(f"  [OK] {var} is set")
            else:
                print(f"  [MISSING] {var} is not set")
    else:
        print("[MISSING] .env file not found")
        print("  Create a .env file with your AWS credentials:")
        print("    AWS_ACCESS_KEY_ID=your_key")
        print("    AWS_SECRET_ACCESS_KEY=your_secret")
        print("    AWS_REGION=us-east-1")

    print()

    # Check database
    db_path = Path("emails.db")
    if db_path.exists():
        print(f"[OK] Database found ({db_path})")

        from sending.db import Database

        db = Database()
        print(f"  Tables: emails, sent_emails, failed_emails, drafts")
        db.close()
    else:
        print("[INFO] Database will be created on first run")

    print()

    # Check directories
    dirs = ["data", "files", "config"]
    for d in dirs:
        if Path(d).exists():
            print(f"[OK] Directory '{d}' exists")
        else:
            print(f"[INFO] Directory '{d}' will be created when needed")


def configure_settings():
    """Interactive settings configuration."""
    pass  # TODO: Implement interactive configuration


if __name__ == "__main__":
    main()
