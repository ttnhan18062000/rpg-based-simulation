---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260825-FORCE-FULL-SCAN-DEAD-CODE
artifact_type: plan
tags: [engine, bug, websocket]
---

# Implementation Plan — TCK-20260825-FORCE-FULL-SCAN-DEAD-CODE

## Summary

`AuthoritativeApplyPipeline._refresh_dirty_set` (`src/engine/pipeline.py:362-388`) is dead code, but
investigation.md proved its `if update.force_full_scan:` branch (372-385) is genuinely needed,
non-redundant logic — without it, no live mechanism forces the *downstream* `StateUpdate.dirty_set`
(the one `Kernel._run_hard_law_checks` copies to `self._status.dirty_set`, and that
`V2EngineManager._update_latest_state` / `ReadModelCache.compute_tick_delta` consume) to actually
contain every entity when `force_full_scan=True`. The method's `else` branch (387-388) must NOT be
wired in — it recomputes via the stateless `DirtySet.from_update()`, which omits `e_upd.task` from
its strategic-dirty check (unlike `DirtySetBuilder.mark_from_update()`), and would silently
reintroduce that documented, deliberately-deferred discrepancy into every ordinary tick if called
unconditionally. This plan implements the third option investigation.md recommends: extract only the
full-scan branch's DirtySet-construction logic directly into `refine()`, gated explicitly on
`update.force_full_scan`, immediately after the existing "Final dirty set for result application"
block (`pipeline.py:351-353`); delete `_refresh_dirty_set` entirely rather than calling it; add a
declared `force_full_scan` field to `RuntimeStatus` populated once at `Kernel.__init__`; update the
three docs investigation.md names; and add the new regression tests test_plan.md specifies (4 of the
5 — test 5 is folded into test 1's file as noted below).

## Steps

### Step 1 — Wire the full-scan branch into `refine()`, gated on `update.force_full_scan`
**Files:** `src/engine/pipeline.py`
**Change:** Verified by direct read (`pipeline.py:330-361`): the "Final dirty set for result
application" block is at lines 351-353 —
```python
        # Final dirty set for result application
        dirty_builder.mark_from_update(state, update)
        update = update.replace(dirty_set=dirty_builder.build())
```
Immediately after this block (still before line 354's `t8 = time.perf_counter_ns()`, or after it —
either is fine since `t8`/`costs["final_integrity"]` only time the dirty-set-rebuild region and this
addition is cheap; insert directly after line 353 to keep the timing region meaningful), add:
```python
        if update.force_full_scan:
            all_ids = set(state.entities.keys())
            update = update.replace(dirty_set=DirtySet(
                movement_entities=all_ids,
                combat_entities=all_ids,
                inventory_entities=all_ids,
                strategic_entities=all_ids,
                social_entities=all_ids,
                lifecycle_entities=all_ids,
                town_entities=state.town_entity_ids,
                biological_entities=all_ids,
                attribute_entities=all_ids
            ))
```
This is the `_refresh_dirty_set` `if update.force_full_scan:` branch's construction (verbatim
field-for-field, read at `pipeline.py:372-385`), relocated and gated identically. `DirtySet` needs a
module-level import — `_refresh_dirty_set` currently does a local `from src.core.dirty import
DirtySet` (line 369); check `pipeline.py`'s existing top-of-file imports for `DirtySet` (it is
already used by `dirty_builder` construction near line 56-59, so `DirtySet`/`DirtySetBuilder` are
very likely already imported at module scope — confirm and reuse the existing import rather than
adding a duplicate local import inside `refine()`).
**Do NOT touch:** `update.dirty_set` when `update.force_full_scan` is `False` — no `else` branch, no
call to `DirtySet.from_update()` anywhere in this step. Do not move this block earlier in `refine()`
(it must run after every phase, per investigation.md's placement rationale — routing already reads
`update.force_full_scan` directly at each `CandidateSelector`/`get_relevant_entity_ids` call site, so
running this override only at the very end cannot change what any phase processed this tick).
**Verify:** New test `test_refine_forces_full_dirty_set_when_force_full_scan_true_with_no_entity_updates`
(Step 6) and `test_refine_does_not_force_full_dirty_set_when_force_full_scan_false` (Step 6) — the
second is the direct anti-drift guard for this step specifically.

