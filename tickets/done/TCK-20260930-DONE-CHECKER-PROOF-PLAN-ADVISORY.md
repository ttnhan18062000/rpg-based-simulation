---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260930-DONE-CHECKER-PROOF-PLAN-ADVISORY
phase: done
date: 2026-09-30
tags: [testing]
---

# TCK-20260930-DONE-CHECKER-PROOF-PLAN-ADVISORY

## Title
done-checker advisory check: list the mandatory Proof Plan fields missing from a standard ticket's test_plan.md (WARN only, never fails the close)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Test-architecture Epic C (`TCK-20260929-EPIC-TEST-WORKFLOW-FAILURE-HANDLING`) acceptance
criterion 1 says the mandatory `test_plan.md` fields must be present on at least 2 tickets **and
`done-checker` checks their presence**; criterion 2 needs a checkable signal for the pilot. The
fields are defined (advisory) by `TCK-20260930-TEST-PLAN-PROOF-FIELDS-AND-TRIAGE-PROCEDURE` in
`.claude/agents/investigator.md` `## Proof Plan`, but nothing checks them. This ticket adds a
report-only check: for a standard-tier ticket it lists the missing mandatory Proof Plan fields as
`WARN` lines and never changes a close verdict.

**Source-pointer correction, recorded before implementing.** The request that filed this ticket
cited `docs/testing/regression_policy.md` §13 as the definition of the proof fields. §13 is the
failure-triage procedure (evidence record, failure classes, prohibitions); it does not define
`test_plan.md` fields. The authoritative field list is `.claude/agents/investigator.md`
`## Proof Plan` (mirroring `docs/plans/test_architecture/roadmap.md` line 157). This ticket
implements against the investigator definition and does not restate the field list in a second
place (the check imports or parses one source; see Implementation Notes).

## Scope
- A new check in `tools/gate_checks/done_checker_static.py` that reads the ticket's `test_plan.md`
  (staging path while in flight, `stored_artifacts/` after migration) and reports which of the
  mandatory Proof Plan fields (level, proof kind, oracle source, expected effect, selected
  commands) are missing, per acceptance criterion where the plan is per-criterion.
- Tier handling: `standard` is checked; `hotfix` has no `test_plan.md` and reports not-applicable;
  `epic` reports not-applicable (scope-only).
- An "advisory" channel that is separate from `run_static_precheck()`'s PASS/FAIL/NA conditions, so
  no existing consumer of that list (`implement-ticket.js`, the done-checker agent's
  `DONE_SCHEMA.checklist`) sees a new status value.
- CLI: the existing `done_checker_static.py` CLI prints the advisory lines as `WARN`/`OK`/`NA`;
  they never affect the `RESULT:` line or the exit code.
- Tests, including the never-fails guarantee, the hotfix/epic not-applicable path, the
  "no testable acceptance criterion" one-line declaration, `oracle: unresolved` counting as filled,
  both accepted layouts (table row per criterion, `### AC<n>` block), and read-only behavior.
- `.claude/agents/done-checker.md` and the delivery docs that describe the static pre-check:
  document the advisory, its WARN semantics, and that it is not a gate.

## Out of Scope
- Making the check blocking, or adding it to `DONE_SCHEMA`'s checklist (Epic C keeps the Proof
  Plan advisory during the pilot; whether it becomes required is the post-pilot decision).
- Validating the *content* of a field (whether the oracle source is correct, whether the command
  runs) — presence only.
- The optional fields (negative cases, fixtures, non-functional risk).
- Epic C parts 5–6 (on HOLD pending owner decisions D-M2 / D-MF).

## Acceptance Criteria
1. For a standard-tier ticket whose `test_plan.md` lacks one or more mandatory Proof Plan fields,
   the advisory reports each missing field by name (per acceptance criterion where applicable) as
   `WARN`.
