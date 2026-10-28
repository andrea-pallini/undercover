# Status

The pilot is being built from `docs/PLAN.md`. Phases 1 to 3 of 6 are done.

## Built

- `backend/`: FastAPI on SQLite. On first start it builds `undercover.db` from `data/` (never `data/evals/`).
  - Records: the queue, each claim, its policy, the customer's claim history (without contact details), the policy wording and the handlers.
  - Workflow: the agent's runs and their steps, with an estimate of the time left; decisions; payments; and handlers' sign-off.
  - The pay operation refuses a payout over $1,000.00 (the limit in `data/company.json`) until a handler signs off, whoever calls it.
  - The agent's instructions are in `backend/instructions.md`, served by `GET /api/instructions`.
  - `POST /api/claims/{claim_id}/agent` starts the agent on a waiting claim in the background.
- `agent/`: the UnderCover Agent. `run(claim_id, thread_id)` fetches its instructions, works the claim with six tools over the backend's API (read the claim, policy, claim history and wording; record the decision; pay), and records each step and refusal for the team.
- `dashboard/`: still one page that shows whether the backend is up
- `e2e/`: one test of that page

A claim is `waiting`, `in_progress`, `waiting_for_sign_off` or `decided`. A run that ends without a decision puts its claim back to `waiting`.

## Running it

- `npm run dev` starts the backend on port 8000 and the dashboard on port 5173
- `npm run agent` works every waiting claim in turn, and `npm run agent -- CLM-1001` works one claim. The backend must be running. It uses the model in `MODEL_NAME`, or `openai/gpt-6-luna`.
- `npm run reset` rebuilds `undercover.db` from `data/`
- `npm run check` runs every check
