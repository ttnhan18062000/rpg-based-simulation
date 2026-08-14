---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT
phase: done
date: 2026-07-08
tags: [agent-monitoring, data-quality, schema]
---

# TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT

## Title
Enforce agent-monitoring schema at write time — non-null required fields + canonical phase/agent vocabulary warning + drift report

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Implements `docs/plans/agent_infrastructure/idea_agent_monitoring_schema_enforcement.md` in full. Live analysis (2026-07-04) found 21% of runs (98/466) with `workflow: null`, 8+ distinct casings of `phase` values for the same concept, 39 free-text `agent` values against 11 canonical subagent names, and `epic-batch`/`epic_batch` tier duplication. `record_run.py`/`record_events.py` already validate that required keys are *present* but not that they're non-null or drawn from a canonical vocabulary. This ticket closes that gap for future writes only — per the idea doc's explicit decision, the 98 historical drifted records are not backfilled or rewritten.

## Scope
- Add non-null enforcement to `REQUIRED` field validation in `record_run.py` and `record_events.py` (a `None` value fails the same way a missing key does)
- Add a per-workflow canonical vocabulary check for `phase` and `agent`, warn-only (stderr), not reject — new legitimate phases/agents must not be blocked
- Add a drift-report summary section to `tools/agent-monitoring/validate.py`: count of null-required-field records, frequency table of non-canonical `phase`/`agent`/`tier` values
- Decide and document where the canonical phase/agent sets live (single source of truth — `docs/agent-monitoring/schema.md` vs. a JSON/YAML sidecar both docs and validators read) per the idea doc's own Open Question

## Out of Scope
- Backfilling or rewriting the 98 historical drifted records (explicit decision already made when the idea was raised)
- Escalating the vocabulary check from warn to reject (idea doc's own Open Question leaves this open pending more data; the hard rule "monitoring write failure must never fail the workflow" argues against it for now)
- Any change to `implement-ticket.js`/`create-tickets.js` phase-calling code itself — this ticket only touches the validation/reporting layer

## Acceptance Criteria
- A record with `"workflow": null` (or any other `REQUIRED` key set to `None`) fails write-time validation identically to a missing key
- A `phase` or `agent` value outside the canonical set for its `workflow` prints a `WARNING: unrecognized ... (did you mean ...)` at write time and still writes successfully
- `make agent-monitoring-validate` output includes a drift-report section with counts/frequency tables as specified above
- Canonical phase/agent vocabulary source is documented as single-sourced (no duplicate copy between docs and code)
- Tests cover: null-required-field rejection, vocabulary warning (both hit and miss cases), drift-report counts against a fixture file with known-drifted records

## Related Tickets
Parent: TCK-20260708-AGENT-INFRA-HARDENING-EPIC. Related: TCK-20260704-CREATE-TICKETS-MONITORING (found the create-tickets coverage gap this idea grew out of).

## Related Docs
docs/plans/agent_infrastructure/idea_agent_monitoring_schema_enforcement.md, docs/agent-monitoring/schema.md, docs/agent-monitoring/README.md, docs/guides/agent_monitoring.md

## Related Stored Artifacts
none yet

## Related Code Areas
tools/agent-monitoring/record_run.py, tools/agent-monitoring/record_events.py, tools/agent-monitoring/validate.py

## Assumptions / Open Questions
- Assumes no current caller intentionally passes `null` for a `REQUIRED` field as a legitimate "genuinely unknown" value — Investigate phase must confirm by scanning current call sites before landing the non-null check.
- Per-workflow vocabulary scoping (vs. one global set) is assumed correct per the idea doc's reasoning; confirm against actual workflow count before committing to the data structure.

## Implementation Notes

Implemented per `staging_artifacts/TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT/plan.md`'s 7 steps.

1. **`tools/agent-monitoring/record_run.py`** — extracted `validate_record(record) -> list[str]`; a
   `REQUIRED` field counts as missing if absent OR `record[field] is None`. Error message format
   (`Missing required fields: [...]`) unchanged.
2. **`tools/agent-monitoring/record_events.py`** — same non-null fold added inside `validate_record`
   (now also runs the pre-existing `VALID_STATUS` check). The summary-truncation block is guarded by
   `if "summary" not in {null/missing fields}` so a `None` summary produces a clean validation error
   instead of `TypeError: object of type 'NoneType' has no len()`.
3. **`tools/agent-monitoring/vocabulary.py`** (new) — canonical `CANONICAL_TIERS`, per-workflow
   `WORKFLOW_PHASES`/`WORKFLOW_AGENTS`, and `infer_workflow(run_id)`. Built by grepping each
   workflow's actual `phase(...)`/`pushEvent(...)` call sites directly (not copied from `schema.md`,
   which was already stale). See Deviations below — grepping surfaced two corrections to the plan's
   stub module.
