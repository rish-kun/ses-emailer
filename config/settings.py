"""
Configuration manager for SES Email application.
Handles loading, saving, and validating user settings with multi-profile support.
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
    default_to: str = ""


@dataclass
class BatchConfig:
    """Batch sending configuration."""

    batch_size: int = 50
    delay_seconds: float = 60.0
    use_bcc: bool = True


@dataclass
class AppConfig:
    """Main application configuration (a single profile)."""

    aws: AWSConfig = field(default_factory=AWSConfig)
    sender: SenderConfig = field(default_factory=SenderConfig)
    batch: BatchConfig = field(default_factory=BatchConfig)
    files_directory: str = "files"
    data_directory: str = "data"
    last_excel_path: str = ""
    last_excel_column: int = 0
    theme: str = "dark"
    test_recipients: List[str] = field(default_factory=list)


class ConfigManager:
    """Manages application configuration with multi-profile support."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self._active_profile: str = "default"
        self._profiles: dict[str, AppConfig] = {}
        self._load_all()

    @property
    def config(self) -> AppConfig:
        """Get the active profile's config."""
        return self._profiles.get(self._active_profile, AppConfig())

    @property
    def active_profile(self) -> str:
        return self._active_profile

    # ── Loading / Saving ──────────────────────────────────────────────

    def _load_all(self) -> None:
        """Load all profiles from the config file."""
        if not self.config_path.exists():
            self._profiles = {"default": AppConfig()}
            self._active_profile = "default"
            self.save()
            return

        try:
            with open(self.config_path, "r") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            self._profiles = {"default": AppConfig()}
            self._active_profile = "default"
            self.save()
            return

        # Detect old flat format (no "profiles" key) and migrate
        if "profiles" not in data:
            profile_data = {
                k: v
                for k, v in data.items()
                if k not in ("active_profile", "profiles")
            }
            # Clear credentials for public safety
            if "aws" in profile_data:
                profile_data["aws"] = {
                    "access_key_id": "",
                    "secret_access_key": "",
                    "region": profile_data.get("aws", {}).get("region", "us-east-1"),
                    "source_email": "",
                }
            self._profiles = {"default": self._dict_to_config(profile_data)}
            self._active_profile = "default"
            self.save()
            return

        self._active_profile = data.get("active_profile", "default")
        self._profiles = {}
        for name, profile_data in data.get("profiles", {}).items():
            self._profiles[name] = self._dict_to_config(profile_data)

        if not self._profiles:
            self._profiles = {"default": AppConfig()}
            self._active_profile = "default"

        if self._active_profile not in self._profiles:
            self._active_profile = next(iter(self._profiles))

    def save(self) -> None:
        """Save all profiles to the config file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "active_profile": self._active_profile,
            "profiles": {
                name: self._config_to_dict(cfg)
                for name, cfg in self._profiles.items()
            },
        }
        with open(self.config_path, "w") as f:
            json.dump(data, f, indent=2)

    def load(self) -> AppConfig:
        """Reload and return the active profile config (legacy compat)."""
        self._load_all()
        return self.config

    # ── Profile management ────────────────────────────────────────────

    def list_profiles(self) -> list[str]:
        """Return list of profile names."""
        return list(self._profiles.keys())

    def switch_profile(self, name: str) -> bool:
        """Switch to a different profile. Returns True if successful."""
        if name not in self._profiles:
            return False
        self._active_profile = name
        self.save()
        return True

    def create_profile(self, name: str, copy_from: Optional[str] = None) -> bool:
        """Create a new profile. Optionally copy settings from an existing one."""
        if name in self._profiles:
            return False
        if copy_from and copy_from in self._profiles:
            source = self._profiles[copy_from]
            new_data = self._config_to_dict(source)
            self._profiles[name] = self._dict_to_config(new_data)
        else:
            self._profiles[name] = AppConfig()
        self.save()
        return True

    def delete_profile(self, name: str) -> bool:
        """Delete a profile. Cannot delete if it's the only one."""
        if name not in self._profiles or len(self._profiles) <= 1:
            return False
        del self._profiles[name]
        if self._active_profile == name:
            self._active_profile = next(iter(self._profiles))
        self.save()
        return True

    def rename_profile(self, old_name: str, new_name: str) -> bool:
        """Rename a profile."""
        if old_name not in self._profiles or new_name in self._profiles:
            return False
        self._profiles[new_name] = self._profiles.pop(old_name)
        if self._active_profile == old_name:
            self._active_profile = new_name
        self.save()
        return True

    # ── Config serialization ──────────────────────────────────────────

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
            theme=data.get("theme", "dark"),
            test_recipients=data.get("test_recipients", []),
        )

    # ── Field update helpers ──────────────────────────────────────────

    def update_aws(self, **kwargs) -> None:
        """Update AWS configuration on active profile."""
        for key, value in kwargs.items():
            if hasattr(self.config.aws, key):
                setattr(self.config.aws, key, value)
        self.save()

    def update_sender(self, **kwargs) -> None:
        """Update sender configuration on active profile."""
        for key, value in kwargs.items():
            if hasattr(self.config.sender, key):
                setattr(self.config.sender, key, value)
        self.save()

    def update_batch(self, **kwargs) -> None:
        """Update batch configuration on active profile."""
        for key, value in kwargs.items():
            if hasattr(self.config.batch, key):
                setattr(self.config.batch, key, value)
        self.save()

    def update_test_recipients(self, recipients: List[str]) -> None:
        """Update test recipients list on active profile."""
        self.config.test_recipients = recipients
        self.save()

    def update_config(self, data: dict) -> None:
        """Bulk update the active profile from a dict."""
        if "aws" in data:
            self.update_aws(**data["aws"])
        if "sender" in data:
            self.update_sender(**data["sender"])
        if "batch" in data:
            self.update_batch(**data["batch"])
        for key in (
            "files_directory",
            "data_directory",
            "last_excel_path",
            "last_excel_column",
            "theme",
            "test_recipients",
        ):
            if key in data:
                setattr(self.config, key, data[key])
        self.save()

    def get_config_dict(self) -> dict:
        """Return the active config as a serializable dict."""
        return self._config_to_dict(self.config)

    # ── Checks ────────────────────────────────────────────────────────

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


# ── Global singleton ──────────────────────────────────────────────────

_config_manager: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def reset_config() -> ConfigManager:
    """Reset and return a fresh ConfigManager (useful after profile changes)."""
    global _config_manager
    _config_manager = ConfigManager()
    return _config_manager


# ── Email formatting helpers ──────────────────────────────────────────


def parse_source_email(source_email: str) -> Tuple[str, str]:
    """Parse a source email that may be in formataddr format."""
    name, email = parseaddr(source_email)
    return (name, email)


def format_source_email(source_email: str, fallback_name: str = "") -> str:
    """Format the source email for use in email headers."""
    name, email = parse_source_email(source_email)
    if name:
        return formataddr((name, email))
    elif fallback_name:
        return formataddr((fallback_name, email))
    else:
        return email


def get_email_address(source_email: str) -> str:
    """Extract just the email address from a source email string."""
    _, email = parse_source_email(source_email)
    return email or source_email
