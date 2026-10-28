"""The UnderCover Agent, which decides claims through the backend's API."""

import os
from typing import Literal

import httpx
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AnyMessage, ToolCall, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, SecretStr

load_dotenv(override=True)

BACKEND_URL = "http://localhost:8000"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-6-luna"
REFUSED = "Refused: "
STEPS = {
    "get_claim": "Reading claim {claim_id}",
    "get_policy": "Reading policy {policy_id}",
    "get_claim_history": "Reading the customer's claim history",
    "get_policy_wording": "Reading the policy wording",
    "record_decision": "Recording the decision: {decision}, ${payout:,.2f}",
    "pay_claim": "Paying ${amount:,.2f}",
}


def backend() -> httpx.Client:
    """Return a client for the UnderCover backend."""
    return httpx.Client(base_url=BACKEND_URL, timeout=30)


def call(
    method: str, path: str, body: dict[str, object] | None = None
) -> httpx.Response:
    """Call an operation on the backend's API."""
    with backend() as client:
        return client.request(method, path, json=body)


def answer(response: httpx.Response) -> str:
    """Return the backend's answer, or its reason for refusing, for the model."""
    if response.is_success:
        return response.text
    return REFUSED + str(response.json()["detail"])


class DecisionArgs(BaseModel):
    claim_id: str
    decision: Literal["approve", "decline", "refer"]
    payout: float = Field(
        description="The payout in US dollars, or 0 unless you approve"
    )
    reasons: str = Field(description="Two or three sentences explaining the decision")
    policy_section: str = Field(
        description="The section of the wording, such as 3. Trip Delay"
    )
    confidence: int = Field(
        description="How sure you are the decision is right, 0 to 100"
    )


@tool
def get_claim(claim_id: str) -> str:
    """Read a claim in full: the story, the items claimed and the documents."""
    return answer(call("GET", f"/api/claims/{claim_id}"))


@tool
def get_policy(policy_id: str) -> str:
    """Read a policy: the plan, add-ons, purchase date, trip and travelers."""
    return answer(call("GET", f"/api/policies/{policy_id}"))


@tool
def get_claim_history(customer_id: str) -> str:
    """Read a customer's earlier claims."""
    return answer(call("GET", f"/api/customers/{customer_id}/history"))


@tool
def get_policy_wording() -> str:
    """Read the policy wording, which every decision follows."""
    return answer(call("GET", "/api/policy-wording"))


@tool(args_schema=DecisionArgs)
def record_decision(claim_id: str, **decision: object) -> str:
    """Record your decision on a claim, once you have decided."""
    return answer(call("POST", f"/api/claims/{claim_id}/decision", decision))


@tool
def pay_claim(claim_id: str, amount: float) -> str:
    """Pay an approved claim its payout."""
    return answer(call("POST", f"/api/claims/{claim_id}/payments", {"amount": amount}))


TOOLS = [
    get_claim,
    get_policy,
    get_claim_history,
    get_policy_wording,
    record_decision,
    pay_claim,
]


def model() -> ChatOpenAI:
    """Return the model named in MODEL_NAME, or GPT-6 Luna by default."""
    name = os.getenv("MODEL_NAME")
    return ChatOpenAI(
        model=name or DEFAULT_MODEL,
        base_url=OPENROUTER_BASE_URL,
        api_key=SecretStr(os.environ["OPENROUTER_API_KEY"]),
        reasoning_effort=None if name else "low",
    )


def describe(tool_call: ToolCall) -> str:
    """Describe a tool call in plain English for the team."""
    try:
        return STEPS[tool_call["name"]].format(**tool_call["args"])
    except (KeyError, ValueError):
        return f"Calling {tool_call['name']}"


def steps(message: AnyMessage) -> list[str]:
    """Return the steps a message from the agent shows the team."""
    if isinstance(message, AIMessage):
        return [describe(tool_call) for tool_call in message.tool_calls]
    if isinstance(message, ToolMessage) and message.text.startswith(REFUSED):
        reason = message.text.removeprefix(REFUSED)
        blocked = "Payment blocked" if message.name == "pay_claim" else "Refused"
        return [f"{blocked}: {reason}"]
    return []


def run(claim_id: str, thread_id: str, llm: BaseChatModel | None = None) -> str:
    """Decide one claim, recording each step, and return the agent's final reply."""
    instructions = call("GET", "/api/instructions").raise_for_status().json()["text"]
    agent = create_agent(llm or model(), tools=TOOLS, system_prompt=instructions)
    call(
        "POST", f"/api/claims/{claim_id}/runs", {"thread_id": thread_id}
    ).raise_for_status()
    reply = ""
    try:
        for update in agent.stream(
            {"messages": [{"role": "user", "content": f"Claim {claim_id}"}]},
            config={"configurable": {"thread_id": thread_id}},
            stream_mode="updates",
        ):
            for node in update.values():
                for message in node["messages"]:
                    for step in steps(message):
                        call(
                            "POST",
                            f"/api/runs/{thread_id}/steps",
                            {"description": step},
                        )
                    reply = message.text
    finally:
        call("POST", f"/api/runs/{thread_id}/finish")
    return reply
