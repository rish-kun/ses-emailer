"""
Drafts Screen for SES Email TUI application.
Allows users to view, load, and manage saved email drafts.
"""

from datetime import datetime
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Static,
)

from sending.db import Database
from tui.components.modals import ConfirmDialog


class DraftsScreen(Screen):
    """Screen for managing email drafts."""

    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("r", "refresh", "Refresh"),
        ("d", "delete_selected", "Delete"),
        ("enter", "load_selected", "Load Draft"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db: Optional[Database] = None
        self.drafts: list[dict] = []
        self.selected_draft_id: Optional[int] = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="drafts-container"):
            yield Static(
                "[bold]>[/] Email Drafts",
                classes="screen-title",
            )
            yield Static(
                "[#5c6370]Select a draft to load it into the compose screen[/]",
                id="drafts-hint",
            )

            with Vertical(id="drafts-content"):
                yield DataTable(id="drafts-table")

                yield Static("", classes="spacer")

                with Horizontal(id="drafts-buttons"):
                    yield Button(
                        "[>] Load Draft",
                        id="btn-load-draft",
                        variant="primary",
                    )
                    yield Button(
                        "[x] Delete Draft",
                        id="btn-delete-draft",
                        variant="error",
                    )
                    yield Button(
                        "[~] Refresh",
                        id="btn-refresh-drafts",
                        variant="default",
                    )
                    yield Button(
                        "[<] Back",
                        id="btn-back",
                        variant="default",
                    )

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the drafts screen."""
        self.db = Database()
        self._setup_table()
        self._load_drafts()

    def _setup_table(self) -> None:
        """Set up the drafts data table."""
        table = self.query_one("#drafts-table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.add_column("ID", key="id", width=6)
        table.add_column("Name", key="name", width=25)
        table.add_column("Subject", key="subject", width=30)
        table.add_column("Recipients", key="recipients", width=12)
        table.add_column("Updated", key="updated", width=20)

    def _load_drafts(self) -> None:
        """Load drafts from the database."""
        if not self.db:
            return

        self.drafts = self.db.get_all_drafts()
        table = self.query_one("#drafts-table", DataTable)
        table.clear()

        if not self.drafts:
            self.notify("No drafts found", severity="information")
            return

        for draft in self.drafts:
            # Format the updated_at timestamp
            updated_at = draft.get("updated_at", "")
            if isinstance(updated_at, str) and updated_at:
                try:
                    dt = datetime.fromisoformat(updated_at)
                    updated_str = dt.strftime("%Y-%m-%d %H:%M")
                except ValueError:
                    updated_str = (
                        updated_at[:16] if len(updated_at) > 16 else updated_at
                    )
            elif isinstance(updated_at, datetime):
                updated_str = updated_at.strftime("%Y-%m-%d %H:%M")
            else:
                updated_str = str(updated_at)[:16] if updated_at else "N/A"

            # Count recipients
            recipients = draft.get("recipients", [])
            recipients_count = len(recipients) if isinstance(recipients, list) else 0

            # Truncate subject if too long
            subject = draft.get("subject", "")
            if len(subject) > 28:
                subject = subject[:25] + "..."

            # Truncate name if too long
            name = draft.get("name", "")
            if len(name) > 23:
                name = name[:20] + "..."

            table.add_row(
                str(draft["id"]),
                name,
                subject,
                str(recipients_count),
                updated_str,
                key=str(draft["id"]),
            )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in the drafts table."""
        if event.row_key and event.row_key.value is not None:
            self.selected_draft_id = int(str(event.row_key.value))

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Handle row highlight changes."""
        if event.row_key and event.row_key.value is not None:
            self.selected_draft_id = int(str(event.row_key.value))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "btn-load-draft":
            self.action_load_selected()
        elif button_id == "btn-delete-draft":
            self.action_delete_selected()
        elif button_id == "btn-refresh-drafts":
            self.action_refresh()
        elif button_id == "btn-back":
            self.action_go_back()

    def action_go_back(self) -> None:
        """Go back to the home screen."""
        self.app.pop_screen()

    def action_refresh(self) -> None:
        """Refresh the drafts list."""
        self._load_drafts()
        self.notify("Drafts refreshed", severity="information")

    def action_load_selected(self) -> None:
        """Load the selected draft into the compose screen."""
        if not self.selected_draft_id:
            self.notify("Please select a draft first", severity="warning")
            return

        if not self.db:
            return

        draft = self.db.get_draft(self.selected_draft_id)
        if not draft:
            self.notify("Draft not found", severity="error")
            return

        # Store draft in app state for compose screen to use
        self.app.email_data = {
            "draft_id": draft["id"],
            "draft_name": draft["name"],
            "subject": draft["subject"],
            "body": draft["body"],
            "sender": draft["sender"],
            "recipients": draft["recipients"],
            "attachments": draft["attachments"],
            "email_type": draft["email_type"],
            "from_draft": True,
        }

        # Navigate to compose screen
        self.app.pop_screen()
        self.app.push_screen("compose")
        self.notify(f"Loaded draft: {draft['name']}", severity="information")

    def action_delete_selected(self) -> None:
        """Delete the selected draft."""
        if not self.selected_draft_id:
            self.notify("Please select a draft first", severity="warning")
            return

        # Find the draft name for confirmation message
        draft_name = "this draft"
        for draft in self.drafts:
            if draft["id"] == self.selected_draft_id:
                draft_name = draft.get("name", "this draft")
                break

        def handle_confirm(confirmed: Optional[bool]) -> None:
            if confirmed is True and self.db and self.selected_draft_id:
                if self.db.delete_draft(self.selected_draft_id):
                    self.notify("Draft deleted successfully", severity="information")
                    self.selected_draft_id = None
                    self._load_drafts()
                else:
                    self.notify("Failed to delete draft", severity="error")

        self.app.push_screen(
            ConfirmDialog(
                title="[bold]Delete Draft?[/]",
                message=f"Are you sure you want to delete\n'{draft_name}'?",
                confirm_label="[ok] Yes, Delete",
                cancel_label="[x] Cancel",
                confirm_variant="error",
            ),
            handle_confirm,
        )
