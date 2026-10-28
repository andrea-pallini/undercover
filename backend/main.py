"""The UnderCover backend."""

import json
import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from statistics import fmean
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException

from backend.db import database_path, get_db
from backend.models import (
    Claim,
    ClaimHistory,
    ClaimSummary,
    Decision,
    DecisionIn,
    Handler,
    Payment,
    PaymentIn,
    Policy,
    PolicyWording,
    Progress,
    RunStart,
    SignOff,
    SignOffIn,
    Status,
    Step,
    StepIn,
)
from backend.seed import DATA, seed

DEFAULT_RUN_SECONDS = 30.0


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Build the database from data/ the first time the backend starts."""
    if not database_path().exists():
        seed()
    yield


app = FastAPI(title="UnderCover", lifespan=lifespan)

Db = Annotated[sqlite3.Connection, Depends(get_db)]


def now() -> datetime:
    """Return the current time in UTC."""
    return datetime.now(UTC)


def seconds_between(start: str, end: str) -> float:
    """Return the seconds between two ISO timestamps."""
    return (datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds()


def money(amount: float) -> str:
    """Format an amount in US dollars, such as $1,250.00."""
    return f"${amount:,.2f}"


def one(db: sqlite3.Connection, query: str, key: str) -> sqlite3.Row:
    """Return the row the query finds for the key, or raise 404."""
    row = db.execute(query, (key,)).fetchone()
    if row is None:
        raise HTTPException(404, f"{key} not found.")
    return row


def company(db: sqlite3.Connection) -> dict[str, Any]:
    """Return the company settings."""
    return json.loads(db.execute("SELECT data FROM company").fetchone()["data"])


def approval_limit(db: sqlite3.Connection) -> float:
    """Return the payout above which a handler must sign off."""
    return company(db)["payout_approval_limit"]


def claim_status(db: sqlite3.Connection, claim_id: str) -> Status:
    """Return where a claim stands, or raise 404 if there's no such claim."""
    return one(db, "SELECT status FROM claims WHERE claim_id = ?", claim_id)["status"]


def set_status(db: sqlite3.Connection, claim_id: str, status: Status) -> None:
    """Move a claim to a new status."""
    db.execute("UPDATE claims SET status = ? WHERE claim_id = ?", (status, claim_id))


def seconds_remaining(db: sqlite3.Connection, run: sqlite3.Row) -> int | None:
    """Estimate a run's time left from the average length of finished runs."""
    if run["finished_at"]:
        return None
    finished = db.execute(
        "SELECT started_at, finished_at FROM runs WHERE finished_at IS NOT NULL"
    ).fetchall()
    lengths = [seconds_between(r["started_at"], r["finished_at"]) for r in finished]
    average = fmean(lengths) if lengths else DEFAULT_RUN_SECONDS
    elapsed = seconds_between(run["started_at"], now().isoformat())
    return max(round(average - elapsed), 0)


def progress(db: sqlite3.Connection, thread_id: str) -> Progress:
    """Return a run with its steps and the time it has left."""
    run = one(db, "SELECT * FROM runs WHERE thread_id = ?", thread_id)
    steps = db.execute(
        "SELECT at, description FROM steps WHERE thread_id = ? ORDER BY rowid",
        (thread_id,),
    ).fetchall()
    return Progress(
        thread_id=thread_id,
        claim_id=run["claim_id"],
        started_at=run["started_at"],
        finished_at=run["finished_at"],
        steps=[Step(at=s["at"], description=s["description"]) for s in steps],
        seconds_remaining=seconds_remaining(db, run),
    )


def find_decision(db: sqlite3.Connection, claim_id: str) -> Decision | None:
    """Return the decision on a claim with its sign-off and payment, if it has one."""
    row = db.execute(
        """SELECT d.*, json_extract(h.data, '$.name') AS handler_name,
                  p.amount, p.paid_at
           FROM decisions d
           LEFT JOIN handlers h ON h.handler_id = d.signed_off_by
           LEFT JOIN payments p USING (claim_id)
           WHERE d.claim_id = ?""",
        (claim_id,),
    ).fetchone()
    if row is None:
        return None
    return Decision(
        claim_id=claim_id,
        decision=row["decision"],
        payout=row["payout"],
        reasons=row["reasons"],
        policy_section=row["policy_section"],
        confidence=row["confidence"],
        decided_at=row["decided_at"],
        needs_sign_off=row["payout"] > approval_limit(db),
        sign_off=SignOff(
            handler_id=row["signed_off_by"],
            handler_name=row["handler_name"],
            at=row["signed_off_at"],
        )
        if row["signed_off_by"]
        else None,
        payment=Payment(amount=row["amount"], paid_at=row["paid_at"])
        if row["paid_at"]
        else None,
    )


