"""The shapes of the API's requests and responses."""

from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator

Status = Literal["waiting", "in_progress", "waiting_for_sign_off", "decided"]
DecisionKind = Literal["approve", "decline", "refer"]


class Item(BaseModel):
    description: str
    category: str
    amount: float


class Document(BaseModel):
    name: str
    type: str
    content: str


class Claim(BaseModel):
    claim_id: str
    policy_id: str
    customer_id: str
    claim_type: str
    submitted_on: str
    incident_date: str
    incident_location: str
    summary: str
    story: str
    items: list[Item]
    amount_claimed: float
    documents: list[Document]
    status: Status


class ClaimSummary(BaseModel):
    claim_id: str
    customer_name: str
    claim_type: str
    summary: str
    amount_claimed: float
    submitted_on: str
    status: Status
    decision: DecisionKind | None
    payout: float | None


class Trip(BaseModel):
    destination: str
    departs_on: str
    returns_on: str
    trip_cost: float


class Policy(BaseModel):
    policy_id: str
    customer_id: str
    plan: str
    add_ons: list[str]
    purchased_on: str
    sold_through: str
    trip: Trip
    travelers: list[str]
    status: str


class PreviousClaim(BaseModel):
    claim_id: str
    filed_on: str
    incident_date: str
    claim_type: str
    summary: str
    outcome: str
    amount_paid: float


class ClaimHistory(BaseModel):
    customer_id: str
    name: str
    customer_since: str
    previous_claims: list[PreviousClaim]


class PolicyWording(BaseModel):
    version: str
    text: str


class Handler(BaseModel):
    handler_id: str
    name: str
    role: str
    email: str
    can_approve_over_limit: bool


class RunStart(BaseModel):
    thread_id: str


class StepIn(BaseModel):
    description: str


class Step(BaseModel):
    at: str
    description: str


class Progress(BaseModel):
    thread_id: str
    claim_id: str
    started_at: str
    finished_at: str | None
    steps: list[Step]
    seconds_remaining: int | None


class DecisionIn(BaseModel):
    decision: DecisionKind
    payout: float = Field(ge=0)
    reasons: str
    policy_section: str
    confidence: int = Field(ge=0, le=100)

    @model_validator(mode="after")
    def payout_fits_decision(self) -> Self:
        if (self.decision == "approve") != (self.payout > 0):
            raise ValueError(
                "An approval needs a payout above zero, "
                "and a decline or referral a payout of zero."
            )
        return self


class SignOff(BaseModel):
    handler_id: str
    handler_name: str
    at: str


class Payment(BaseModel):
    amount: float
    paid_at: str


class Decision(BaseModel):
    claim_id: str
    decision: DecisionKind
    payout: float
    reasons: str
    policy_section: str
    confidence: int
    decided_at: str
    needs_sign_off: bool
    sign_off: SignOff | None
    payment: Payment | None


class PaymentIn(BaseModel):
    amount: float


class SignOffIn(BaseModel):
    handler_id: str
