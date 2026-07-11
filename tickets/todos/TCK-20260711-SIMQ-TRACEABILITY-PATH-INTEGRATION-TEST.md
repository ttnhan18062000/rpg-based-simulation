---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260711-SIMQ-TRACEABILITY-PATH-INTEGRATION-TEST
phase: open
date: 2026-07-11
tags: [simulation-quality]
---

# TCK-20260711-SIMQ-TRACEABILITY-PATH-INTEGRATION-TEST

## Title
Add integration test validating the §9 Traceability Design drill-down path end-to-end

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Filed as a genuine gap found during `TCK-20260710-SIMQ-CONTRACT-AC-CLOSEOUT`'s verification pass
over `docs/simulation_quality/quality_scoring_contract.md` §12. The Traceability checklist's third
item — "The traceability path in §9 is validated by an integration test" — could not be checked
true. §9 documents a 6-step drill-down: `QualityReport` → low-grade pillar → `worst_events[:5]`
(`ScoreRecord.event_id`) → cross-reference that `event_id` in
`data/runs/{run_id}/simulation_events.jsonl` → entity/world-level follow-up. A repo-wide search
(`grep -rln "simulation_events.jsonl" tests/ tools/`) found no test in `tests/simulation_quality/`
or elsewhere that exercises this path end-to-end — i.e. runs a scenario, captures both
`quality_scores.jsonl`/`quality_report.json` and `simulation_events.jsonl` from the same run, and
asserts a worst_event's `event_id` is actually resolvable in the sibling file.

Note this is not a functional bug: `event_id=envelope.event_id` is set identically in all 10
scorers (confirmed by direct code read of `src/simulation_quality/scorers/*.py`) and
`EventRecorder` writes that same `envelope.event_id` field into `simulation_events.jsonl`
(`src/observability/event_recorder.py:114`) — since both paths consume the same
`ObservabilityEventEnvelope` instance, the cross-reference holds by construction. What's missing is
the integration test asserting this explicitly, per §12's literal wording.

## Scope
- Add one integration test (likely `tests/simulation_quality/test_traceability_path.py`, following
  the existing `test_kernel_simq_integration.py` pattern of a minimal `Kernel` + injected
  `SimulationEvent`s) that:
  1. Runs a minimal kernel/session that produces at least one negative-delta `ScoreRecord` landing
     in some pillar's `worst_events`.
  2. Reads back the persisted `quality_scores.jsonl` (or the in-memory `QualityReport`) and picks a
     `worst_events` entry.
  3. Reads back `simulation_events.jsonl` from the same run directory and asserts the worst event's
     `event_id` is present in it.
- Update `docs/simulation_quality/quality_scoring_contract.md` §12's Traceability item 3 checkbox to
  `[x]` with a citation to the new test once it exists and passes.
- Cross-reference/update the relevant `docs/parity_ledger/infrastructure.yaml` entry if one is
  added or amended for this behavior.

## Out of Scope
- Any change to the traceability mechanism itself (`event_id` propagation, `simulation_events.jsonl`
  writing) — current behavior is already correct per the code-read evidence above; this ticket adds
  test coverage only.
- Re-scoping §12's other 24 items — those were separately verified and cited in
  `TCK-20260710-SIMQ-CONTRACT-AC-CLOSEOUT`.
- Steps 4–6 of §9's path (`cognition_graph_snapshots.jsonl`, `world.yaml`/compiled state,
  root-cause library lookup) — out of scope for this ticket; only the `ScoreRecord.event_id` →
  `simulation_events.jsonl` cross-reference (steps 1–3) needs a test, since that's the only
  cross-reference §12's item literally requires ("validated by an integration test").

## Acceptance Criteria
- A new integration test exists and passes, asserting that a `ScoreRecord.event_id` present in a
  pillar's `worst_events` resolves to a real entry in `simulation_events.jsonl` from the same run.
- `quality_scoring_contract.md` §12 Traceability item 3 is checked `[x]` with a citation to the new
  test.
- Test is added to the relevant scoped test run path (`tests/simulation_quality/`).

## Related Tickets
- `tickets/done/TCK-20260710-SIMQ-CONTRACT-AC-CLOSEOUT.md` — origin of this gap (§12 verification
  pass); this ticket implements the fix that closeout ticket was barred from implementing directly
  (hotfix tier, verification-only scope).

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` §9 (Traceability Design — the path to test),
  §12 (Traceability checklist item 3 — the checkbox this closes).

## Related Code Areas
- `src/simulation_quality/scorers/*.py` (`event_id=envelope.event_id` propagation).
- `src/observability/event_recorder.py` (`simulation_events.jsonl` writer, line ~114).
- `src/simulation_quality/persistence.py` (`quality_scores.jsonl` / `quality_report.json` writer).
- `tests/simulation_quality/test_kernel_simq_integration.py` — reference pattern for a minimal
  kernel + injected-event integration test.

## Assumptions / Open Questions
- Assumes a minimal in-process kernel run (as in `test_kernel_simq_integration.py`) is sufficient
  to produce both files in the same `tmp_path` run directory; if `simulation_events.jsonl` requires
  a fuller `EventRecorder` configuration than that fixture currently provides, the implementer
  should extend the fixture rather than introduce a second, divergent test harness.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
