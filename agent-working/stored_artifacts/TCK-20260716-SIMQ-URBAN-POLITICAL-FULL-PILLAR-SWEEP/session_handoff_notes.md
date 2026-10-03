---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP
artifact_type: investigation
tags: [simulation-quality, calibration, determinism, corpus]
---

# Session Handoff Notes — TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP

Not a mandatory pipeline artifact. Two directly-verified environment facts, kept deliberately
narrow to avoid asserting anything not checked firsthand this session. Safe to delete once read.

- **Use `.venv/bin/python3`, not bare `python3`, for pytest/calibration commands in this repo.**
  Bare `python3` lacks `pydantic` and fails immediately. Not documented elsewhere (checked
  `CLAUDE.md` and `docs/`) — confirmed by hitting this directly, more than once, this session.
- **`data/calibration/` is gitignored/ephemeral but not covered by the standard workflow's
  automated cleanup** (`clean_data_runs_early` only targets `data/runs/` and
  `reports/release_proof/`). Leftovers here caused a Verify-phase repo-state-consistency
  failure twice this session — clean it manually (`rm -rf data/calibration/*`) after any
  manual calibration regen.

Everything else about how to run this ticket — methodology, prior findings, exact code
locations — is already in the ticket body and its Related Stored Artifacts; that content was
written for durability and should be trusted over anything not stated there.
