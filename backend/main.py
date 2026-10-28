"""The UnderCover backend."""

import json
import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException

from backend.db import database_path, get_db
from backend.models import (
    Claim,
    ClaimHistory,
    ClaimSummary,
    Handler,
    Policy,
    PolicyWording,
)
from backend.seed import DATA, seed


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Build the database from data/ the first time the backend starts."""
    if not database_path().exists():
        seed()
    yield


app = FastAPI(title="UnderCover", lifespan=lifespan)

Db = Annotated[sqlite3.Connection, Depends(get_db)]


def one(db: sqlite3.Connection, query: str, key: str) -> sqlite3.Row:
    """Return the row the query finds for the key, or raise 404."""
    row = db.execute(query, (key,)).fetchone()
    if row is None:
        raise HTTPException(404, f"{key} not found.")
    return row


def company(db: sqlite3.Connection) -> dict[str, Any]:
    """Return the company settings."""
    return json.loads(db.execute("SELECT data FROM company").fetchone()["data"])


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
