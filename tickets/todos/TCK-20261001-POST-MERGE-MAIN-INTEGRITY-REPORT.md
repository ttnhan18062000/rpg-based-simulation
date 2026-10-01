---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261001-POST-MERGE-MAIN-INTEGRITY-REPORT
phase: open
date: 2026-10-01
tags: [agent-monitoring, data-quality]
---

# TCK-20261001-POST-MERGE-MAIN-INTEGRITY-REPORT

## Title
Report-only integrity check of origin/main after a merge (rows, shards, tracked evidence)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Three problems in two weeks were found late and by hand: working-log rows moved into another checkout's CSV, evidence written as `.json` that never reached the remote, and live-shard tests that changed with the branch. Per-ticket checks cannot see these. Add one command that reads a git ref (not the working tree) and reports them.

## Scope
1. `make agent-monitoring-main-integrity REF=origin/main`, reading via `git ls-tree`/`git show` like `delivery_cost_measurement.py --ref`, with the output labelled as a snapshot of that ref and SHA.
2. Checks: every closed ticket has exactly one working-log row; no leftover per-batch shard for a closed week; every `stored_artifacts/` path cited by a closed ticket exists at the ref; duplicate-run and event-seq anomalies (reuse `duplicate_run_record_check.py` and `event_seq_integrity_check.py`).
3. Report-only: prints findings, exit code 0 by default, with an opt-in `--strict` for local use.

## Out of Scope
- Any blocking CI job.
- Repairing what it finds.
- A per-ticket check (the done-checker owns those).

## Acceptance Criteria
1. On a fixture ref with one planted defect per check, each defect is reported with its path or ticket.
2. On a clean fixture ref the report is empty.
3. The tool never reads the working tree; a test with a dirty working tree and clean ref proves it.

## Related Tickets
- TCK-20260928-WORKING-LOG-CONSOLIDATION-CROSS-CHECKOUT-ROW-LOSS (done; the incident)
- TCK-20260930-CITED-EVIDENCE-PATH-GITIGNORE-CHECK (done; the per-ticket analogue)
- TCK-20260924-DELIVERY-COST-MEASUREMENT (done; the ref-reading pattern)

## Related Docs
- `docs/plans/agent_infrastructure/agent_working_direction.md` (update the matching row's status in this ticket's own batch)

## Related Stored Artifacts
None.

## Related Code Areas
- `tools/agent-monitoring/` (new module), `tools/gate_checks/duplicate_run_record_check.py`, `tools/gate_checks/event_seq_integrity_check.py`, `Makefile`

## Assumptions / Open Questions
- Open: whether to run it from the post-merge hook, or only on demand; start on demand.

## Implementation Notes
Draft by agent-working-design; the implementer commits it.

## Test Summary
Not started.

## Files Changed
None yet.

## Completion Summary
Not started.
