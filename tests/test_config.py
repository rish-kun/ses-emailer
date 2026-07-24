import json

from config.settings import ConfigManager


def test_profile_crud(tmp_path):
    cm = ConfigManager(config_path=tmp_path / "settings.json")
    assert cm.list_profiles() == ["default"]

    assert cm.create_profile("staging") is True
    assert cm.create_profile("staging") is False  # duplicate
    assert set(cm.list_profiles()) == {"default", "staging"}

    assert cm.switch_profile("staging") is True
    assert cm.active_profile == "staging"

    assert cm.delete_profile("staging") is True
    assert cm.active_profile == "default"
    assert cm.delete_profile("default") is False  # cannot delete last


def test_update_and_is_configured(tmp_path):
    cm = ConfigManager(config_path=tmp_path / "settings.json")
    assert cm.is_configured() is False
    cm.update_aws(
        access_key_id="k", secret_access_key="s", region="us-east-1", source_email="a@x.com"
    )
    assert cm.is_configured() is True


def test_legacy_flat_format_migration(tmp_path):
    """A legacy flat settings.json migrates into the profiles format, keeping creds."""
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps({"aws": {"access_key_id": "legacy", "secret_access_key": "sek"}})
    )
    cm = ConfigManager(config_path=path)
    assert cm.config.aws.access_key_id == "legacy"
    assert "profiles" in json.loads(path.read_text())
    assert cm.migration_notices  # a notice was recorded
