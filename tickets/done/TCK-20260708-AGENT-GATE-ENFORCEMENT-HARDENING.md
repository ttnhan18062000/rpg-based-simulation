---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260708-AGENT-GATE-ENFORCEMENT-HARDENING
phase: done
date: 2026-07-08
tags: [hooks, determinism, process-improvement]
---

# TCK-20260708-AGENT-GATE-ENFORCEMENT-HARDENING

## Title
Escalate the two silently-unenforced hook cases to hard blocks + document `lane-architecture`'s actual coverage

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`idea_agent_gate_determinism.md`'s 4 static-verifier gates (done-checker/parity-updater/mechanics-auditor/architecture-reviewer) were fully implemented by `gate-determinism-followups` (2026-07-05, `tickets/done/gate-determinism-followups/`) — but that work only covered the "give each judged gate a deterministic backstop" half. The idea's own "Enforcement: nudge vs. block" section, and audit Recommendations #1 (log/escalate hook near-misses) and #3 (document what `lane-architecture` covers), were never built. Confirmed still open by reading `.claude/settings.json` directly: both `PreToolUse` hooks only ever emit `additionalContext`, never a block. This ticket closes both remaining items and corrects the now-stale idea doc.

## Scope
- Escalate case (b) — a commit touching a `src/` path mapped to a parity-ledger subsystem with no matching ledger entry touched in the same diff — to a real hard block (not just `additionalContext`)
- **Revised during Review (architecture-reviewer NEEDS_CHANGES, resolved by user decision):** case (a) — a ticket finalizing with no corresponding `agent-monitoring` run/event write — does NOT become a hard block. The original scope (hard-block both cases) conflicted with CLAUDE.md's explicit Hard Rule "monitoring write failure must never fail the workflow": withholding `DONE` because a monitoring write didn't land is exactly the outcome that rule forbids, and the plan did not propose amending the rule. User chose to keep the rule intact and redesign case (a) as loud-but-non-blocking instead: a missing write now produces a strong `pushEvent('Finalize', ..., 'failed', ...)` record and a persistent `WARNING` surfaced in Finalize's returned `message` field, but the run still reports `DONE`.
- Resolve the idea doc's own open question: do hard blocks fail outright, or downgrade into the existing `NEEDS_CHANGES`/`BLOCKED`/`DOD_BLOCKED` status vocabulary? Resolved: case (b) reuses no pre-existing status (Parity had none) and introduces exactly one new phase-specific status, `PARITY_INCOMPLETE`, following the `FINALIZE_INCOMPLETE` precedent. Case (a) is no longer a status-vocabulary question at all, since it no longer blocks.
- Write down explicitly what `make lane-architecture` covers relative to the 4 static gate-checker modules in `tools/gate_checks/` — closing audit Recommendation #3
- Update `docs/plans/agent_infrastructure/idea_agent_gate_determinism.md`'s status/maturity header to reflect the static-verifier half is done (link `gate-determinism-followups`) and only the enforcement-escalation half was open before this ticket
- Update `docs/ai/agent_infrastructure_audit.md` to mark Recommendations #1 and #3 closed with a pointer to this ticket

## Out of Scope
- Re-implementing or modifying any of the 4 already-shipped static verifiers (`done_checker_static.py`, `parity_updater_static.py`, `mechanics_auditor_static.py`, `architecture_reviewer_static.py`)
- The context-scan grep/find advisory hook — the audit and idea doc both explicitly keep this one advisory (low stakes, high false-positive risk from keyword matching); do not escalate it
- Cost/token telemetry (separate child ticket in this epic)

## Acceptance Criteria
- A ticket finalize step with no matching `agent-monitoring` write is loud but non-blocking: a `failed`-status event is recorded and a persistent `WARNING` is surfaced in Finalize's returned `message` field, but the ticket still reports `DONE` (CLAUDE.md's Hard Rule stays intact, unmodified)
- A commit touching a parity-ledger-mapped `src/` path with no matching ledger touch is hard-blocked, not just nudged (`PARITY_INCOMPLETE`)
- The one new hard block (case b) introduces exactly one new status string (`PARITY_INCOMPLETE`) — justified because Parity had no pre-existing failure status, per the `FINALIZE_INCOMPLETE` precedent
- `docs/ai/workflows.md` or a new doc explicitly states `lane-architecture`'s coverage boundary against the 4 gate-checker modules
- `idea_agent_gate_determinism.md` and `agent_infrastructure_audit.md` both reflect current reality (no doc claims "not scheduled" for already-shipped work)
- Tests cover: the case (b) hard-block trigger condition (positive control), the case (a) warning-but-DONE behavior (positive control confirming DONE is still returned), and confirm no false-positive block on a normal compliant run

