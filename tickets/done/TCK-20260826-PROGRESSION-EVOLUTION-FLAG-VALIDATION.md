---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION
phase: done
date: 2026-08-26
tags: [feature-flags]
---

# TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION

## Title
Produce real validation evidence for `ENABLE_PROGRESSION_EVOLUTION` before deciding its default

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Named follow-up from `TCK-20260824-ROLLOUT-FLAG-DECISIONS`: `ENABLE_PROGRESSION_EVOLUTION` was
kept `OFF` by default -- real call site (`ProgressionConversionPhase.execute`, gated by the
`progression_conversion` phase name at `src/engine/pipeline.py:322`), 2 test files, but no corpus
profile turns it on and no SHADOW-validation history exists. This confirms
`TCK-20260824-ROLLOUT-FLAG-DECISIONS`'s own open Assumption: the M1 epic plan's "Progression
Conversion" prose naming maps to this exact flag. This ticket's job is to produce real evidence.

## Scope
- Run a real corpus-profile trial with the flag `ON` against at least one world.
- Given only 2 test files reference this flag (the thinnest coverage of the 5 deferred flags),
  confirm real test depth before trusting a trial's result -- a false-clean pass from shallow
  coverage would be worse than an honest "not enough coverage to trust a trial yet" finding.
- Produce a real keep/flip recommendation with evidence.

## Out of Scope
- Actually flipping the flag's default.
- Writing new test coverage beyond what's needed to trust the trial itself (a full coverage
  build-out, if warranted, is its own separate scope decision).

## Acceptance Criteria
- [x] Test coverage depth is assessed honestly before the trial, not assumed adequate
- [x] A real corpus-profile ON trial is run and documented
- [x] A keep/flip recommendation with evidence is produced

## Related Tickets
- TCK-20260824-ROLLOUT-FLAG-DECISIONS (source of this deferral; also resolved the
  Progression-Conversion-naming-maps-to-this-flag assumption)

## Related Docs
- docs/guidelines/intentional_divergences.md (DEV-002, DEV-003)

## Related Stored Artifacts
- staging_artifacts/TCK-20260824-ROLLOUT-FLAG-DECISIONS/investigation.md

## Related Code Areas
- src/engine/pipeline.py (progression_conversion phase)
- src/domains/optimization/feature_flags.py

## Assumptions / Open Questions
None yet -- to be surfaced during this ticket's own investigation.

## Implementation Notes
Carried forward investigation.md's own Test Coverage Depth Assessment verdict (deep isolated
domain-logic coverage across 10 `test_phase6_*.py` files, but thin pipeline-wiring coverage — only
2 files reference the flag by name, and the one real-`Kernel`-loop test only proves the OFF state).
That gap is exactly why the finding below went undetected until this ticket's real trial.

