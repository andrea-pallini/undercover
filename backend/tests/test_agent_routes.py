from fastapi.testclient import TestClient

from agent import main as agent
from backend.main import INSTRUCTIONS, app

client = TestClient(app)


def test_get_instructions():
    instructions = client.get("/api/instructions").json()
    assert instructions == {"text": INSTRUCTIONS.read_text(encoding="utf-8")}
    assert instructions["text"].startswith("# The UnderCover Agent")


def test_start_agent(monkeypatch):
    runs = []
    monkeypatch.setattr(agent, "run", lambda *args: runs.append(args))
    response = client.post("/api/claims/CLM-1001/agent")
    assert response.status_code == 202
    assert runs == [("CLM-1001", response.json()["thread_id"])]


def test_start_agent_on_a_claim_in_progress(monkeypatch):
    monkeypatch.setattr(agent, "run", lambda *args: None)
    client.post("/api/claims/CLM-1001/runs", json={"thread_id": "t1"})
    response = client.post("/api/claims/CLM-1001/agent")
    assert response.status_code == 409
    assert response.json() == {
        "detail": "CLM-1001 isn't waiting, so the agent can't start."
    }
