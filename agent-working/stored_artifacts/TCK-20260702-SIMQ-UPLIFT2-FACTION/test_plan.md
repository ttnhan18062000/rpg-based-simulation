# Test Plan — TCK-20260702-SIMQ-UPLIFT2-FACTION

## Regression Surface (existing tests that must pass)

Code areas touched: `src/worldbuilding/schema.py` (`FactionSpec`),
`src/worldbuilding/compiler.py` (`WorldCompiler.compile()` step 3),
`data/content/world_modules/bandit_road_trade_pressure.yaml` and/or
`frontier_village_core.yaml` (module-level faction declarations),
`data/worlds/urban_political/resolved/world.resolved.yaml` (regenerated, not hand-edited),
`docs/parity_ledger/faction.yaml`.

| Test file | Why it must still pass |
|---|---|
| `tests/unit/worldbuilding/test_worldspec_schema.py` | `test_valid_minimal_world_spec_loads` asserts `spec.factions == []` for a spec with no `factions:` key — must still hold; adding an optional `initial_tension_level` field with a default must not change empty-list behavior. |
| `tests/unit/worldbuilding/test_world_compiler.py` | `test_compiler_minimal_world` compiles a spec whose `factions` entries have no `initial_tension_level` key — must still compile and must not assert on `state.factions` today (baseline: no regression if a new `state.factions` assertion is added elsewhere, but this existing test's assertions on `global_resources` faction vaults must be untouched). |
| `tests/unit/worldbuilding/test_compiler_context.py` | Exercises `CompileContext` overrides during compile; must not break if `WorldCompiler.compile()` gains new logic reading `f_spec.initial_tension_level`. |
| `tests/unit/faction/test_faction_state.py` (all 10 tests) | `FactionState`/`FactionUpdate`/apply-path behavior is unchanged by this ticket — these must pass unmodified as a sanity check that the durable-state contract itself isn't touched. |
| `tests/unit/faction/test_diplomacy.py` | `compute_transitions()` threshold logic (`pair_tension > 0.4` etc.) is unchanged — this ticket only changes what value flows *into* that function, not the function itself. |
| `tests/unit/faction/test_faction_awareness.py`, `test_faction_decision_phase.py` | Both iterate `state.factions` — must confirm they still pass with `state.factions` now non-empty by default for worlds with `factions:` declared (these tests likely construct `AuthoritativeState` directly with explicit `factions=` kwargs, so should be unaffected, but must be run to confirm no implicit assumption of "factions can be assumed empty unless explicitly passed"). |
| `tests/certification/test_world_compile_determinism.py` | Verifies `report1["state_hash"] == report2["state_hash"]` for same seed and `!=` for different seed/spec. Confirmed via `src/replay/fingerprint.py` that `factions` is **not** part of the hashed fields — this test should be unaffected, but run it to confirm no incidental coupling. |
| `tests/unit/chronicle/test_faction_chronicle.py` | Downstream faction-event rendering tests; unaffected by tension seeding directly but shares the faction domain — run as a smoke check. |
| `tests/unit/worldassembly/` (whole dir, if present) or resolver-adjacent tests | `WorldAssemblyResolver`'s faction-merge step must tolerate the new `FactionSpec` field across modules without collision-detection false positives. Locate exact test dir/file during implementation (not enumerated here — confirm via `find tests -iname '*resolver*' -o -iname '*assembly*'`). |
| `tests/simulation_quality/` calibration/scoring tests that assert `FACTION` grade or `calibration_hits` baselines | Any fixture pinned to the current "FACTION=C, 0 hits" baseline for `urban_political_*` scenarios will need updating alongside `grade_anchors.json` — treat any such assertion as an intentional-change target, not a regression to preserve as-is. |

## New Tests Required (per AC)

1. **`FactionSpec` accepts `initial_tension_level`, defaults to 0.0**
   (`tests/unit/worldbuilding/test_worldspec_schema.py`, new test):
   - `FactionSpec(id="x", type="civilian")` → `.initial_tension_level == 0.0` (default,
     backward compatible).
   - `FactionSpec(id="x", type="civilian", initial_tension_level=0.5)` → round-trips.
   - A `WorldSpec` loaded from YAML with a `factions:` entry that omits
     `initial_tension_level` still validates (regression guard, mirrors existing
     `test_valid_minimal_world_spec_loads` pattern).
   - Optional: reject out-of-range values (`initial_tension_level=1.5`) if the
     implementation adds a `Field(..., ge=0.0, le=1.0)` bound — decide during
     implementation and test whichever behavior is chosen (bounded field vs. unbounded
     float clamped later by the compiler).

2. **`WorldCompiler.compile()` seeds `FactionState.tension_level` from the spec**
   (`tests/unit/worldbuilding/test_world_compiler.py`, new tests):
   - `test_compiler_seeds_faction_tension_from_spec`: build a spec with
     `factions=[FactionSpec(id="a", type="x", initial_tension_level=0.5), FactionSpec(id="b", type="y")]`,
     compile, assert `state.factions["a"].tension_level == 0.5` and
     `state.factions["b"].tension_level == 0.0`.
   - `test_compiler_seeds_full_faction_roster_at_zero_tension_by_default`
     (regression/AC): a spec with `factions` declared but no
     `initial_tension_level` anywhere → every faction ID in `spec.factions` appears in
     `state.factions` with `tension_level == 0.0` (confirms the roster now populates,
     addressing the "closed loop with no bootstrap" finding in investigation.md, not just
     the tension value).
   - `test_compiler_no_factions_declared_yields_empty_factions_dict`: a spec with
     `factions=[]` (or omitted) → `state.factions == {}` (confirms no behavior change for
     faction-less specs, e.g. `dungeon_crawl`).
   - Assert `state.factions[id].faction_id == id` and that other `FactionState` fields
     (`territory`, `resources`, `diplomatic_relations`, `military_strength`) retain their
     dataclass defaults (`()`, `{}`, `{}`, `1.0`) since `FactionSpec` does not currently
     supply values for those — only `tension_level` should be non-default.

3. **`urban_political` world declares `bandit_company`/`town_council` tension**
   (integration-level, exercised via compiled resolved spec, not a new unit test file):
   - Add/extend a test (e.g. `tests/integration/worlds/test_urban_political_world.py` if
     such a file exists, else a new focused test in
     `tests/unit/worldbuilding/test_world_compiler.py`) that loads
     `data/worlds/urban_political/resolved/world.resolved.yaml` via
     `load_world_spec_from_yaml`, compiles it with a fixed seed, and asserts
     `state.factions["bandit_company"].tension_level >= 0.5` (or `town_council`,
     depending on which faction(s) the implementation seeds — confirm against the final
     Implementation Notes).
   - Search `tests/` for an existing `urban_political` world-load test before adding a
     new file (`grep -rl "urban_political" tests/`) to avoid duplicating fixture setup.

4. **`compute_transitions()` fires `NEUTRAL → TENSE` with the new seed value**
   (`tests/unit/faction/test_diplomacy.py`, new test — pure-function-level, no engine run
   needed):
   - Construct `factions = {"bandit_company": FactionState(faction_id="bandit_company", tension_level=0.5), "town_council": FactionState(faction_id="town_council")}`.
   - `compute_transitions(factions)` returns two `FactionUpdate` records setting
     `diplomatic_relations_set={"town_council": DiplomaticState.TENSE}` (and the mirror).
   - This isolates the pure-function proof from the full-pipeline/calibration proof —
     cheap and deterministic, should be added regardless of calibration re-run cost.

5. **Calibration produces non-zero FACTION hits** (manual/tool-driven, not pytest):
   - `python3 tools/calibrate_simq.py --ticks 500 --seed 42 --name urban_political`
     (matches ticket's `urban_political_seed42_500t` scenario naming) — inspect
     `data/calibration/urban_political_seed42_500t/quality_report.json` (or wherever the
     tool writes it — confirm exact path via `calibrate_simq.py` before running) for
     `diplomatic_transition` or `faction_tension_delta` `calibration_hits > 0`.
   - Cross-check against `docs/simulation_quality/event_type_coverage.md` lines 115/118 —
     update the `calibration_hits` column from `0` to the observed count.

6. **`make evaluate --dry-run` / `tools/evaluate_simq.py --dry-run` exits 0**
   (manual gate, not a new pytest test):
   - Run after `grade_anchors.json` (`tests/simulation_quality/fixtures/grade_anchors.json`)
     is updated for any FACTION grade change on `urban_political_*` scenarios.
   - Confirm 0 regressions on every other pillar/scenario — a passing exit code alone is
     not sufficient; diff the tool's stdout/report for unexpected grade movement outside
     FACTION on `urban_political`.

## Scoped Pytest Commands

```bash
# Schema + compiler unit tests (primary regression + new-test surface)
pytest tests/unit/worldbuilding/ -x -v

# Faction domain (state, diplomacy, awareness, decision phase) — must be untouched in behavior
pytest tests/unit/faction/ -x -v

# Determinism/state-hash certification — confirm factions addition doesn't perturb hash
pytest tests/certification/test_world_compile_determinism.py -x -v

# Chronicle smoke check (downstream faction event rendering, unaffected but cheap to confirm)
pytest tests/unit/chronicle/ -x -v

# Full targeted run before claiming completion (excludes slow/full-suite runs per project rule)
pytest tests/unit/worldbuilding/ tests/unit/faction/ tests/certification/test_world_compile_determinism.py -v
```

Do not run `pytest tests/` (full suite) or omit `-m "not slow"` filters where applicable —
per project Testing Rule, scope to the domain under modification.

## Anti-Drift Test Guards

- **No pair-keyed test fixtures**: new tests must construct `FactionSpec`/`FactionState`
  with `tension_level` as a per-`faction_id` scalar. A test that asserts on a
  `("bandit_company", "town_council")` tuple key anywhere would indicate the
  implementation drifted into inventing a pair-keyed structure not supported by
  `FactionState` — reject any such implementation at review time, not just the test.
- **Regression guard on empty-faction worlds**: `test_compiler_no_factions_declared_yields_empty_factions_dict`
  must exist and pass — this is the guard against silently changing behavior for
  `dungeon_crawl` or any other world with no `factions:` block declared, which is
  explicitly Out of Scope per the ticket ("Activating FACTION in any world other than
  urban_political ... follow-up batch"). If any other calibration world unexpectedly
  gains non-empty `state.factions` as a side effect of this change (e.g. because a shared
  module used by multiple worlds gets `initial_tension_level` added by mistake), this
  guard test will not catch it — additionally re-run
  `python3 tools/calibrate_simq.py --name dungeon_crawl ...` and confirm FACTION stays at
  `calibration_hits=0` there (the DA decision in
  `TCK-20260702-SIMQ-UPLIFT-DUNGEON-ECON-COG` treats `dungeon_crawl` FACTION=C as
  archetype-correct — do not accidentally invalidate that decision).
- **Weight-change guard**: no test in this ticket should touch
  `config/simulation_quality/profiles/urban_political.yaml`
  `pillar_weights.FACTION` (currently `1.5`) or `FactionScorer` scoring logic — this is
  explicitly Out of Scope. A diff touching scorer weights should fail review regardless
  of test outcome.
- **Parity ledger guard**: `docs/parity_ledger/faction.yaml` must gain a new entry (or
  amend FAC-001's `v2_evidence`) documenting the compile-time seeding path, with a
  `test_path` pointing at one of the new `test_world_compiler.py` tests above — a diff
  that changes compiler behavior without a corresponding parity ledger update should fail
  review per the project's Authoritative Mechanics Rule (parity required in the same
  session as the logic change).
