---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260914-BOSS-KINDS-OBSERVABILITY-CONSTANT-DRIFT
artifact_type: plan
tags: [observability, world]
---

# Implementation Plan — TCK-20260914-BOSS-KINDS-OBSERVABILITY-CONSTANT-DRIFT

## Summary
Define the two entity-kind concepts once (boss set, spawn-cadence exclusion tuple) in a new dependency-free leaf module `src/observability/entity_kind_constants.py`, with the extractor's current membership (includes `dragonkin`). Replace the inline literals in `event_extractor.py` (membership byte-identical) and `event_shapers.py` (gains `dragonkin` in both) with imports of those constants. This is a live default-path emitted-output change: `dragonkin` spawns newly emit `boss_spawned` + `narrative_milestone` (`first_boss_spawned`) and leave `spawn_cadence_fired.spawned_count`. Tests are written first (red on pre-fix shapers), then the constants and edits, then docs/ledger.

## Verified Facts (read this session)
- Shaper boss set: `src/observability/event_shapers.py:1144` `_BOSS_KINDS = frozenset(("world_boss", "ancient_sentinel"))` (class attribute of `WorldDynamicsShaper`), used `:1181`; `goblin_raider` elif `:1194`.
- Shaper exclusion: `event_shapers.py:1216` inline `(None, "world_boss", "ancient_sentinel", "goblin_raider")`.
- Extractor boss set: `event_extractor.py:1459` function-local `frozenset(("world_boss", "ancient_sentinel", "dragonkin"))`, used `:1462`; `goblin_raider` elif `:1480`.
- Extractor exclusion: `event_extractor.py:1355` `(None, "world_boss", "ancient_sentinel", "goblin_raider", "dragonkin")`.
- `event_shapers.py:26` already imports from `event_extractor`, so no new cycle risk from a leaf imported by both.
- Existing tests: `tests/unit/observability/test_event_shapers_world_dynamics.py` has `_entity`, `_update`, `_prior_state`, `_types` helpers and `test_boss_spawned_and_narrative_milestone` (`:112`).
- Parity entries: WORLD-109 (`docs/parity_ledger/world_dynamics.yaml:1422`, text lines ~1430-1447 state the shaper gap as a follow-up) and WORLD-115 (`:1614`).
- Doc rows: `docs/simulation_quality/event_type_coverage.md` `:179`, `:200`, `:345`.

## Steps

### Step 1 — Write failing tests first
**Files:** new `tests/unit/observability/test_entity_kind_constants.py`; edit `tests/unit/observability/test_event_shapers_world_dynamics.py` (append two tests, reuse existing helpers).
**Change:**
- In the new file, import `src.observability.entity_kind_constants as ekc` (names fixed in Step 2: `BOSS_ENTITY_KINDS` frozenset, `SPAWN_CADENCE_EXCLUDED_KINDS` tuple), `src.observability.event_shapers`, `src.observability.event_extractor`. Tests: (1) `WorldDynamicsShaper._BOSS_KINDS is ekc.BOSS_ENTITY_KINDS`, `event_extractor.BOSS_ENTITY_KINDS is ekc.BOSS_ENTITY_KINDS`, membership == `{world_boss, ancient_sentinel, dragonkin}`; (2) same identity for the exclusion tuple across both modules (shaper module-level name `SPAWN_CADENCE_EXCLUDED_KINDS`, extractor likewise), membership == `{None, world_boss, ancient_sentinel, goblin_raider, dragonkin}`; (3) `goblin_raider` in exclusion and not in boss set, `dragonkin` in both. No source-text/AST parsing.
- In the shapers test file add: dragonkin `entities_add` emits `boss_spawned` and `narrative_milestone` (`first_boss_spawned`), no `raid_party_spawned`; at tick 50 a dragonkin-only `entities_add` yields no `spawn_cadence_fired`, and dragonkin + villager yields `spawned_count == 1`.
- Run and confirm these fail for the right reason (ImportError / missing dragonkin) before Step 2.
**Do NOT touch:** existing tests, the fixture copy under `tests/fixtures/open_ticket_overlap/corpus/todos/`.
**Verify:** red run recorded; AC3 requires failure on pre-fix shapers.

