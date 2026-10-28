# Status

The pilot is being built from `docs/PLAN.md`. Phase 1 of 6 is done.

## Built

- `backend/`: FastAPI on SQLite. On first start it builds `undercover.db` from `data/` (never `data/evals/`). It serves the queue, each claim, its policy, the customer's claim history (without contact details), the policy wording and the handlers.
- `agent/`: still the hello-world skeleton, `run(claim_id, thread_id)` with one tool that calls the health route
- `dashboard/`: still one page that shows whether the backend is up
- `e2e/`: one test of that page

## Running it

- `npm run dev` starts the backend on port 8000 and the dashboard on port 5173
- `npm run reset` rebuilds `undercover.db` from `data/`
- `npm run check` runs every check
