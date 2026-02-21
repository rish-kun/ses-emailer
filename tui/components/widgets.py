"""
Custom widgets for the SES Email TUI application.
Provides reusable UI components like spinners and status bars.
"""

from typing import Optional

from rich.spinner import Spinner
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widgets import Static


class SpinnerWidget(Static):
    """A widget that displays an animated spinner."""

    CSS = """
    SpinnerWidget {
        width: auto;
        height: 1;
        padding: 0 1;
    }
    """

    spinning: reactive[bool] = reactive(False)

    def __init__(
        self,
        text: str = "Loading...",
        spinner_style: str = "dots",
        *,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ) -> None:
        super().__init__("", id=id, classes=classes)
        self._text = text
        self._spinner = Spinner(spinner_style, text=text)
        self._update_timer = None

    def on_mount(self) -> None:
        """Start the spinner animation when mounted."""
        if self.spinning:
            self._start_animation()

    def watch_spinning(self, spinning: bool) -> None:
        """React to changes in the spinning state."""
        if spinning:
            self._start_animation()
        else:
            self._stop_animation()

    def _start_animation(self) -> None:
        """Start the spinner animation."""
        if self._update_timer is None:
            self._update_timer = self.set_interval(1 / 12, self._update_spinner)

    def _stop_animation(self) -> None:
        """Stop the spinner animation."""
        if self._update_timer is not None:
            self._update_timer.stop()
            self._update_timer = None
        self.update("")

    def _update_spinner(self) -> None:
        """Update the spinner frame."""
        self.update(self._spinner)

    def set_text(self, text: str) -> None:
        """Update the spinner text."""
        self._text = text
        self._spinner = Spinner(self._spinner.name, text=text)


class StatusBar(Static):
    """A status bar widget that displays status with icons."""

    CSS = """
    StatusBar {
        width: 100%;
        height: 1;
        background: #21252b;
        color: #abb2bf;
        padding: 0 1;
    }

    StatusBar.success {
        background: #98c379 20%;
        color: #98c379;
    }

    StatusBar.error {
        background: #e06c75 20%;
        color: #e06c75;
    }

    StatusBar.warning {
        background: #e5c07b 20%;
        color: #e5c07b;
    }

    StatusBar.info {
        background: #61afef 20%;
        color: #61afef;
    }
    """

    def __init__(
        self,
        message: str = "",
        status: str = "info",
        *,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ) -> None:
        super().__init__(message, id=id, classes=classes)
        self._status = status
        self.add_class(status)

    def set_status(self, message: str, status: str = "info") -> None:
        """Update the status bar message and style."""
        # Remove old status class
        self.remove_class(self._status)
        # Add new status class
        self._status = status
        self.add_class(status)
        # Update message with icon
        icon = self._get_icon(status)
        self.update(f"{icon} {message}")

    def _get_icon(self, status: str) -> str:
        """Get the icon for a given status."""
        icons = {
            "success": "[ok]",
            "error": "[x]",
            "warning": "[!]",
            "info": "[i]",
        }
        return icons.get(status, "[*]")


class IconLabel(Static):
    """A label with a leading icon indicator."""

    CSS = """
    IconLabel {
        width: auto;
        height: 1;
        padding: 0 1;
    }
    """

    def __init__(
        self,
        text: str = "",
        icon: str = "[>]",
        color: str = "#abb2bf",
        *,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ) -> None:
        formatted = f"[{color}]{icon}[/] {text}"
        super().__init__(formatted, id=id, classes=classes)
        self._text = text
        self._icon = icon
        self._color = color

    def set_text(self, text: str) -> None:
        """Update the label text."""
        self._text = text
        self.update(f"[{self._color}]{self._icon}[/] {text}")

    def set_icon(self, icon: str) -> None:
        """Update the label icon."""
        self._icon = icon
        self.update(f"[{self._color}]{self._icon}[/] {self._text}")


class StatCard(Static):
    """A card widget for displaying a statistic."""

    CSS = """
    StatCard {
        width: 1fr;
        height: 5;
        background: #21252b;
        border: tall #3e4451;
        padding: 0 1;
        content-align: center middle;
    }

    StatCard:focus {
        border: tall #61afef;
    }

    StatCard > .stat-value {
        text-align: center;
        text-style: bold;
        width: 100%;
    }

    StatCard > .stat-label {
        text-align: center;
        color: #5c6370;
        width: 100%;
    }
    """

    def __init__(
        self,
        label: str = "Stat",
        value: str = "0",
        color: str = "#61afef",
        *,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ) -> None:
        super().__init__(id=id, classes=classes)
        self._label = label
        self._value = value
        self._color = color

    def compose(self) -> ComposeResult:
        yield Static(
            f"[{self._color}]{self._value}[/]",
            classes="stat-value",
        )
        yield Static(self._label, classes="stat-label")

    def set_value(self, value: str) -> None:
        """Update the statistic value."""
        self._value = value
        value_widget = self.query_one(".stat-value", Static)
        value_widget.update(f"[{self._color}]{value}[/]")


class KeyHint(Static):
    """A widget showing keyboard shortcuts."""

    CSS = """
    KeyHint {
        width: auto;
        height: 1;
        padding: 0 1;
        color: #5c6370;
    }

    KeyHint .key {
        background: #3e4451;
        color: #61afef;
        padding: 0 1;
    }
    """

    def __init__(
        self,
        key: str = "",
        action: str = "",
        *,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ) -> None:
        formatted = f"[#3e4451 on #61afef] {key} [/] {action}"
        super().__init__(formatted, id=id, classes=classes)