### Step 2 — Create leaf constants module
**Files:** new `src/observability/entity_kind_constants.py`.
**Change:** Two module-level constants with extractor's current membership: `BOSS_ENTITY_KINDS = frozenset(("world_boss", "ancient_sentinel", "dragonkin"))` and `SPAWN_CADENCE_EXCLUDED_KINDS = (None, "world_boss", "ancient_sentinel", "goblin_raider", "dragonkin")` (tuple, order preserved). No imports beyond `from __future__ import annotations`. Comment names `src/world/boss.py` `check_for_boss_spawn()` / `check_for_lair_spawn()` as canonical producer and states the observability home is a deliberate interim, and that the two concepts must stay distinct (`goblin_raider` is not a boss kind). Writers/readers of this new file: none besides Steps 3-4 imports.
**Do NOT touch:** `src/world/boss.py`, `src/observability/config.py`; do not put the constants in `event_extractor.py`; do not merge the two constants.
**Verify:** import succeeds; Step 1 tests (1)-(3) still red on shaper identity only.

### Step 3 — Point the extractor at the constants (literal-to-import, membership identical)
**Files:** `src/observability/event_extractor.py` (imports; `:1355` tuple; `:1459` local set).
**Change:** Add module-level `from src.observability.entity_kind_constants import BOSS_ENTITY_KINDS, SPAWN_CADENCE_EXCLUDED_KINDS`. At `:1355` replace the inline tuple with `SPAWN_CADENCE_EXCLUDED_KINDS`; at `:1459` delete the local frozenset and use `BOSS_ENTITY_KINDS` at `:1462`. Rollback-path behavior must be byte-identical (extractor sets are never edited in membership).
**Do NOT touch:** the `_push_shapers_phase2_active` gating, the `goblin_raider` elif at `:1480`, any other extractor logic.
**Verify:** `tests/unit/observability/test_event_extractor_world_dynamics.py` (dragonkin cases, `TestSpawnCadrenceFired`), `test_event_extractor_world.py`, `test_event_extractor_narrative.py` pass unchanged.

### Step 4 — Point the shaper at the constants (the behavior change)
**Files:** `src/observability/event_shapers.py` (imports; `:1144`; `:1216`).
**Change:** Import the two constants. `:1144` becomes `_BOSS_KINDS = BOSS_ENTITY_KINDS` (alias kept so `self._BOSS_KINDS` at `:1181` is unchanged and identity holds). `:1216` uses `SPAWN_CADENCE_EXCLUDED_KINDS`. Effect: dragonkin now emits `boss_spawned` + `narrative_milestone`, and is excluded from `spawned_count`.
**Do NOT touch:** the `goblin_raider` branch (`:1194`), other shapers, `PHASE2_SHAPER_REGISTRY`, event payload shapes.
**Verify:** all Step 1 tests green; `test_event_shapers_world_dynamics.py`, `test_event_shapers.py` pass.

### Step 5 — Architecture and regression checks (report, never re-record)
**Files:** none edited.
**Change:** Run the scoped commands in test_plan.md: observability unit set, SimQ scorers (`tests/simulation_quality/test_world_dynamics_scorer.py`, `test_scenario_coverage.py`, `test_grade_regression.py`), and `tests/architecture/test_phase19_observability_boundaries.py`, `test_phase18_import_boundaries.py`, `tests/integration/observability/test_kernel_event_recording.py`. Record in the ticket Test Summary whether any recorded fixture/hash/baseline moved (investigation found none). If any moved: stop and report; do not re-record (`docs/testing/regression_policy.md` s13); doc/ledger change precedes test change; a moved fixture means a `docs/parity_ledger/infrastructure.yaml` touch.
**Do NOT touch:** any hash, baseline or scorer weight.
**Verify:** all green, or reported move.

