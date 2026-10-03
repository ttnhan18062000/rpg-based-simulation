---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260817-HOTFIX-WORLD-PROFILE-FIXTURE-4-MISSING-WORLDS
phase: done
date: 2026-08-17
tags: [simulation-quality, feature-flags, bug]
---

# TCK-20260817-HOTFIX-WORLD-PROFILE-FIXTURE-4-MISSING-WORLDS

## Title
Add 4 new worlds (added by commit `29d78798`) to `expected_world_flag_state.json`

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Real CI failures on the "Integration" job (run
https://github.com/ttnhan18062000/rpg-based-simulation/actions/runs/32000421496):
`tests/integration/test_world_profile_feature_flag_guardrail.py::test_all_worlds_have_a_resolvable_profile_or_default_fallback`
and `::test_fixture_covers_every_live_world_exactly` both failed.

Root cause (confirmed via investigation): `tests/simulation_quality/fixtures/expected_world_flag_state.json`
(17-world fixture, last touched by `TCK-20260704-SIMQ-CORPUS-SCENARIO-FLAG-GUARDRAIL`) was never
updated when 4 new worlds landed in commit `29d78798`: `lifecycle_full_coverage_world`,
`simq_scale_stress_seed42`, `unit_information_density`, `quest_dense_frontier`. Live world count is
now 21; fixture still had 17.

## Scope
- Add fixture entries for all 4 new worlds to
  `tests/simulation_quality/fixtures/expected_world_flag_state.json`, verified directly against
  each world's real `config/simulation_quality/profiles/*.yaml` (via `_resolve_profile()`'s actual
  file-existence check) and `data/worlds/*/world.yaml` content fields — not copied from the
  investigation report without independent verification:
  - `lifecycle_full_coverage_world`: profile file exists → `"lifecycle_full_coverage_world.yaml"`;
    flags `ADVENTURE_ROUTING=ON, BELIEF_ASSIMILATION=ON` (rest OFF); content
    `faction_tension_overrides=true, information_content=true, self_model_content=false`.
  - `simq_scale_stress_seed42`: profile file exists (empty `feature_flags: {}`) →
    `"simq_scale_stress_seed42.yaml"`; all 4 flags OFF; content `faction_tension_overrides=true`
    (real non-empty overrides), `information_content=false, self_model_content=false` (both empty
    lists in `world.yaml`).
  - `unit_information_density`: profile file exists → `"unit_information_density.yaml"`; flags
    `BELIEF_ASSIMILATION=ON` (rest OFF); content `faction_tension_overrides=false` (no such field
    in `world.yaml`), `information_content=true, self_model_content=false`.
  - `quest_dense_frontier`: no profile file → resolves to `"default"` → `profile_file: null`; all 4
    flags OFF (default.yaml has no `feature_flags:` key); content all `false` (no
    faction/information/self-model fields in `world.yaml`).
  - Bumped `_meta.world_count` from 17 to 21.

## Out of Scope
- Any other ticket in this batch.
- The 3 separate `Cluster 1` Integration-job failures (belief-event tests, hunger starvation) —
  own tickets.

## Acceptance Criteria
- [ ] `test_all_worlds_have_a_resolvable_profile_or_default_fallback` passes.
- [ ] `test_fixture_covers_every_live_world_exactly` passes.
- [ ] All other tests in the file (which cross-check flags/content bidirectionally against real
      production code, `_resolve_profile()`/`_load_profile_feature_flags()`) also pass — this is
      the strongest available correctness check on the new entries' values.

## Related Tickets
None — standalone, pre-existing, unrelated to recent session work.

## Related Docs
None.

## Related Stored Artifacts
None (hotfix tier).

## Related Code Areas
- `tests/simulation_quality/fixtures/expected_world_flag_state.json`

## Implementation Notes
Added the 4 entries above, each independently verified against the real profile YAML files (via
`_resolve_profile()`'s file-existence semantics) and each world's real `world.yaml` content fields,
not merely transcribed from the earlier investigation report. All 67 tests in
`test_world_profile_feature_flag_guardrail.py` pass, including the bidirectional
flag↔content-pairing tests (T4/T5) which would fail if any new entry's `information_content` or
`self_model_content` value disagreed with its flag state.

## Test Summary
- `pytest tests/integration/test_world_profile_feature_flag_guardrail.py -q`: 67 passed.

## Files Changed
- `tests/simulation_quality/fixtures/expected_world_flag_state.json` — added 4 world entries,
  bumped `world_count` to 21.

## Completion Summary
Fixed the stale fixture: added and independently verified fixture entries for the 4 worlds
introduced by commit `29d78798`, which the fixture's own source ticket predates. All bidirectional
consistency checks in the same test file pass, giving strong confidence the new entries are
correct, not just internally self-consistent.