### Step 2 — Delete `_refresh_dirty_set` entirely
**Files:** `src/engine/pipeline.py`
**Change:** Remove the whole `_refresh_dirty_set` static method (lines 362-388, verified above),
including its docstring ("Hardening Phase: Ensure DirtySet is always current" / "Logic ID:
PERF-006-REFRESH" / "M7 Optimization: Incremental derivation.") and the "Phase 17 Law" inline
comment. Investigation.md confirmed via full-repo grep that the only reference to
`_refresh_dirty_set` anywhere in the repository besides its own `def` line is a comment in
`tools/perf/live_map_ws_payload_measure.py:32-33` documenting the *zero-call-sites finding itself* —
that comment describes historical fact about a prior ticket's investigation and is explicitly listed
in this ticket's Out of Scope (`TCK-20260821-LIVE-MAP-PERF-VALIDATION`'s deliverables must not be
touched), so leave that file alone. No other writer/reader of `_refresh_dirty_set` exists to update
or break.
**Do NOT touch:** Any other method in `pipeline.py`. Do not leave a stub/deprecated wrapper — delete
the method body and signature outright, per investigation.md's explicit recommendation ("delete
`_refresh_dirty_set` as a standalone method... rather than calling it").
**Verify:** `grep -rn "_refresh_dirty_set" --include="*.py" .` from repo root returns zero hits
(confirms full removal); existing suite `tests/perf/test_dirty_set_integrity.py` and
`tests/integration/pipeline/test_authoritative_apply.py` stay green (neither ever referenced this
method — investigation.md confirmed zero call sites pre-fix).

### Step 3 — Add `force_full_scan: bool = False` field to `RuntimeStatus`
**Files:** `src/engine/runtime_status.py`
**Change:** Verified by direct read (`runtime_status.py:9-33`): `RuntimeStatus` is a plain
`@dataclass` (not frozen, not slotted) with declared fields `current_mode`, `mode_dwell_ticks`,
`signal_history`, `total_dropped_work`, `dropped_work_delta`, `last_transition_tick`,
`max_mode_reached` — no `force_full_scan`, no `dirty_set`. Add one new declared field after
`max_mode_reached` (line 33):
```python
    max_mode_reached: RuntimeMode = RuntimeMode.NORMAL
    force_full_scan: bool = False
```
**Other writers to this dataclass** (enumerated per investigation.md's "Current Behavior" section,
confirmed as an established pattern, not something this step introduces): `Kernel` already bolts six
undeclared attributes onto `self._status` at runtime — `dirty_set` (`kernel.py:843-844`, gated on
`ObservabilityConfig.get_mode() != OFF`), `current_tick_violations` (850), `cumulative_violations`
(854-855, 863), `hard_law_violations` (856-857, 859), `last_hard_law_violation_tick` (860, 775),
`previous_mode` (554). This new `force_full_scan` field does not collide with any of them (different
attribute name) and does not change how any of the six are assigned — it is purely additive. Do not
declare any of those six as fields in this step (see Scope Guards).
**Do NOT touch:** Any of the six existing ad-hoc `self._status.X = ...` assignment sites, and do not
declare any of those six attributes on `RuntimeStatus` in this ticket.
**Verify:** New test `test_kernel_status_exposes_force_full_scan_from_boot_flag` (Step 6) — its first
assertion (`RuntimeStatus()` default-constructed has `force_full_scan is False`) exercises this step
directly.

