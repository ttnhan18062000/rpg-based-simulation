---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260915-MONITORING-ANOMALY-VALIDATOR
phase: done
date: 2026-09-15
tags: [agent-monitoring, data-quality, process-improvement]
---

# TCK-20260915-MONITORING-ANOMALY-VALIDATOR

## Title
Nothing checks monitoring records for *implausibility* — add a validator that fails on incoherent records the way `agent-monitoring-validate` fails on missing ones

## Status
DONE

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
- [x] The validator reports each anomaly class with a count, against a recorded baseline —
      `check_monitoring_anomalies()` aggregates 9 conditions across 5 checks, each with its own
      `evidence` string naming the count and ceiling.
- [x] It ratchets: a count above baseline fails; at or below passes. No check asserts zero — every
      one of the 9 conditions is a positive ceiling (1/71/46/49/66/55/34/162/2), none zero.
- [x] A test pins the wiring: `test_makefile_wires_monitoring_anomaly_validate` (target exists) +
      `test_cli_prints_marker_output_not_merely_a_return_code` (asserts real stdout content
      containing `MARKER:`/`"check":`/`"status":`, not merely a subprocess return code).
- [x] A deliberately-planted bad record makes it fail:
      `test_ts_shape_check_detects_planted_bad_record` (a `start_ts: None` run, ceiling
      monkeypatched to 0, proves FAIL) and `test_vocabulary_drift_agent_condition_fails_when_exceeded`
      / `test_vocabulary_drift_tier_condition_fails_when_exceeded` (synthetic unknown literals,
      same pattern).

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
  Resolved: built as a sibling tool (`tools/gate_checks/monitoring_anomaly_validator.py`),
  matching this epic's own established `tools/gate_checks/*.py` pattern rather than growing
  `validate.py`'s already-well-scoped presence-only job. It also `sys.exit(1)`s on any FAIL, same
  as `validate.py` — not rolled out advisory-only, since every underlying ratchet ceiling was
  already independently verified against the real corpus (exit 0) before wiring.

## Implementation Notes
See `staging_artifacts/TCK-20260915-MONITORING-ANOMALY-VALIDATOR/investigation.md` for the full
candidate-check-by-candidate-check mapping against sibling-ticket reality.

The ticket's own three named "non-canonical agent" examples (`orchestrator` 144,
`concern-investigator` 6, `context-packet-wrapper` 1) were all wrong when re-measured — the real
counts were 401-501, 8, and 59 respectively, and all three (plus 3 more found during
investigation: `implement-ticket`/`implement-epic` self-referential labels, `write-sequence`) are
real, confirmed, legitimate mechanisms missing from `tools/agent-monitoring/vocabulary.py`'s
registry, not corpus drift. Registered all 6 there (each with a confirming comment) rather than
ratcheted as anomalies — matching the exact "most flagged instances turn out legitimate"
discipline every other ticket in this epic already established. The peer session that originally
scoped this candidate check independently re-derived the same correction from a different angle
before this investigation completed, confirming it rather than contradicting it.

`working_log` schema conformance (the 6th candidate check) needed no new ratchet: ticket 7 already
fixed it to a genuine, structurally-protected zero (sole-writer test), which doesn't need its own
entry here.

The remaining 4 candidate checks were already built by sibling tickets — this ticket's own real
work was: (a) extract `compute_vocabulary_drift_counts()` from `validate.py`'s existing
`compute_drift_report()` so a ratchet check can consume structured counts, proven byte-identical to
the prior text-only output via the existing drift-report test suite; (b) build the new
`check_vocabulary_drift()` for the genuine post-registration residual (162 agent / 2 tier); (c)
build a thin `check_ts_shape_and_unknown_week()` wrapper reusing ticket 7's own item-4/5 functions
(deliberately excluding its item 2, since presence-of-a-run-record is `validate.py`'s domain, not
this coherence-focused validator's); (d) aggregate all 5 checks into one
`check_monitoring_anomalies()` surface, wired to a real Makefile target, with the wiring itself
pinned by a test that asserts actual stdout content rather than a bare return code.

One further finding recorded explicitly, not ratcheted: 258 events have no `agent` field at all
(field absence, a different check shape than a wrong-literal check covers) — historical, partially
already covered by the ts-unusable ratchet, documented in the validator module's own docstring.

## Test Summary
- `tests/tools/test_validate_agent_monitoring.py`: existing 15 drift-report tests re-run unchanged,
  proving `compute_vocabulary_drift_counts()`'s extraction is byte-identical to the prior inline
  logic.
- `tests/tools/test_monitoring_anomaly_validator.py` (new, 12 tests): per-check unit coverage
  (clean-pass, registered-literal-not-flagged, FAIL-on-exceeded-ceiling via monkeypatched
  ceilings), a deliberately-planted-bad-record detection test, an aggregate-tagging test, a
  real-corpus pass test, a Makefile-wiring test, and a subprocess-level stdout-content test.
- Full `tests/tools/` suite: 2677 passed (0 failures) after this ticket's changes.
- Manual: `make monitoring-anomaly-validate` (equivalently, `python3
  tools/gate_checks/monitoring_anomaly_validator.py`) against the real corpus — all 9 conditions
  PASS, exit 0.

## Files Changed
- `tools/agent-monitoring/vocabulary.py` — 6 new registered agent literals across
  `implement-ticket`/`create-tickets`/`implement-epic`, each with a confirming comment.
- `tools/agent-monitoring/validate.py` — extracted `compute_vocabulary_drift_counts()` from
  `compute_drift_report()` (structured data, no behavior change; proven byte-identical).
- `tools/gate_checks/monitoring_anomaly_validator.py` (new) — the aggregate validator.
- `Makefile` — new `monitoring-anomaly-validate` target + `.PHONY` entry.
- `tests/tools/test_monitoring_anomaly_validator.py` (new) — 12 tests.

## Completion Summary
Investigated all 6 of the ticket's own candidate checks against tickets 1-7's actual confirmed
findings before writing any new code, per the epic's explicit "scope this last" instruction. Found
the ticket's own three named vocabulary-drift examples were all wrong (numbers stale by 3-60x, and
all three literals legitimate rather than drift) and corrected the registry rather than ratcheting
false positives — the exact failure mode (a check pinning the wrong invariant) this ticket's own
text warned against. Built one aggregate validator reusing all 4 already-built sibling ratchet
checks plus a new vocabulary-drift check for the genuine post-registration residual, wired to a
real Makefile target and pinned with both a stdout-content test and a detection-proof test. All 8
tickets of this epic's original 9-ticket child list are done as of this ticket's close (ticket 9,
the retro-CLI-overwrite fix, remains — independently scoped, "pick up whenever").
