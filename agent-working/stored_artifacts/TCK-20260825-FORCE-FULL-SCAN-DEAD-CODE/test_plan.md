---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260825-FORCE-FULL-SCAN-DEAD-CODE
artifact_type: test_plan
tags: [engine, bug, websocket]
---

# Test Plan — TCK-20260825-FORCE-FULL-SCAN-DEAD-CODE

## Regression Surface

Existing tests that must keep passing, grouped by domain. The fix touches only (a) the tail end of
`AuthoritativeApplyPipeline.refine()` (pipeline.py:351-353 region, gated on `update.force_full_scan`)
and (b) `RuntimeStatus`/`Kernel.__init__` (a new declared field, populated once at boot) — so the
regression surface is everything that exercises `refine()`'s final `StateUpdate.dirty_set`,
force_full_scan phase-routing, `RuntimeStatus` construction, and the WS/read-model delta path.

**Unit — dirty-set / candidate-selection core (`src/core/dirty.py`)**
- `tests/perf/test_dirty_set_integrity.py` — `DirtySet.from_update()` derivation, `DirtySetLeakError`,
  incremental merge correctness. Must stay green: this ticket does not touch `from_update` or
  `mark_from_update` themselves.
- `tests/unit/domains/optimization/test_candidate_selector.py` — `CandidateSelector` domain routing
  (15 mappings). Unaffected: routing reads `update.force_full_scan` directly, never `dirty_set`
  content.
- `tests/unit/domains/optimization/test_phase_dependency_graph.py` — `PhaseDependencyGraph
  .should_run_phase`'s force-full-scan override. Unaffected: reads `update.force_full_scan`/
  `state._force_full_scan` directly (phase_graph.py:87), not `dirty_set`.
- `tests/unit/domains/optimization/test_movement_candidate_selector.py` — Tier 3 force-full-scan
  bypass stage. Unaffected for the same reason.
- `tests/unit/domains/optimization/test_strategic_work_queue.py` — `work_queue.py:36`'s own
  `force_full_scan` check. Unaffected.

**Unit — read-model / API (`src/api/`)**
- `tests/unit/api/test_read_model_cache.py` — all `test_compute_tick_delta_*` and
  `test_read_model_invalidation_policy` tests. These construct `DirtySet`/`force_full_scan` args by
  hand and call `ReadModelCache`/`ReadModelInvalidationPolicy` directly — none of them exercise
  `refine()`, so they are unaffected by the pipeline-side fix, but they remain the correctness
  baseline the new integration test below builds on top of.

**Integration — force-full-scan phase compliance & pipeline parity**
- `tests/integration/optimization/test_force_full_scan_phase_compliance.py` — six tests calling
  individual phase functions (`InteractionPhase`, `MovementPhase`, `StrategicIntelligenceSystem`,
  `ShopSystem`, `CapacityEnforcementPhase`, `GroupPhase`, `LifecycleSystem`) directly with
  `force_full_scan=True` and an empty `dirty_set=DirtySet()`. These assert on `refined
  .entity_updates`, never on `refined.dirty_set` completeness — unaffected by this fix, and continue
  to prove the routing half of `force_full_scan` (Tier 2 candidate selection) independently of the
  downstream dirty-set-completeness half this ticket adds.
- `tests/perf/test_dirty_parity.py::test_dirty_set_vs_full_scan_parity` (`@pytest.mark.perf
  @pytest.mark.slow`) — compares `StateFingerprinter` state hashes between an optimized kernel and a
  `force_full_scan=True` reference kernel over 100 ticks. Must stay bit-identical: `StateUpdate
  .dirty_set` is advisory routing metadata, not part of `AuthoritativeState`/the fingerprint, so
  widening the final dirty set cannot change either kernel's resulting entity state. Run explicitly
  (it is `slow`, likely excluded from default `-m "not slow"` runs) as part of this ticket's own
  verification, not just left to CI's periodic slow sweep.
- `tests/integration/optimization/test_static_dirtyset_guard.py` (OPT-INV-001) — proves no gameplay
  system references `state.dirty_set` directly. Unaffected: this fix stays inside
  `AuthoritativeApplyPipeline.refine()`, a pipeline-internal method, not a gameplay system.
- `tests/integration/optimization/test_phase_skip_parity.py`,
  `tests/integration/optimization/test_apply_plan_parity.py`,
  `tests/integration/optimization/test_component_patch_apply_parity.py` — broader
  optimization-parity suite; run as a sanity net since they share `refine()`'s call path.

