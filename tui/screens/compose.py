"""
Compose Screen for SES Email TUI application.
Allows users to draft emails with recipients, subject, body, and attachments.
"""

import tempfile
import webbrowser
from pathlib import Path
from typing import Optional, Union

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    DirectoryTree,
    Footer,
    Header,
    Input,
    Label,
    OptionList,
    RadioButton,
    RadioSet,
    Select,
    Static,
    TabbedContent,
    TabPane,
    TextArea,
)
from textual.widgets.option_list import Option

from sending.db import Database
from tui.components.modals import (
    CompareRecipientsDialog,
    ConfirmDialog,
    SaveDraftDialog,
)


class ComposeScreen(Screen):
    """Email composition screen."""

    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("ctrl+s", "save_draft", "Save Draft"),
        ("ctrl+enter", "proceed_to_send", "Send"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.recipients: list[str] = []
        self.attachments: list[str] = []
        self.email_type: str = "html"
        # Draft-related state
        self.current_draft_id: Optional[int] = None
        self.current_draft_name: Optional[str] = None
        self.db: Optional[Database] = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="compose-container"):
            yield Static(
                "[bold]>[/] Compose Email",
                classes="screen-title",
            )
            with TabbedContent(id="compose-tabs"):
                # Tab 1: Recipients
                with TabPane("[#] Recipients", id="tab-recipients"):
                    with Vertical(id="recipients-form"):
                        yield Static(
                            "Quick Add Test Recipients",
                            classes="section-header",
                        )
                        yield Static(
                            "[#5c6370]Select from pre-configured test recipients (configure in Settings)[/]",
                            id="test-recipients-hint",
                        )
                        with Horizontal(id="test-recipient-row"):
                            yield Select(
                                [],
                                prompt="Select a test recipient",
                                id="test-recipient-select",
                                allow_blank=True,
                            )
                            yield Button(
                                "[+] Add Selected",
                                id="btn-add-test-recipient",
                                variant="primary",
                            )
                            yield Button(
                                "[++] Add All",
                                id="btn-add-all-test-recipients",
                                variant="default",
                            )

                        yield Static("", classes="spacer")
                        yield Static(
                            "Load Recipients from Excel",
                            classes="section-header",
                        )
                        with Horizontal(id="excel-row"):
                            yield Input(
                                placeholder="Path to Excel file (e.g., data/recipients.xlsx)",
                                id="excel-path",
                            )
                            yield Button("[...] Browse", id="btn-browse-excel")
                        with Horizontal(id="column-row"):
                            yield Label("Column Index (0-based):")
                            yield Input(
                                placeholder="0",
                                id="column-index",
                                value="0",
                            )
                            yield Button(
                                "[v] Load", id="btn-load-excel", variant="primary"
                            )

                        yield Static("", classes="spacer")
                        yield Static(
                            "Excel File Browser",
                            classes="section-header",
                        )
                        yield DirectoryTree(".", id="excel-file-tree")

                        yield Static("", classes="spacer")
                        yield Static(
                            "Or Enter Recipients Manually",
                            classes="section-header",
                        )
                        yield TextArea(
                            id="manual-recipients",
                        )
                        yield Static(
                            "[#5c6370]Enter one email per line[/]",
                            id="manual-hint",
                        )
                        yield Button(
                            "[+] Add Manual Recipients",
                            id="btn-add-manual",
                            variant="default",
                        )

                        yield Static("", classes="spacer")
                        yield Static(
                            "Current Recipients",
                            classes="section-header",
                        )
                        yield Static(
                            "[#5c6370]No recipients loaded yet[/]",
                            id="recipients-count",
                        )
                        with Horizontal(id="recipients-actions"):
                            yield Button(
                                "[?] Compare with Previous",
                                id="btn-compare-recipients",
                                variant="primary",
                            )
                            yield Button(
                                "[x] Clear All",
                                id="btn-clear-recipients",
                                variant="warning",
                            )

                # Tab 2: Email Content
                with TabPane("[=] Content", id="tab-content"):
                    with Vertical(id="content-form"):
                        yield Label("Subject:")
                        yield Input(
                            placeholder="Enter email subject",
                            id="email-subject",
                        )

                        yield Static("", classes="spacer")
                        yield Label("Email Type:")
                        with RadioSet(id="email-type"):
                            yield RadioButton("HTML", id="type-html", value=True)
                            yield RadioButton("Plain Text", id="type-plain")

                        yield Static("", classes="spacer")
                        yield Label("Email Body:")
                        yield TextArea(
                            id="email-body",
                        )
                        yield Static(
                            "[#5c6370][i] For HTML emails, you can use HTML tags like <b>, <i>, <a>, etc.[/]",
                            id="body-hint",
                        )

                # Tab 3: Attachments
                with TabPane("[+] Attachments", id="tab-attachments"):
                    with Vertical(id="attachments-form"):
                        yield Static(
                            "Add Attachments",
                            classes="section-header",
                        )
                        with Horizontal(id="attachment-input-row"):
                            yield Input(
                                placeholder="Path to file",
                                id="attachment-path",
                            )
                            yield Button("[...] Browse", id="btn-browse-attachment")
                            yield Button(
                                "[+] Add", id="btn-add-attachment", variant="primary"
                            )

                        yield Static("", classes="spacer")
                        yield Static(
                            "File Browser",
                            classes="section-header",
                        )
                        yield DirectoryTree(".", id="file-tree")

                        yield Static("", classes="spacer")
                        yield Static(
                            "Current Attachments",
                            classes="section-header",
                        )
                        yield OptionList(id="attachments-list")
                        yield Static(
                            "[#5c6370]No attachments added[/]",
                            id="attachments-count",
                        )
                        with Horizontal(id="attachment-buttons"):
                            yield Button(
                                "[-] Remove Selected",
                                id="btn-remove-attachment",
                                variant="warning",
                            )
                            yield Button(
                                "[x] Clear All",
                                id="btn-clear-attachments",
                                variant="error",
                            )

                # Tab 4: Preview
                with TabPane("[o] Preview", id="tab-preview"):
                    with Vertical(id="preview-form"):
                        yield Static(
                            "Email Preview",
                            classes="section-header",
                        )
                        yield Static(
                            "",
                            id="preview-content",
                        )
                        yield Button(
                            "[~] Refresh Preview",
                            id="btn-refresh-preview",
                            variant="default",
                        )
                        yield Button(
                            "[🌐] Preview in Browser",
                            id="btn-preview-browser",
                            variant="primary",
                        )

            with Horizontal(id="compose-buttons"):
                yield Button("[>] Proceed to Send", id="btn-send", variant="primary")
                yield Button("[+] Save Draft", id="btn-save-draft", variant="default")
                yield Button("[<] Back", id="btn-back", variant="default")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the compose screen."""
        self.db = Database()
        self._load_defaults()
        self._load_test_recipients()
        # Set placeholder for manual recipients TextArea
        manual_ta = self.query_one("#manual-recipients", TextArea)
        manual_ta.text = ""
        # Set placeholder for email body TextArea
        body_ta = self.query_one("#email-body", TextArea)
        body_ta.text = ""

        # Check if we're loading from a draft
        self._load_from_draft_if_available()

    def _load_test_recipients(self) -> None:
        """Load test recipients from configuration into the select dropdown."""
        from config import get_config

        config = get_config().config
        test_recipients = config.test_recipients

        select_widget = self.query_one("#test-recipient-select", Select)
        if test_recipients:
            options = [(email, email) for email in test_recipients]
            select_widget.set_options(options)
        else:
            select_widget.set_options([])

    def _add_selected_test_recipient(self) -> None:
        """Add the selected test recipient to the recipients list."""
        select_widget = self.query_one("#test-recipient-select", Select)
        selected = select_widget.value

        if selected is None or selected == Select.BLANK:
            self.notify("Please select a test recipient first", severity="warning")
            return

        email = str(selected)
        if email not in self.recipients:
            self.recipients.append(email)
            self._update_recipients_display()
            self.notify(f"[ok] Added test recipient: {email}", severity="information")
        else:
            self.notify("This recipient is already in the list", severity="warning")

    def _add_all_test_recipients(self) -> None:
        """Add all configured test recipients to the recipients list."""
        from config import get_config

        config = get_config().config
        test_recipients = config.test_recipients

        if not test_recipients:
            self.notify(
                "No test recipients configured. Add them in Settings.",
                severity="warning",
            )
            return

        added_count = 0
        for email in test_recipients:
            if email not in self.recipients:
                self.recipients.append(email)
                added_count += 1

        if added_count > 0:
            self._update_recipients_display()
            self.notify(
                f"[ok] Added {added_count} test recipient(s)", severity="information"
            )
        else:
            self.notify(
                "All test recipients are already in the list", severity="warning"
            )

    def on_directory_tree_file_selected_excel(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        """Handle file selection from the Excel file browser."""
        file_path = str(event.path)
        # Check if it's an Excel file
        if file_path.endswith((".xlsx", ".xls", ".csv")):
            self.query_one("#excel-path", Input).value = file_path
            self.notify(f"Selected: {event.path.name}", severity="information")
        else:
            self.notify(
                "Please select an Excel file (.xlsx, .xls, .csv)", severity="warning"
            )

    def _load_defaults(self) -> None:
        """Load default values from configuration."""
        from config import get_config

        config = get_config().config

        # Set last used excel path
        if config.last_excel_path:
            self.query_one("#excel-path", Input).value = config.last_excel_path
        if config.last_excel_column:
            self.query_one("#column-index", Input).value = str(config.last_excel_column)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "btn-load-excel":
            self._load_from_excel()
        elif button_id == "btn-add-manual":
            self._add_manual_recipients()
        elif button_id == "btn-clear-recipients":
            self._clear_recipients()
        elif button_id == "btn-compare-recipients":
            self._compare_with_previous()
        elif button_id == "btn-add-test-recipient":
            self._add_selected_test_recipient()
        elif button_id == "btn-add-all-test-recipients":
            self._add_all_test_recipients()
        elif button_id == "btn-add-attachment":
            self._add_attachment()
        elif button_id == "btn-remove-attachment":
            self._remove_selected_attachment()
        elif button_id == "btn-clear-attachments":
            self._clear_attachments()
        elif button_id == "btn-refresh-preview":
            self._refresh_preview()
        elif button_id == "btn-send":
            self.action_proceed_to_send()
        elif button_id == "btn-save-draft":
            self.action_save_draft()
        elif button_id == "btn-back":
            self.action_go_back()
        elif button_id == "btn-browse-excel":
            self._browse_for_file("excel")
        elif button_id == "btn-browse-attachment":
            self._browse_for_file("attachment")
        elif button_id == "btn-preview-browser":
            self._preview_in_browser()

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Handle radio button changes for email type."""
        if event.radio_set.id == "email-type":
            self.email_type = "html" if event.pressed.id == "type-html" else "plain"

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        """Handle file selection from directory tree."""
        # Check which tree triggered the event
        if event.control.id == "excel-file-tree":
            file_path = str(event.path)
            # Check if it's an Excel file
            if file_path.endswith((".xlsx", ".xls", ".csv")):
                self.query_one("#excel-path", Input).value = file_path
                self.notify(f"Selected: {event.path.name}", severity="information")
            else:
                self.notify(
                    "Please select an Excel file (.xlsx, .xls, .csv)",
                    severity="warning",
                )
        else:
            # Attachment file tree
            self.query_one("#attachment-path", Input).value = str(event.path)

    def _load_from_excel(self) -> None:
        """Load recipients from Excel file."""
        import sys
        from pathlib import Path

        excel_path = self.query_one("#excel-path", Input).value
        column_str = self.query_one("#column-index", Input).value

        if not excel_path:
            self.notify("Please enter an Excel file path", severity="error")
            return

        if not Path(excel_path).exists():
            self.notify(f"File not found: {excel_path}", severity="error")
            return

        try:
            column_index = int(column_str) if column_str else 0
        except ValueError:
            self.notify("Invalid column index", severity="error")
            return

        try:
            # Add sending directory to path for import
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "sending"))
            from email_list import scrape_excel_column

            emails = scrape_excel_column(excel_path, column_index)
            if emails:
                # Add new emails, avoiding duplicates
                new_count = 0
                for email in emails:
                    if email not in self.recipients:
                        self.recipients.append(email)
                        new_count += 1

                self._update_recipients_display()
                self.notify(
                    f"[ok] Loaded {new_count} new recipients ({len(emails)} total in file)",
                    severity="information",
                )

                # Save path to config
                from config import get_config

                config = get_config()
                config.config.last_excel_path = excel_path
                config.config.last_excel_column = column_index
                config.save()
            else:
                self.notify(
                    "No valid emails found in the specified column", severity="warning"
                )
        except Exception as e:
            self.notify(f"Error loading Excel: {e}", severity="error")

    def _add_manual_recipients(self) -> None:
        """Add manually entered recipients."""
        manual_ta = self.query_one("#manual-recipients", TextArea)
        text = manual_ta.text

        if not text.strip():
            self.notify("Please enter at least one email address", severity="warning")
            return

        lines = text.strip().split("\n")
        added_count = 0

        for line in lines:
            email = line.strip()
            if email and "@" in email and email not in self.recipients:
                self.recipients.append(email)
                added_count += 1

        if added_count > 0:
            self._update_recipients_display()
            manual_ta.text = ""
            self.notify(f"[ok] Added {added_count} recipients", severity="information")
        else:
            self.notify("No new valid emails to add", severity="warning")

    def _clear_recipients(self) -> None:
        """Clear all recipients."""
        self.recipients = []
        self._update_recipients_display()
        self.notify("All recipients cleared", severity="information")

    def _compare_with_previous(self) -> None:
        """Compare current recipients with previously sent emails."""
        if not self.recipients:
            self.notify(
                "No recipients to compare. Add recipients first.", severity="warning"
            )
            return

        try:
            # Get emails summary from database
            db = Database()
            emails_summary = db.get_grouped_emails_summary()
            db.close()

            if not emails_summary or all(e["sent_count"] == 0 for e in emails_summary):
                self.notify(
                    "No previous sent emails to compare against.", severity="warning"
                )
                return

            def handle_compare_result(new_recipients: list[str] | None) -> None:
                """Handle the result from the compare dialog."""
                if new_recipients is not None:
                    old_count = len(self.recipients)
                    self.recipients = new_recipients
                    self._update_recipients_display()
                    removed = old_count - len(new_recipients)
                    self.notify(
                        f"Filtered to {len(new_recipients)} new recipients ({removed} already sent)",
                        severity="information",
                    )

            self.app.push_screen(
                CompareRecipientsDialog(
                    current_recipients=self.recipients,
                    emails_summary=emails_summary,
                ),
                handle_compare_result,
            )

        except Exception as e:
            self.notify(f"Error comparing recipients: {e}", severity="error")

    def _update_recipients_display(self) -> None:
        """Update the recipients count display."""
        count_label = self.query_one("#recipients-count", Static)
        if self.recipients:
            count_label.update(
                f"[#98c379][ok] {len(self.recipients)} recipient(s) loaded[/]\n"
                f"[#5c6370]First few: {', '.join(self.recipients[:3])}{'...' if len(self.recipients) > 3 else ''}[/]"
            )
        else:
            count_label.update("[#5c6370]No recipients loaded yet[/]")

    def _add_attachment(self) -> None:
        """Add an attachment."""
        attachment_path = self.query_one("#attachment-path", Input).value

        if not attachment_path:
            self.notify("Please enter a file path", severity="warning")
            return

        path = Path(attachment_path)
        if not path.exists():
            self.notify(f"File not found: {attachment_path}", severity="error")
            return

        if attachment_path not in self.attachments:
            self.attachments.append(attachment_path)
            self._update_attachments_display()
            self.query_one("#attachment-path", Input).value = ""
            self.notify(f"[ok] Added: {path.name}", severity="information")
        else:
            self.notify("File already added", severity="warning")

    def _remove_selected_attachment(self) -> None:
        """Remove the selected attachment."""
        option_list = self.query_one("#attachments-list", OptionList)
        if option_list.highlighted is not None and self.attachments:
            idx = option_list.highlighted
            if 0 <= idx < len(self.attachments):
                removed = self.attachments.pop(idx)
                self._update_attachments_display()
                self.notify(f"Removed: {Path(removed).name}", severity="information")

    def _clear_attachments(self) -> None:
        """Clear all attachments."""
        self.attachments.clear()
        self._update_attachments_display()
        self.notify("All attachments cleared", severity="information")

    def _update_attachments_display(self) -> None:
        """Update the attachments list display."""
        option_list = self.query_one("#attachments-list", OptionList)
        option_list.clear_options()

        for attachment in self.attachments:
            path = Path(attachment)
            option_list.add_option(Option(f"[+] {path.name}"))

        count_label = self.query_one("#attachments-count", Static)
        if self.attachments:
            count_label.update(
                f"[#98c379][ok] {len(self.attachments)} attachment(s)[/]"
            )
        else:
            count_label.update("[#5c6370]No attachments added[/]")

    def _browse_for_file(self, file_type: str) -> None:
        """Show file browser hint."""
        self.notify(
            "Use the File Browser in the Attachments tab to select files",
            severity="information",
        )

    def _refresh_preview(self) -> None:
        """Refresh the email preview."""
        subject = self.query_one("#email-subject", Input).value
        body = self.query_one("#email-body", TextArea).text

        preview_lines = [
            f"[bold #61afef]Subject:[/bold #61afef] {subject or '(No subject)'}",
            "",
            f"[bold #61afef]Type:[/bold #61afef] {self.email_type.upper()}",
            "",
            f"[bold #61afef]Recipients:[/bold #61afef] {len(self.recipients)} recipient(s)",
            "",
            f"[bold #61afef]Attachments:[/bold #61afef] {len(self.attachments)} file(s)",
        ]

        if self.attachments:
            for att in self.attachments[:5]:
                preview_lines.append(f"  [+] {Path(att).name}")
            if len(self.attachments) > 5:
                preview_lines.append(f"  ... and {len(self.attachments) - 5} more")

        preview_lines.extend(
            [
                "",
                "[bold #61afef]Body Preview:[/bold #61afef]",
                "-" * 50,
                body[:500] + ("..." if len(body) > 500 else "")
                if body
                else "(No body)",
                "-" * 50,
            ]
        )

        preview_content = self.query_one("#preview-content", Static)
        preview_content.update("\n".join(preview_lines))

    def _preview_in_browser(self) -> None:
        """Open the email HTML content in the default web browser for preview."""
        subject = self.query_one("#email-subject", Input).value
        body = self.query_one("#email-body", TextArea).text

        if not body:
            self.notify("[!] Please enter email body content first", severity="warning")
            return

        if self.email_type != "html":
            self.notify(
                "[i] Plain text emails won't render as HTML. Switch to HTML type for rich preview.",
                severity="information",
            )

        # Create a complete HTML document for preview
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject or "Email Preview"}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .email-container {{
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        .email-header {{
            border-bottom: 1px solid #eee;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }}
        .email-subject {{
            font-size: 1.5em;
            font-weight: bold;
            color: #333;
            margin: 0;
        }}
        .email-meta {{
            color: #666;
            font-size: 0.9em;
            margin-top: 10px;
        }}
        .email-body {{
            line-height: 1.6;
            color: #444;
        }}
        .preview-banner {{
            background-color: #61afef;
            color: white;
            padding: 10px 20px;
            text-align: center;
            font-weight: bold;
            margin-bottom: 20px;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="preview-banner">📧 Email Preview - {len(self.recipients)} recipient(s)</div>
    <div class="email-container">
        <div class="email-header">
            <h1 class="email-subject">{subject or "(No Subject)"}</h1>
            <div class="email-meta">
                <strong>Type:</strong> {self.email_type.upper()} |
                <strong>Attachments:</strong> {len(self.attachments)} file(s)
            </div>
        </div>
        <div class="email-body">
            {body if self.email_type == "html" else f"<pre>{body}</pre>"}
        </div>
    </div>
</body>
</html>"""

        # Write to a temporary file
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".html", delete=False, encoding="utf-8"
            ) as f:
                f.write(html_content)
                temp_path = f.name

            # Open in browser using app.open_url if available, otherwise fallback to webbrowser
            file_url = f"file://{temp_path}"
            if hasattr(self.app, "open_url"):
                self.app.open_url(file_url)
            else:
                webbrowser.open(file_url)

            self.notify(
                "[✓] Opened email preview in browser",
                severity="information",
            )
        except Exception as e:
            self.notify(
                f"[!] Failed to open preview: {str(e)}",
                severity="error",
            )

    def action_proceed_to_send(self) -> None:
        """Validate and proceed to send screen."""
        # Validate required fields
        subject = self.query_one("#email-subject", Input).value
        body = self.query_one("#email-body", TextArea).text

        if not self.recipients:
            self.notify("[!] Please add at least one recipient", severity="error")
            return

        if not subject:
            self.notify("[!] Please enter a subject", severity="error")
            return

        if not body:
            self.notify("[!] Please enter an email body", severity="error")
            return

        # Store email data in app for send screen
        self.app.email_data = {
            "recipients": self.recipients.copy(),
            "subject": subject,
            "body": body,
            "email_type": self.email_type,
            "attachments": self.attachments.copy(),
        }

        self.app.push_screen("send")

    def action_save_draft(self) -> None:
        """Save current email as draft."""
        # Get current email data
        subject = self.query_one("#email-subject", Input).value
        body = self.query_one("#email-body", TextArea).text

        # Get sender from config
        from config import get_config

        config = get_config().config
        sender = config.aws.source_email or ""

        # Determine if this is an update or new draft
        is_update = self.current_draft_id is not None
        default_name = self.current_draft_name or subject or "Untitled Draft"

        def handle_save_draft(draft_name: Optional[str]) -> None:
            if draft_name is None:
                return  # User cancelled

            if not self.db:
                self.notify("Database not available", severity="error")
                return

            try:
                if is_update and self.current_draft_id:
                    # Update existing draft
                    self.db.update_draft(
                        draft_id=self.current_draft_id,
                        name=draft_name,
                        subject=subject,
                        body=body,
                        sender=sender,
                        recipients=self.recipients,
                        attachments=self.attachments,
                        email_type=self.email_type,
                    )
                    self.current_draft_name = draft_name
                    self.notify(
                        f"Draft '{draft_name}' updated successfully!",
                        severity="information",
                    )
                else:
                    # Create new draft
                    draft_id = self.db.add_draft(
                        name=draft_name,
                        subject=subject,
                        body=body,
                        sender=sender,
                        recipients=self.recipients,
                        attachments=self.attachments,
                        email_type=self.email_type,
                    )
                    self.current_draft_id = draft_id
                    self.current_draft_name = draft_name
                    self.notify(
                        f"Draft '{draft_name}' saved successfully!",
                        severity="information",
                    )
            except Exception as e:
                self.notify(f"Error saving draft: {e}", severity="error")

        self.app.push_screen(
            SaveDraftDialog(
                title="[+] Save Draft" if not is_update else "[+] Update Draft",
                default_name=default_name,
                is_update=is_update,
            ),
            handle_save_draft,
        )

    def _load_from_draft_if_available(self) -> None:
        """Load draft data if available from app state."""
        if not hasattr(self.app, "email_data") or not self.app.email_data:
            return

        email_data = self.app.email_data

        # Check if this is from a draft or a template (from history resend)
        is_draft = email_data.get("from_draft", False)
        is_template = email_data.get("template_email_id") is not None

        if not is_draft and not is_template:
            return

        # Load draft data into the compose screen
        self.current_draft_id = email_data.get("draft_id")
        self.current_draft_name = email_data.get("draft_name")

        # Set subject
        subject = email_data.get("subject", "")
        self.query_one("#email-subject", Input).value = subject

        # Set body
        body = email_data.get("body", "")
        self.query_one("#email-body", TextArea).text = body

        # Set recipients
        recipients = email_data.get("recipients", [])
        if isinstance(recipients, list):
            self.recipients = recipients.copy()
            self._update_recipients_display()

        # Set attachments
        attachments = email_data.get("attachments", [])
        if isinstance(attachments, list):
            self.attachments = attachments.copy()
            self._update_attachments_display()

        # Set email type
        email_type = email_data.get("email_type", "html")
        self.email_type = email_type
        if email_type == "html":
            self.query_one("#type-html", RadioButton).value = True
        else:
            self.query_one("#type-plain", RadioButton).value = True

        # Clear the app state so it doesn't persist across screens
        self.app.email_data = None

        # Notify user
        if self.current_draft_name:
            self.notify(
                f"Editing draft: {self.current_draft_name}", severity="information"
            )
        elif is_template:
            self.notify(
                "Template loaded. Add recipients and use 'Compare with Previous' to filter out already-sent.",
                severity="information",
                timeout=5,
            )

    def _has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes."""
        has_recipients = len(self.recipients) > 0
        has_subject = bool(self.query_one("#email-subject", Input).value)
        has_body = bool(self.query_one("#email-body", TextArea).text)
        has_attachments = len(self.attachments) > 0
        return has_recipients or has_subject or has_body or has_attachments

    def action_go_back(self) -> None:
        """Go back to home screen with confirmation if there are unsaved changes."""
        if self._has_unsaved_changes():

            def handle_confirm(confirmed: Optional[bool]) -> None:
                if confirmed is True:
                    self.app.pop_screen()

            self.app.push_screen(
                ConfirmDialog(
                    title="[bold]Discard Changes?[/]",
                    message="You have unsaved changes.\nAre you sure you want to go back?",
                    confirm_label="[ok] Yes, Discard",
                    cancel_label="[x] Keep Editing",
                    confirm_variant="warning",
                ),
                handle_confirm,
            )
        else:
            self.app.pop_screen()
