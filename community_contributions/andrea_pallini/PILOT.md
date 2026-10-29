# Week 1 Day 3: Pilot page

## What we built

The UnderCover pilot, planned in `docs/PLAN.md` and built in six committed phases:

- **Backend:** FastAPI on SQLite, seeded from `data/`. It records claims, decisions, payments and the agent's steps, and refuses payouts over $1,000 until a handler signs off.
- **Agent:** six tools to read a claim, decide it with reasons, policy section and a 0–100 confidence, then pay.
- **Dashboard:** the claims queue, each claim with the agent's live steps and time remaining, a sign-off form, and the agent's instructions.
- **Checks:** 46 Python, 29 TypeScript and 8 Playwright tests, all passing.

## Live runs (`openai/gpt-6-luna`)

- CLM-1001: approved $420, paid.
- CLM-1003: approved $3,750, blocked, then signed off and paid.
- CLM-1004: approved $74 at 84% confidence.

## My comments

-

-

-
