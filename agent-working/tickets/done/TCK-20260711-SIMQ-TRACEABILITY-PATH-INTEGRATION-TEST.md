---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260711-SIMQ-TRACEABILITY-PATH-INTEGRATION-TEST
phase: done
date: 2026-07-11
tags: [simulation-quality]
---

# TCK-20260711-SIMQ-TRACEABILITY-PATH-INTEGRATION-TEST

## Title
Add integration test validating the §9 Traceability Design drill-down path end-to-end

## Status
DONE

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
Implemented per `staging_artifacts/TCK-20260711-SIMQ-TRACEABILITY-PATH-INTEGRATION-TEST/plan.md`
Steps 1-7 with no logic deviations:

- Created `tests/simulation_quality/test_traceability_path.py` with a `minimal_kernel` fixture
  (real `run_id="simq-traceability-test"`, no `QUALITY_RUN_DIR`, teardown reads
  `kernel._event_recorder.filepath` and `shutil.rmtree()`s its parent dir), matching
  `tests/integration/observability/test_run_artifact_flow.py`'s `clean_runs` pattern and the
  investigation's resolved-decision recommendation (option (a): real run_dir, not a
  monkeypatched `base_dir`).
- Added `test_worst_event_id_resolves_in_simulation_events_jsonl`: injects one
  `combat_hard_law_violation` `SimulationEvent` (unconditional -30.0 weight, no tick-gate,
  `src/simulation_quality/scorers/combat.py:111-112`), asserts `report.pillars["COMBAT"].worst_events`
  is non-empty (unconditional precondition assertion, not a vacuous `if`-guard), then asserts
  `worst_events[0].event_id` is present in the run's `simulation_events.jsonl`.
- Added `test_worst_event_id_matches_originating_envelope_exactly`: same injection, but asserts
  exactly one matching JSONL line and checks `event_type`/`tick`/`entity_id` match the injected
  values exactly.
- Added `test_run_directory_cleaned_up_after_test`: constructs a second `Kernel` with the same
  `RUN_ID`, shuts it down, `shutil.rmtree()`s its run dir, asserts the directory no longer exists —
  an explicit, pytest-verifiable guard independent of fixture teardown ordering.
- Ran the new file alone (3 passed), together with the reference pattern
  (`test_kernel_simq_integration.py` + `test_quality_hub_integration.py`, 17 passed total, no
  regression), and the full `tests/simulation_quality/` suite (463 passed, 2 skipped — pre-existing
  broker-mode skips, unrelated to this change). No stray `data/runs/simq-traceability-test/`
  directory found after any run.
- Added `INFRA-268` to `docs/parity_ledger/infrastructure.yaml`, additive-only, `status: verified`,
  `priority: P1`. Deviated slightly from the plan's literal YAML snippet by also including
  `proof_type` and `test_path` fields — `docs/parity_ledger/schema.json` requires `test_path` as a
  hard field whenever `status` is `verified`; the plan's snippet (which listed only `id`, `text`,
  `status`, `priority`, `legacy_evidence`, `v2_evidence`) would have failed schema validation.
  Verified full-file YAML validity and per-entry schema conformance for the new entry directly
  (a pre-existing, unrelated entry — `SIMQ-CALIBRATED-001` — already violates the `id` regex and
  is untouched by this change).
- Flipped `docs/simulation_quality/quality_scoring_contract.md` §12 Traceability item 3 from `[ ]`
  to `[x]`, citing both new test names and the resolution date; removed the "confirmed genuine
  gap" / follow-up-ticket language since this ticket is that follow-up, now closed.
- Cleaned `data/runs/` (removed `simq-wire-test` left by the reference test's own run and confirmed
  no `simq-traceability-test` directory existed).

## Test Summary
- `pytest tests/simulation_quality/test_traceability_path.py -v` — 3 passed.
- `pytest tests/simulation_quality/test_kernel_simq_integration.py tests/simulation_quality/test_quality_hub_integration.py tests/simulation_quality/test_traceability_path.py -v` — 17 passed, no regression in the reference pattern.
- `pytest tests/simulation_quality/ -q` — 463 passed, 2 skipped (pre-existing broker-mode skips).
- `find data/runs -maxdepth 1 -type d` — empty of any `simq-traceability-test` directory after every run.
- `python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/infrastructure.yaml'))"` — loads cleanly; new `INFRA-268` entry independently checked against `schema.json`'s per-item `required`/`if`/`then` rules.

## Files Changed
- `tests/simulation_quality/test_traceability_path.py` (new)
- `docs/parity_ledger/infrastructure.yaml` (additive: `INFRA-268`)
- `docs/simulation_quality/quality_scoring_contract.md` (§12 Traceability item 3 checkbox flip)

## Completion Summary
Added an integration test proving the §9 Traceability Design drill-down path (steps 1-3) holds
end-to-end: a `combat_hard_law_violation` event injected into a minimal `Kernel` produces a
`ScoreRecord` whose `event_id` lands in the COMBAT pillar's `worst_events` and is verifiably
present, with matching fields, in that run's `simulation_events.jsonl`. No production code changed
— this closes a test-coverage gap identified by `TCK-20260710-SIMQ-CONTRACT-AC-CLOSEOUT`, not a
functional bug. `docs/parity_ledger/infrastructure.yaml::INFRA-268` and
`quality_scoring_contract.md` §12's Traceability item 3 are both updated to reflect the closed gap.
All acceptance criteria met; all scoped tests pass; no stray run directories remain.