def pay(db: sqlite3.Connection, claim_id: str, amount: float) -> Payment:
    """Record a payment on a claim."""
    payment = Payment(amount=amount, paid_at=now().isoformat())
    db.execute(
        "INSERT INTO payments VALUES (?, ?, ?)",
        (claim_id, payment.amount, payment.paid_at),
    )
    return payment


@app.get("/api/health", operation_id="health")
def health() -> dict[str, str]:
    """Check that the backend is running."""
    return {"status": "ok"}


@app.get("/api/claims", operation_id="list_claims")
def list_claims(db: Db) -> list[ClaimSummary]:
    """List the claims in the queue with where each one stands."""
    rows = db.execute(
        """SELECT c.data, c.status, json_extract(cu.data, '$.name') AS customer_name,
                  d.decision, d.payout
           FROM claims c
           JOIN customers cu USING (customer_id)
           LEFT JOIN decisions d USING (claim_id)
           ORDER BY c.claim_id"""
    ).fetchall()
    return [
        ClaimSummary.model_validate(
            json.loads(row["data"])
            | {
                "status": row["status"],
                "customer_name": row["customer_name"],
                "decision": row["decision"],
                "payout": row["payout"],
            }
        )
        for row in rows
    ]


@app.get("/api/claims/{claim_id}", operation_id="get_claim")
def get_claim(claim_id: str, db: Db) -> Claim:
    """Get a claim in full: the story, the items claimed and the documents."""
    row = one(db, "SELECT data, status FROM claims WHERE claim_id = ?", claim_id)
    return Claim.model_validate(json.loads(row["data"]) | {"status": row["status"]})


@app.get("/api/policies/{policy_id}", operation_id="get_policy")
def get_policy(policy_id: str, db: Db) -> Policy:
    """Get a policy: the plan, add-ons, purchase date, trip and travelers."""
    row = one(db, "SELECT data FROM policies WHERE policy_id = ?", policy_id)
    return Policy.model_validate_json(row["data"])


@app.get("/api/customers/{customer_id}/history", operation_id="get_claim_history")
def get_claim_history(customer_id: str, db: Db) -> ClaimHistory:
    """Get a customer's name and earlier claims, without their contact details."""
    row = one(db, "SELECT data FROM customers WHERE customer_id = ?", customer_id)
    return ClaimHistory.model_validate_json(row["data"])


@app.get("/api/policy-wording", operation_id="get_policy_wording")
def get_policy_wording(db: Db) -> PolicyWording:
    """Get the policy wording that decisions follow."""
    return PolicyWording(
        version=company(db)["policy_wording_version"],
        text=(DATA / "policy_wording.md").read_text(encoding="utf-8"),
    )


@app.get("/api/handlers", operation_id="list_handlers")
def list_handlers(db: Db) -> list[Handler]:
    """List the claims handlers."""
    rows = db.execute("SELECT data FROM handlers ORDER BY handler_id").fetchall()
    return [Handler.model_validate_json(row["data"]) for row in rows]


@app.post("/api/claims/{claim_id}/runs", operation_id="start_run", status_code=201)
def start_run(claim_id: str, run: RunStart, db: Db) -> Progress:
    """Start the agent's run on a waiting claim, which puts the claim in progress."""
    if claim_status(db, claim_id) != "waiting":
        raise HTTPException(409, f"{claim_id} isn't waiting, so the agent can't start.")
    db.execute(
        "INSERT INTO runs VALUES (?, ?, ?, NULL)",
        (run.thread_id, claim_id, now().isoformat()),
    )
    set_status(db, claim_id, "in_progress")
    return progress(db, run.thread_id)


@app.post("/api/runs/{thread_id}/steps", operation_id="record_step", status_code=201)
def record_step(thread_id: str, step: StepIn, db: Db) -> Step:
    """Add a step to the agent's run, for the team to follow."""
    one(db, "SELECT thread_id FROM runs WHERE thread_id = ?", thread_id)
    recorded = Step(at=now().isoformat(), description=step.description)
    db.execute(
        "INSERT INTO steps VALUES (?, ?, ?)",
        (thread_id, recorded.at, recorded.description),
    )
    return recorded


