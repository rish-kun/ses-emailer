"""
Modal dialog components for the SES Email TUI application.
Provides reusable confirmation, error, and info dialogs.
"""

from typing import Literal, Optional

from textual.app import ComposeResult
from textual.containers import Center, Horizontal, ScrollableContainer, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Input, Label, Static

# Type alias for button variants
ButtonVariant = Literal["default", "primary", "success", "warning", "error"]


class ConfirmDialog(ModalScreen[bool]):
    """A modal confirmation dialog."""

    CSS = """
    ConfirmDialog {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }

    #confirm-dialog-container {
        width: 50;
        height: auto;
        max-height: 20;
        background: #21252b;
        border: tall #3e4451;
        padding: 1 2;
    }

    #confirm-dialog-title {
        text-align: center;
        text-style: bold;
        color: #c678dd;
        padding: 1;
        width: 100%;
    }

    #confirm-dialog-message {
        text-align: center;
        color: #abb2bf;
        padding: 1;
        width: 100%;
    }

    #confirm-dialog-buttons {
        align: center middle;
        height: 5;
        padding-top: 1;
    }

    #confirm-dialog-buttons Button {
        min-width: 12;
        margin: 0 1;
    }
    """

    def __init__(
        self,
        title: str = "Confirm",
        message: str = "Are you sure?",
        confirm_label: str = "[ok] Yes",
        cancel_label: str = "[x] No",
        confirm_variant: ButtonVariant = "primary",
    ) -> None:
        super().__init__()
        self.dialog_title = title
        self.dialog_message = message
        self.confirm_label = confirm_label
        self.cancel_label = cancel_label
        self.confirm_variant = confirm_variant

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-dialog-container"):
            yield Static(self.dialog_title, id="confirm-dialog-title")
            yield Static(self.dialog_message, id="confirm-dialog-message")
            with Horizontal(id="confirm-dialog-buttons"):
                yield Button(
                    self.confirm_label,
                    id="btn-confirm",
                    variant=self.confirm_variant,  # type: ignore[arg-type]
                )
                yield Button(
                    self.cancel_label,
                    id="btn-cancel",
                    variant="default",
                )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-confirm":
            self.dismiss(True)
        else:
            self.dismiss(False)

    def on_key(self, event) -> None:
        """Handle key presses."""
        if event.key == "escape":
            self.dismiss(False)
        elif event.key == "enter":
            self.dismiss(True)