2. A complete Proof Plan reports `OK`; a hotfix or epic ticket reports `NA`; a Proof Plan that
   states in one line that the ticket has no testable acceptance criterion reports `OK`
   (declared).
3. The check never changes `run_static_precheck()`'s result list, the CLI `RESULT:` line, or the
   exit code; an unreadable or missing `test_plan.md` degrades to a WARN, never an exception.
4. Tests cover the paths above, both layouts, `oracle: unresolved`, and read-only behavior.
5. The done-checker agent prose and the delivery/testing docs that describe the pre-check name the
   advisory and its non-blocking status.

## Related Tickets
- `TCK-20260929-EPIC-TEST-WORKFLOW-FAILURE-HANDLING` (Epic C, criteria 1–2 need this)
- `TCK-20260930-TEST-PLAN-PROOF-FIELDS-AND-TRIAGE-PROCEDURE` (defined the fields; done)

## Related Docs
- `docs/plans/test_architecture/roadmap.md` §4.4
- `docs/testing/regression_policy.md` §13 (failure triage — not the field definition)
- `docs/testing/test_taxonomy.md` §10

## Related Stored Artifacts
`stored_artifacts/TCK-20260930-TEST-PLAN-PROOF-FIELDS-AND-TRIAGE-PROCEDURE/test_plan.md` (example
of a filled Proof Plan table).

## Related Code Areas
- `tools/gate_checks/done_checker_static.py`
- `.claude/agents/done-checker.md`, `.claude/agents/investigator.md`

## Assumptions / Open Questions
- Presence is judged textually (field name appears literally, per the investigator prose: "every
  field name below must appear literally"), and an empty table cell counts as missing.

## Implementation Notes
The check lives in `tools/gate_checks/proof_plan_advisory.py`; `done_checker_static.py` gains
`run_advisory_checks()` (kept out of `run_static_precheck()` so no existing consumer sees a new status
value) and the CLI prints `[advisory]` lines that never touch `RESULT:` or the exit code. Presence is
judged textually: a table column with a non-empty cell, or a `name: value` line in a per-criterion
block; `oracle: unresolved` is a filled value; a one-line "no testable acceptance criterion" statement
is OK. `MANDATORY_FIELDS` is a single list, pinned by a test against `investigator.md`'s Proof Plan
prose. The field definition is `investigator.md`, not `regression_policy.md` §13 (see Request Summary).
Real-file check: `TCK-20260930-TEST-PLAN-PROOF-FIELDS-AND-TRIAGE-PROCEDURE`'s test_plan reports OK.

## Test Summary
`tests/tools/test_proof_plan_advisory.py`, 12 test functions (13 cases), and `tests/tools/test_done_checker_static.py`
(unchanged, 165 pass alongside): complete table OK incl. `oracle: unresolved`; stored_artifacts
location after migration; missing cell and missing column named per criterion; `### AC<n>` block
layout; one-line declaration OK; Disposition closure NA; missing section and missing file WARN not raise; hotfix and epic NA;
read-only; unreadable plan degrades to WARN; advisory absent from precheck/finalize source and CLI
exit stays 0 with a WARN; field list equals the investigator prose. All pass.

## Files Changed
- `tools/gate_checks/proof_plan_advisory.py` (new), `tools/gate_checks/done_checker_static.py`
- `tests/tools/test_proof_plan_advisory.py` (new)
- `.claude/agents/done-checker.md` (Step 0c), `docs/guides/delivery_process.md`
- this ticket and its artifacts; `docs/REGISTRY.yaml`

## Completion Summary
Done. Standard-tier tickets now get an advisory list of the mandatory Proof Plan fields missing from
`test_plan.md`, printed as `WARN` by `done_checker_static.py`, never affecting a close. AC1-AC5 as
tested above. This supplies the presence check test-architecture Epic C criterion 1 asks
`done-checker` to perform; whether the Proof Plan becomes required stays the post-pilot decision.
