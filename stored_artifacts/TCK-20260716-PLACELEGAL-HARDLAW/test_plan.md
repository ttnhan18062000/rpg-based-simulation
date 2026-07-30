---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260716-PLACELEGAL-HARDLAW
artifact_type: test_plan
tags: [observability, determinism, world, bug]
---

# Test Plan — TCK-20260716-PLACELEGAL-HARDLAW

## Regression Surface

Existing tests that must keep passing — grouped by category. All are affected either because `HardLawMonitor` gains a new method (unit), `Kernel.__init__` gains a new call site (integration), or a real-world compile pipeline is exercised (arena/world-compile-adjacent).

**Unit**
- `tests/engine/test_hard_law_monitor.py` — `test_hard_law_monitor_individual_laws`, `test_hard_law_occupancy_collision`, `test_observability_modes_and_kernel_integration` (this file directly imports and exercises `HardLawMonitor.check`/`check_occupancy`; must confirm the new `check_initial_placement` staticmethod does not alter `check()`'s existing orchestration or signature).
- `tests/unit/worldbuilding/test_world_compiler.py` — broad suite of `WorldCompiler.compile()` behavior tests (faction tension, information source profiles, population resolution, etc.). Not directly touched by this ticket (compiler.py is read-only reference), but any accidental import-order or fixture coupling introduced while wiring the new check must not break these.
- `tests/unit/worldbuilding/test_compiler_context.py` — compile-context serialization; same no-touch guarantee as above.
- `tests/unit/optimization/test_world_index_service.py` — `WorldIndexService`/`Kernel.get_world_indexes` behavior; relevant because the new check likely reuses or extends this service's index-building patterns (entity index is already full-population; must confirm no regression to `_build_entity_index`/`_build_resource_index`/`_build_building_index` semantics).

**Integration**
- `tests/integration/kernel/test_kernel_boundaries.py` — `test_hook_isolation_from_authoritative_state`, `test_authoritative_hash_purity`. Directly exercises `Kernel.__init__` construction; the new call site sits inside `__init__`, so these must confirm the new check does not mutate authoritative state or leak hash-affecting side effects.
- `tests/integration/observability/test_kernel_event_recording.py` — Kernel + observability wiring; relevant since the new check must respect `ObservabilityConfig.get_mode()` gating exactly like `_run_hard_law_checks`.
- `tests/integration/observability/test_rule_engine_pipeline.py` — downstream consumers of hard-law-style violations; confirm no unexpected new violation types break assumptions there.
- `tests/simulation_quality/test_kernel_simq_integration.py` — Kernel construction is exercised as part of SimQ hub wiring; confirm no new exception paths from the added `__init__` check under SimQ-enabled configs.

**Performance / overhead**
- `tests/perf/test_hard_law_monitor_overhead.py::test_hard_law_monitor_overhead` — currently measures per-tick overhead of the existing dirty-scoped checks. The new check runs once at `__init__`, not per-tick, so this test's *tick-loop* overhead assertion should be unaffected — but worth confirming it doesn't also assert on `Kernel()` construction wall-time, which the new full-population scan will add to (`O(N)` over entities+buildings+resource_nodes, once, at startup, not amortized per tick).

## New Tests Required

Per acceptance criteria (`tickets/inprogress/TCK-20260716-PLACELEGAL-HARDLAW.md`):

1. **`test_check_initial_placement_full_population_scan_unit`**
   - Category: unit
   - Verifies: `HardLawMonitor.check_initial_placement(state)` exists, is unconditional (no `DirtySet` parameter), and detects an entity-vs-entity tile overlap on a hand-built `AuthoritativeState` (mirrors `test_hard_law_occupancy_collision`'s construction style but with two entities placed at literally the same tile, no `DirtySet` involved).
   - Location: `tests/engine/test_hard_law_monitor.py`

2. **`test_check_initial_placement_covers_buildings_and_resource_nodes_unit`**
   - Category: unit
   - Verifies: the 5-part occupancy rule is applied across all three object kinds — an entity overlapping a building's tile, and a building overlapping a resource-node's tile, both produce violations with the correct `details["object_kind"]` value (`"entity"` / `"building"` / `"resource_node"`).
   - Location: `tests/engine/test_hard_law_monitor.py`

3. **`test_check_initial_placement_reuses_verify_occupancy_wall_terrain_unit`**
   - Category: unit
   - Verifies: a hand-built state with `WALL` terrain at an occupied position produces a violation via the terrain branch of the reused `LegalityServiceV2.verify_occupancy` rule (even though real content never uses `WALL` today, the rule itself must be exercised so the branch isn't silently dead code).
   - Location: `tests/engine/test_hard_law_monitor.py`

4. **`test_seed42_entity6_entity14_tile_27_38_collision` (regression)**
   - Category: unit or integration (compiles a real world spec — borderline; place under `tests/engine/` alongside the other `HardLawMonitor` tests since the assertion under test is `HardLawMonitor`'s behavior, not the compiler's)
   - Marker: `@pytest.mark.regression`, with a docstring/comment citing `TCK-20260716-PLACELEGAL-HARDLAW` and `docs/plans/idea_placement_legality_check.md` as originating evidence, per `docs/testing/test_taxonomy.md`'s `regression` marker standard ("must include a comment or link to the original ticket/issue").
   - Verifies: compiling `unit_information_density` (or `unit_information_source`/`unit_selfmodel_pilot`) at `seed=42` via `WorldCompiler.compile(spec, seed=42)` (same pattern as `tests/unit/worldbuilding/test_world_compiler.py`) and calling `HardLawMonitor.check_initial_placement(state)` on the result reproduces the exact real, previously-observed bug: a `LAW-SPAWN-OCCUPANCY` violation naming entities 6 and 14 at tile `(27, 38)`.
   - Location: `tests/engine/test_hard_law_monitor.py`

5. **`test_seed137_and_seed999_no_initial_placement_violations` (negative control)**
   - Category: unit
   - Verifies: compiling the same world(s) at `seed=137` and `seed=999` (the two seeds the idea doc's prototype confirmed produce no collision) and calling `check_initial_placement()` produces **zero** violations — proves the new check isn't over-firing on ordinary compiled content, directly satisfying the ticket's "clean seed produces zero new-law violations" AC.
   - Location: `tests/engine/test_hard_law_monitor.py`

6. **`test_kernel_init_calls_check_initial_placement_once` (integration)**
   - Category: integration
   - Verifies: constructing a `Kernel` with a state containing a known placement collision results in exactly one `LAW-SPAWN-OCCUPANCY` entry written to that run's `hard_law_violations.jsonl` at `tick=0`, using `self._artifact_repo.resolve_path(self._run_id, "violations")` — i.e. no new persistence path, reuses the existing per-run artifact exactly like `_run_hard_law_checks` does. Also verifies the check runs exactly once (not once per tick) by asserting `tick_once()` calls afterward don't re-add the same violation to the file.
   - Location: `tests/integration/kernel/test_kernel_boundaries.py` or a new `tests/integration/observability/test_initial_placement_check.py` if `test_kernel_boundaries.py`'s existing fixtures don't support full `Kernel()` construction with a real `AuthoritativeState` + `ObservabilityConfig` override (check fixture shape during implementation before deciding final location).

7. **`test_check_initial_placement_mode_gating_matches_precedent` (integration)**
   - Category: integration
   - Verifies mode-gating parity with `_run_hard_law_checks`'s existing behavior: `OFF` → check is skipped entirely (no artifact write, no exception); `DEBUG`/`CERTIFICATION` → `Kernel(...)` construction raises `HardLawViolationError` when the compiled state has a known collision; all other modes (`LIGHT`, `LONG_RUN`) → `Kernel(...)` construction succeeds without raising, violation is still logged/persisted. Directly satisfies the ticket's mode-gating AC.
   - Location: same file as #6.

8. **`test_existing_six_laws_unaffected_by_init_time_check` (architecture guard)**
   - Category: architecture guard / regression
   - Verifies: adding `check_initial_placement()` and its `Kernel.__init__` call site does not change the behavior, call count, or return values of any of the 6 existing laws under normal per-tick operation — i.e. re-run `test_hard_law_monitor_individual_laws` and `test_hard_law_occupancy_collision`'s exact assertions after the change lands (can be a direct re-assertion, not necessarily a new test if those two tests already cover it — flag as a "must still pass" check rather than new code if so).
   - Location: `tests/engine/test_hard_law_monitor.py` (may be satisfied by the existing tests passing unmodified, per Regression Surface above, rather than a new test).

## Scoped Pytest Commands

```bash
# HardLawMonitor unit tests (existing + new)
.venv/bin/python3 -m pytest tests/engine/test_hard_law_monitor.py -v

# Kernel construction / boundaries integration tests
.venv/bin/python3 -m pytest tests/integration/kernel/ -v

# Observability + kernel wiring integration
.venv/bin/python3 -m pytest tests/integration/observability/ -v

# WorldIndexService (index-building semantics touched by reuse)
.venv/bin/python3 -m pytest tests/unit/optimization/test_world_index_service.py -v

# WorldCompiler regression surface (read-only reference area — confirm zero collateral change)
.venv/bin/python3 -m pytest tests/unit/worldbuilding/ -v

# Hard-law-monitor overhead perf check (confirm no unexpected tick-loop regression)
.venv/bin/python3 -m pytest tests/perf/test_hard_law_monitor_overhead.py -v

# Regression-marker-only run, to isolate the new bug-reproduction test specifically
.venv/bin/python3 -m pytest tests/engine/test_hard_law_monitor.py -m regression -v
```

Do not run `pytest tests/` — scope to the domains above (observability/hard-law, kernel construction, worldbuilding compiler, and the targeted perf test) per project testing rule.

## Anti-Drift Test Guards

- **`test_check_occupancy_signature_unchanged`** (or an explicit assertion inside an existing test): confirm `HardLawMonitor.check_occupancy(state, dirty_set)`'s signature and `DirtySet.movement_entities`-gated early-return (L143 today) are byte-for-byte unchanged — guards against the temptation to add an `initial_scan: bool` flag to the existing method instead of a dedicated one, which the ticket's Scope section explicitly rejects.
- **`test_worldcompiler_compile_unchanged`**: existing `tests/unit/worldbuilding/test_world_compiler.py` suite passing unmodified is itself the guard that `WorldCompiler.compile()` was not touched — this ticket's Scope section is explicit that `compiler.py` is read-only reference only.
- **`test_no_autocorrect_on_violation`**: assert that after `check_initial_placement()` detects a collision, the two colliding entities' `navigation.position` values are byte-identical to their pre-check values (state is read-only from the check's perspective) — guards against accidentally introducing nudge-to-valid-tile auto-correction, explicitly out of scope.
- **`test_severity_is_always_error_for_new_law`**: assert every `HardLawViolation` produced by `check_initial_placement()` has `severity == "ERROR"`, never `"WARNING"` — guards the "matches existing 6-law severity convention" AC against silent drift.
- **`test_conservation_law_not_introduced`**: a light guard (can be a single assertion in an existing or new test) that no `law_id` starting with `CONSERVATION` is emitted anywhere in this ticket's new code paths — guards against scope creep into the separately-flagged, explicitly-out-of-scope `CONSERVATION`-prefixed law gap the idea doc identified but did not assign to this ticket.
- **`test_simq_translate_invariant_unmodified`**: confirm `src/simulation_quality/quality_hub.py::_translate_invariant()` and `WorldDynamicsScorer.EVENT_TYPES` are untouched by this ticket's diff (e.g. via a diff-scoped check in CI, or simply by the SimQ test suite passing unmodified) — guards against pulling `TCK-20260716-PLACELEGAL-SIMQ-SIGNAL`'s scope into this ticket.