4. **`record_events.py`** — added `warn_vocabulary_drift(record)`, called after `validate_record`
   passes cleanly; prints `WARNING: unrecognized phase/agent ...` to stderr, never appends to
   `errors`, never affects `sys.exit`.
5. **`tools/agent-monitoring/validate.py`** — extracted `compute_drift_report(runs, events) -> str`
   (mirrors `generate_retro.py`'s `generate()` shape); wired into `main()` after the existing
   error/warning printing, before the final `OK:` line — i.e. it only prints on the exit-0 path,
   matching existing behavior where the `OK:` line itself is exit-0-only.
6. **`docs/agent-monitoring/schema.md`** — added one pointer sentence before the `phase` values
   sections directing readers to `vocabulary.py` as the single source of truth.
7. Regression pass: all new + sibling tests green (see Test Summary). Real-data sanity check (not
   the Makefile target — see Deviations) confirms `compute_drift_report` reports exactly 98
   `workflow: null` records against the live `agent-monitoring/runs.jsonl`, matching the ticket's
   own cited figure.

See `staging_artifacts/.../plan.md`'s Deviations section for two corrections made to the plan's
`vocabulary.py` stub (both confirmed by grep, not guessed) and one environment-reality note about
Step 7's Makefile smoke test.

## Test Summary
`pytest tests/tools/test_record_run.py tests/tools/test_record_events.py tests/tools/test_validate_agent_monitoring.py tests/tools/test_generate_retro.py tests/tools/test_done_checker_static.py -q` — 81 passed, 0 failed. Covers: null-vs-missing-field parity, falsy-non-null pass-through, vocabulary warn-not-reject behavior, orchestrator-pseudo-agent allowlist, drift-report counts/frequency table, and the single-source-of-truth guard. Regression files (`test_generate_retro.py`, `test_done_checker_static.py`) included since both read the same `runs.jsonl`/`events.jsonl` records this ticket's checks gate, or share the `tools/gate_checks/` sibling directory and `final_status` vocabulary.

## Files Changed
- tools/agent-monitoring/record_run.py
- tools/agent-monitoring/record_events.py
- tools/agent-monitoring/vocabulary.py (new)
- tools/agent-monitoring/validate.py
- docs/agent-monitoring/schema.md
- tests/tools/test_record_run.py (new)
- tests/tools/test_record_events.py (new)
- tests/tools/test_validate_agent_monitoring.py (new)

## Completion Summary
All 5 acceptance criteria implemented per `staging_artifacts/TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT/plan.md`'s 7 steps: (1) non-null enforcement is a hard reject in both `record_run.py` and `record_events.py`, extending the existing missing-key rejection path; (2) a per-workflow phase/agent vocabulary check is warn-only (stderr), verified to never escalate to `sys.exit`; (3) `compute_drift_report()` in `validate.py` reports null-required-field counts and non-canonical phase/agent/tier frequency tables, confirmed against real data (exactly 98 `workflow: null` records, matching the ticket's own cited figure); (4) `tools/agent-monitoring/vocabulary.py` is the single source of truth, imported identically by both the write-time warning and the read-time drift report, guarded by a same-module-identity test; (5) 81 tests pass across 3 new + 2 regression test files.

**Known caveat, not a gap requiring follow-up**: AC3 ("`make agent-monitoring-validate` output includes a drift-report section") is verified via direct `compute_drift_report()` invocation against the live `agent-monitoring/runs.jsonl`/`events.jsonl`, not via the `make agent-monitoring-validate` CLI target itself — that target currently exits 1 on 6 pre-existing, unrelated "Run with no events" errors (confirmed identical before and after this change via `git stash`) before reaching the new drift-report print statement. This is a pre-existing data-quality issue unrelated to this ticket's scope, not a regression introduced here. No follow-up ticket filed — the underlying 6 errors are a known, separate data-quality gap already covered by the historical-drift framing in this ticket's own Request Summary (the 98 `workflow: null` records and friends), and backfilling/fixing historical records is explicitly out of scope per this ticket and the source idea doc.

No historical records were backfilled or rewritten, per the ticket's Out of Scope. No `src/` files were touched; no parity ledger entries were affected (confirmed no P0 intersection).
