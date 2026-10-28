import pytest
from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, ToolMessage

from agent import main
from backend.main import app

client = TestClient(app)


class StubModel(GenericFakeChatModel):
    """A chat model that gives scripted replies in place of a real model."""

    def bind_tools(self, tools, **kwargs):
        return self


@pytest.fixture(autouse=True)
def local_backend(monkeypatch):
    monkeypatch.setattr(main, "backend", lambda: TestClient(app))


def calls(*tool_calls):
    return AIMessage(
        content="",
        tool_calls=[
            {"name": name, "args": args, "id": str(i)}
            for i, (name, args) in enumerate(tool_calls)
        ],
    )


def decision(claim_id, payout):
    return {
        "claim_id": claim_id,
        "decision": "approve",
        "payout": payout,
        "reasons": "The claim is covered.",
        "policy_section": "3. Trip Delay",
        "confidence": 85,
    }


def script(claim_id, policy_id, customer_id, payout):
    return [
        calls(("get_claim", {"claim_id": claim_id})),
        calls(
            ("get_policy", {"policy_id": policy_id}),
            ("get_claim_history", {"customer_id": customer_id}),
            ("get_policy_wording", {}),
        ),
        calls(("record_decision", decision(claim_id, payout))),
        calls(("pay_claim", {"claim_id": claim_id, "amount": payout})),
        AIMessage(content=f"Approved {claim_id}."),
    ]


def descriptions(claim_id):
    progress = client.get(f"/api/claims/{claim_id}/progress").json()
    return [step["description"] for step in progress["steps"]]


def test_the_agent_has_only_its_six_tools():
    assert [t.name for t in main.TOOLS] == [
        "get_claim",
        "get_policy",
        "get_claim_history",
        "get_policy_wording",
        "record_decision",
        "pay_claim",
    ]


def test_tools_read_through_the_api():
    assert "Maya Patel" in main.get_claim_history.invoke({"customer_id": "CUS-3001"})
    assert "2026.1" in main.get_policy_wording.invoke({})
    assert main.get_claim.invoke({"claim_id": "CLM-9999"}) == (
        "Refused: CLM-9999 not found."
    )


def test_run_approves_and_pays():
    replies = script("CLM-1001", "POL-2001", "CUS-3001", 420.0)
    reply = main.run("CLM-1001", "thread-1", StubModel(messages=iter(replies)))
    assert reply == "Approved CLM-1001."
    claim_decision = client.get("/api/claims/CLM-1001/decision").json()
    assert claim_decision["decision"] == "approve"
    assert claim_decision["confidence"] == 85
    assert claim_decision["payment"]["amount"] == 420.0
    assert client.get("/api/claims/CLM-1001").json()["status"] == "decided"
    assert descriptions("CLM-1001") == [
        "Reading claim CLM-1001",
        "Reading policy POL-2001",
        "Reading the customer's claim history",
        "Reading the policy wording",
        "Recording the decision: approve, $420.00",
        "Paying $420.00",
    ]
    progress = client.get("/api/claims/CLM-1001/progress").json()
    assert progress["finished_at"] is not None


def test_run_over_the_limit_waits_for_sign_off():
    replies = script("CLM-1002", "POL-2002", "CUS-3002", 1100.0)
    main.run("CLM-1002", "thread-2", StubModel(messages=iter(replies)))
    assert client.get("/api/claims/CLM-1002").json()["status"] == "waiting_for_sign_off"
    assert client.get("/api/claims/CLM-1002/decision").json()["payment"] is None
    assert descriptions("CLM-1002")[-2:] == [
        "Paying $1,100.00",
        "Payment blocked: A payout over $1,000.00 needs a handler's sign-off.",
    ]


def failing_replies():
    yield calls(("get_claim", {"claim_id": "CLM-1001"}))
    raise RuntimeError("The model is down")


def test_failed_run_puts_the_claim_back():
    with pytest.raises(RuntimeError, match="The model is down"):
        main.run("CLM-1001", "thread-3", StubModel(messages=failing_replies()))
    assert client.get("/api/claims/CLM-1001").json()["status"] == "waiting"
    progress = client.get("/api/claims/CLM-1001/progress").json()
    assert progress["finished_at"] is not None
    assert descriptions("CLM-1001") == ["Reading claim CLM-1001"]


def test_describe_falls_back_to_the_tool_name():
    assert main.describe({"name": "pay_claim", "args": {}, "id": "1"}) == (
        "Calling pay_claim"
    )
    assert main.describe(
        {"name": "pay_claim", "args": {"amount": "lots"}, "id": "1"}
    ) == ("Calling pay_claim")


def test_steps_show_refusals():
    refused = ToolMessage(
        "Refused: CLM-9999 not found.", tool_call_id="1", name="get_claim"
    )
    assert main.steps(refused) == ["Refused: CLM-9999 not found."]
    assert main.steps(ToolMessage("{}", tool_call_id="1", name="get_claim")) == []


def test_model_name(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.delenv("MODEL_NAME", raising=False)
    assert main.model().model_name == "openai/gpt-6-luna"
    monkeypatch.setenv("MODEL_NAME", "openrouter/free")
    assert main.model().model_name == "openrouter/free"