**Integration — kernel / apply / determinism**
- `tests/integration/pipeline/test_authoritative_apply.py` — `apply_generation()` isolation and
  determinism. `ApplyPath.apply_generation()` consumes `update.dirty_set` only for
  `audit_dirty_set=True` leak validation, which treats a wider dirty set as safe (documented in
  `docs/core/dirty_state_and_dependency.md`'s "conservative by design" rule) — must stay green.
- `tests/integration/kernel/test_determinism_suite.py`,
  `tests/integration/kernel/test_minimal_kernel.py` — general kernel tick-loop regression net.

## New Tests Required

1. **Test name**: `test_refine_forces_full_dirty_set_when_force_full_scan_true_with_no_entity_updates`
   **Category**: unit (pipeline-level, but exercising `refine()` directly rather than the full
   `Kernel`)
   **What it verifies**: builds an `AuthoritativeState` with several entities, none of which produce
   any `EntityUpdate` this tick (an empty/near-empty raw `StateUpdate`), calls
   `AuthoritativeApplyPipeline.refine(state, update, force_full_scan=True)`, and asserts
   `refined.dirty_set.all_dirty_entities == set(state.entities.keys())` (and, separately, that each
   of the nine per-domain sets — `movement_entities`, `combat_entities`, ..., `attribute_entities` —
   equals `set(state.entities.keys())`, and `town_entities == state.town_entity_ids`). This is the
   direct regression test for the crux finding: without the fix, this assertion fails today because
   `mark_from_update` only marks entities with real field changes, and with no entity updates at all
   the resulting dirty set would be empty.
   **Where it lives**: `tests/perf/test_dirty_set_integrity.py` (co-located with the other
   `DirtySet`/`DirtySetBuilder` unit coverage) or a new
   `tests/integration/optimization/test_force_full_scan_dirty_set_completeness.py` — prefer the
   latter, since it exercises the full `refine()` pipeline (17 phases), not just `DirtySetBuilder`
   in isolation, and sits naturally alongside
   `test_force_full_scan_phase_compliance.py` in the same directory.

2. **Test name**: `test_refine_does_not_force_full_dirty_set_when_force_full_scan_false`
   **Category**: unit / anti-drift guard
   **What it verifies**: same setup as (1) but `force_full_scan=False` (default) — asserts
   `refined.dirty_set.all_dirty_entities` reflects only entities with real changes (i.e., is a
   proper subset of `state.entities.keys()`, matching current/unfixed behavior for this case). This
   guards against the "wire in verbatim/unconditionally" failure mode flagged in investigation.md —
   if the fix is implemented as an unconditional call rather than one gated on `force_full_scan`,
   this test catches it immediately.
   **Where it lives**: same file as (1).

3. **Test name**: `test_kernel_status_exposes_force_full_scan_from_boot_flag`
   **Category**: unit
   **What it verifies**: `RuntimeStatus()` default-constructed has `force_full_scan is False`;
   `Kernel(profile, state, rng, flags={"force_full_scan": True})` produces a `.status.force_full_scan
   is True` immediately after construction (before any `tick_once()` call, proving it is boot-time,
   not tick-derived); a `Kernel` constructed without the flag (or `flags=None`) has `.status
   .force_full_scan is False`.
   **Where it lives**: `tests/unit/engine/test_runtime_status.py` — confirmed this file does not
   exist yet in `tests/unit/engine/` (which itself already exists and holds other single-module unit
   suites like `test_capability_registry.py`), so this is a new file, not an addition to an existing
   one. `tests/integration/kernel/test_minimal_kernel.py` is the fallback location only if the
   implementer judges a dedicated file unwarranted for one small test.

4. **Test name**: `test_v2_engine_manager_ws_delta_changed_includes_every_alive_entity_under_force_full_scan`
   **Category**: integration (the ticket's explicitly-required regression test — AC2/scope bullet 3)
   **What it verifies**: `V2EngineManager.__init__(self, profile, seed=42, entities_count=10)`
   (`engine_manager.py:22`) takes no `flags` parameter today, and `_build()`'s internal
   `Kernel(profile=self._profile, state=state, rng=rng)` call (`engine_manager.py:148`) never passes
   `flags` — so there is no way to construct a `force_full_scan=True` `V2EngineManager` without
   adding a new constructor parameter, which is scope this ticket does not need and should not add
   (the ticket's Scope names `V2EngineManager._update_latest_state`'s `getattr` read as what must be
   fixed, not a new construction-time knob). Instead, build a
   `Kernel(profile, state, rng, flags={"force_full_scan": True})` directly, call
   `tick_once()`, then call `ReadModelCache().compute_tick_delta(kernel.state,
   getattr(kernel.status, "dirty_set", None), getattr(kernel.status, "force_full_scan", False),
   kernel.state.tick)` and assert the returned payload's `changed` list contains a slim-DTO entry for
   every entity in `kernel.state.entities` with `combat.alive is True` (matching
   `StatePresenter.present_entity_slim`'s id set) — the exact `getattr(...)` call sites `engine_
   manager.py:155-156` use, so this test fails today (before the fix) via the same `RuntimeStatus`
   gap the ticket's Scope/AC3 names explicitly. Explicitly set `ObservabilityConfig` to a known,
   non-`OFF` mode for the duration of the test (context-manager or explicit `set_mode`/env var,
   whichever the existing test suite's convention is — check `tests/integration/kernel/` for the
   established pattern) so the test exercises the real `_run_hard_law_checks`-populated `dirty_set`
   path rather than accidentally passing via the `dirty_set is None → invalidate everything` fallback
   documented as a risk in investigation.md.
   **Where it lives**: `tests/integration/optimization/test_force_full_scan_dirty_set_completeness.py`
   (same new file as tests 1-2, since it is the natural landing spot for "force_full_scan produces a
   complete downstream artifact" coverage) or `tests/unit/api/test_read_model_cache.py` if the test
   is written at the `ReadModelCache` level with a hand-built `Kernel` fixture rather than through
   `V2EngineManager` — implementer's call once the `V2EngineManager` flags-passthrough question above
   is resolved during planning/implementation.

5. **Test name**: `test_optimized_vs_full_scan_dirty_set_content_diverges_by_design`
   **Category**: architecture guard / documentation-of-intent
   **What it verifies**: runs the same complex-world fixture `tests/perf/test_dirty_parity.py
   ::test_dirty_set_vs_full_scan_parity` already uses (or a lighter-weight variant) for a handful of
   ticks with both an optimized kernel and a `force_full_scan=True` kernel, and asserts that (a) both
   kernels' final entity **state hashes** are identical (already proven by the existing parity test —
   re-asserting here only if this test is kept independent of that file) while (b) the two kernels'
   `refine()`-produced `dirty_set.all_dirty_entities` sets are **not required to be, and in general
   will not be, identical in size** — i.e., explicitly documents that this fix changes *dirty-set
   completeness* for downstream consumers without changing *simulation outcome*. This test exists to
   prevent a future reader from conflating "the dirty set is now full" with "the simulation now
   behaves differently," which the investigation explicitly ruled out but which is easy to
   misremember later.
   **Where it lives**: optional / lower priority — fold into test (1)'s file as a second assertion on
   the same fixture rather than a fully separate test, if the implementer judges the dedicated test
   redundant with (1) and the existing `test_dirty_set_vs_full_scan_parity`.

## Scoped Pytest Commands

```
# Core dirty-set / candidate-selection unit coverage
.venv/bin/python3 -m pytest tests/perf/test_dirty_set_integrity.py tests/unit/domains/optimization/ -v

# Read-model / API unit coverage
.venv/bin/python3 -m pytest tests/unit/api/test_read_model_cache.py -v

# New force-full-scan dirty-set-completeness tests + existing force-full-scan phase compliance
.venv/bin/python3 -m pytest tests/integration/optimization/ -v

# RuntimeStatus / Kernel boot-flag coverage
.venv/bin/python3 -m pytest tests/integration/kernel/test_minimal_kernel.py tests/unit/engine/ -v

# Slow parity test — must be run explicitly, not covered by default -m "not slow"
.venv/bin/python3 -m pytest tests/perf/test_dirty_parity.py::test_dirty_set_vs_full_scan_parity -v -m "perf and slow"

# Authoritative apply / determinism regression net
.venv/bin/python3 -m pytest tests/integration/pipeline/test_authoritative_apply.py tests/integration/kernel/test_determinism_suite.py -v
```

Never `pytest tests/` — all commands above are scoped to the domains this fix touches
(dirty-set/candidate-selection core, read-model/API, optimization integration, kernel boot, apply
determinism) plus the one explicitly-slow parity test this fix's determinism claim depends on.

## Anti-Drift Test Guards

- Test 2 (`test_refine_does_not_force_full_dirty_set_when_force_full_scan_false`) is the primary
  guard against the "wire in `_refresh_dirty_set` verbatim/unconditionally" failure mode — it fails
  immediately if the implementer calls the relocated full-scan logic without gating it, or
  accidentally also wires in the unsafe `else` branch (`DirtySet.from_update(...)`) that would
  reintroduce the `e_upd.task` discrepancy on ordinary ticks.
- `tests/perf/test_dirty_set_integrity.py` and `tests/integration/pipeline/test_authoritative_apply.py`
  together guard against the `e_upd.task` discrepancy specifically leaking into the default
  (non-force-full-scan) path — if a future edit accidentally routes ordinary ticks through
  `DirtySet.from_update()` instead of the builder, any existing test asserting `strategic`-dirty
  marking from a `task`-only change (if one exists in that suite) would catch it; if no such test
  currently exists, this ticket should not add one — that discrepancy is explicitly out of scope
  (`dirty_state_and_dependency.md`'s own deferral).
- `tests/integration/optimization/test_static_dirtyset_guard.py` (OPT-INV-001) guards against the fix
  accidentally exposing `dirty_set` construction logic outside `AuthoritativeApplyPipeline` (e.g., if
  a future refactor moves the full-scan-override logic into a shared/importable helper that a
  gameplay system could then reach into directly).
- Test 5 (or its folded-in equivalent) guards against a future reader conflating "dirty set now full
  under force_full_scan" with "simulation behavior changed" — an easy misunderstanding to introduce
  into a future PR description or doc edit if not pinned down by an explicit test.
- The observability-mode pinning called out in test 4 guards against a false-positive-passing test
  that only appears to prove the fix works because it accidentally exercises the unrelated
  `dirty_set is None` fallback (see investigation.md's Risks section) rather than the real
  `RuntimeStatus.force_full_scan` fix.
