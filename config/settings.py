"""
Configuration manager for SES Email TUI application.
Handles loading, saving, and validating user settings.
"""

import json
import os
from dataclasses import asdict, dataclass, field
from email.utils import formataddr, parseaddr
from pathlib import Path
from typing import List, Optional, Tuple

DEFAULT_CONFIG_PATH = Path(__file__).parent / "settings.json"


@dataclass
class AWSConfig:
    """AWS SES configuration."""

    access_key_id: str = ""
    secret_access_key: str = ""
    region: str = "us-east-1"
    source_email: str = ""


@dataclass
class SenderConfig:
    """Email sender configuration."""

    sender_name: str = "SES Email Sender"
    reply_to: str = ""
    default_to: str = ""  # Default TO address (usually same as source)


@dataclass
class BatchConfig:
    """Batch sending configuration."""

    batch_size: int = 50
    delay_seconds: float = 60.0
    use_bcc: bool = True  # Send as BCC by default


@dataclass
class AppConfig:
    """Main application configuration."""

    aws: AWSConfig = field(default_factory=AWSConfig)
    sender: SenderConfig = field(default_factory=SenderConfig)
    batch: BatchConfig = field(default_factory=BatchConfig)
    files_directory: str = "files"
    data_directory: str = "data"
    last_excel_path: str = ""
    last_excel_column: int = 0
    theme: str = "textual-dark"
    test_recipients: List[str] = field(default_factory=list)


class ConfigManager:
    """Manages application configuration persistence."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self.config = self.load()

    def load(self) -> AppConfig:
        """Load configuration from file or create default."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    data = json.load(f)
                return self._dict_to_config(data)
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                print(f"Error loading config: {e}. Using defaults.")
                return AppConfig()
        return AppConfig()

    def save(self) -> None:
        """Save current configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump(self._config_to_dict(self.config), f, indent=2)

    def _config_to_dict(self, config: AppConfig) -> dict:
        """Convert AppConfig to dictionary."""
        return {
            "aws": asdict(config.aws),
            "sender": asdict(config.sender),
            "batch": asdict(config.batch),
            "files_directory": config.files_directory,
            "data_directory": config.data_directory,
            "last_excel_path": config.last_excel_path,
            "last_excel_column": config.last_excel_column,
            "theme": config.theme,
            "test_recipients": config.test_recipients,
        }

    def _dict_to_config(self, data: dict) -> AppConfig:
        """Convert dictionary to AppConfig."""
        return AppConfig(
            aws=AWSConfig(**data.get("aws", {})),
            sender=SenderConfig(**data.get("sender", {})),
            batch=BatchConfig(**data.get("batch", {})),
            files_directory=data.get("files_directory", "files"),
            data_directory=data.get("data_directory", "data"),
            last_excel_path=data.get("last_excel_path", ""),
            last_excel_column=data.get("last_excel_column", 0),
            theme=data.get("theme", "textual-dark"),
            test_recipients=data.get("test_recipients", []),
        )

    def update_aws(self, **kwargs) -> None:
        """Update AWS configuration."""
        for key, value in kwargs.items():
            if hasattr(self.config.aws, key):
                setattr(self.config.aws, key, value)
        self.save()

    def update_sender(self, **kwargs) -> None:
        """Update sender configuration."""
        for key, value in kwargs.items():
            if hasattr(self.config.sender, key):
                setattr(self.config.sender, key, value)
        self.save()

    def update_batch(self, **kwargs) -> None:
        """Update batch configuration."""
        for key, value in kwargs.items():
            if hasattr(self.config.batch, key):
                setattr(self.config.batch, key, value)
        self.save()

    def update_test_recipients(self, recipients: List[str]) -> None:
        """Update test recipients list."""
        self.config.test_recipients = recipients
        self.save()

    def is_configured(self) -> bool:
        """Check if essential configuration is set."""
        return bool(
            self.config.aws.access_key_id
            and self.config.aws.secret_access_key
            and self.config.aws.region
            and self.config.aws.source_email
        )

    def get_env_vars(self) -> dict:
        """Get AWS credentials as environment variables."""
        return {
            "AWS_ACCESS_KEY_ID": self.config.aws.access_key_id,
            "AWS_SECRET_ACCESS_KEY": self.config.aws.secret_access_key,
            "AWS_REGION": self.config.aws.region,
        }

    def apply_env_vars(self) -> None:
        """Apply AWS credentials to environment."""
        for key, value in self.get_env_vars().items():
            if value:
                os.environ[key] = value


# Global config instance
_config_manager: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def parse_source_email(source_email: str) -> Tuple[str, str]:
    """
    Parse a source email that may be in formataddr format.

    Accepts formats like:
    - "My Name <myemail@test.com>" -> ("My Name", "myemail@test.com")
    - "myemail@test.org" -> ("", "myemail@test.org")

    Returns:
        Tuple of (name, email_address)
    """
    name, email = parseaddr(source_email)
    return (name, email)


def format_source_email(source_email: str, fallback_name: str = "") -> str:
    """
    Format the source email for use in email headers.

    If source_email already contains a name (formataddr style), use it as-is.
    Otherwise, combine with fallback_name.

    Args:
        source_email: The source email, possibly in formataddr format
        fallback_name: Name to use if source_email doesn't include one

    Returns:
        Properly formatted email address string
    """
    name, email = parse_source_email(source_email)
    if name:
        # Source email already has a name, use it
        return formataddr((name, email))
    elif fallback_name:
        # Use the fallback name
        return formataddr((fallback_name, email))
    else:
        # Just the email address
        return email


def get_email_address(source_email: str) -> str:
    """
    Extract just the email address from a source email string.

    Args:
        source_email: The source email, possibly in formataddr format

    Returns:
        Just the email address portion
    """
    _, email = parse_source_email(source_email)
    return email or source_email
