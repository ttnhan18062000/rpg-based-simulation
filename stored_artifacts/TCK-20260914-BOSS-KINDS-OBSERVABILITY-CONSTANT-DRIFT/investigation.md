---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260914-BOSS-KINDS-OBSERVABILITY-CONSTANT-DRIFT
artifact_type: investigation
tags: [observability, world]
---

# Investigation — TCK-20260914-BOSS-KINDS-OBSERVABILITY-CONSTANT-DRIFT

Search note: `search_docs` was called first (surfaced the push-shaper tickets and `docs/simulation_quality/event_type_coverage.md`). `graphify query` failed (`graphify-out/graph.json` absent in this worktree), so source was read directly afterwards.

## Current Behavior
Two concepts, four sites (verified in source, not just from the ticket):

- Shaper boss set: `src/observability/event_shapers.py:1144` `WorldDynamicsShaper._BOSS_KINDS = frozenset(("world_boss","ancient_sentinel"))` (class attribute). Used at `:1181` (`if kind in self._BOSS_KINDS` emits `boss_spawned` + `narrative_milestone`/`first_boss_spawned`; `elif kind == "goblin_raider"` at `:1194` emits `raid_party_spawned`).
- Shaper exclusion tuple: `event_shapers.py:1216` inline `(None,"world_boss","ancient_sentinel","goblin_raider")` in the `tick % 50 == 0` `spawn_cadence_fired` block (`spawned_count`).
- Extractor boss set: `src/observability/event_extractor.py:1459` function-local `_BOSS_KINDS = frozenset(("world_boss","ancient_sentinel","dragonkin"))`, used `:1462`; `goblin_raider` elif `:1480`.
- Extractor exclusion tuple: `event_extractor.py:1355` inline `(None,"world_boss","ancient_sentinel","goblin_raider","dragonkin")`.

Live-path verification: the extractor's boss block iterates `[] if _push_shapers_phase2_active`, and the cadence block is `if not _push_shapers_phase2_active and ...`. `_push_shapers_phase2_active` defaults ON (`event_extractor.py:146`, `ENABLE_PUSH_EVENT_SHAPERS_PHASE2` default "ON"). So the shaper is the live default path and is the one missing `dragonkin`; the extractor is rollback-only. The relayed claim is confirmed. Producer: `src/world/boss.py` `check_for_lair_spawn()` (kind `dragonkin` at ~:234), `check_for_boss_spawn()` (:30).

Net effect on the default path: a `dragonkin` entity in `entities_add` newly emits `boss_spawned` + `narrative_milestone` and no longer counts toward `spawn_cadence_fired.spawned_count`. This is an emitted-output change, not a pure refactor.

Full-set diff (the ticket asked not to just add `dragonkin`): boss sets differ only by `dragonkin`; exclusion tuples differ only by `dragonkin`. No other discrepancy.

## Mechanics / Engine Constraints
- Telemetry-only; observers are read-only (`docs/guides/observability.md`). `docs/mechanics/05_world_evolution.md` (Lair note ~:412) and `docs/world/raid_boss_camp_contract.md` (~:195, Lair spawn generalization) define the producer; no formula changes.
- The new leaf constants module must not import forbidden heavy analyzers: `tests/architecture/test_phase19_observability_boundaries.py::test_hot_path_does_not_import_heavy_analyzers` treats `event_extractor.py` as hot path (forbidden prefixes anomaly/cognition/reporting). A dependency-free leaf is safe. Verify `tests/architecture/test_phase18_import_boundaries.py` still passes.
- Determinism: frozensets with fixed membership; no ordering dependence.
- `docs/testing/regression_policy.md` §13: no re-recording hashes/baselines to pass a gate.

## Docs Requiring Update
- `docs/parity_ledger/world_dynamics.yaml`: WORLD-109 `text`/`v2_evidence` state the shaper lists were "intentionally left unchanged ... known follow-up gap" and quote shaper sets without dragonkin; this becomes false. Update to describe the shared constants. WORLD-115 text/`v2_evidence` should note the shaper now recognizes dragonkin via the shared constants.
- `docs/simulation_quality/event_type_coverage.md`: the `boss_spawned` row (~:200) says "entity kind in (world_boss, ancient_sentinel)"; the `spawn_cadence_fired` rows (~:179, :345) say "non-boss entities_add". Update to include dragonkin and name the shared constants module.

Considered and excluded (prose only): `docs/guides/observability.md` file table needs no change (an optional one-line mention of the new leaf module is the implementer's call); `docs/parity_ledger/infrastructure.yaml` is touched only if a recorded event-count fixture moves (none found, see Risks); `docs/mechanics/05_world_evolution.md` and `docs/world/raid_boss_camp_contract.md` describe producers, not observability classification, so they need no change.

## Parity Ledger Overlap
- WORLD-109 (verified, P1; test_path `tests/unit/observability/test_event_extractor_world_dynamics.py::TestSpawnCadrenceFired` etc.). Its text records the gap this ticket closes.
- WORLD-115 (verified, P1; shaper definition). Check its test_path exists before editing.
- No P0 entries involved. infrastructure.yaml only if a fixture moves.

## Prior Work
- `TCK-20260904-LAIR-ENTITY-ANCHOR` added `dragonkin` to the extractor only and recorded the shaper gap as a follow-up (WORLD-109 note).
- `TCK-20260806-PUSH-SHAPER-REGISTRY-WORLD-DYNAMICS` (stored_artifacts) created WorldDynamicsShaper with 1:1 extractor parity at that time; the drift arose afterward.
- Sibling: `TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY` (`tests/unit/world/test_boss_gate_reachability.py`).

## Risks and Open Questions
- Fixtures/hashes/scorers that could move (the plan must list them and the run must report): scorer `src/simulation_quality/scorers/world_dynamics.py` keys on `boss_spawned` (`boss_active` weight, ~:86) and `spawn_cadence_fired`; `tests/simulation_quality/test_world_dynamics_scorer.py` and `test_scenario_coverage.py::test_sq17_world_owns_boss_spawned` use synthetic envelopes (unaffected). A search of tests/ for json/jsonl/yaml fixtures containing `boss_spawned`/`spawn_cadence` found none; `test_grade_regression.py` has no boss reference. Whether any corpus run spawns `dragonkin` is unmeasured; if a corpus-backed baseline (grades/event counts) moves, report it and do not re-record.
- Existing shaper tests use MagicMock entities with an explicit `kind`; unaffected.
- Open: confirm the new module does not trip any module-listing/layering architecture test (14 files currently in `src/observability/`).
- No oracle conflict: oracle for the telemetry set is the ledger plus the `src/world/boss.py` producer; no Bible section defines it.

## Anti-Drift Hazards
- Do not merge the boss set and the exclusion tuple (`goblin_raider` must stay out of the boss set and in the exclusion tuple).
- Do not alter extractor membership or remove `dragonkin` anywhere; the extractor edit is literal-to-import only with byte-identical membership.
- The extractor's `_BOSS_KINDS` is function-local; the shaper's is a class attribute `self._BOSS_KINDS`. If an alias is kept, tests must assert identity (`is`) with the module constant.
- No source-text/AST parsing in tests. No restructuring of the shaper pipeline. Do not edit the fixture copy under `tests/fixtures/open_ticket_overlap/corpus/todos/`.
- Do not claim dragonkin events are observed in corpus runs.
