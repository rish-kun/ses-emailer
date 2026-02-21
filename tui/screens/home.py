"""
Home Screen for SES Email TUI application.
Main menu with navigation to other screens.
"""

from typing import Optional

from textual.app import ComposeResult
from textual.containers import Center, Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

from tui.components.modals import ConfirmDialog


class HomeScreen(Screen):
    """Main home screen with navigation menu."""

    BINDINGS = [
        ("c", "compose", "Compose Email"),
        ("d", "drafts", "Drafts"),
        ("s", "settings", "Settings"),
        ("h", "history", "History"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="home-container"):
            with Center():
                with Vertical(id="home-menu"):
                    # Clean ASCII art logo using simple box characters
                    yield Static(
                        """[bold #61afef]
+-----------------------------------------------------------+
|                                                           |
|   ███████ ███████ ███████   ███    ███  █████  ██ ██      |
|   ██      ██      ██        ████  ████ ██   ██ ██ ██      |
|   ███████ █████   ███████   ██ ████ ██ ███████ ██ ██      |
|        ██ ██           ██   ██  ██  ██ ██   ██ ██ ██      |
|   ███████ ███████ ███████   ██      ██ ██   ██ ██ ██████  |
|                                                           |
|           [#c678dd]AWS SES Email Sender[/]                          |
|                                                           |
+-----------------------------------------------------------+
[/]""",
                        id="logo",
                    )
                    yield Static(
                        "[#abb2bf]Send bulk emails efficiently with AWS SES[/]",
                        id="subtitle",
                    )

                    yield Static("", classes="spacer")

                    yield Button(
                        "[bold]>[/] Compose Email",
                        id="btn-compose",
                        variant="primary",
                    )
                    yield Button(
                        "[bold]+[/] Drafts",
                        id="btn-drafts",
                        variant="default",
                    )
                    yield Button(
                        "[bold]*[/] Settings",
                        id="btn-settings",
                        variant="default",
                    )
                    yield Button(
                        "[bold]#[/] Email History",
                        id="btn-history",
                        variant="default",
                    )
                    yield Button(
                        "[bold]x[/] Exit",
                        id="btn-exit",
                        variant="error",
                    )

                    yield Static("", classes="spacer")

                    yield Static(
                        "[#5c6370]Press [bold]?[/] for help  |  [bold]d[/] for drafts  |  [bold]q[/] to quit[/]",
                        id="help-hint",
                    )
        yield Footer()

    def on_mount(self) -> None:
        """Handle screen mount - check configuration status."""
        self._check_config_status()

    def _check_config_status(self) -> None:
        """Check if the app is properly configured."""
        from config import get_config

        config = get_config()
        if not config.is_configured():
            self.notify(
                "[!] AWS credentials not configured. Please go to Settings.",
                severity="warning",
                timeout=5,
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "btn-compose":
            self.action_compose()
        elif button_id == "btn-drafts":
            self.action_drafts()
        elif button_id == "btn-settings":
            self.action_settings()
        elif button_id == "btn-history":
            self.action_history()
        elif button_id == "btn-exit":
            self.action_quit()

    def action_compose(self) -> None:
        """Navigate to compose screen."""
        from config import get_config

        config = get_config()
        if not config.is_configured():
            self.notify(
                "[!] Please configure AWS credentials first!",
                severity="error",
                timeout=3,
            )
            self.app.push_screen("config")
        else:
            self.app.push_screen("compose")

    def action_drafts(self) -> None:
        """Navigate to drafts screen."""
        self.app.push_screen("drafts")

    def action_settings(self) -> None:
        """Navigate to settings screen."""
        self.app.push_screen("config")

    def action_history(self) -> None:
        """Navigate to history screen."""
        self.app.push_screen("history")

    def action_quit(self) -> None:
        """Quit the application with confirmation."""

        def handle_confirm(confirmed: Optional[bool]) -> None:
            if confirmed is True:
                self.app.exit()

        self.app.push_screen(
            ConfirmDialog(
                title="[bold]Exit Application[/]",
                message="Are you sure you want to quit?",
                confirm_label="[ok] Yes, Exit",
                cancel_label="[x] Cancel",
                confirm_variant="error",
            ),
            handle_confirm,
        )
