"""
TUI module for SES Email application.
Provides a terminal user interface for sending emails via AWS SES.
"""

from .app import SESEmailApp, main

__all__ = ["SESEmailApp", "main"]