### Step 4 — Populate `RuntimeStatus.force_full_scan` once at `Kernel.__init__`
**Files:** `src/engine/kernel.py`
**Change:** Verified by direct read (`kernel.py:80-118`): `self._force_full_scan = flags.get(
"force_full_scan", False) if flags else False` is set at line 84; `self._status = status or
DefaultStatus()` is set at line 109. Immediately after line 109, add:
```python
        self._status = status or DefaultStatus()
        self._status.force_full_scan = self._force_full_scan
```
This is a boot-time-fixed value (unlike `dirty_set`, which is genuinely per-tick and conditionally
set inside `_run_hard_law_checks`) — setting it once, unconditionally, in `__init__` means
`getattr(self._kernel.status, "force_full_scan", False)` in `engine_manager.py:156` returns the
correct value in every observability mode, including `OFF`, closing the gap without depending on
`_run_hard_law_checks`'s mode gate at all.
**Other writers to `self._status`:** confirmed by reading `kernel.py:80-118` and investigation.md's
enumeration — no other site in `Kernel.__init__` writes to `self._status` between line 109 and the
end of `__init__`; the six ad-hoc post-construction writes (`dirty_set`, `current_tick_violations`,
etc.) all happen later, per-tick, inside `_phase_advancement`/`_run_hard_law_checks`, not at
`__init__` time, so there is no ordering race with this addition. If a caller passes an explicit
`status=` argument to `Kernel.__init__` (a pre-built `RuntimeStatus`, bypassing `DefaultStatus()`),
this line still overwrites `.force_full_scan` on that passed-in object to match the boot flag — this
is correct: the boot flag is the single source of truth for this field regardless of which
`RuntimeStatus` instance is supplied.
**Do NOT touch:** `Kernel._force_full_scan`'s own assignment at line 84, or the `object.__setattr__`
mirroring onto `AuthoritativeState._force_full_scan` at line 91 — both stay exactly as-is.
**Verify:** `test_kernel_status_exposes_force_full_scan_from_boot_flag` (Step 6) — its second and
third assertions (`Kernel(..., flags={"force_full_scan": True})` produces `.status.force_full_scan is
True` immediately after construction, before any `tick_once()`; a `Kernel` without the flag has
`.status.force_full_scan is False`) exercise this step directly.

### Step 5 — Update the three docs investigation.md names
**Files:** `docs/core/dirty_state_and_dependency.md`, `docs/performance/optimization_invariants.md`,
`docs/parity_ledger/infrastructure.yaml`

