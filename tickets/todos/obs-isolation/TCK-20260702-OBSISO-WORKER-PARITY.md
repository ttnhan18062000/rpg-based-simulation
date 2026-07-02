---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260702-OBSISO-WORKER-PARITY
phase: open
date: 2026-07-02
tags: [simulation-quality, broker-mode, worker, scorers, grade-parity, determinism]
---

# TCK-20260702-OBSISO-WORKER-PARITY

## Title
QualityWorker full-pillar scorer registry + in-process/broker grade parity

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`QualityWorker.__init__` (`src/simulation_quality/worker.py`) constructs only `AgencyScorer` and `CombatScorer` — 2 of the 10 pillar scorers. Broker-mode runs therefore produce grades that silently omit 8 pillars and are not comparable to in-process grades or to the 25-anchor calibration corpus. Extract the scorer-registry construction the kernel path uses into one shared builder, use it in both paths, and prove grade parity between modes.

## Scope
- Locate the in-process scorer construction (kernel init path, `src/engine/kernel.py` around the `QualityHub` setup — follow `_quality_hub` construction) and extract a shared factory, e.g. `build_all_scorers(weights) -> list[PillarScorer]` in `src/simulation_quality/` (natural home: `scorers/__init__.py` or `quality_hub.py`), covering all 10 pillars (AGENCY, COMBAT, ECONOMY, SOCIAL, FACTION, INFORMATION, COGNITION, PROGRESSION, NARRATIVE, WORLD).
- `QualityWorker` and the kernel path both consume the factory — one construction site, impossible to drift.
- Grade-parity proof: a test replays a recorded envelope stream (reuse fixtures/pattern from `tests/simulation_quality/test_quality_hub_event_translation.py` / `test_quality_hub_integration.py`) through (a) a hub built the in-process way and (b) a hub built the worker way, asserting identical `ScoreRecord` output per pillar. Scoring must be deterministic given the same envelope sequence.
- Extend `/health` payload in `worker.py` with per-pillar processed-event counts (cheap dict), so a crippled registry is observable at runtime rather than silent.
- Worker weights/config loading: verify `ScoringWeights.load(...)` in the worker resolves the same profile files the engine uses; align env defaults if they diverge.

## Out of Scope
- Stream config unification and kernel routing (TCK-20260702-OBSISO-BROKER-CONFIG — must land first)
- Changing any scorer logic or weights
- Anchor recalibration (grades must not change in-process; if the parity work reveals in-process registry gaps, that becomes its own finding)

## Acceptance Criteria
- Grep-proof: no scorer list literal exists outside the shared factory (`AgencyScorer(` appears only in the factory and tests).
- Parity test passes: identical `ScoreRecord`s from both construction paths over the same envelope fixture, all 10 pillars represented.
- `make evaluate --dry-run` unchanged (in-process grades unaffected).
- Worker `/health` reports all 10 pillars with event counts after consuming a fixture stream.
- Existing `tests/simulation_quality/` suite passes.

## Related Tickets
TCK-20260702-OBSISO-BROKER-CONFIG (prerequisite), TCK-20260628-SIMQ-E1-FOUNDATION (scorer/model layer), TCK-20260702-OBSISO-EPIC

## Related Docs
docs/plans/observability_process_isolation.md (G2), docs/simulation_quality/quality_scoring_contract.md (§ pillars, §11 tests), docs/guides/simulation_quality.md

## Related Stored Artifacts
stored_artifacts/TCK-20260628-SIMQ-E1-FOUNDATION (if present)

## Related Code Areas
src/simulation_quality/worker.py, src/simulation_quality/quality_hub.py, src/simulation_quality/scorers/__init__.py + scorers/*.py, src/engine/kernel.py (hub construction), src/simulation_quality/weights.py

## Assumptions / Open Questions
- Assumption: all 10 scorers are stateless w.r.t. process boundary (no engine-state reads outside envelope payloads) — the ScoringContext design suggests yes; the parity test will prove it. Any scorer that reads live engine state is itself an isolation violation → report as new finding.

## Implementation Notes
The 2-scorer list in the worker looks like scaffold code from the feed's original ticket that was never revisited once all 10 scorers existed. Check `git log`/`stored_artifacts` for the worker's origin ticket before assuming intent.

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