Ran the real 4-leg corpus trial per plan.md Steps 2-3, using
`/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3` (bare `python3` in this worktree
lacks `pydantic`, the same pre-existing environment gap all 3 prior sibling flag-validation
tickets hit): `dungeon_crawl` (32 entities, seed 42, 2000 ticks) and `frontier_extended` (59
entities, seed 42, 1000 ticks — no `--profile default` needed since `frontier_extended.yaml`
exists and `calibrate_simq.py`'s `_resolve_profile()` auto-resolves to it), each OFF then
`ENABLE_PROGRESSION_EVOLUTION=ON`.

**Both OFF legs completed cleanly (exit 0). Both ON legs crashed the real `Kernel` pipeline
(exit 1), deterministically, in both worlds** — `TypeError: Object of type ProgressionDecisionResult
is not JSON serializable` inside `CanonicalStateHasher.get_hash()`
(`src/engine/checkpoint.py:48`), triggered the moment `ProgressionConversionPhase.execute()`
(`src/domains/progression/phase.py:80`) writes its raw decision dataclass into
`property_updates["last_progression_decision"]` and the next tick's `_phase_persistence()` tries
to canonically hash the full state under `calibrate_simq.py`'s `replay_richness == "FULL"` policy.
Reproduced 4 independent times (2x `dungeon_crawl` ON, 1x `frontier_extended` ON via
`calibrate_simq.py`, 1x a read-only diagnostic replay used only to sample the decision
distribution before the crash — no `src/` edits, no fabricated ledger data). This is a genuinely
new finding beyond what investigation.md predicted: investigation.md had flagged the raw-dataclass
storage as an architecture smell adjacent to the Durable State Rule, but not that it crashes
`Kernel` persistence. The diagnostic replay also directly confirmed investigation.md's separate
prediction: all 32 sampled `dungeon_crawl` entities converged 100% on `SAVE_FOR_LATER` (the
reward-ledger producer gap — `RewardLedgerService` has zero live callers anywhere in `src/`).

Per the plan's own Anti-Drift/Scope Guards, this defect is disclosed, not fixed —
`src/domains/progression/phase.py` was not touched (confirmed via `git diff --stat -- src/`,
empty). Wrote the full raw record to
`staging_artifacts/TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION/trial_evidence.md` and
updated `docs/architecture/rollout_flag_decisions_m1.md`'s `ENABLE_PROGRESSION_EVOLUTION` row plus
a new "Validation Trial Result" section (placed after the `ENABLE_WORLD_EMERGENCE` section, before
`RolloutProfileManager — Cut`, matching the 3 sibling sections' format).

Ran the scoped pytest suite from test_plan.md's "Scoped Pytest Commands" section — both blocks
pass unmodified (140 passed; 1 passed). Cleaned up `data/runs/*`, `reports/release_proof/*`, and
the 4 `data/calibration/*progression_evolution*` trial directories per Definition of Done.
`src/domains/optimization/feature_flags.py`'s `ENABLE_PROGRESSION_EVOLUTION` default was not
changed (confirmed unmodified).

## Test Summary
```
pytest tests/unit/domains/progression/ tests/integration/domains/progression/ \
  tests/integration/scenarios/test_phase6_progression_conversion_scenarios.py \
  tests/integration/progression/test_allocate_ap_dormancy.py \
  tests/integration/test_scenario_feature_flag_defaults.py \
  tests/unit/entity/test_phase6_reward_ledger_component.py \
  tests/unit/observability/test_event_extractor_equipment.py \
  tests/unit/observability/test_event_extractor_progression.py \
  tests/unit/observability/test_event_shapers_progression.py \
  tests/unit/quest/test_progression_regression.py \
  tests/unit/config/test_phase10_feature_flags.py \
  -m "not slow"
=> 140 passed

pytest tests/perf/test_phase6_progression_conversion_budget.py
=> 1 passed
```
No new test files were written (test_plan.md's "New Tests Required: None" — this ticket's scope is
evidence-gathering only, per its Out of Scope: "Writing new test coverage beyond what's needed to
trust the trial itself").

## Files Changed
- `staging_artifacts/TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION/trial_evidence.md` (new)
- `docs/architecture/rollout_flag_decisions_m1.md` (row update + new section)
- `tickets/inprogress/TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION.md` (this file)
- `staging_artifacts/TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION/investigation.md`,
  `plan.md`, `test_plan.md` — already present from this run's own prior Investigate/Plan phases
  (not authored during this Implement step, but part of this run's real changeset; no
  deviation from either was required during Implement)
- No `src/` files changed (confirmed: `git diff --stat -- src/` is empty)

## Completion Summary
Ran a real 4-leg (2-world x OFF/ON) corpus trial for `ENABLE_PROGRESSION_EVOLUTION` via
`tools/calibrate_simq.py`. Both OFF legs completed cleanly; **both ON legs deterministically
crashed the real pipeline** (`CanonicalStateHasher.get_hash()` cannot JSON-serialize the raw
`ProgressionDecisionResult` the phase stores into `property_updates`), a materially stronger "keep
OFF" finding than any of the 3 prior sibling flag-validation tickets produced. A supplementary
diagnostic replay also directly confirmed investigation.md's separate prediction — 100%
`SAVE_FOR_LATER` convergence across all sampled entities, caused by the reward-ledger producer gap
(`RewardLedgerService` has zero live callers in `src/`). Recommendation: **keep OFF, deferred**,
with two concrete, named blocking prerequisites for any future flip-ON decision: (1) fix the
JSON-serialization crash (make `last_progression_decision` a typed serializable structure, or
strip it before persistence), and (2) wire a real reward-ledger producer so a future trial can
exercise the phase's non-fallback decision paths. Neither was fixed inline, per this ticket's
explicit evidence-gathering scope. No `src/` files were touched; the flag's code default remains
unchanged.