### Step 6 — Update ledger and docs
**Files:** `docs/parity_ledger/world_dynamics.yaml` (WORLD-109, WORLD-115); `docs/simulation_quality/event_type_coverage.md` (`:179`, `:200`, `:345`).
**Change:** WORLD-109 text/`v2_evidence`: remove the "intentionally left unchanged / known follow-up gap" statement and the shaper-without-dragonkin quote; state both modules now import `BOSS_ENTITY_KINDS` and `SPAWN_CADENCE_EXCLUDED_KINDS` from `src/observability/entity_kind_constants.py`. WORLD-115: note the shaper recognizes dragonkin via the shared constants; confirm its `test_path` exists before editing; add the new test file to evidence. Event coverage rows: `boss_spawned` kinds become (world_boss, ancient_sentinel, dragonkin); `spawn_cadence_fired` rows name dragonkin in the exclusion and the shared module. Keep status `verified`, priority unchanged. If doc edits happen, run `make knowledge-index-update` at close.
**Do NOT touch:** `docs/parity_ledger/infrastructure.yaml` (unless a fixture moved), `docs/mechanics/05_world_evolution.md`, `docs/world/raid_boss_camp_contract.md`, `docs/guides/observability.md` (optional one-line mention only).
**Verify:** ledger YAML loads and validates against `docs/parity_ledger/schema.json`; WORLD-109 test_path still resolves.

## Fixtures / Hashes / Scorers That Could Move (AC4)
- Scorer `src/simulation_quality/scorers/world_dynamics.py` keys on `boss_spawned` (`boss_active`) and `spawn_cadence_fired`; its tests (`test_world_dynamics_scorer.py`, `test_scenario_coverage.py::test_sq17_world_owns_boss_spawned`) use synthetic envelopes, expected unaffected.
- `tests/simulation_quality/test_grade_regression.py`: no boss reference found.
- No json/jsonl/yaml fixture under `tests/` references `boss_spawned` or `spawn_cadence` (investigation survey).
- Corpus-backed baselines: whether runs spawn dragonkin is unmeasured; any move is reported, not re-recorded.

## Scope Guards
- Do not change extractor membership or remove `dragonkin` anywhere.
- Do not merge the boss set and exclusion tuple; `goblin_raider` stays out of the boss set.
- No other observability constants, no pipeline restructuring, no changes to `src/world/boss.py` or the sibling ticket's maturity/tier/loot questions.
- No source-text/AST test; no claim that dragonkin spawns in corpus runs.
- Do not edit the fixture copy under `tests/fixtures/open_ticket_overlap/corpus/todos/`.
- No hash/baseline re-recording.

## Dependency Map
Step 1 first (red). Step 2 before 3 and 4. Steps 3 and 4 independent of each other. Step 5 after 3 and 4. Step 6 after 4 (can parallel 5), but ledger text must match the final constant names.

## Acceptance Criteria Map
| AC | Step(s) | Verified by |
|---|---|---|
| Boss sets and exclusion tuples have identical membership across shaper and extractor | 2, 3, 4 | `test_entity_kind_constants.py` tests 1-2 |
| `goblin_raider` in neither boss set | 2 | test 3 |
| Drift test fails on pre-fix shapers (identity + membership) | 1 | red run in Step 1, green after Step 4; shapers tests 4-5 |
| Plan names fixtures/hashes/scorers; run reports whether any moved | 5 | "Fixtures/Hashes/Scorers" section; Step 5 report in Test Summary |

AC cross-check: ticket AC names (boss-kind set, inline exclusion tuple, `goblin_raider`, shared constant objects) match the Steps; constant names are fixed as `BOSS_ENTITY_KINDS` and `SPAWN_CADENCE_EXCLUDED_KINDS` throughout.

## Anti-Drift Notes
- Extractor's set is function-local, the shaper's is a class attribute; the alias `_BOSS_KINDS = BOSS_ENTITY_KINDS` must be an identity (`is`), not a copy (`frozenset(...)` of it would break identity).
- Shared resource writers: the new module has no other writers; the two edited files' other writers (extractor rollback path, shaper default path) are mutually exclusive via `_push_shapers_phase2_active` (default ON, `event_extractor.py:146`), so no double-emission.
- Verify `test_phase19_observability_boundaries.py` hot-path import check: the leaf has no forbidden imports.

## Unresolved Questions
None. (Constant names are a plan decision within the ticket's "e.g." latitude; tell the implementer if architecture review prefers others.)
