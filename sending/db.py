import datetime
import sqlite3


class Database:
    path: str = ""
    conn: sqlite3.Connection
    cursor: sqlite3.Cursor

    def __init__(self, file_name="emails.db") -> None:
        self.path = "emails.db"
        self.conn = sqlite3.connect(self.path)
        self.cursor = self.conn.cursor()
        if not self.check_table_exists():
            self.create_tables()
        if not self.check_drafts_table_exists():
            self.create_drafts_table()
        if not self.check_failed_emails_table_exists():
            self.create_failed_emails_table()

    def check_table_exists(self):
        self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='emails'"
        )
        return bool(self.cursor.fetchone())

    def check_drafts_table_exists(self):
        self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='drafts'"
        )
        return bool(self.cursor.fetchone())

    def check_failed_emails_table_exists(self):
        self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='failed_emails'"
        )
        return bool(self.cursor.fetchone())

    def create_tables(self):
        self.cursor.execute(
            """
            CREATE TABLE emails (
                id TEXT PRIMARY KEY,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                sender TEXT NOT NULL,
                files TEXT NOT NULL DEFAULT ''
            )
            """
        )
        self.cursor.execute(
            """
            CREATE TABLE sent_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id TEXT NOT NULL,
                sent_to TEXT NOT NULL,
                sent_type TEXT NOT NULL DEFAULT 'bcc',
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (email_id) REFERENCES emails(id)
            )
            """
        )
        self.conn.commit()

    def create_drafts_table(self):
        """Create the drafts table for storing email drafts."""
        self.cursor.execute(
            """
            CREATE TABLE drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                subject TEXT NOT NULL DEFAULT '',
                body TEXT NOT NULL DEFAULT '',
                sender TEXT NOT NULL DEFAULT '',
                recipients TEXT NOT NULL DEFAULT '',
                attachments TEXT NOT NULL DEFAULT '',
                email_type TEXT NOT NULL DEFAULT 'html',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.conn.commit()

    def create_failed_emails_table(self):
        """Create the failed_emails table for tracking failed email attempts."""
        self.cursor.execute(
            """
            CREATE TABLE failed_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id TEXT NOT NULL,
                recipient TEXT NOT NULL,
                error_reason TEXT NOT NULL DEFAULT '',
                failed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                retried INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (email_id) REFERENCES emails(id)
            )
            """
        )
        self.conn.commit()

    def close(self):
        self.conn.close()

    def add_email(self, email):
        if email.files:
            files = ", ".join(email.files)
        else:
            files = ""
        resp = self.cursor.execute(
            "INSERT INTO emails (id, subject, body, sender, files) VALUES (?, ?, ?, ?, ?)",
            (email.id, email.subject, email.body, email.sender, files),
        )
        self.conn.commit()
        return resp

    def get_email(self, email_id):
        self.cursor.execute("SELECT * FROM emails WHERE id = ?", (email_id,))
        return self.cursor.fetchone()

    def get_email_by_sender(self, sender):
        self.cursor.execute("SELECT * FROM emails WHERE sender = ?", (sender,))
        return self.cursor.fetchall()

    def get_all_emails(self):
        self.cursor.execute("SELECT * FROM emails")
        return self.cursor.fetchall()

    def add_sent(self, email_id, sent_to, sent_type):
        self.cursor.execute(
            "INSERT INTO sent_emails (email_id, sent_to, sent_type, sent_at) VALUES (?, ?, ?, ?)",
            (email_id, sent_to, sent_type, datetime.datetime.now()),
        )
        self.conn.commit()

    def check_sent(self, email_id, sent_to):
        self.cursor.execute(
            "SELECT * FROM sent_emails WHERE email_id = ? AND sent_to = ?",
            (email_id, sent_to),
        )
        return self.cursor.fetchone()

    def get_sent_emails(self):
        self.cursor.execute("SELECT * FROM sent_emails")
        return self.cursor.fetchall()

    def get_sent_emails_by_sender(self, sender):
        self.cursor.execute("SELECT * FROM sent_emails WHERE sent_to = ?", (sender,))
        return self.cursor.fetchall()

    def get_sent_emails_by_email_id(self, email_id):
        self.cursor.execute("SELECT * FROM sent_emails WHERE email_id = ?", (email_id,))
        return self.cursor.fetchall()

    def get_all_sent_recipients(self) -> set[str]:
        """Get all unique recipients that have ever been sent an email."""
        self.cursor.execute("SELECT DISTINCT sent_to FROM sent_emails")
        return {row[0] for row in self.cursor.fetchall()}

    def get_sent_recipients_by_email_id(self, email_id: str) -> set[str]:
        """Get all recipients that received a specific email."""
        self.cursor.execute(
            "SELECT DISTINCT sent_to FROM sent_emails WHERE email_id = ?",
            (email_id,),
        )
        return {row[0] for row in self.cursor.fetchall()}

    def get_sent_recipients_by_subject(self, subject: str) -> set[str]:
        """Get all recipients that received emails with a specific subject."""
        self.cursor.execute(
            """
            SELECT DISTINCT se.sent_to
            FROM sent_emails se
            JOIN emails e ON se.email_id = e.id
            WHERE e.subject = ?
            """,
            (subject,),
        )
        return {row[0] for row in self.cursor.fetchall()}

    def compare_recipients(
        self,
        current_recipients: list[str],
        email_id: str | None = None,
        email_ids: list[str] | None = None,
    ) -> dict:
        """
        Compare a list of recipients against previously sent emails.

        Args:
            current_recipients: List of email addresses to compare
            email_id: Optional specific email ID to compare against.
                     If None, compares against all sent emails.
            email_ids: Optional list of email IDs to compare against (for grouped emails).
                      Takes precedence over email_id if provided.

        Returns:
            Dictionary with comparison results:
            - total: Total recipients in current list
            - already_sent: Recipients who already received this/any email
            - new_recipients: Recipients who haven't received this/any email
            - already_sent_list: List of already sent addresses
            - new_recipients_list: List of new addresses
        """
        current_set = {r.strip().lower() for r in current_recipients if r.strip()}

        if email_ids:
            # Get recipients from multiple email IDs (grouped emails)
            sent_set = set()
            for eid in email_ids:
                sent_set.update(
                    r.lower() for r in self.get_sent_recipients_by_email_id(eid)
                )
        elif email_id:
            sent_set = {
                r.lower() for r in self.get_sent_recipients_by_email_id(email_id)
            }
        else:
            sent_set = {r.lower() for r in self.get_all_sent_recipients()}

        already_sent = current_set & sent_set
        new_recipients = current_set - sent_set

        return {
            "total": len(current_set),
            "already_sent": len(already_sent),
            "new_recipients": len(new_recipients),
            "already_sent_list": list(already_sent),
            "new_recipients_list": list(new_recipients),
        }

    def get_emails_summary(self) -> list[dict]:
        """
        Get a summary of all emails with their send counts.

        Returns:
            List of dictionaries with email info and send count.
        """
        self.cursor.execute(
            """
            SELECT e.id, e.subject, e.sender,
                   COUNT(DISTINCT se.sent_to) as sent_count,
                   MAX(se.sent_at) as last_sent
            FROM emails e
            LEFT JOIN sent_emails se ON e.id = se.email_id
            GROUP BY e.id
            ORDER BY last_sent DESC NULLS LAST
            """
        )
        results = []
        for row in self.cursor.fetchall():
            results.append(
                {
                    "id": row[0],
                    "subject": row[1],
                    "sender": row[2],
                    "sent_count": row[3] or 0,
                    "last_sent": row[4],
                }
            )
        return results

    def get_grouped_emails_summary(self) -> list[dict]:
        """
        Get a summary of emails grouped by subject, sender, and body.
        This consolidates duplicate email templates into single entries.

        Returns:
            List of dictionaries with grouped email info and aggregated stats.
        """
        # First, get all emails and group them by (subject, sender, body)
        self.cursor.execute(
            """
            SELECT id, subject, body, sender, files
            FROM emails
            ORDER BY subject, sender
            """
        )
        emails = self.cursor.fetchall()

        # Group by (subject, sender, body)
        groups: dict[tuple, dict] = {}
        for email in emails:
            email_id, subject, body, sender, files = email
            group_key = (subject, sender, body)

            if group_key not in groups:
                groups[group_key] = {
                    "email_ids": [],
                    "subject": subject,
                    "sender": sender,
                    "body": body,
                    "files": files,
                    "sent_count": 0,
                    "failed_count": 0,
                    "last_sent": None,
                }
            groups[group_key]["email_ids"].append(email_id)

        # Now get aggregated stats for each group
        results = []
        for group_key, group_data in groups.items():
            email_ids = group_data["email_ids"]

            # Get sent count and last sent date for all email_ids in this group
            placeholders = ",".join("?" * len(email_ids))
            self.cursor.execute(
                f"""
                SELECT COUNT(DISTINCT sent_to), MAX(sent_at)
                FROM sent_emails
                WHERE email_id IN ({placeholders})
                """,
                email_ids,
            )
            sent_result = self.cursor.fetchone()
            sent_count = sent_result[0] if sent_result else 0
            last_sent = sent_result[1] if sent_result else None

            # Get failed count for all email_ids in this group
            self.cursor.execute(
                f"""
                SELECT COUNT(*)
                FROM failed_emails
                WHERE email_id IN ({placeholders})
                """,
                email_ids,
            )
            failed_result = self.cursor.fetchone()
            failed_count = failed_result[0] if failed_result else 0

            # Use the first email_id as the group key for the UI
            primary_id = email_ids[0]

            results.append(
                {
                    "id": primary_id,
                    "email_ids": email_ids,
                    "subject": group_data["subject"],
                    "sender": group_data["sender"],
                    "body": group_data["body"],
                    "files": group_data["files"],
                    "sent_count": sent_count,
                    "failed_count": failed_count,
                    "last_sent": last_sent,
                    "template_count": len(email_ids),
                }
            )

        # Sort by last_sent descending (most recent first)
        results.sort(key=lambda x: x["last_sent"] or "", reverse=True)
        return results

    def get_sent_emails_by_email_ids(self, email_ids: list[str]) -> list:
        """Get all sent email records for multiple email IDs."""
        if not email_ids:
            return []
        placeholders = ",".join("?" * len(email_ids))
        self.cursor.execute(
            f"SELECT * FROM sent_emails WHERE email_id IN ({placeholders}) ORDER BY sent_at DESC",
            email_ids,
        )
        return self.cursor.fetchall()

    def get_failed_emails_by_email_ids(self, email_ids: list[str]) -> list:
        """Get all failed email records for multiple email IDs."""
        if not email_ids:
            return []
        placeholders = ",".join("?" * len(email_ids))
        self.cursor.execute(
            f"SELECT * FROM failed_emails WHERE email_id IN ({placeholders}) ORDER BY failed_at DESC",
            email_ids,
        )
        return self.cursor.fetchall()

    def migrate_consolidate_duplicate_emails(self) -> dict:
        """
        Migrate duplicate email templates by consolidating them.

        This finds emails with identical (subject, sender, body), keeps the oldest one,
        updates sent_emails and failed_emails to point to it, and deletes the duplicates.

        Returns:
            Dictionary with migration stats:
            - groups_found: Number of duplicate groups found
            - templates_removed: Number of duplicate templates removed
            - sent_emails_updated: Number of sent_emails records updated
            - failed_emails_updated: Number of failed_emails records updated
        """
        stats = {
            "groups_found": 0,
            "templates_removed": 0,
            "sent_emails_updated": 0,
            "failed_emails_updated": 0,
        }

        # Find duplicate groups
        self.cursor.execute(
            """
            SELECT subject, sender, body, GROUP_CONCAT(id) as ids, COUNT(*) as cnt
            FROM emails
            GROUP BY subject, sender, body
            HAVING cnt > 1
            """
        )
        duplicate_groups = self.cursor.fetchall()

        stats["groups_found"] = len(duplicate_groups)

        for group in duplicate_groups:
            subject, sender, body, ids_str, count = group
            email_ids = ids_str.split(",")

            # Keep the first one (canonical), remove the rest
            canonical_id = email_ids[0]
            duplicate_ids = email_ids[1:]

            for dup_id in duplicate_ids:
                # Update sent_emails to point to canonical
                self.cursor.execute(
                    "UPDATE sent_emails SET email_id = ? WHERE email_id = ?",
                    (canonical_id, dup_id),
                )
                stats["sent_emails_updated"] += self.cursor.rowcount

                # Update failed_emails to point to canonical
                self.cursor.execute(
                    "UPDATE failed_emails SET email_id = ? WHERE email_id = ?",
                    (canonical_id, dup_id),
                )
                stats["failed_emails_updated"] += self.cursor.rowcount

                # Delete the duplicate email template
                self.cursor.execute("DELETE FROM emails WHERE id = ?", (dup_id,))
                stats["templates_removed"] += self.cursor.rowcount

        self.conn.commit()
        return stats

    # Failed emails operations

    def add_failed_email(
        self, email_id: str, recipient: str, error_reason: str
    ) -> int | None:
        """
        Add a failed email record to the database.

        Args:
            email_id: The ID of the email template
            recipient: The recipient email address that failed
            error_reason: The reason for the failure

        Returns:
            The ID of the newly created record
        """
        self.cursor.execute(
            """
            INSERT INTO failed_emails (email_id, recipient, error_reason, failed_at)
            VALUES (?, ?, ?, ?)
            """,
            (email_id, recipient, error_reason, datetime.datetime.now()),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_failed_emails(self) -> list:
        """Get all failed email records."""
        self.cursor.execute("SELECT * FROM failed_emails ORDER BY failed_at DESC")
        return self.cursor.fetchall()

    def get_failed_emails_by_email_id(self, email_id: str) -> list:
        """Get all failed email records for a specific email template."""
        self.cursor.execute(
            "SELECT * FROM failed_emails WHERE email_id = ? ORDER BY failed_at DESC",
            (email_id,),
        )
        return self.cursor.fetchall()

    def get_unretried_failed_emails(self, email_id: str) -> list:
        """Get failed emails that haven't been retried yet."""
        self.cursor.execute(
            "SELECT * FROM failed_emails WHERE email_id = ? AND retried = 0 ORDER BY failed_at DESC",
            (email_id,),
        )
        return self.cursor.fetchall()

    def mark_failed_email_retried(self, failed_id: int) -> bool:
        """Mark a failed email record as retried."""
        self.cursor.execute(
            "UPDATE failed_emails SET retried = 1 WHERE id = ?",
            (failed_id,),
        )
        self.conn.commit()
        return self.cursor.rowcount > 0

    def delete_failed_email(self, failed_id: int) -> bool:
        """Delete a failed email record."""
        self.cursor.execute(
            "DELETE FROM failed_emails WHERE id = ?",
            (failed_id,),
        )
        self.conn.commit()
        return self.cursor.rowcount > 0

    def get_failed_email_count(self) -> int:
        """Get the total count of failed emails."""
        self.cursor.execute("SELECT COUNT(*) FROM failed_emails")
        result = self.cursor.fetchone()
        return result[0] if result else 0

    # Draft CRUD operations

    def add_draft(
        self,
        name: str,
        subject: str = "",
        body: str = "",
        sender: str = "",
        recipients: list[str] | None = None,
        attachments: list[str] | None = None,
        email_type: str = "html",
    ) -> int | None:
        """
        Add a new draft to the database.

        Args:
            name: Name/title for the draft
            subject: Email subject
            body: Email body content
            sender: Sender email address
            recipients: List of recipient email addresses
            attachments: List of attachment file paths
            email_type: Type of email ('html' or 'plain')

        Returns:
            The ID of the newly created draft
        """
        recipients_str = ",".join(recipients) if recipients else ""
        attachments_str = ",".join(attachments) if attachments else ""
        now = datetime.datetime.now()

        self.cursor.execute(
            """
            INSERT INTO drafts (name, subject, body, sender, recipients, attachments, email_type, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                subject,
                body,
                sender,
                recipients_str,
                attachments_str,
                email_type,
                now,
                now,
            ),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def update_draft(
        self,
        draft_id: int,
        name: str | None = None,
        subject: str | None = None,
        body: str | None = None,
        sender: str | None = None,
        recipients: list[str] | None = None,
        attachments: list[str] | None = None,
        email_type: str | None = None,
    ) -> bool:
        """
        Update an existing draft in the database.

        Args:
            draft_id: The ID of the draft to update
            name: New name/title for the draft (optional)
            subject: New email subject (optional)
            body: New email body content (optional)
            sender: New sender email address (optional)
            recipients: New list of recipient email addresses (optional)
            attachments: New list of attachment file paths (optional)
            email_type: New type of email ('html' or 'plain') (optional)

        Returns:
            True if the draft was updated, False otherwise
        """
        # Build update query dynamically based on provided fields
        updates = []
        values = []

        if name is not None:
            updates.append("name = ?")
            values.append(name)
        if subject is not None:
            updates.append("subject = ?")
            values.append(subject)
        if body is not None:
            updates.append("body = ?")
            values.append(body)
        if sender is not None:
            updates.append("sender = ?")
            values.append(sender)
        if recipients is not None:
            updates.append("recipients = ?")
            values.append(",".join(recipients))
        if attachments is not None:
            updates.append("attachments = ?")
            values.append(",".join(attachments))
        if email_type is not None:
            updates.append("email_type = ?")
            values.append(email_type)

        if not updates:
            return False

        # Always update the updated_at timestamp
        updates.append("updated_at = ?")
        values.append(datetime.datetime.now())

        # Add the draft_id for the WHERE clause
        values.append(draft_id)

        query = f"UPDATE drafts SET {', '.join(updates)} WHERE id = ?"
        self.cursor.execute(query, values)
        self.conn.commit()
        return self.cursor.rowcount > 0

    def get_draft(self, draft_id: int) -> dict | None:
        """
        Get a draft by its ID.

        Args:
            draft_id: The ID of the draft to retrieve

        Returns:
            A dictionary with draft data, or None if not found
        """
        self.cursor.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,))
        row = self.cursor.fetchone()
        if row:
            return self._row_to_draft_dict(row)
        return None

    def get_all_drafts(self) -> list[dict]:
        """
        Get all drafts from the database.

        Returns:
            A list of dictionaries with draft data
        """
        self.cursor.execute("SELECT * FROM drafts ORDER BY updated_at DESC")
        rows = self.cursor.fetchall()
        return [self._row_to_draft_dict(row) for row in rows]

    def delete_draft(self, draft_id: int) -> bool:
        """
        Delete a draft from the database.

        Args:
            draft_id: The ID of the draft to delete

        Returns:
            True if the draft was deleted, False otherwise
        """
        self.cursor.execute("DELETE FROM drafts WHERE id = ?", (draft_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0

    def _row_to_draft_dict(self, row: tuple) -> dict:
        """
        Convert a database row to a draft dictionary.

        Args:
            row: A tuple representing a row from the drafts table

        Returns:
            A dictionary with draft data
        """
        return {
            "id": row[0],
            "name": row[1],
            "subject": row[2],
            "body": row[3],
            "sender": row[4],
            "recipients": [r.strip() for r in row[5].split(",") if r.strip()],
            "attachments": [a.strip() for a in row[6].split(",") if a.strip()],
            "email_type": row[7],
            "created_at": row[8],
            "updated_at": row[9],
        }
