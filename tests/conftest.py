"""Shared pytest fixtures: isolated DB + config, and a TestClient with mocked SES."""


import pytest


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    """Point the app's SQLite DB at a throwaway file for the duration of a test."""
    path = tmp_path / "test.db"
    monkeypatch.setenv("SES_DB_PATH", str(path))
    return str(path)


@pytest.fixture
def configured(tmp_path, monkeypatch):
    """Install a fully-configured, isolated ConfigManager as the global singleton."""
    import config.settings as settings_mod

    cm = settings_mod.ConfigManager(config_path=tmp_path / "settings.json")
    cm.update_aws(
        access_key_id="AKIA_TEST",
        secret_access_key="secret_test",
        region="us-east-1",
        source_email="Fest Team <from@test.com>",
    )
    monkeypatch.setattr(settings_mod, "_config_manager", cm)
    return cm


@pytest.fixture
def client(db_path, configured, monkeypatch):
    """FastAPI TestClient with a known token and boto3 SES fully mocked."""
    from unittest.mock import MagicMock

    monkeypatch.setenv("API_TOKEN", "test-token")

    fake_ses = MagicMock()
    fake_ses.send_email.return_value = {"MessageId": "0000000000000000-msg"}

    import boto3

    monkeypatch.setattr(boto3, "client", lambda *a, **k: fake_ses)

    from fastapi.testclient import TestClient

    from api.main import app

    test_client = TestClient(app)
    test_client.fake_ses = fake_ses  # expose for assertions
    return test_client


@pytest.fixture
def auth():
    return {"Authorization": "Bearer test-token"}