## Related Tickets
Parent: TCK-20260708-AGENT-INFRA-HARDENING-EPIC. Prior art (done): TCK-20260705-GATE-DET-DONE-CHECKER, TCK-20260705-GATE-DET-PARITY-UPDATER, TCK-20260705-GATE-DET-MECHANICS-AUDITOR, TCK-20260705-GATE-DET-ARCHITECTURE-REVIEWER.

## Related Docs
docs/plans/agent_infrastructure/idea_agent_gate_determinism.md, docs/ai/agent_infrastructure_audit.md, docs/ai/workflows.md, docs/ai/agents.md

## Related Stored Artifacts
tickets/done/gate-determinism-followups/ (the 4 prior tickets' stored_artifacts, for the existing verified_by/failure-vocabulary design decisions)

## Related Code Areas
.claude/settings.json (hooks), tools/gate_checks/*.py, Makefile (lane-architecture target)

## Assumptions / Open Questions
- Assumes the two hard-block cases named by the audit are still the correct, highest-value pair to escalate — Investigate phase should confirm no third case has emerged since 2026-07-03.
- The idea doc's own open question (hard-block-immediately vs. downgrade-to-existing-status) must be resolved as a design decision before Implement, not deferred to code review.

## Implementation Notes

Implemented per the revised plan (post architecture-review NEEDS_CHANGES round-trip; Design
Decision 2 in `staging_artifacts/.../plan.md` is authoritative — case (a) stays loud-but-non-blocking,
case (b) is a true hard block).

**Step 1** — Added `_jsonl_rows_for_run_id` helper and `check_monitoring_write_recorded(ticket_id,
runs_path, events_path)` to `tools/gate_checks/done_checker_static.py` (Part B section, after
`check_working_log_exactly_one_row`, before `run_finalize_selfcheck`). Added `import json`. No
`tier` parameter — deliberately applies identically under hotfix, per CLAUDE.md's Hard Rule wording
("including hotfix"). Not added to `run_finalize_selfcheck`'s aggregator (would always FAIL there,
since it runs before any `writeMonitoring` call for the current attempt).

**Step 2** — Confirmed actual existing test count via `grep -c '^def test_'
tests/tools/test_done_checker_static.py` = 41 (plan's own "38" baseline was stale, as the plan itself
flagged). Added 4 new tests (`test_check_monitoring_write_recorded_fails_when_run_missing`,
`..._fails_when_events_missing`, `..._passes_when_both_present`,
`..._applies_under_hotfix_tier`) plus a small `_write_jsonl` test helper. Full suite:
`pytest tests/tools/test_done_checker_static.py -v` → 45 passed (41 + 4), matching the plan's
predicted total exactly.

**Step 3 (revised)** — Wired `check_monitoring_write_recorded` into Finalize in
`.claude/workflows/implement-ticket.js`, called via `bash()` immediately after `await
writeMonitoring('DONE')`. A FAIL (or unparseable output) produces `pushEvent('Finalize',
'finalizer', 'failed', ...)` plus a `log('WARNING: ...')` line, and the returned `message` field
carries a `WARNING:` prefix — but `status` remains unconditionally `'DONE'` in every path through
this block. Verified by manual review: only one status-changing `return` exists inside this
function's Finalize block (the pre-existing `FINALIZE_INCOMPLETE` branches for the self-check,
untouched), and the new block never sets `status`. `node --check
.claude/workflows/implement-ticket.js` passes.

**Step 4** — Wired a genuine `parityCrossRefFailures.length > 0` result into a new hard-blocking
early return (`status: 'PARITY_INCOMPLETE'`) in the Parity phase's full-call (`else`) branch,
immediately after `parityCrossRefFailures` is computed. The unparseable (`parityCrossRef === null`)
case stays non-blocking, unchanged. Did not touch `cross_reference_touched` or the skip-eligible
branch. `tests/tools/test_parity_updater_static.py` (10 tests, unmodified) still passes — confirms
`cross_reference_touched`'s own semantics are untouched.

**Step 5** — Read `.claude/workflows/implement-epic.js` line 203:
`if (result.status !== 'DONE') { batchStatus = result.status; ... }`. Confirmed string-agnostic —
catches any status literal other than `'DONE'`, so `PARITY_INCOMPLETE` (new, Step 4) is caught with
zero code changes. No edit made to this file, per plan.

**Step 6** — Added the `lane-architecture` coverage-boundary paragraph to `docs/ai/workflows.md`
directly under `implement-ticket`'s "Artifacts produced" list. Updated the Parity phase-table row's
gate-condition text to state the new hard block (unparseable stays non-blocking). Updated the
Finalize phase-table row's parenthetical for the monitoring-write check — worded as
loud-but-non-blocking (not as a second `FINALIZE_INCOMPLETE` trigger), since the plan's own Step 6
item 3 wording was stale pre-revision text that would have misdescribed actual (non-blocking)
behavior; see Deviations note in plan.md. Added a `PARITY_INCOMPLETE` row to the Return Values
table.

**Step 7** — Updated `docs/plans/agent_infrastructure/idea_agent_gate_determinism.md`: maturity
banner changed from "PARTIALLY SHIPPED" to "SHIPPED", describing both the hard-block (case b) and
the non-blocking-warning revision (case a). Resolved the first Open Questions bullet with a note
citing this ticket's actual resolution (one new status for case b, no status change at all for
case a). Corrected the "Natural Integration Points" table's hook row, which previously claimed the
hard-block escalation was a `.claude/settings.json` hook change — replaced with the accurate
description (`implement-ticket.js` control flow, no hook-blocking precedent exists in this harness).

**Step 8** — In `docs/ai/agent_infrastructure_audit.md`, closed Recommendation #1 with a pointer
noting it was closed via hard-blocking the two named cases directly, not via literal near-miss
logging (the originally proposed mechanism). Closed Recommendation #3 with a pointer to
`docs/ai/workflows.md`'s new coverage-boundary note. Recommendations #2, #4, #5 left untouched.

No `src/` file, Mechanics Bible chapter, engine contract, or parity ledger entry was touched, per
investigation's confirmed "Parity Ledger Overlap: None found."

## Test Summary
`pytest tests/tools/test_done_checker_static.py tests/tools/test_parity_updater_static.py -v` — 55 passed, 0 failed (45 in `test_done_checker_static.py`: 41 pre-existing + 4 new for `check_monitoring_write_recorded`; 10 in `test_parity_updater_static.py`, unmodified, confirming `cross_reference_touched`'s existing semantics are untouched by the new Parity hard block). `.claude/workflows/implement-ticket.js` has no JS test harness in this repo — verified by two rounds of manual/structural architecture review instead (confirming `status: 'DONE'` is unconditional in every Finalize code path, and `PARITY_INCOMPLETE` triggers only on a genuine parsed `parityCrossRefFailures` result, never on the unparseable case).

## Files Changed
- tools/gate_checks/done_checker_static.py
- tests/tools/test_done_checker_static.py
- .claude/workflows/implement-ticket.js
- docs/ai/workflows.md
- docs/plans/agent_infrastructure/idea_agent_gate_determinism.md
- docs/ai/agent_infrastructure_audit.md
- staging_artifacts/TCK-20260708-AGENT-GATE-ENFORCEMENT-HARDENING/plan.md
- staging_artifacts/TCK-20260708-AGENT-GATE-ENFORCEMENT-HARDENING/test_plan.md

## Completion Summary
All 6 acceptance criteria met, after one architecture-review round-trip. Case (b) (Parity cross-reference miss) is now a genuine hard block returning `PARITY_INCOMPLETE` — a deliberate, documented reversal of the prior `GATE-DET-PARITY-UPDATER` decision to stay visibility-only, since closing that exact gap was this ticket's whole premise. Case (a) (missing agent-monitoring write) was originally scoped as a hard block too, but the first architecture-review round returned `NEEDS_CHANGES`: hard-blocking Finalize on a missing monitoring write is an undisclosed reversal of CLAUDE.md's own Hard Rule ("monitoring write failure must never fail the workflow"). Presented with a choice between amending that rule or redesigning case (a), the user chose to keep CLAUDE.md intact — case (a) now produces a `failed`-status event and a persistent `WARNING` in Finalize's returned message, but `status` stays unconditionally `DONE`. The revised plan passed a second architecture-review round cleanly. `lane-architecture`'s coverage boundary against the 4 `tools/gate_checks/*.py` static verifiers is now documented in `docs/ai/workflows.md` (closing audit Recommendation #3), and both `idea_agent_gate_determinism.md` and `agent_infrastructure_audit.md` (Recommendation #1) now reflect shipped reality instead of "not scheduled."

No material gaps: no `src/` file, Mechanics Bible chapter, engine contract, or parity ledger entry was touched (confirmed twice — investigation and Parity phase both independently grepped all `docs/parity_ledger/*.yaml` files for zero matches). No follow-up ticket is needed for this scope. One doc correction made during Test: `test_plan.md`'s item 1 (4th sub-bullet) called for wiring the new check into `run_finalize_selfcheck`'s aggregator — stale text written pre-revision, before Design Decision 2 explicitly rejected that integration point (the aggregator runs before `writeMonitoring` for the current attempt, so a check there would always FAIL). Corrected in place to describe the actual, shipped, twice-reviewed design rather than leave a contradiction between `test_plan.md` and `plan.md`.