**5a. `docs/core/dirty_state_and_dependency.md`** — verified by direct read (lines 186-188, the
`### force_full_scan fallback` subsection): current text is exactly "When `StateUpdate
.force_full_scan=True` or `StateUpdate.dirty_set is None`, both `CandidateSelector.entities()` and
`get_relevant_entity_ids()` return all entity IDs from `state.entities` regardless of dirty flags.
This is the global re-evaluation path used for initial ticks, calamity events, and any scenario where
the full entity pool must be re-evaluated. The dirty set is still computed and attached — it is just
not used for filtering." The last sentence becomes only true for `force_full_scan=False` ticks after
this fix. Replace the last sentence with two sentences describing both post-fix halves: (1) routing
bypass is unchanged — the dirty set's content still plays no role in phase candidate selection; (2)
for `force_full_scan=True` ticks, the dirty set `refine()` finally returns is now *replaced* with an
all-entities `DirtySet` specifically so downstream consumers outside `refine()` (`ReadModelCache`,
the WS broadcast) also see full coverage, not just the in-pipeline phases. Then update the
"Regression tests" table (lines 237-243, verified — currently three rows:
`tests/perf/test_dirty_set_integrity.py`, `tests/perf/test_dirty_parity.py
::test_dirty_set_vs_full_scan_parity`, `tests/integration/pipeline/test_authoritative_apply.py`) by
appending one new row for the new
`tests/integration/optimization/test_force_full_scan_dirty_set_completeness.py` file added in Step 6,
describing what it verifies (downstream `DirtySet` completeness under `force_full_scan=True`, and the
anti-drift guard that it stays untouched when `False`).

**5b. `docs/performance/optimization_invariants.md`** — verified by direct read (lines 59-72, "##
3. OPT-INV-002: Force Full Scan Compliance"): "Invariant Rules" currently has exactly 3 numbered
rules (lines 65-67) covering phase-checking, exhaustive evaluation, and state-hash equivalence — none
of them mention the downstream `DirtySet` consumed by read-model/API/WS layers. Add a 4th numbered
rule under "Invariant Rules", e.g.: "4. The `StateUpdate.dirty_set` that `refine()` returns when
`force_full_scan` is active must itself contain every live entity across all nine domain sets — not
merely have permitted every phase to evaluate every entity internally — so that consumers outside the
pipeline (`ReadModelCache.compute_tick_delta`, the `/api/v1/ws` broadcast) also observe full
coverage." Update "Enforcement & Verification" (lines 69-71) to cite the new test from Step 6
alongside the existing `test_force_full_scan_phase_compliance.py` citation.

**5c. `docs/parity_ledger/infrastructure.yaml` — `INFRA-388`** — verified by direct read (lines
11300-11340): current `text` describes `ReadModelCache.compute_tick_delta` classifying
`DirtySet.all_dirty_entities` into changed/removed but never mentions `force_full_scan`, even though
`V2EngineManager._update_latest_state` already threads a `force_full` value into `compute_tick_delta`
(confirmed at `engine_manager.py:159-161`, read directly: `self._read_cache.compute_tick_delta(state,
dirty_set, force_full, state.tick)`). Add a clause to `text` describing that `force_full_scan=True`
now genuinely produces an all-entities `changed` list end-to-end (previously always `False` via the
`RuntimeStatus` gap this ticket fixes). Append the new test path(s) from Step 6 to the existing
comma-separated `test_path` value (current value verified: three tests already listed, e.g.
`tests/unit/api/test_read_model_cache.py::test_compute_tick_delta_changed_includes_only_dirty_and_alive_entities,...`
— append after the last entry, comma-separated, same format). Leave `status: verified` as-is (already
correct for the pre-fix, non-force-full-scan path this fix does not change) — do not mark
`divergent`. Leave `priority: P1` unchanged.
**Do NOT touch:** `docs/engine/candidate_selection.md` or `docs/core/update_intents.md` — both
confirmed accurate as-is by investigation.md and independently unaffected by this fix (routing
behavior is unchanged; only the final post-routing `DirtySet` changes).
**Verify:** No automated test verifies doc prose directly; `done-checker`'s frontmatter-valid check
applies to these docs' existing frontmatter (unchanged by this edit — only body prose changes).

### Step 6 — Add new tests
**Files:** new file `tests/integration/optimization/test_force_full_scan_dirty_set_completeness.py`;
new file `tests/unit/engine/test_runtime_status.py`

**Judgment calls resolved** (test_plan.md left these open for the implementer/planner to decide):
- **Tests 1 and 2** (`test_refine_forces_full_dirty_set_when_force_full_scan_true_with_no_entity_updates`,
  `test_refine_does_not_force_full_dirty_set_when_force_full_scan_false`): land in the new
  `tests/integration/optimization/test_force_full_scan_dirty_set_completeness.py`, per test_plan.md's
  own stated preference — it exercises the full 17-phase `refine()` pipeline, not `DirtySetBuilder`
  in isolation, and sits naturally alongside the existing
  `test_force_full_scan_phase_compliance.py` in the same directory (confirmed that directory already
  exists and holds five sibling test files: `test_apply_plan_parity.py`,
  `test_cache_memory_bounds.py`, `test_component_patch_apply_parity.py`,
  `test_force_full_scan_phase_compliance.py`, `test_phase_skip_parity.py`,
  `test_profile_specific_behavior.py`).
- **Test 3** (`test_kernel_status_exposes_force_full_scan_from_boot_flag`): lands in a new
  `tests/unit/engine/test_runtime_status.py`. Confirmed `tests/unit/engine/` already exists (15
  sibling files: `test_capability_registry.py`, `test_hash_scheduler.py`, etc.) and confirmed no
  `test_runtime_status.py` exists there yet — this is a genuinely new file, not an addition to an
  existing one, resolving test_plan.md's stated fallback question in favor of the dedicated-file
  option (a `RuntimeStatus`-focused unit test is a natural fit for that directory's existing
  single-module-suite pattern, and the test also needs a `Kernel(...)` construction, which
  `tests/integration/kernel/test_minimal_kernel.py` already covers extensively for other purposes —
  keeping this test isolated in its own small file avoids bloating that file with an unrelated
  concern).
- **Test 4** (`test_v2_engine_manager_ws_delta_changed_includes_every_alive_entity_under_force_full_scan`):
  lands in the same new `tests/integration/optimization/test_force_full_scan_dirty_set_completeness.py`
  file as tests 1-2 (test_plan.md's first-listed option), NOT `tests/unit/api/test_read_model_cache.py`.
  Rationale: `V2EngineManager.__init__` takes no `flags` parameter (confirmed by direct read,
  `engine_manager.py:140-150` — `self._kernel = Kernel(profile=self._profile, state=state, rng=rng)`,
  no `flags=` passed) and adding one is out of scope (the ticket's Scope names the `getattr` *read*
  as what must be fixed, not a new construction-time knob), so per test_plan.md's own instruction the
  test must build a `Kernel(profile, state, rng, flags={"force_full_scan": True})` directly rather
  than going through `V2EngineManager`. Verified the exact `getattr` call sites this test targets:
  `engine_manager.py:155` (`dirty_set = getattr(self._kernel.status, "dirty_set", None) if
  self._kernel else False`) and `engine_manager.py:156` (`force_full = getattr(self._kernel.status,
  "force_full_scan", False) if self._kernel else False`), then verified `ReadModelCache
  .compute_tick_delta`'s signature directly (`read_model_cache.py:118`,
  `def compute_tick_delta(self, state, dirty_set, force_full_scan, tick)` — confirms the parameter
  order test_plan.md's item 4 assumes is correct) and `ReadModelInvalidationPolicy
  .get_dirty_entity_ids`'s signature (`read_model_cache.py:21`, `(dirty_set, all_entity_ids,
  force_full_scan=False)`, body at 26-28: `if force_full_scan or dirty_set is None: return
  set(all_entity_ids)`). Since this test constructs a raw `Kernel` (not a `V2EngineManager`), it
  belongs with the other `refine()`/`Kernel`-level tests in the same new file rather than
  `test_read_model_cache.py`, which test_plan.md itself describes as constructing `DirtySet`/
  `force_full_scan` args by hand without ever exercising `refine()` or `Kernel` — a different testing
  style this test does not match.
  **Observability-mode pinning**: verified `src/observability/config.py:296` (`ObservabilityConfig
  .get_mode`) and the established test convention (`tests/unit/config/test_phase19_observability_feature_flags.py:8,14,27-28`)
  — use `ObservabilityConfig.clear_all_overrides()` in setup/teardown and
  `ObservabilityConfig.set_override_mode(ObservabilityMode.LIGHT)` explicitly for the duration of the
  test (do not rely on ambient default), so the test exercises the real `_run_hard_law_checks`-
  populated `dirty_set` path rather than accidentally passing via the `dirty_set is None →
  invalidate everything` fallback (`get_dirty_entity_ids` line 26-28) that would make the test pass
  even without this ticket's fix.
- **Test 5** (`test_optimized_vs_full_scan_dirty_set_content_diverges_by_design`): **included**, folded
  into test 1's file as a lightweight second assertion on the same fixture used for test 1, per
  test_plan.md's own stated fallback ("fold into test (1)'s file... if the implementer judges the
  dedicated test redundant with (1) and the existing `test_dirty_set_vs_full_scan_parity`") — a
  one-paragraph addition to test 1 asserting the produced `dirty_set.all_dirty_entities` is a strict
  superset of (or unequal in size to) what an equivalent `force_full_scan=False` run would produce, is
  low-cost and directly documents the "dirty set is now full, simulation outcome is unchanged"
  distinction investigation.md flags as an easy future misunderstanding. Not a separate test function.

**Do NOT touch:** any existing test file's assertions (Steps 1-5 only add new tests/files; no existing
test in the Regression Surface list below should need modification for this fix to pass).
**Verify:** the Build Gate list below.

## Scope Guards

Carried forward from investigation.md's Anti-Drift Hazards, verbatim in substance:
- Do not call `_refresh_dirty_set` verbatim/unconditionally as "the fix" — it must be deleted, not
  called; only its full-scan branch's logic is relocated, explicitly gated.
- Do not touch `DirtySetBuilder.mark_from_update` or `DirtySet.from_update` to "fix" the `e_upd.task`
  discrepancy as a side effect of this ticket — that is explicitly deferred to its own dedicated
  bugfix ticket per `dirty_state_and_dependency.md`.
- Do not widen this ticket into building a new full-scan-cadence feature (e.g. automatic periodic
  full re-sync) — out of scope per the ticket itself.
- Do not change `docs/engine/candidate_selection.md` or `docs/core/update_intents.md` — both
  confirmed accurate as-is post-fix.
- Do not retroactively "clean up" the other five ad-hoc `self._status.X = ...` assignments
  (`current_tick_violations`, `cumulative_violations`, `hard_law_violations`,
  `last_hard_law_violation_tick`, `previous_mode`) while touching `RuntimeStatus` for
  `force_full_scan`.
- Be precise about `AuthoritativeState._force_full_scan` (`state.py:1146`) vs.
  `StateUpdate.force_full_scan` (`updates.py:920`) — two different fields on two different objects,
  reconciled only inside `refine()`'s lines 48-51; do not conflate them in new test/doc prose.
- Do not touch `tools/perf/live_map_ws_payload_measure.py` or any `TCK-20260821-LIVE-MAP-PERF-VALIDATION`
  deliverable (ticket's own Out of Scope).
- Do not touch the frontend (`frontend/src/hooks/useSimulation.ts` and friends) — ticket's own Out of
  Scope.
- Do not add a `flags` constructor parameter to `V2EngineManager.__init__` — Step 6's test 4 builds a
  raw `Kernel` directly instead; adding that parameter is scope this ticket does not need.

## Dependency Map

- Step 1 (pipeline.py wiring) and Step 2 (delete `_refresh_dirty_set`) touch the same file and should
  be done together/sequentially in one edit pass, but Step 1 does not functionally depend on Step 2
  having landed first — the new gated block works whether or not the dead method still physically
  exists below it. Do Step 1 before Step 2 to avoid a moment where the new code and the still-present
  dead method both exist with overlapping-looking logic, which would confuse a mid-review reader.
- Step 3 (RuntimeStatus field) must land before Step 4 (Kernel.__init__ wiring) — Step 4's assignment
  target doesn't exist as a declared field until Step 3 lands (though Python's dynamic attributes
  would technically allow the assignment either order; declare-then-assign is the correct order for
  clarity and matches how the ticket's own AC3 frames "add a declared field").
- Steps 1-2 (pipeline.py) and Steps 3-4 (RuntimeStatus/Kernel) are independent of each other and can
  be implemented/verified in either order.
- Step 5 (docs) depends on Steps 1-4 being finalized (doc text describes the landed behavior) and on
  Step 6 (new test paths/names must exist to cite in the Regression-tests table and INFRA-388's
  `test_path`) — do Step 5 last.
- Step 6 (tests) depends on Steps 1-4 (the behavior under test must exist) but not on Step 5.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| "`AuthoritativeApplyPipeline._refresh_dirty_set`'s dead/orphaned status is resolved one way or the other (wired in correctly, or removed with its 'Phase 17 Law' comment and any now-stale references), not left in its current half-documented, uncalled state" | Step 1 (wire in the useful branch), Step 2 (delete the method + its docstring/comment) | `grep -rn "_refresh_dirty_set" --include="*.py" .` → zero hits; `test_refine_forces_full_dirty_set_when_force_full_scan_true_with_no_entity_updates`; `test_refine_does_not_force_full_dirty_set_when_force_full_scan_false` |
| "A `force_full_scan=True`-booted `Kernel`/`V2EngineManager` genuinely produces ... a WS delta whose `changed` list contains every live entity, proven by a real, passing test" | Step 1 (produces the all-entities dirty set), Step 3+4 (surfaces `force_full_scan` through `.status` so `_update_latest_state` passes the correct `force_full` value into `compute_tick_delta`) | `test_v2_engine_manager_ws_delta_changed_includes_every_alive_entity_under_force_full_scan` |
| "`V2EngineManager._update_latest_state`'s `getattr(self._kernel.status, "force_full_scan", False)` read is fixed to actually reflect the Kernel's boot-time `force_full_scan` flag" | Step 3 (declared field), Step 4 (populated at `__init__`) | `test_kernel_status_exposes_force_full_scan_from_boot_flag` |
| "`docs/parity_ledger/infrastructure.yaml`'s `INFRA-388` (or a new entry) reflects the true, post-fix end state" | Step 5c | No automated test — doc-body edit; frontmatter validity unaffected (script-checkable, not content-checkable) |

## Build Gate — Scoped Pytest Commands

All commands must run under `.venv/bin/python3` — test_plan.md's own "Scoped Pytest Commands" section
cites this exact interpreter path for every command it lists, matching this project's established
pattern for this worktree.

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

Never `pytest tests/` — all commands above are scoped to the domains this fix touches (dirty-set/
candidate-selection core, read-model/API, optimization integration, kernel boot, apply determinism)
plus the one explicitly-slow parity test this fix's determinism claim depends on.

**Note on a stale citation found during planning**: test_plan.md's "Anti-Drift Test Guards" section
and `docs/performance/optimization_invariants.md:55` both cite
`tests/integration/optimization/test_static_dirtyset_guard.py` (OPT-INV-001's guard test) as existing,
currently-passing coverage. Direct verification during planning (`find tests -iname
"*static_dirtyset*"` and `find tests -iname "*dirtyset_guard*"` from repo root) found **no such file
exists anywhere in this worktree**. This is a pre-existing stale citation in both
`optimization_invariants.md` and test_plan.md, not something this ticket's Out of Scope excludes
fixing, but also not something this ticket's own Scope asks for — flag it to the orchestrator/user as
a separate, small follow-up (a doc-accuracy hotfix on `optimization_invariants.md:55` and/or
recreating the missing test) rather than silently fixing it inside this ticket's diff or silently
dropping the citation from this plan. Do not add `test_static_dirtyset_guard.py` to the Build Gate
list above (`tests/integration/optimization/ -v` will simply not collect a file that isn't there — no
action needed to avoid a false failure), and do not claim in Step 5 doc edits that this ticket
verified OPT-INV-001 coverage — it did not, and doing so would misrepresent this ticket's actual test
surface.

## Anti-Drift Notes

(Restated from investigation.md's "Anti-Drift Hazards" for the implementer's direct attention while
coding, distinct from the Scope Guards list above which is the audit-facing enumeration.)

- The single highest-risk failure mode is wiring in `_refresh_dirty_set` as a whole — including its
  `else: DirtySet.from_update(...)` branch — either verbatim as a call, or by accidentally omitting
  the `if update.force_full_scan:` gate on the relocated logic. Test 2
  (`test_refine_does_not_force_full_dirty_set_when_force_full_scan_false`) exists specifically to
  catch this and must be run and confirmed passing, not just written.
- `RuntimeStatus` already carries six precedent-setting undeclared/ad-hoc attributes bolted on by
  `Kernel` at runtime (see Step 3). This ticket adds a seventh as a *declared* field, which is a
  narrower, better-scoped fix than the ad-hoc pattern — but resist any urge to also declare the
  existing six while the file is open; that is a separate, larger refactor with its own blast radius
  the investigation explicitly says not to take on here.
- `force_full_scan` (boot-time-fixed, `StateUpdate`/`RuntimeStatus`) and `_force_full_scan`
  (per-object, `AuthoritativeState`) are two distinct fields reconciled only in `refine()`'s
  lines 48-51 — keep this distinction precise in all new test/doc prose (see Scope Guards).

## Determinism / Correctness Verification

This is a change inside the engine's core 17-phase pipeline (`AuthoritativeApplyPipeline.refine()`)
and touches `Kernel.__init__`, so per this project's Architecture Rule (durable state, authoritative
mutation boundaries) this section is held to a higher rigor bar than a typical step's "Verify" line.
Restating investigation.md's own reasoning, which this plan relies on rather than re-deriving:

1. **Cannot affect the state hash.** `StateUpdate.dirty_set` is advisory routing/reporting metadata,
   not a field of `AuthoritativeState`. The fingerprint/hash machinery (`CanonicalStateHasher
   .get_hash`, `StateFingerprinter`) operates over `AuthoritativeState` fields (entities, world,
   etc.) — never over `StateUpdate.dirty_set`. Widening the final `dirty_set` for `force_full_scan
   =True` runs therefore cannot change either an optimized or a full-scan kernel's resulting entity
   state. `tests/perf/test_dirty_parity.py::test_dirty_set_vs_full_scan_parity` (already passing, run
   explicitly per the Build Gate list) compares `final_state_opt`/`final_state_ref` fingerprints and
   never inspects `dirty_set` content at all — this fix's change is invisible to that comparison by
   construction, not merely by coincidence.
2. **Cannot trigger `DirtySetLeakError`.** `AuthoritativeState.validate_dirty_set()`'s leak-detection
   (audit mode, `state.py:1159-1205` per investigation.md's citation) treats a *too-broad* `DirtySet`
   as safe by design — `dirty_state_and_dependency.md`'s own "conservative by design" framing states
   false positives (dirty set claims more than actually changed) are safe; only false negatives
   (dirty set claims less than actually changed) fire `DirtySetLeakError`. Since this fix only ever
   *widens* the dirty set (to the full entity set) and only when `force_full_scan=True`, it can only
   ever mask a genuine leak during a force-full-scan tick specifically — an acceptable, narrow
   audit-blind-spot risk on a diagnostic/rare-by-design flag (per `optimization_invariants.md` §3's
   own framing: "Under chaos testing, diagnostic auditing, or `DEBUG_REFERENCE` profiling"), not a
   correctness risk, and not a new risk this fix introduces relative to the pre-fix state (pre-fix,
   force_full_scan already bypassed dirty-set-based routing entirely for phase candidate selection —
   this fix only extends the same "trust force_full_scan" posture to the final reported dirty set).
3. **Cannot regress phase routing/candidate selection.** Confirmed via investigation.md's repo-wide
   `grep -rn "force_full_scan" src/`: every other consumer of the flag
   (`phase_graph.py:87`'s `should_run_phase`, `candidate_selector.py:113`'s Stage 4 bypass,
   `work_queue.py:36`, `dirty.py`'s `get_relevant_entity_ids`/`get_relevant_group_ids`/
   `CandidateSelector.entities`, `updates.py:920,951`'s `StateUpdate.force_full_scan` field/
   `is_noop()`, `long_run_harness.py:152`) reads `update.force_full_scan` or `state._force_full_scan`
   directly — none of them read the `DirtySet`'s *contents* to decide whether force-full-scan is
   active. This fix touches only the final `dirty_set` *value* returned by `refine()`, never
   `update.force_full_scan` itself, so none of these other consumers can be affected by this change.
4. **Performance cost is negligible and does not risk watchdog/tick-budget violations.** For a
   2500-entity reference-scale world, the added block does 9 set copies of `state.entities.keys()`
   (~22,500 int insertions total) — microseconds, against a tick compute budget in the tens of
   milliseconds (`Kernel._tick_once_inner`'s watchdog compares against `max(20.0, avg_ms * 2.0)`).
   `force_full_scan` is opt-in (`Kernel(flags={"force_full_scan": True})`), used today only by
   `src/perf/profile_governance.py`'s profiling harness and `tests/perf/test_dirty_parity.py`'s
   reference kernel — not a hot/every-tick path in production.
5. **`apply_generation()` is unaffected.** `ApplyPath.apply_generation()` consumes `update.dirty_set`
   only for `audit_dirty_set=True` leak validation (point 2 above) — it does not use `dirty_set`
   content to decide *what* to apply, only to audit-check afterward. `tests/integration/pipeline/
   test_authoritative_apply.py` (apply isolation, deterministic order, resource-delta correctness)
   stays green because this fix changes no application-order or mutation logic whatsoever — it only
   changes a downstream reporting artifact after all phases and application have already been decided.

## Unresolved Questions

None. Investigation.md's own "Risks and Open Questions" section states explicitly: "No open question
blocks implementation. The insertion point, the exact logic to relocate, the `RuntimeStatus` fix, and
the doc/parity-ledger updates are all concretely determined by the evidence above." This plan concurs
after independently re-verifying every cited file:line during planning (see Step-level "Change"
citations above). The one genuinely open item found during planning — the stale
`test_static_dirtyset_guard.py` citation in `optimization_invariants.md` and test_plan.md — is not a
question that changes this ticket's implementation approach; it is flagged under "Build Gate" above as
a separate follow-up, not left as a blocking unresolved question here.
