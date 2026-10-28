from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from backend import main
from backend.main import app

client = TestClient(app)


def start(claim_id, thread_id="thread-1"):
    return client.post(f"/api/claims/{claim_id}/runs", json={"thread_id": thread_id})


def decide(claim_id, decision="approve", payout=420.0, confidence=90):
    return client.post(
        f"/api/claims/{claim_id}/decision",
        json={
            "decision": decision,
            "payout": payout,
            "reasons": "The flight was canceled for a crew problem.",
            "policy_section": "3. Trip Delay",
            "confidence": confidence,
        },
    )


def pay(claim_id, amount):
    return client.post(f"/api/claims/{claim_id}/payments", json={"amount": amount})


def status(claim_id):
    return client.get(f"/api/claims/{claim_id}").json()["status"]


class Clock:
    def __init__(self):
        self.time = datetime(2026, 10, 28, 9, 0, tzinfo=UTC)

    def __call__(self):
        return self.time

    def advance(self, seconds):
        self.time += timedelta(seconds=seconds)


@pytest.fixture
def clock(monkeypatch):
    clock = Clock()
    monkeypatch.setattr(main, "now", clock)
    return clock


def test_start_run():
    response = start("CLM-1001")
    assert response.status_code == 201
    assert response.json()["claim_id"] == "CLM-1001"
    assert status("CLM-1001") == "in_progress"
    again = start("CLM-1001", "thread-2")
    assert again.status_code == 409
    assert again.json() == {
        "detail": "CLM-1001 isn't waiting, so the agent can't start."
    }


def test_record_step_and_progress(clock):
    start("CLM-1001")
    clock.advance(5)
    step = client.post(
        "/api/runs/thread-1/steps", json={"description": "Reading claim CLM-1001"}
    )
    assert step.status_code == 201
    progress = client.get("/api/claims/CLM-1001/progress").json()
    assert progress["steps"] == [
        {"at": "2026-10-28T09:00:05+00:00", "description": "Reading claim CLM-1001"}
    ]
    assert progress["seconds_remaining"] == 25
    assert progress["finished_at"] is None


def test_step_on_unknown_run():
    response = client.post("/api/runs/nope/steps", json={"description": "Hello"})
    assert response.status_code == 404


def test_progress_before_any_run():
    response = client.get("/api/claims/CLM-1001/progress")
    assert response.status_code == 404
    assert response.json() == {"detail": "The agent hasn't worked on CLM-1001 yet."}


def test_approve_and_pay():
    start("CLM-1001")
    decision = decide("CLM-1001")
    assert decision.status_code == 201
    assert decision.json()["needs_sign_off"] is False
    assert status("CLM-1001") == "decided"
    paid = pay("CLM-1001", 420.0)
    assert paid.status_code == 201
    assert paid.json()["amount"] == 420.0
    again = pay("CLM-1001", 420.0)
    assert again.status_code == 409
    assert again.json() == {"detail": "This claim has already been paid."}
    assert (
        client.get("/api/claims/CLM-1001/decision").json()["payment"]["amount"] == 420.0
    )


def test_payment_over_the_limit_waits_for_sign_off():
    start("CLM-1002", "thread-2")
    decide("CLM-1002", payout=1100.0)
    assert status("CLM-1002") == "waiting_for_sign_off"
    blocked = pay("CLM-1002", 1100.0)
    assert blocked.status_code == 409
    assert blocked.json() == {
        "detail": "A payout over $1,000.00 needs a handler's sign-off."
    }
    decision = client.get("/api/claims/CLM-1002/decision").json()
    assert decision["needs_sign_off"] is True
    assert decision["payment"] is None
    assert decision["sign_off"] is None


def test_sign_off_pays_and_decides():
    start("CLM-1002", "thread-2")
    decide("CLM-1002", payout=1100.0)
    response = client.post(
        "/api/claims/CLM-1002/sign-off", json={"handler_id": "HND-01"}
    )
    assert response.status_code == 200
    decision = response.json()
    assert decision["sign_off"]["handler_name"] == "Dana Whitfield"
    assert decision["payment"]["amount"] == 1100.0
    assert status("CLM-1002") == "decided"
    assert client.get("/api/claims").json()[1]["payout"] == 1100.0


