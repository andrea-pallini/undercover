from pathlib import Path

from fastapi.testclient import TestClient

from backend import seed
from backend.db import database_path
from backend.main import app

client = TestClient(app)


def test_list_claims():
    claims = client.get("/api/claims").json()
    assert len(claims) == 25
    assert {claim["status"] for claim in claims} == {"waiting"}
    assert claims[0] == {
        "claim_id": "CLM-1001",
        "customer_name": "Maya Patel",
        "claim_type": "trip_delay",
        "summary": "Flight home canceled by the airline, rebooked the next morning",
        "amount_claimed": 420.0,
        "submitted_on": "2026-06-24",
        "status": "waiting",
        "decision": None,
        "payout": None,
    }


def test_get_claim():
    claim = client.get("/api/claims/CLM-1001").json()
    assert claim["story"].startswith("My flight home from Rome")
    assert len(claim["items"]) == 3
    assert len(claim["documents"]) == 4
    assert claim["status"] == "waiting"


def test_unknown_claim():
    response = client.get("/api/claims/CLM-9999")
    assert response.status_code == 404
    assert response.json() == {"detail": "CLM-9999 not found."}


def test_get_policy():
    policy = client.get("/api/policies/POL-2001").json()
    assert policy["plan"] == "premium"
    assert policy["trip"]["destination"] == "Rome, Italy"
    assert policy["trip"]["departs_on"] == "2026-06-10"
    assert policy["trip"]["returns_on"] == "2026-06-18"


def test_claim_history_leaves_out_contact_details():
    history = client.get("/api/customers/CUS-3001/history").json()
    assert history["name"] == "Maya Patel"
    assert [c["claim_id"] for c in history["previous_claims"]] == ["CLM-0412"]
    assert not {"email", "phone", "address", "date_of_birth"} & history.keys()


def test_policy_wording():
    wording = client.get("/api/policy-wording").json()
    assert wording["version"] == "2026.1"
    assert wording["text"].startswith("# UnderCover Travel Insurance: Policy Wording")


def test_list_handlers():
    handlers = client.get("/api/handlers").json()
    assert [h["handler_id"] for h in handlers] == ["HND-01", "HND-02", "HND-03"]


def test_seed_counts():
    assert seed.seed() == {
        "claims": 25,
        "policies": 50,
        "customers": 49,
        "handlers": 3,
    }


def test_seed_never_reads_evals(monkeypatch):
    opened = []
    read_text = Path.read_text

    def recording(self, *args, **kwargs):
        opened.append(self.resolve())
        return read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", recording)
    seed.seed()
    evals = (seed.DATA / "evals").resolve()
    assert opened
    assert not [path for path in opened if path.is_relative_to(evals)]


def test_backend_builds_the_database_once(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "new.db"))
    with TestClient(app) as fresh:
        assert len(fresh.get("/api/claims").json()) == 25
    built = database_path().stat().st_mtime_ns
    with TestClient(app):
        pass
    assert database_path().stat().st_mtime_ns == built


def test_every_operation_is_complete():
    spec = app.openapi()
    schemas = spec["components"]["schemas"]
    for path in spec["paths"].values():
        for operation in path.values():
            assert operation["operationId"]
            assert operation["description"]
            assert all(p["required"] for p in operation.get("parameters", []))
            body = operation.get("requestBody")
            if body:
                ref = body["content"]["application/json"]["schema"]["$ref"]
                schema = schemas[ref.split("/")[-1]]
                assert set(schema.get("required", [])) == set(schema["properties"])
