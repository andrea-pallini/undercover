from fastapi.testclient import TestClient

from agent import __main__ as cli
from agent import main
from backend.main import app


def test_named_claims(monkeypatch, capsys):
    runs = []
    monkeypatch.setattr(cli, "run", lambda claim_id, thread_id: runs.append(claim_id))
    cli.main(["CLM-1001"])
    assert runs == ["CLM-1001"]
    assert capsys.readouterr().out == "CLM-1001: None\n"


def test_whole_queue(monkeypatch):
    monkeypatch.setattr(main, "backend", lambda: TestClient(app))
    client = TestClient(app)
    client.post("/api/claims/CLM-1001/runs", json={"thread_id": "t1"})
    runs = []
    monkeypatch.setattr(cli, "run", lambda claim_id, thread_id: runs.append(thread_id))
    cli.main([])
    assert len(runs) == 24
    assert len(set(runs)) == 24
