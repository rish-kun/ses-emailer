"""
Screens module for SES Email TUI application.
Contains all screen definitions for the application.
"""

from .compose import ComposeScreen
from .config import ConfigScreen
from .drafts import DraftsScreen
from .history import HistoryScreen
from .home import HomeScreen
from .send import SendScreen

__all__ = [
    "HomeScreen",
    "ConfigScreen",
    "ComposeScreen",
    "DraftsScreen",
    "SendScreen",
    "HistoryScreen",
]
