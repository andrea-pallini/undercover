import pytest

from backend.seed import seed


@pytest.fixture(autouse=True)
def database(tmp_path, monkeypatch):
    """Give each test a fresh database built from data/."""
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "undercover.db"))
    seed()