def test_sign_off_refusals():
    start("CLM-1001")
    decide("CLM-1001")
    not_waiting = client.post(
        "/api/claims/CLM-1001/sign-off", json={"handler_id": "HND-01"}
    )
    assert not_waiting.status_code == 409
    assert not_waiting.json() == {"detail": "CLM-1001 isn't waiting for sign-off."}
    start("CLM-1002", "thread-2")
    decide("CLM-1002", payout=1100.0)
    unknown = client.post(
        "/api/claims/CLM-1002/sign-off", json={"handler_id": "HND-09"}
    )
    assert unknown.status_code == 404
    assert status("CLM-1002") == "waiting_for_sign_off"


def test_payment_refusals():
    start("CLM-1001")
    decide("CLM-1001")
    wrong = pay("CLM-1001", 500.0)
    assert wrong.status_code == 409
    assert wrong.json() == {
        "detail": "The amount must match the approved payout of $420.00."
    }
    start("CLM-1003", "thread-2")
    decide("CLM-1003", decision="decline", payout=0)
    declined = pay("CLM-1003", 100.0)
    assert declined.status_code == 409
    assert declined.json() == {"detail": "Only an approved claim can be paid."}
    assert pay("CLM-1004", 100.0).status_code == 409
    assert pay("CLM-9999", 100.0).status_code == 404


def test_decision_needs_a_claim_in_progress():
    response = decide("CLM-1001")
    assert response.status_code == 409
    assert response.json() == {
        "detail": "CLM-1001 isn't in progress, so it can't be decided."
    }


@pytest.mark.parametrize(
    ("decision", "payout", "confidence"),
    [
        ("decline", 50.0, 90),
        ("refer", 10.0, 90),
        ("approve", 0, 90),
        ("approve", 420.0, 120),
        ("approve", 420.0, -1),
        ("pay", 420.0, 90),
    ],
)
def test_invalid_decisions(decision, payout, confidence):
    start("CLM-1001")
    assert decide("CLM-1001", decision, payout, confidence).status_code == 422
    assert status("CLM-1001") == "in_progress"


def test_referral_is_decided():
    start("CLM-1001")
    decide("CLM-1001", decision="refer", payout=0)
    assert status("CLM-1001") == "decided"
    summary = client.get("/api/claims").json()[0]
    assert (summary["decision"], summary["payout"]) == ("refer", 0.0)


def test_get_decision_before_a_decision():
    response = client.get("/api/claims/CLM-1001/decision")
    assert response.status_code == 404
    assert response.json() == {"detail": "CLM-1001 has no decision yet."}


def test_finish_without_a_decision_returns_the_claim_to_waiting():
    start("CLM-1001")
    finished = client.post("/api/runs/thread-1/finish")
    assert finished.status_code == 200
    assert finished.json()["finished_at"] is not None
    assert finished.json()["seconds_remaining"] is None
    assert status("CLM-1001") == "waiting"
    assert start("CLM-1001", "thread-2").status_code == 201


def test_finish_after_a_decision_keeps_it():
    start("CLM-1001")
    decide("CLM-1001")
    client.post("/api/runs/thread-1/finish")
    assert status("CLM-1001") == "decided"
    assert start("CLM-1001", "thread-2").status_code == 409


def test_estimate_uses_the_average_of_finished_runs(clock):
    start("CLM-1001", "run-a")
    clock.advance(20)
    client.post("/api/runs/run-a/finish")
    start("CLM-1002", "run-b")
    clock.advance(40)
    client.post("/api/runs/run-b/finish")
    start("CLM-1003", "run-c")
    clock.advance(10)
    assert client.get("/api/claims/CLM-1003/progress").json()["seconds_remaining"] == 20
    clock.advance(60)
    assert client.get("/api/claims/CLM-1003/progress").json()["seconds_remaining"] == 0
    client.post("/api/runs/run-c/finish")
    assert (
        client.get("/api/claims/CLM-1003/progress").json()["seconds_remaining"] is None
    )
