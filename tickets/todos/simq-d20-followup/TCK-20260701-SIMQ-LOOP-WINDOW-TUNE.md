---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260701-SIMQ-LOOP-WINDOW-TUNE
phase: open
date: 2026-07-01
tags: [simq, calibration, loop-detection, tooling]
---

# TCK-20260701-SIMQ-LOOP-WINDOW-TUNE

## Title
Add per-run loop-detection window override to calibrate_simq.py; tune window per world type

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
D20 audit (Actionable Next Steps, P2 row) observes that loop detection for `hazard_active`
and `quest_active` suppresses events after ~40 ticks in 200-tick `sandbox_world` runs, cutting
off signal that should still score (NARRATIVE dropped from 16 events at 57 ticks to 3-4 events
at 200 ticks).

Investigation confirms:
- The window is defined in `src/simulation_quality/pillar_accumulator.py` (`PillarAccumulator.
  __init__`, default `window_size=200`) and the ratio threshold in the same class
  (`LOOP_THRESHOLD`, default 0.70, per `docs/simulation_quality/quality_scoring_contract.md`
  §4.7).
- Both values are already externalized to `config/simulation_quality/detection_params.yaml`
  and loaded via `ScoringWeights.detection` — this is **not hardcoded**, contrary to a naive
  read of the audit.
- The gap is that `window_size`/threshold apply **globally to every pillar and every world
  type** — there is no per-world-type profile, and `tools/calibrate_simq.py` has no CLI flag
  to try alternate values without hand-editing the YAML between runs.
- 1000-tick sandbox_world calibration data shows `quest_active` looping at tick 272, not ~40 —
  so the "~40 ticks" figure in the audit is an approximation for a specific pillar/tag
  combination in the 200-tick run, not a fixed constant across all loop flags. This needs
  empirical, not assumed, correction.

## Scope
1. Add a `--window-size` (and optionally `--loop-threshold`) CLI override to
   `tools/calibrate_simq.py` that overrides the YAML-loaded `ScoringWeights.detection` values
   for that run only (does not mutate `detection_params.yaml`).
2. Run a small sweep (e.g. window sizes 100/150/200/300) against 2-3 corpus worlds
   (sandbox_world, dungeon_crawl) to empirically determine whether the current 200-tick /
   0.70 threshold is actually suppressing real signal, and by how much, per pillar.
3. Based on sweep results, decide: keep global window/threshold as-is (if suppression is
   negligible), OR introduce a per-world-type detection profile (e.g.
   `detection_params_<world>.yaml`) loaded based on `--name`.
4. Document the decision and final values in `docs/simulation_quality/quality_scoring_contract.md`
   §4.7/4.8.
5. If parity ledger has no entry for loop detection, add one (`docs/parity_ledger/
   infrastructure.yaml` or `world_dynamics.yaml`, whichever governs SimQ tooling — confirm
   at implementation time).

## Out of Scope
- Changing the scoring deltas/weights for any pillar
- Adding new loop-detection tags beyond `hazard_active`/`quest_active`
- Re-running the full 13-run calibration corpus (only the sweep subset needed to decide)

## Acceptance Criteria
- [ ] `calibrate_simq.py` accepts a window-size override without editing
      `detection_params.yaml`
- [ ] Sweep data recorded (even informally, in the ticket's Implementation Notes or a stored
      artifact) showing suppressed-event counts at 2+ window sizes
- [ ] A documented decision: either "200/0.70 confirmed correct, no change" or "changed to
      X, per-world profile introduced" — not left ambiguous
- [ ] `quality_scoring_contract.md` §4.7/4.8 updated to match the decision
- [ ] No regression in `tests/simulation_quality/test_accumulator.py` or
      `test_grade_regression.py`

## Related Tickets
- **TCK-20260701-SIMQ-CALIBRATE-REFRESH — blocked on this ticket (see `SEQUENCE.md`).**
  Finish the window/threshold decision here first so the calibration refresh baselines
  against final settings instead of needing a second re-run.
- TCK-20260628-SIMQ-E7-CALIBRATE — original calibration script ticket
- TCK-20260630-SIMQ-CALFIX — fixed calibrate_simq.py world loading (prerequisite work)
- TCK-20260630-SIMQ-ANCHORS — grade regression anchors that may need revisiting if window
  size changes shift grades
- TCK-20260628-SIMQ-EPIC — parent epic (done)

## Related Docs
- `docs/audits/D20_simq_integration.md` — Actionable Next Steps, P2 row
- `docs/simulation_quality/quality_scoring_contract.md` §4.3 (PillarAccumulator state),
  §4.7 (Loop and Stagnation Detection)

## Related Stored Artifacts
- (none yet)

## Related Code Areas
- `src/simulation_quality/pillar_accumulator.py` — `PillarAccumulator.__init__`, loop-fire logic
- `config/simulation_quality/detection_params.yaml` — window_size, LOOP_THRESHOLD source
- `tools/calibrate_simq.py` — `_build_hub()`, CLI arg parsing

## Assumptions / Open Questions
- Assumes a single global window/threshold is the current intended design (per
  quality_scoring_contract.md §4.7) and any move to per-world profiles is a deliberate
  divergence requiring an entry in `docs/guidelines/v2_intentional_divergences.md`.
- Open question: is the "~40 ticks" audit figure specific to `quest_active` in
  `sandbox_world`'s exact event density, or a general pattern? Sweep data should resolve
  this rather than assuming either way.

## Implementation Notes
(to be filled at implementation)

## Test Summary
(to be filled at implementation)

## Files Changed
(to be filled at implementation)

## Completion Summary
(to be filled at completion)
