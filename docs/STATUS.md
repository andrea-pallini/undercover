# Status

The pilot is being built from `docs/PLAN.md`. Phases 1 to 4 of 6 are done.

## Built

- `backend/`: FastAPI on SQLite. On first start it builds `undercover.db` from `data/` (never `data/evals/`).
  - Records: the queue, each claim, its policy, the customer's claim history (without contact details), the policy wording and the handlers.
  - Workflow: the agent's runs and their steps, with an estimate of the time left; decisions; payments; and handlers' sign-off.
  - The pay operation refuses a payout over $1,000.00 (the limit in `data/company.json`) until a handler signs off, whoever calls it.
  - The agent's instructions are in `backend/instructions.md`, served by `GET /api/instructions`.
  - `POST /api/claims/{claim_id}/agent` starts the agent on a waiting claim in the background.
- `agent/`: the UnderCover Agent. `run(claim_id, thread_id)` fetches its instructions, works the claim with six tools over the backend's API (read the claim, policy, claim history and wording; record the decision; pay), and records each step and refusal for the team.
- `dashboard/`: React in the UnderCover brand, in light and dark mode, chosen by the address with no routing library:
  - `#/`: the claims queue, with a count of claims in each status. It refreshes every 5 seconds.
  - `#/claims/CLM-1001`: the claim in full, its policy and the customer's earlier claims. It refreshes every 2 seconds.
  - `#/instructions`: the agent's instructions, read only
- `e2e/`: Playwright tests of the queue, a claim and the instructions. They start their own backend on port 8001, with a fresh `e2e/undercover.db`, and their own dashboard on port 5174, so they never touch the dev database.

A claim is `waiting`, `in_progress`, `waiting_for_sign_off` or `decided`. A run that ends without a decision puts its claim back to `waiting`.

## Running it

- `npm run dev` starts the backend on port 8000 and the dashboard on port 5173
- `npm run agent` works every waiting claim in turn, and `npm run agent -- CLM-1001` works one claim. The backend must be running. It uses the model in `MODEL_NAME`, or `openai/gpt-6-luna`.
- `npm run reset` rebuilds `undercover.db` from `data/`
- `npm run check` runs every check
