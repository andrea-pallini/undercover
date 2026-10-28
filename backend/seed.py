"""Build the database from UnderCover's records in data/: uv run -m backend.seed"""

import json
from pathlib import Path

from backend.db import SCHEMA, connect

DATA = Path(__file__).parent.parent / "data"


def load(name: str) -> list[dict[str, object]]:
    """Load a JSON file from data/."""
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def seed() -> dict[str, int]:
    """Rebuild the database from data/ and return how many records it loaded."""
    claims = load("claims.json")
    policies = load("policies.json")
    customers = load("customers.json")
    handlers = load("handlers.json")
    company = (DATA / "company.json").read_text(encoding="utf-8")
    with connect() as db:
        db.executescript(SCHEMA)
        db.execute("INSERT INTO company VALUES (?)", (company,))
        db.executemany(
            "INSERT INTO claims VALUES (?, ?, 'waiting', ?)",
            [(c["claim_id"], c["customer_id"], json.dumps(c)) for c in claims],
        )
        db.executemany(
            "INSERT INTO policies VALUES (?, ?)",
            [(p["policy_id"], json.dumps(p)) for p in policies],
        )
        db.executemany(
            "INSERT INTO customers VALUES (?, ?)",
            [(c["customer_id"], json.dumps(c)) for c in customers],
        )
        db.executemany(
            "INSERT INTO handlers VALUES (?, ?)",
            [(h["handler_id"], json.dumps(h)) for h in handlers],
        )
    return {
        "claims": len(claims),
        "policies": len(policies),
        "customers": len(customers),
        "handlers": len(handlers),
    }


if __name__ == "__main__":
    counts = seed()
    print("Loaded " + ", ".join(f"{n} {name}" for name, n in counts.items()))
