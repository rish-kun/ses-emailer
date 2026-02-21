"""
Configuration Screen for SES Email TUI application.
Allows users to configure AWS credentials, sender info, and batch settings.
"""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.validation import Number
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    OptionList,
    Static,
    Switch,
    TabbedContent,
    TabPane,
)
from textual.widgets.option_list import Option


class ConfigScreen(Screen):
    """Configuration screen for managing app settings."""

    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("ctrl+s", "save", "Save"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_recipients: list[str] = []

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="config-container"):
            yield Static(
                "[bold]*[/] Configuration Settings",
                classes="screen-title",
            )
            with TabbedContent(id="config-tabs"):
                with TabPane("[bold]>[/] AWS Credentials", id="tab-aws"):
                    with Vertical(id="aws-form"):
                        yield Label("AWS Access Key ID:")
                        yield Input(
                            placeholder="Enter your AWS Access Key ID",
                            id="aws-access-key",
                            password=False,
                        )
                        yield Label("AWS Secret Access Key:")
                        yield Input(
                            placeholder="Enter your AWS Secret Access Key",
                            id="aws-secret-key",
                            password=True,
                        )
                        yield Label("AWS Region:")
                        yield Input(
                            placeholder="e.g., us-east-1",
                            id="aws-region",
                            value="us-east-1",
                        )
                        yield Label("Source Email (must be verified in SES):")
                        yield Input(
                            placeholder="Name <sender@yourdomain.com> or sender@yourdomain.com",
                            id="source-email",
                        )
                        yield Static(
                            "[#5c6370][i] Your AWS credentials are stored locally and never shared.[/]",
                            id="aws-hint",
                        )

                with TabPane("[bold]>[/] Sender Settings", id="tab-sender"):
                    with Vertical(id="sender-form"):
                        yield Label("Sender Display Name:")
                        yield Input(
                            placeholder="e.g., My Company",
                            id="sender-name",
                        )
                        yield Label("Reply-To Email:")
                        yield Input(
                            placeholder="reply@yourdomain.com",
                            id="reply-to",
                        )
                        yield Label("Default TO Address:")
                        yield Input(
                            placeholder="Usually same as source email",
                            id="default-to",
                        )
                        yield Static(
                            "[#5c6370][i] These settings determine how your emails appear to recipients.[/]",
                            id="sender-hint",
                        )

                with TabPane("[bold]>[/] Batch Settings", id="tab-batch"):
                    with Vertical(id="batch-form"):
                        yield Label("Batch Size (emails per batch):")
                        yield Input(
                            placeholder="50",
                            id="batch-size",
                            validators=[Number(minimum=1, maximum=1000)],
                        )
                        yield Label("Delay Between Batches (seconds):")
                        yield Input(
                            placeholder="60",
                            id="batch-delay",
                            validators=[Number(minimum=0, maximum=3600)],
                        )
                        with Horizontal(id="bcc-toggle"):
                            yield Switch(value=True, id="use-bcc")
                            yield Label("Send as BCC (recommended for bulk emails)")
                        yield Static(
                            "[#5c6370][i] AWS SES has rate limits. Adjust batch settings accordingly.[/]",
                            id="batch-hint",
                        )

                with TabPane("[bold]>[/] Paths", id="tab-paths"):
                    with Vertical(id="paths-form"):
                        yield Label("Files Directory (for attachments):")
                        yield Input(
                            placeholder="files",
                            id="files-dir",
                        )
                        yield Label("Last Excel File Path:")
                        yield Input(
                            placeholder="path/to/recipients.xlsx",
                            id="last-excel",
                        )
                        yield Label("Excel Column Index (0-based):")
                        yield Input(
                            placeholder="0",
                            id="excel-column",
                            validators=[Number(minimum=0, maximum=100)],
                        )
                        yield Static(
                            "[#5c6370][i] These paths are used as defaults when composing emails.[/]",
                            id="paths-hint",
                        )

                with TabPane("[bold]>[/] Test Recipients", id="tab-test-recipients"):
                    with Vertical(id="test-recipients-form"):
                        yield Static(
                            "Add Test Recipients",
                            classes="section-header",
                        )
                        yield Static(
                            "[#5c6370][i] Add email addresses here for quick selection when sending test emails.[/]",
                            id="test-recipients-hint",
                        )
                        with Horizontal(id="test-recipient-input-row"):
                            yield Input(
                                placeholder="Enter test email address",
                                id="test-recipient-input",
                            )
                            yield Button(
                                "[+] Add",
                                id="btn-add-test-recipient",
                                variant="primary",
                            )
                        yield Static("", classes="spacer")
                        yield Static(
                            "Current Test Recipients",
                            classes="section-header",
                        )
                        yield OptionList(id="test-recipients-list")
                        yield Static(
                            "[#5c6370]No test recipients configured[/]",
                            id="test-recipients-count",
                        )
                        with Horizontal(id="test-recipient-buttons"):
                            yield Button(
                                "[-] Remove Selected",
                                id="btn-remove-test-recipient",
                                variant="warning",
                            )
                            yield Button(
                                "[x] Clear All",
                                id="btn-clear-test-recipients",
                                variant="error",
                            )

            with Horizontal(id="config-buttons"):
                yield Button("[+] Save", id="btn-save", classes="-primary")
                yield Button("[<] Back", id="btn-back")
                yield Button("[~] Reset", id="btn-reset", classes="-warning")

        yield Footer()

    def on_mount(self) -> None:
        """Load existing configuration when screen mounts."""
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration values into form fields."""
        from config import get_config

        config = get_config().config

        # AWS settings
        self.query_one("#aws-access-key", Input).value = config.aws.access_key_id
        self.query_one("#aws-secret-key", Input).value = config.aws.secret_access_key
        self.query_one("#aws-region", Input).value = config.aws.region
        self.query_one("#source-email", Input).value = config.aws.source_email

        # Sender settings
        self.query_one("#sender-name", Input).value = config.sender.sender_name
        self.query_one("#reply-to", Input).value = config.sender.reply_to
        self.query_one("#default-to", Input).value = config.sender.default_to

        # Batch settings
        self.query_one("#batch-size", Input).value = str(config.batch.batch_size)
        self.query_one("#batch-delay", Input).value = str(config.batch.delay_seconds)
        self.query_one("#use-bcc", Switch).value = config.batch.use_bcc

        # Paths
        self.query_one("#files-dir", Input).value = config.files_directory
        self.query_one("#last-excel", Input).value = config.last_excel_path
        self.query_one("#excel-column", Input).value = str(config.last_excel_column)

        # Test Recipients
        self.test_recipients = config.test_recipients.copy()
        self._update_test_recipients_display()

    def _save_config(self) -> bool:
        """Save form values to configuration."""
        from config import get_config

        config_manager = get_config()

        try:
            # Update AWS settings
            config_manager.update_aws(
                access_key_id=self.query_one("#aws-access-key", Input).value,
                secret_access_key=self.query_one("#aws-secret-key", Input).value,
                region=self.query_one("#aws-region", Input).value,
                source_email=self.query_one("#source-email", Input).value,
            )

            # Update sender settings
            config_manager.update_sender(
                sender_name=self.query_one("#sender-name", Input).value,
                reply_to=self.query_one("#reply-to", Input).value,
                default_to=self.query_one("#default-to", Input).value,
            )

            # Update batch settings
            batch_size_str = self.query_one("#batch-size", Input).value
            delay_str = self.query_one("#batch-delay", Input).value

            config_manager.update_batch(
                batch_size=int(batch_size_str) if batch_size_str else 50,
                delay_seconds=float(delay_str) if delay_str else 60.0,
                use_bcc=self.query_one("#use-bcc", Switch).value,
            )

            # Update paths
            config_manager.config.files_directory = self.query_one(
                "#files-dir", Input
            ).value
            config_manager.config.last_excel_path = self.query_one(
                "#last-excel", Input
            ).value
            excel_col_str = self.query_one("#excel-column", Input).value
            config_manager.config.last_excel_column = (
                int(excel_col_str) if excel_col_str else 0
            )

            # Update test recipients
            config_manager.update_test_recipients(self.test_recipients)

            config_manager.save()

            # Apply environment variables
            config_manager.apply_env_vars()

            return True
        except ValueError as e:
            self.notify(f"Invalid value: {e}", severity="error")
            return False
        except Exception as e:
            self.notify(f"Error saving config: {e}", severity="error")
            return False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "btn-save":
            self.action_save()
        elif button_id == "btn-back":
            self.action_go_back()
        elif button_id == "btn-reset":
            self._load_config()
            self.notify(
                "Configuration reset to last saved values", severity="information"
            )
        elif button_id == "btn-add-test-recipient":
            self._add_test_recipient()
        elif button_id == "btn-remove-test-recipient":
            self._remove_selected_test_recipient()
        elif button_id == "btn-clear-test-recipients":
            self._clear_test_recipients()

    def _add_test_recipient(self) -> None:
        """Add a test recipient to the list."""
        input_widget = self.query_one("#test-recipient-input", Input)
        email = input_widget.value.strip()

        if not email:
            self.notify("Please enter an email address", severity="warning")
            return

        if "@" not in email:
            self.notify("Please enter a valid email address", severity="error")
            return

        if email in self.test_recipients:
            self.notify("This email is already in the list", severity="warning")
            return

        self.test_recipients.append(email)
        self._update_test_recipients_display()
        input_widget.value = ""
        self.notify(f"Added: {email}", severity="information")

    def _remove_selected_test_recipient(self) -> None:
        """Remove the selected test recipient."""
        option_list = self.query_one("#test-recipients-list", OptionList)
        if option_list.highlighted is not None and self.test_recipients:
            idx = option_list.highlighted
            if 0 <= idx < len(self.test_recipients):
                removed = self.test_recipients.pop(idx)
                self._update_test_recipients_display()
                self.notify(f"Removed: {removed}", severity="information")

    def _clear_test_recipients(self) -> None:
        """Clear all test recipients."""
        self.test_recipients.clear()
        self._update_test_recipients_display()
        self.notify("All test recipients cleared", severity="information")

    def _update_test_recipients_display(self) -> None:
        """Update the test recipients list display."""
        option_list = self.query_one("#test-recipients-list", OptionList)
        option_list.clear_options()

        for email in self.test_recipients:
            option_list.add_option(Option(f"[@] {email}"))

        count_label = self.query_one("#test-recipients-count", Static)
        if self.test_recipients:
            count_label.update(
                f"[#98c379][ok] {len(self.test_recipients)} test recipient(s) configured[/]"
            )
        else:
            count_label.update("[#5c6370]No test recipients configured[/]")

    def action_save(self) -> None:
        """Save configuration."""
        if self._save_config():
            self.notify(
                "[ok] Configuration saved successfully!", severity="information"
            )

    def action_go_back(self) -> None:
        """Go back to home screen."""
        self.app.pop_screen()
