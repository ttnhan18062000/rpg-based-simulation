---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260915-MONITORING-ANOMALY-VALIDATOR
phase: open
date: 2026-09-15
tags: [agent-monitoring, data-quality, process-improvement]
---

# TCK-20260915-MONITORING-ANOMALY-VALIDATOR

## Title
Nothing checks monitoring records for *implausibility* — add a validator that fails on incoherent records the way `agent-monitoring-validate` fails on missing ones

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`make agent-monitoring-validate` answers "is the record present?" — every DONE working_log entry has
a run, every run has an event. Nothing answers "is the record *coherent*?"

The 2026-09-15 anomaly sweep found eight classes of implausible record, **none of which registers as
a failure anywhere**: a run written twice with identical identifiers, a `seq` that skips or repeats,
a `tool_call_count` contradicting its own tool rows, a summary severed at exactly 200 characters, a
quarter of tool rows belonging to no run, an index reporting zero for a report containing 249 runs.
All of it reads as green.

This is the thirteenth instance in this arc of a mechanism that exists, looks authoritative, and
does not report what it appears to
(`docs/plans/agent_infrastructure/reachability_verification_findings.md`). The remedy that has
worked repeatedly in this codebase is a ratcheted detector wired into a real target.

**Scope this ticket LAST.** Its checks should encode the causes the sibling tickets confirm, not
this epic's hypotheses. Writing the validator first risks pinning the wrong invariant — precisely
the failure `TCK-20260913-DONE-CHECKER-WORKING-LOG-ROW-COUNT-REJECTS-LEGITIMATE-REOPEN` describes,
where a check measured a proxy rather than the property it cared about.

## Scope
- A validator (or an extension of `validate.py`) checking coherence, not just presence. Candidate
  checks, to be confirmed against sibling-ticket findings:
  - duplicate run records (identical `run_id` + `execution_id` + `start_ts`)
  - `seq` uniqueness/contiguity, per whatever the schema ends up guaranteeing
  - `tool_call_count` versus real `tools.jsonl` rows, beyond an agreed tolerance
  - `ts` type/shape conformance, and rows landing in `unknown-week`
  - vocabulary conformance: non-canonical agents (`orchestrator` 144, `concern-investigator` 6,
    `context-packet-wrapper` 1) and tiers (`epic_batch`, `epic-batch`)
  - working_log rows not matching the 6-column schema
- **Every check must ratchet from a measured baseline.** The corpus is dirty and nobody is going to
  retroactively clean it; a check asserting zero is unlandable and gets disabled on day one. See
  `SEQUENCE.md`'s baseline table.
- Wire it somewhere real — a Makefile target and/or CI lane — and pin that wiring with a test. An
  unwired detector is the exact defect class this epic documents.

## Out of Scope
- Fixing any of the underlying anomalies; the sibling tickets own those.
- Cleaning historical data.
- Gating CI on the ratchet before the baselines have settled — start advisory if that is safer, but
  record the intent to make it blocking.

## Acceptance Criteria
- [ ] The validator reports each anomaly class with a count, against a recorded baseline.
- [ ] It ratchets: a count above baseline fails; at or below passes. No check asserts zero.
- [ ] A test pins the wiring (target exists, runs, and fails when the baseline is exceeded) — and
      the test asserts **presence of output**, not merely a return value, since the failure mode
      this whole arc keeps hitting is silence.
- [ ] A deliberately-planted bad record makes it fail, proving it can detect rather than only
      report clean.

## Related Tickets
- `TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC` (parent)
- All seven sibling tickets — this one encodes their confirmed findings
- `TCK-20260914-MONITORING-SURFACE-DEAD-MECHANISMS` (done) — the ratchet pattern to follow
- `TCK-20260913-PARITY-BASELINE-EQUALITY-GATE-PENALIZES-IMPROVEMENT` (open) — why zero-assertions fail

## Related Docs
- `agent-monitoring/retro/RETRO-LAST14D.md`
- `docs/plans/agent_infrastructure/reachability_verification_findings.md`
- `docs/agent-monitoring/schema.md`

## Related Stored Artifacts
- None yet.

## Related Code Areas
- `tools/agent-monitoring/validate.py`
- `tools/gate_checks/` (for the ratchet pattern already in use)
- `Makefile` (`agent-monitoring-validate` target)

## Assumptions / Open Questions
- Whether this belongs inside `validate.py` or as a sibling tool is an open design question —
  `validate.py` currently `sys.exit(1)`s, which may or may not suit an advisory-first rollout.

## Implementation Notes
The sweep that produced these findings is reproducible from the JSONL shards directly; do not build
on `monitoring.db`, which goes stale and which `generate_retro.py` already warns about.

## Test Summary
_To be completed by the implementer._

## Files Changed
_To be completed by the implementer._

## Completion Summary
_Open._
