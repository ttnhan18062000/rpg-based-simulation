---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260930-DONE-CHECKER-PROOF-PLAN-ADVISORY
artifact_type: plan
tags: [testing]
---

# Plan

1. New `tools/gate_checks/proof_plan_advisory.py`: `check_proof_plan_fields(ticket_id, tier)` -> `(OK|WARN|NA, evidence)`; reads staging then stored `test_plan.md`; table and `### AC<n>` block layouts; empty cell = missing; `oracle: unresolved` counts as filled; a one-line "no testable acceptance criterion" statement is OK; never raises.
2. `done_checker_static.py`: `run_advisory_checks()` separate from `run_static_precheck()` (no new status value for existing consumers); CLI prints `[advisory]` lines that never affect `RESULT:` or the exit code.
3. `.claude/agents/done-checker.md` Step 0c and `docs/guides/delivery_process.md` document it as report-only.
4. `MANDATORY_FIELDS` is one list, pinned by a test against `investigator.md`'s `## Proof Plan` prose.
