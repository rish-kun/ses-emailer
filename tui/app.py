"""
Main TUI Application for SES Email Sender.
Provides a terminal user interface for managing and sending bulk emails via AWS SES.
"""

import sys
from pathlib import Path
from typing import Any, Optional

from textual.app import App
from textual.binding import Binding

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class SESEmailApp(App):
    """Main SES Email TUI Application."""

    TITLE = "SES Email Sender"
    SUB_TITLE = "Send bulk emails via AWS SES"

    CSS_PATH = "styles.tcss"

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True, priority=True),
        Binding("ctrl+h", "go_home", "Home", show=True),
        Binding("?", "show_help", "Help", show=True),
    ]

    # Screen registry - lazy loading
    SCREENS = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Application state
        self.email_data: Optional[dict[str, Any]] = None

    def on_mount(self) -> None:
        """Set up the application when it starts."""
        # Import screens here to avoid circular imports
        from tui.screens import (
            ComposeScreen,
            ConfigScreen,
            DraftsScreen,
            HistoryScreen,
            HomeScreen,
            SendScreen,
        )

        # Register screens
        self.install_screen(HomeScreen(), name="home")
        self.install_screen(ConfigScreen(), name="config")
        self.install_screen(ComposeScreen(), name="compose")
        self.install_screen(DraftsScreen(), name="drafts")
        self.install_screen(SendScreen(), name="send")
        self.install_screen(HistoryScreen(), name="history")

        # Load configuration
        from config import get_config

        config = get_config()

        # Apply environment variables
        config.apply_env_vars()

        # Push the home screen
        self.push_screen("home")

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()

    def action_go_home(self) -> None:
        """Navigate to home screen."""
        # Pop all screens and push home
        while len(self.screen_stack) > 1:
            self.pop_screen()
        if self.screen.name != "home":
            # Use push_screen instead of switch_screen to avoid callback stack error
            self.push_screen("home")

    def action_show_help(self) -> None:
        """Show help information."""
        help_text = """
[bold #c678dd]SES Email Sender - Help[/]

[bold #56b6c2]Navigation:[/bold #56b6c2]
  [>] [#61afef]Tab/Shift+Tab[/] - Navigate between elements
  [>] [#61afef]Enter[/] - Select/Activate
  [>] [#61afef]Escape[/] - Go back / Cancel
  [>] [#61afef]Ctrl+H[/] - Go to Home screen
  [>] [#61afef]Ctrl+Q[/] - Quit application

[bold #56b6c2]Home Screen:[/bold #56b6c2]
  [>] [#61afef]C[/] - Compose new email
  [>] [#61afef]S[/] - Open Settings
  [>] [#61afef]H[/] - View History
  [>] [#61afef]Q[/] - Quit

[bold #56b6c2]Compose Screen:[/bold #56b6c2]
  [>] [#61afef]Ctrl+Enter[/] - Proceed to send
  [>] [#61afef]Ctrl+S[/] - Save draft

[bold #56b6c2]History Screen:[/bold #56b6c2]
  [>] [#61afef]/[/] - Focus search
  [>] [#61afef]R[/] - Refresh data
  [>] [#61afef]D[/] - Delete selected

[bold #56b6c2]Tips:[/bold #56b6c2]
  [>] Configure AWS credentials in Settings before sending
  [>] Use Excel import to load recipient lists quickly
  [>] BCC mode is recommended for bulk emails
        """
        self.notify(help_text, title="Help", timeout=15)


def main():
    """Entry point for the SES Email TUI application."""
    app = SESEmailApp()
    app.run()


if __name__ == "__main__":
    main()
