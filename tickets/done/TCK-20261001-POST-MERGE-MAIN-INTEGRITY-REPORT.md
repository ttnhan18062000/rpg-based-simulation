---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261001-POST-MERGE-MAIN-INTEGRITY-REPORT
phase: done
date: 2026-10-01
tags: [agent-monitoring, data-quality]
---

# TCK-20261001-POST-MERGE-MAIN-INTEGRITY-REPORT

## Title
Report-only integrity check of origin/main after a merge (rows, shards, tracked evidence)

## Status
DONE

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
New `tools/agent-monitoring/main_integrity_report.py` and `make agent-monitoring-main-integrity`. All reads go through one resolved SHA (`git ls-tree` + `git show`); a `RefReader` never opens the working tree. Duplicate-run and event-seq checks reuse `check_duplicate_run_records(runs=...)` and `find_seq_duplicates_and_gaps(events=...)` by passing the ref's rows. Added `--since-date` (not in the ticket) because the unfiltered corpus is dominated by pre-September tickets. Cited paths containing `...`, `*` or `<>` are treated as placeholders and skipped. On demand only, per the ticket's open question; no hook. Review fixes (design peer review of PR #274): the first version counted every working-log row and flagged 52 legitimate tickets (BLOCKED progress rows, post-merge fix rounds under the same id). The check now means: at least one DONE row and no identical (title, status, summary) duplicate; cited-evidence strips a trailing `:LINE` and skips directory citations; each false-positive shape has a positive-control test. Real-corpus reading of origin/main @ 71c4aa321 (snapshot, not final), `--since-date 20260901`: 135 findings = working_log 15 (identical duplicate rows or no DONE row; a few are epics with no row), shards 0, cited_evidence 1 (TCK-20260907-FILTERED-REPLAY-EVAL-PILOT cites a pilot_run_raw_output.json that never reached main, the gitignore trap), duplicate_runs 0, event_seq 119 (historical and NOT examined; event_seq has no date filter). Findings are reported, not repaired.
Draft by agent-working-design; the implementer commits it.

## Test Summary
5 tests in tests/tools/test_main_integrity_report.py: clean ref reports nothing and is SHA-labelled (AC2); one planted defect per check, each named by ticket or path (AC1); a dirty working tree (deleted tracked file, edited CSV, untracked ticket and shard) leaves a clean-ref report unchanged (AC3); exit 0 by default and 1 only with --strict; --since-date filter. All pass.
Not started.

## Files Changed
- `tools/agent-monitoring/main_integrity_report.py`, `Makefile`
- `tests/tools/test_main_integrity_report.py`
- `docs/agent-monitoring/README.md`, `docs/plans/agent_infrastructure/agent_working_direction.md`
None yet.

## Completion Summary
A report-only, ref-based integrity check exists and already surfaces real findings on origin/main.
Not started.