@app.post("/api/runs/{thread_id}/finish", operation_id="finish_run")
def finish_run(thread_id: str, db: Db) -> Progress:
    """Close the agent's run. A claim it left in progress goes back to waiting."""
    run = one(db, "SELECT claim_id FROM runs WHERE thread_id = ?", thread_id)
    db.execute(
        "UPDATE runs SET finished_at = ? WHERE thread_id = ? AND finished_at IS NULL",
        (now().isoformat(), thread_id),
    )
    db.execute(
        "UPDATE claims SET status = 'waiting' "
        "WHERE claim_id = ? AND status = 'in_progress'",
        (run["claim_id"],),
    )
    return progress(db, thread_id)


@app.get("/api/claims/{claim_id}/progress", operation_id="get_progress")
def get_progress(claim_id: str, db: Db) -> Progress:
    """Get the agent's latest run on a claim, with its steps and time left."""
    claim_status(db, claim_id)
    run = db.execute(
        "SELECT thread_id FROM runs WHERE claim_id = ? ORDER BY rowid DESC LIMIT 1",
        (claim_id,),
    ).fetchone()
    if run is None:
        raise HTTPException(404, f"The agent hasn't worked on {claim_id} yet.")
    return progress(db, run["thread_id"])


@app.post(
    "/api/claims/{claim_id}/decision", operation_id="record_decision", status_code=201
)
def record_decision(claim_id: str, decision: DecisionIn, db: Db) -> Decision:
    """Record the agent's decision on a claim in progress."""
    if claim_status(db, claim_id) != "in_progress":
        raise HTTPException(
            409, f"{claim_id} isn't in progress, so it can't be decided."
        )
    db.execute(
        """INSERT INTO decisions (claim_id, decision, payout, reasons, policy_section,
                                  confidence, decided_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            claim_id,
            decision.decision,
            round(decision.payout, 2),
            decision.reasons,
            decision.policy_section,
            decision.confidence,
            now().isoformat(),
        ),
    )
    over_limit = decision.payout > approval_limit(db)
    set_status(db, claim_id, "waiting_for_sign_off" if over_limit else "decided")
    return get_decision(claim_id, db)


@app.get("/api/claims/{claim_id}/decision", operation_id="get_decision")
def get_decision(claim_id: str, db: Db) -> Decision:
    """Get the decision on a claim, with its sign-off and payment."""
    claim_status(db, claim_id)
    decision = find_decision(db, claim_id)
    if decision is None:
        raise HTTPException(404, f"{claim_id} has no decision yet.")
    return decision


@app.post("/api/claims/{claim_id}/payments", operation_id="pay_claim", status_code=201)
def pay_claim(claim_id: str, payment: PaymentIn, db: Db) -> Payment:
    """Pay an approved claim. A payout over the limit waits for a handler's sign-off."""
    claim_status(db, claim_id)
    decision = find_decision(db, claim_id)
    if decision is None or decision.decision != "approve":
        raise HTTPException(409, "Only an approved claim can be paid.")
    if round(payment.amount, 2) != decision.payout:
        raise HTTPException(
            409,
            f"The amount must match the approved payout of {money(decision.payout)}.",
        )
    if decision.payment:
        raise HTTPException(409, "This claim has already been paid.")
    if decision.needs_sign_off and not decision.sign_off:
        raise HTTPException(
            409,
            f"A payout over {money(approval_limit(db))} needs a handler's sign-off.",
        )
    return pay(db, claim_id, decision.payout)


@app.post("/api/claims/{claim_id}/sign-off", operation_id="sign_off_claim")
def sign_off_claim(claim_id: str, sign_off: SignOffIn, db: Db) -> Decision:
    """Sign off a large payout as a handler, which pays it and decides the claim."""
    if claim_status(db, claim_id) != "waiting_for_sign_off":
        raise HTTPException(409, f"{claim_id} isn't waiting for sign-off.")
    one(db, "SELECT handler_id FROM handlers WHERE handler_id = ?", sign_off.handler_id)
    db.execute(
        "UPDATE decisions SET signed_off_by = ?, signed_off_at = ? WHERE claim_id = ?",
        (sign_off.handler_id, now().isoformat(), claim_id),
    )
    pay(db, claim_id, get_decision(claim_id, db).payout)
    set_status(db, claim_id, "decided")
    return get_decision(claim_id, db)
