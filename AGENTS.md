# CIVP Contributor Guide

- This is a portfolio project the owner must understand and defend in interviews.
- Work only on the step the owner explicitly names. Read `docs/PLAN.md` for context but never build ahead.
- Test the statistical engine before building API routes, frontend, deployment, or UI.
- Never edit, weaken, skip, or delete a test merely to make it pass. If a test fails, report why.
- Do not add dependencies outside `docs/PLAN.md` without asking.
- Never fabricate metrics, dataset results, citations, or causal conclusions.
- Do not start real CPCB/Odd-Even modeling until synthetic validation is complete.
- Tests must be deterministic and use fixed seeds.
- Keep `backend/causal_engine` independent of API routes and frontend code.
- After each implementation step, explain every statistical choice in plain language.
- After each implementation step, give five questions the owner should be able to answer.
- Prefer simple, readable code. Comment statistical intent, not obvious syntax.
- Never say diagnostics prove causality.
- Use phrases such as “consistent with,” “raises concern,” “insufficient evidence,” and “cannot establish causality.”
- A non-significant pre-trend test does not prove parallel trends.
- Every verdict, including “Credible,” must display a methodological caveat.
