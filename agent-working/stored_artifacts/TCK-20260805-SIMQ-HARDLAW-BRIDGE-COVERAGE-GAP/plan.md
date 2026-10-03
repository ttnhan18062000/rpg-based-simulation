---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260805-SIMQ-HARDLAW-BRIDGE-COVERAGE-GAP
artifact_type: plan
tags: [simulation-quality, observability, world]
---

# plan.md — TCK-20260805-SIMQ-HARDLAW-BRIDGE-COVERAGE-GAP

## Ordered Steps

1. **Check git history for the `COMBAT`/`CONSERVATION` prefix branches' origin** — determine
   whether to repurpose them or add new branches (this ticket's central open question).
   - No files changed — investigation only.
2. **Add exact-match `law_id` routing** for the 6 previously-untranslated laws in
   `quality_hub.py::_translate_invariant()`, reusing `combat_hard_law_violation`/
   `conservation_law_violated` where domain fit is genuine (HP/READINESS, GOLD), adding a new
   `world_hard_law_violation` signal for the 3 that don't fit any existing generic signal
   (STAMINA, POSITION, OCCUPANCY-COLLISION).
   - Files: `src/simulation_quality/quality_hub.py`.
3. **Wire `world_hard_law_violation` into `WorldDynamicsScorer`** — `EVENT_TYPES`, `score()`
   branch, `scoring_weights.yaml` entry — following `spawn_occupancy_violation`'s exact pattern.
   - Files: `src/simulation_quality/scorers/world_dynamics.py`,
     `config/simulation_quality/scoring_weights.yaml`.
4. **Update and fix tests** — the existing `test_invariant_spawn_occupancy_no_violation_no_translation`
   test used `LAW-HP-NONNEGATIVE` as its "unknown law" example, which is no longer true after step
   2; corrected and renamed, plus new explicit tests for all 6 routed laws and the new scorer
   signal.
   - Files: `tests/simulation_quality/test_quality_hub_event_translation.py`,
     `tests/simulation_quality/test_world_dynamics_scorer.py`.
5. **Update docs**: `quality_scoring_contract.md` (WORLD DYNAMICS event list + signal table),
   `event_type_coverage.md` (scored count 83→84, translation table rows, "Last updated" note),
   `extension_points.md` axis 9 (from "open gap" to "fixed").
   - Files: `docs/simulation_quality/quality_scoring_contract.md`,
     `docs/simulation_quality/event_type_coverage.md`, `docs/simulation_quality/extension_points.md`.

## Scope Guards

- Do NOT touch `HardLawMonitor`'s law-check logic — laws themselves are correct and unchanged.
- Do NOT rename the 6 real laws to match the speculative `COMBAT`/`CONSERVATION` prefixes.
- Do NOT touch the already-known `LONG_RUN` mode logging gap noted in `hard_law_monitor.md` —
  unrelated to SimQ translation.

## Dependency Map

Step 1 informs step 2's design (repurpose vs. extend). Step 3 depends on step 2 (needs the new
event type name decided). Step 4 depends on steps 2-3. Step 5 is independent, can run in parallel
with 2-4.

## Acceptance Criteria Map

- AC1 (explicit decision per law, documented) → investigation.md's table.
- AC2 (new bridges follow the existing pattern, anchors recalibrated if affected) → Steps 2-3; no
  anchor recalibration needed since 0 real corpus scenarios currently trigger any of these 6 laws
  (confirmed via full test suite run — 0 score deltas).
- AC3 (dormant COMBAT/CONSERVATION branches explicitly resolved) → Step 1's finding, documented in
  investigation.md and `event_type_coverage.md`.
- AC4 (extension_points.md axis 9 updated) → Step 5.

No unresolved questions requiring human review.
