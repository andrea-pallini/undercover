"""The UnderCover database, in SQLite."""

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

SCHEMA = """
DROP TABLE IF EXISTS company;
DROP TABLE IF EXISTS claims;
DROP TABLE IF EXISTS policies;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS handlers;
DROP TABLE IF EXISTS runs;
DROP TABLE IF EXISTS steps;
DROP TABLE IF EXISTS decisions;
DROP TABLE IF EXISTS payments;

CREATE TABLE company (data TEXT NOT NULL);
CREATE TABLE claims (
    claim_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    status TEXT NOT NULL,
    data TEXT NOT NULL
);
CREATE TABLE policies (policy_id TEXT PRIMARY KEY, data TEXT NOT NULL);
CREATE TABLE customers (customer_id TEXT PRIMARY KEY, data TEXT NOT NULL);
CREATE TABLE handlers (handler_id TEXT PRIMARY KEY, data TEXT NOT NULL);
CREATE TABLE runs (
    thread_id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT
);
CREATE TABLE steps (
    thread_id TEXT NOT NULL,
    at TEXT NOT NULL,
    description TEXT NOT NULL
);
CREATE TABLE decisions (
    claim_id TEXT PRIMARY KEY,
    decision TEXT NOT NULL,
    payout REAL NOT NULL,
    reasons TEXT NOT NULL,
    policy_section TEXT NOT NULL,
    confidence INTEGER NOT NULL,
    decided_at TEXT NOT NULL,
    signed_off_by TEXT,
    signed_off_at TEXT
);
CREATE TABLE payments (
    claim_id TEXT PRIMARY KEY,
    amount REAL NOT NULL,
    paid_at TEXT NOT NULL
);
"""


def database_path() -> Path:
    """Return the database file, from DATABASE_PATH or undercover.db by default."""
    return Path(os.getenv("DATABASE_PATH", "undercover.db"))


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    """Open the database in a transaction that commits on success."""
    connection = sqlite3.connect(database_path(), check_same_thread=False)
    connection.row_factory = sqlite3.Row
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def get_db() -> Iterator[sqlite3.Connection]:
    """Give a route its own connection to the database."""
    with connect() as connection:
        yield connection