class InfoDialog(ModalScreen[None]):
    """A modal information dialog."""

    CSS = """
    InfoDialog {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }

    #info-dialog-container {
        width: 60;
        height: auto;
        max-height: 25;
        background: #21252b;
        border: tall #61afef;
        padding: 1 2;
    }

    #info-dialog-title {
        text-align: center;
        text-style: bold;
        color: #61afef;
        padding: 1;
        width: 100%;
    }

    #info-dialog-message {
        text-align: center;
        color: #abb2bf;
        padding: 1;
        width: 100%;
    }

    #info-dialog-buttons {
        align: center middle;
        height: 5;
        padding-top: 1;
    }
    """

    def __init__(
        self,
        title: str = "Information",
        message: str = "",
    ) -> None:
        super().__init__()
        self.dialog_title = title
        self.dialog_message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="info-dialog-container"):
            yield Static(self.dialog_title, id="info-dialog-title")
            yield Static(self.dialog_message, id="info-dialog-message")
            with Center(id="info-dialog-buttons"):
                yield Button("[ok] OK", id="btn-ok", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        self.dismiss(None)

    def on_key(self, event) -> None:
        """Handle key presses."""
        if event.key in ("escape", "enter"):
            self.dismiss(None)


class ErrorDialog(ModalScreen[None]):
    """A modal error dialog."""

    CSS = """
    ErrorDialog {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }

    #error-dialog-container {
        width: 60;
        height: auto;
        max-height: 25;
        background: #21252b;
        border: tall #e06c75;
        padding: 1 2;
    }

    #error-dialog-title {
        text-align: center;
        text-style: bold;
        color: #e06c75;
        padding: 1;
        width: 100%;
    }

    #error-dialog-message {
        text-align: center;
        color: #abb2bf;
        padding: 1;
        width: 100%;
    }

    #error-dialog-buttons {
        align: center middle;
        height: 5;
        padding-top: 1;
    }
    """

    def __init__(
        self,
        title: str = "[!] Error",
        message: str = "An error occurred.",
    ) -> None:
        super().__init__()
        self.dialog_title = title
        self.dialog_message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="error-dialog-container"):
            yield Static(self.dialog_title, id="error-dialog-title")
            yield Static(self.dialog_message, id="error-dialog-message")
            with Center(id="error-dialog-buttons"):
                yield Button("[ok] OK", id="btn-ok", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        self.dismiss(None)

    def on_key(self, event) -> None:
        """Handle key presses."""
        if event.key in ("escape", "enter"):
            self.dismiss(None)


class SaveDraftDialog(ModalScreen[Optional[str]]):
    """A modal dialog for saving a draft with a name."""

    CSS = """
    SaveDraftDialog {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }

    #save-draft-container {
        width: 60;
        height: auto;
        max-height: 20;
        background: #21252b;
        border: tall #98c379;
        padding: 1 2;
    }

    #save-draft-title {
        text-align: center;
        text-style: bold;
        color: #98c379;
        padding: 1;
        width: 100%;
    }

    #save-draft-label {
        color: #abb2bf;
        padding: 0 1;
    }

    #draft-name-input {
        margin: 1;
    }

    #save-draft-buttons {
        align: center middle;
        height: 5;
        padding-top: 1;
    }

    #save-draft-buttons Button {
        min-width: 12;
        margin: 0 1;
    }
    """

    def __init__(
        self,
        title: str = "[+] Save Draft",
        default_name: str = "",
        is_update: bool = False,
    ) -> None:
        super().__init__()
        self.dialog_title = title
        self.default_name = default_name
        self.is_update = is_update

    def compose(self) -> ComposeResult:
        with Vertical(id="save-draft-container"):
            yield Static(self.dialog_title, id="save-draft-title")
            yield Label("Draft Name:", id="save-draft-label")
            yield Input(
                placeholder="Enter a name for this draft",
                id="draft-name-input",
                value=self.default_name,
            )
            with Horizontal(id="save-draft-buttons"):
                save_label = "[ok] Update" if self.is_update else "[ok] Save"
                yield Button(
                    save_label,
                    id="btn-save-draft",
                    variant="success",
                )
                yield Button(
                    "[x] Cancel",
                    id="btn-cancel-draft",
                    variant="default",
                )

    def on_mount(self) -> None:
        """Focus the input when dialog opens."""
        self.query_one("#draft-name-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-save-draft":
            name = self.query_one("#draft-name-input", Input).value.strip()
            if name:
                self.dismiss(name)
            else:
                self.notify("Please enter a name for the draft", severity="warning")
        else:
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in input field."""
        name = event.value.strip()
        if name:
            self.dismiss(name)
        else:
            self.notify("Please enter a name for the draft", severity="warning")

    def on_key(self, event) -> None:
        """Handle key presses."""
        if event.key == "escape":
            self.dismiss(None)


class CompareRecipientsDialog(ModalScreen[Optional[list[str]]]):
    """A modal dialog for comparing recipients with previous sends."""

    CSS = """
    CompareRecipientsDialog {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }

    #compare-dialog-container {
        width: 80;
        height: 35;
        background: #21252b;
        border: tall #56b6c2;
        padding: 1 2;
    }

    #compare-dialog-title {
        text-align: center;
        text-style: bold;
        color: #56b6c2;
        padding: 1;
        width: 100%;
        height: 3;
    }

    #compare-dialog-hint {
        text-align: center;
        color: #5c6370;
        padding: 0 1;
        height: 2;
    }

    #compare-emails-table {
        height: 10;
        margin: 1 0;
    }

    #compare-stats-container {
        height: auto;
        padding: 1;
        background: #282c34;
        border: tall #3e4451;
        margin: 1 0;
    }

    #compare-stats {
        height: auto;
    }

    #compare-dialog-buttons {
        align: center middle;
        height: 5;
        padding-top: 1;
    }

    #compare-dialog-buttons Button {
        min-width: 18;
        margin: 0 1;
    }
    """

    def __init__(
        self,
        current_recipients: list[str],
        emails_summary: list[dict],
    ) -> None:
        super().__init__()
        self.current_recipients = current_recipients
        self.emails_summary = emails_summary
        self.selected_email_id: Optional[str] = None
        self.selected_email_ids: Optional[list[str]] = None  # For grouped emails
        self.comparison_result: Optional[dict] = None

    def compose(self) -> ComposeResult:
        with Vertical(id="compare-dialog-container"):
            yield Static(
                "[bold]Compare Recipients with Previous Sends[/]",
                id="compare-dialog-title",
            )
            yield Static(
                "Select a previous email to compare against, or compare against all sent emails",
                id="compare-dialog-hint",
            )

            yield DataTable(id="compare-emails-table", cursor_type="row")

            with Vertical(id="compare-stats-container"):
                yield Static(
                    "[#5c6370]Select an email above or click 'Compare All' to see comparison[/]",
                    id="compare-stats",
                )

            with Horizontal(id="compare-dialog-buttons"):
                yield Button(
                    "[=] Compare All",
                    id="btn-compare-all",
                    variant="default",
                )
                yield Button(
                    "[>] Keep Only New",
                    id="btn-keep-new",
                    variant="success",
                    disabled=True,
                )
                yield Button(
                    "[x] Cancel",
                    id="btn-cancel-compare",
                    variant="default",
                )

    def on_mount(self) -> None:
        """Set up the emails table."""
        table = self.query_one("#compare-emails-table", DataTable)
        table.add_column("Subject", key="subject", width=35)
        table.add_column("Sender", key="sender", width=20)
        table.add_column("Sent", key="sent", width=8)
        table.add_column("Last Sent", key="last_sent", width=18)
        table.zebra_stripes = True

        for email in self.emails_summary:
            if email["sent_count"] > 0:  # Only show emails that have been sent
                subject = email["subject"]
                if len(subject) > 33:
                    subject = subject[:30] + "..."
                sender = email["sender"]
                if len(sender) > 18:
                    sender = sender[:15] + "..."
                last_sent = str(email["last_sent"])[:16] if email["last_sent"] else "-"

                table.add_row(
                    subject,
                    sender,
                    str(email["sent_count"]),
                    last_sent,
                    key=email["id"],
                )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle email selection."""
        row_key = event.row_key
        email_id = row_key.value if hasattr(row_key, "value") else str(row_key)
        self.selected_email_id = email_id
        # Find the email_ids list for this group
        for e in self.emails_summary:
            if e["id"] == email_id:
                self.selected_email_ids = e.get("email_ids", [email_id])
                break
        self._run_comparison(email_id)

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Handle email highlight (cursor movement)."""
        if event.row_key:
            row_key = event.row_key
            email_id = row_key.value if hasattr(row_key, "value") else str(row_key)
            self.selected_email_id = email_id
            # Find the email_ids list for this group
            for e in self.emails_summary:
                if e["id"] == email_id:
                    self.selected_email_ids = e.get("email_ids", [email_id])
                    break
            self._run_comparison(email_id)

    def _run_comparison(self, email_id: Optional[str] = None) -> None:
        """Run comparison against a specific email or all emails."""
        try:
            from sending.db import Database

            db = Database()
            # Use email_ids if available (for grouped emails), otherwise fall back to single email_id
            if email_id and self.selected_email_ids:
                self.comparison_result = db.compare_recipients(
                    self.current_recipients,
                    email_id=None,
                    email_ids=self.selected_email_ids,
                )
            else:
                self.comparison_result = db.compare_recipients(
                    self.current_recipients, email_id
                )
            db.close()

            total = self.comparison_result["total"]
            already_sent = self.comparison_result["already_sent"]
            new_count = self.comparison_result["new_recipients"]

            # Calculate percentages
            if total > 0:
                already_pct = (already_sent / total) * 100
                new_pct = (new_count / total) * 100
            else:
                already_pct = 0
                new_pct = 0

            if email_id:
                # Find the email subject for display
                subject = "Selected Email"
                for e in self.emails_summary:
                    if e["id"] == email_id:
                        subject = e["subject"][:30]
                        break
                compare_against = f"[#61afef]{subject}[/]"
            else:
                compare_against = "[#61afef]All Previous Sends[/]"

            stats_lines = [
                f"[bold #56b6c2]Comparing against:[/] {compare_against}",
                "",
                f"[#61afef]Total in current list:[/] {total}",
                f"[#e5c07b]Already received:[/] {already_sent} ({already_pct:.1f}%)",
                f"[#98c379]New recipients:[/] {new_count} ({new_pct:.1f}%)",
            ]

            if new_count > 0:
                stats_lines.append("")
                stats_lines.append(
                    f"[#98c379]Click 'Keep Only New' to filter to {new_count} new recipients[/]"
                )
                self.query_one("#btn-keep-new", Button).disabled = False
            else:
                stats_lines.append("")
                stats_lines.append(
                    "[#e06c75]All recipients have already received this email![/]"
                )
                self.query_one("#btn-keep-new", Button).disabled = True

            self.query_one("#compare-stats", Static).update("\n".join(stats_lines))

        except Exception as e:
            self.query_one("#compare-stats", Static).update(
                f"[#e06c75]Error running comparison: {e}[/]"
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-compare-all":
            self._run_comparison(None)  # Compare against all
        elif event.button.id == "btn-keep-new":
            if self.comparison_result and self.comparison_result["new_recipients_list"]:
                self.dismiss(self.comparison_result["new_recipients_list"])
            else:
                self.notify("No new recipients to keep", severity="warning")
        elif event.button.id == "btn-cancel-compare":
            self.dismiss(None)

    def on_key(self, event) -> None:
        """Handle key presses."""
        if event.key == "escape":
            self.dismiss(None)
