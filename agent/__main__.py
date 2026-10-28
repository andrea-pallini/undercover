"""Run the UnderCover Agent: uv run -m agent [CLAIM_ID ...]"""

import sys
from uuid import uuid4

from agent.main import call, run


def main(claim_ids: list[str]) -> None:
    """Decide the claims named, or every waiting claim in the queue in turn."""
    if not claim_ids:
        queue = call("GET", "/api/claims").raise_for_status().json()
        claim_ids = [c["claim_id"] for c in queue if c["status"] == "waiting"]
    for claim_id in claim_ids:
        print(f"{claim_id}: {run(claim_id, str(uuid4()))}")


if __name__ == "__main__":
    main(sys.argv[1:])
