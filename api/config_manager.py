import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from config.settings import AppConfig, AWSConfig, SenderConfig, BatchConfig

PROFILES_CONFIG_PATH = Path("config/profiles.json")

@dataclass
class Profile:
    id: str
    name: str
    config: AppConfig

class ConfigProfileManager:
    def __init__(self, profiles_path: Optional[Path] = None):
        self.profiles_path = profiles_path or PROFILES_CONFIG_PATH
        self.profiles: Dict[str, Profile] = {}
        self.active_profile_id: Optional[str] = None
        self.load()

    def load(self):
        if self.profiles_path.exists():
            try:
                with open(self.profiles_path, "r") as f:
                    data = json.load(f)

                self.active_profile_id = data.get("active_profile_id")

                for p_data in data.get("profiles", []):
                    # Reconstruct config
                    cfg_data = p_data.get("config", {})
                    app_config = AppConfig(
                        aws=AWSConfig(**cfg_data.get("aws", {})),
                        sender=SenderConfig(**cfg_data.get("sender", {})),
                        batch=BatchConfig(**cfg_data.get("batch", {})),
                        files_directory=cfg_data.get("files_directory", "files"),
                        data_directory=cfg_data.get("data_directory", "data"),
                        last_excel_path=cfg_data.get("last_excel_path", ""),
                        last_excel_column=cfg_data.get("last_excel_column", 0),
                        theme=cfg_data.get("theme", "textual-dark"),
                        test_recipients=cfg_data.get("test_recipients", [])
                    )

                    profile = Profile(
                        id=p_data["id"],
                        name=p_data["name"],
                        config=app_config
                    )
                    self.profiles[profile.id] = profile

            except Exception as e:
                print(f"Error loading profiles: {e}")
                self._create_default_profile()
        else:
            self._create_default_profile()

    def _create_default_profile(self):
        default_id = uuid.uuid4().hex
        self.profiles[default_id] = Profile(
            id=default_id,
            name="Default Profile",
            config=AppConfig()
        )
        self.active_profile_id = default_id
        self.save()

    def save(self):
        self.profiles_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "active_profile_id": self.active_profile_id,
            "profiles": [
                {
                    "id": p.id,
                    "name": p.name,
                    "config": {
                        "aws": asdict(p.config.aws),
                        "sender": asdict(p.config.sender),
                        "batch": asdict(p.config.batch),
                        "files_directory": p.config.files_directory,
                        "data_directory": p.config.data_directory,
                        "last_excel_path": p.config.last_excel_path,
                        "last_excel_column": p.config.last_excel_column,
                        "theme": p.config.theme,
                        "test_recipients": p.config.test_recipients
                    }
                }
                for p in self.profiles.values()
            ]
        }
        with open(self.profiles_path, "w") as f:
            json.dump(data, f, indent=2)

    def get_active_profile(self) -> Profile:
        if not self.active_profile_id or self.active_profile_id not in self.profiles:
            if self.profiles:
                self.active_profile_id = next(iter(self.profiles.values())).id
            else:
                self._create_default_profile()
        return self.profiles[self.active_profile_id]

    def set_active_profile(self, profile_id: str) -> bool:
        if profile_id in self.profiles:
            self.active_profile_id = profile_id
            self.save()
            return True
        return False

    def create_profile(self, name: str, config: Optional[AppConfig] = None) -> Profile:
        new_id = uuid.uuid4().hex
        new_profile = Profile(
            id=new_id,
            name=name,
            config=config or AppConfig()
        )
        self.profiles[new_id] = new_profile
        self.save()
        return new_profile

    def update_profile(self, profile_id: str, name: Optional[str] = None, config: Optional[AppConfig] = None) -> bool:
        if profile_id in self.profiles:
            if name is not None:
                self.profiles[profile_id].name = name
            if config is not None:
                self.profiles[profile_id].config = config
            self.save()
            return True
        return False

    def delete_profile(self, profile_id: str) -> bool:
        if profile_id in self.profiles and len(self.profiles) > 1:
            del self.profiles[profile_id]
            if self.active_profile_id == profile_id:
                self.active_profile_id = next(iter(self.profiles.values())).id
            self.save()
            return True
        return False

    def get_all_profiles(self) -> List[Profile]:
        return list(self.profiles.values())
