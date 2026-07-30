---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260716-PLACELEGAL-HARDLAW
artifact_type: plan
tags: [observability, determinism, world, bug]
---

# Implementation Plan — TCK-20260716-PLACELEGAL-HARDLAW

## Summary

Add a 7th `HardLawMonitor` law, `LAW-SPAWN-OCCUPANCY`, that performs an unconditional full-population placement-legality scan (entities + buildings + resource nodes) once at `Kernel.__init__` time, closing the gap where `WorldCompiler.compile()` never validates spawn positions against terrain/occupancy and the only live check (`check_occupancy()`) is dirty-set-gated and therefore blind to initial state. The new method is a fully separate `@staticmethod` on `HardLawMonitor` (`src/observability/hard_law_monitor.py`) that reuses `LegalityServiceV2.verify_occupancy()` for the WALL/blocked_tiles/building_tiles/transient_claims branches and a local, method-scoped tile-position map (following the prototype's `by_pos` pattern) to catch object-vs-object overlaps that `verify_occupancy()`'s entity-centric occupancy branch does not itself cover (building-vs-resource-node, resource-node-vs-resource-node). The call site is a new private `Kernel._run_initial_placement_check()` method invoked once near the end of `Kernel.__init__`, mirroring `_run_hard_law_checks()`'s existing mode-gating/persistence/alert-routing shape exactly, including its LONG_RUN blind spot (deliberately inherited, not fixed, per Resolved Decision 2 below). Work closes with a regression test reproducing the real seed-42 / entities-6-and-14 / tile-(27,38) bug, a negative-control test at seeds 137/999, doc and parity-ledger updates (including correcting `WORLD-076`'s currently-contradicted `verified` status), and a full run of the existing regression surface to confirm zero collateral change to the 6 existing laws or `WorldCompiler.compile()`.

## Steps

### Step 1 — Add `HardLawMonitor.check_initial_placement(state)`
**Files:** `src/observability/hard_law_monitor.py`

**Change:**
Add a new `@staticmethod check_initial_placement(state: AuthoritativeState) -> List[HardLawViolation]`, placed alongside `check_entities`/`check_occupancy` (do not modify either). Signature takes only `state` — no `DirtySet` parameter, matching the ticket's "unconditional full-population scan" requirement.

Algorithm:
1. Obtain the full-population entity-by-tile index for free via `Kernel.get_world_indexes(state, None)` (confirmed in investigation: with no `dirty_set`, this always rebuilds fresh and full — `_build_entity_index()` is not itself dirty-filtered).
2. Build a local, method-scoped tile-position map spanning all three object kinds — entities (from the index above or directly from `state.entities`), buildings (iterate `buildings_by_kind` or `state.buildings` directly — not tile-keyed today), and resource nodes (iterate `active_resource_nodes` or `state.resource_nodes` directly — not tile-keyed today), following `experiments/placement_integrity/prototype/check_placement.py`'s `by_pos` pattern (L53-57). Each map entry is a list of `(object_id, object_kind)` tuples so multi-occupant tiles are directly detectable, mirroring `check_occupancy()`'s dedupe-via-`reported_tiles` convention.
3. For each occupiable object's position, call `LegalityServiceV2.verify_occupancy(pos, state, ignore_entity_id=<the object's own id if it is an entity>)` to exercise the WALL-terrain, `blocked_tiles`, `building_tiles`, and `transient_claims` branches — this is the "reuse the existing 5-part rule" requirement; do not hand-roll a parallel WALL/blocked_tiles check.
4. Separately, walk the local tile-position map from step 2 and flag any tile with more than one occupant across entities/buildings/resource_nodes — this covers the object-vs-object overlap cases `verify_occupancy()`'s entity-centric occupancy branch does not itself catch (e.g. building-vs-resource-node), and is the direct mechanism that reproduces the real entity-6/entity-14 bug.
5. For every violation found (either from step 3's `verify_occupancy` result or step 4's multi-occupant tile), construct `HardLawViolation(law_id="LAW-SPAWN-OCCUPANCY", entity_id=<real id from its own disjoint ID space>, severity="ERROR", message=..., details={"object_kind": "entity" | "building" | "resource_node", ...})`. Confirm `LAW-SPAWN-OCCUPANCY` does not collide with any of the 6 existing law IDs before finalizing the string (investigation already confirmed no collision via grep — no further check needed, just use the string as-is).
6. Return the accumulated `List[HardLawViolation]` (empty list if none found) — same return shape as `check_occupancy()`.

**Do NOT touch:** `check_occupancy()`'s signature, its `DirtySet`-gated early return (`if not dirty_set or not dirty_set.movement_entities: return []`), or any of its call sites. Do NOT touch `check_entities()`. Do NOT touch `src/worldbuilding/compiler.py` — read-only reference only, no changes.

**Verify:** `test_check_initial_placement_full_population_scan_unit`, `test_check_initial_placement_covers_buildings_and_resource_nodes_unit`, `test_check_initial_placement_reuses_verify_occupancy_wall_terrain_unit` (all new, `tests/engine/test_hard_law_monitor.py`, per test_plan.md items 1-3).

---

### Step 2 — Regression test + negative control
**Files:** `tests/engine/test_hard_law_monitor.py`

**Change:** Add two tests using `WorldCompiler.compile(spec, seed=...)` against `unit_information_density` (or `unit_information_source`/`unit_selfmodel_pilot`) to produce a real compiled `AuthoritativeState`, then call `HardLawMonitor.check_initial_placement(state)` on the result directly (no `Kernel` needed for this test — pure function of `state`):
- `test_seed42_entity6_entity14_tile_27_38_collision`, marked `@pytest.mark.regression`, with a docstring/comment citing `TCK-20260716-PLACELEGAL-HARDLAW` and `docs/plans/idea_placement_legality_check.md` per `docs/testing/test_taxonomy.md`'s regression-marker standard. Asserts a `LAW-SPAWN-OCCUPANCY` violation naming entities 6 and 14 at tile `(27, 38)` is present.
- `test_seed137_and_seed999_no_initial_placement_violations` — same world(s) at `seed=137` and `seed=999`, asserts `check_initial_placement()` returns zero `LAW-SPAWN-OCCUPANCY` violations (proves the check is not over-firing on ordinary content).

**Do NOT touch:** `tests/unit/worldbuilding/test_world_compiler.py` or any other compiler test file — this step only calls `WorldCompiler.compile()` as a fixture-building utility inside the new test file, it does not modify the compiler's own test suite.

**Verify:** the two tests themselves; also confirms AC "New law fires and is correctly recorded... when reproducing the real seed-42 collision" and "world with no placement collisions... produces zero new-law violations."

---

### Step 3 — Wire the call site into `Kernel.__init__`
**Files:** `src/engine/kernel.py`

**Change:** Add a new private method `Kernel._run_initial_placement_check(self)`, placed near `_run_hard_law_checks()` (kernel.py:738-804) for locality, that mirrors its shape exactly:
1. Mode-gate via `ObservabilityConfig.get_mode()`: return immediately (no-op) if `OFF` (matching kernel.py:742-744).
2. Call `HardLawMonitor.check_initial_placement(self._state)`.
3. If no violations, return early (matching kernel.py:755-756).
4. Accumulate onto `self._status.hard_law_violations` / `cumulative_violations` (matching kernel.py:758-767).
5. Write violations to `hard_law_violations.jsonl` via `self._artifact_repo.resolve_path(self._run_id, "violations")`, with `tick=0` explicitly (not `self._state.tick`, since this runs before the first tick) — reuses the existing per-run artifact path, no new persistence/lifecycle code (matching kernel.py:770-788).
6. Route through `AlertsManager.get_router().route(...)` exactly as the existing template does (matching kernel.py:790-798) — reuse the existing routing call for consistency, per the ticket's own resolution of the "is init-time alerting desirable" open question (no concrete reason found in investigation to special-case it).
7. Mode-branch: raise `HardLawViolationError` only in `DEBUG`/`CERTIFICATION` (matching kernel.py:800-801); log-only in `LIGHT` (matching kernel.py:802-804); **deliberately replicate the existing `LONG_RUN` fall-through gap** (no explicit log, no raise) rather than fixing it for this one call site — see Resolved Decision 2.

Call `self._run_initial_placement_check()` exactly once, near the end of `__init__`, after `self.validate(flags)` (L311) and the `ContentWarmupService.warmup()` try/except block (L313-319) — the last statement block in `__init__` before it returns, matching the ticket's cited insertion point and its `WORLD-CAT-004` precedent for "one-time, non-fatal, pre-first-tick work."

**Do NOT touch:** `_run_hard_law_checks()` itself (kernel.py:738-804) — read as a template only, not modified. Do NOT touch `self._run_id`/`self._artifact_repo` assignment logic (kernel.py:120-125, 175-180) — only add a new call after they are already settled. Do NOT add any call site in `WorldCompiler.compile()`.

**Verify:** `test_kernel_init_calls_check_initial_placement_once` and `test_check_initial_placement_mode_gating_matches_precedent` (new, `tests/integration/kernel/test_kernel_boundaries.py` or a new `tests/integration/observability/test_initial_placement_check.py` if existing fixtures don't support full `Kernel()` construction with an injectable colliding state — decide file location based on fixture shape found during implementation, per test_plan.md item 6's own noted contingency).

---

### Step 4 — Anti-drift guard tests
**Files:** `tests/engine/test_hard_law_monitor.py`

**Change:** Add/confirm the following guard assertions (test_plan.md's "Anti-Drift Test Guards" section):
- `test_check_occupancy_signature_unchanged` — assert `HardLawMonitor.check_occupancy(state, dirty_set)`'s signature and its `DirtySet.movement_entities`-gated early return are byte-for-byte unchanged after Step 1.
- `test_no_autocorrect_on_violation` — assert that after `check_initial_placement()` detects a collision, the colliding objects' positions are byte-identical to their pre-check values (the check is read-only; no nudge-to-valid-tile logic was introduced).
- `test_severity_is_always_error_for_new_law` — assert every `HardLawViolation` from `check_initial_placement()` has `severity == "ERROR"`, never `"WARNING"`.
- `test_conservation_law_not_introduced` — assert no `law_id` starting with `CONSERVATION` is emitted by any of this ticket's new code paths.
- Re-run `test_hard_law_monitor_individual_laws` and `test_hard_law_occupancy_collision` unmodified and confirm they still pass (satisfies `test_existing_six_laws_unaffected_by_init_time_check` — no new test code required if these already cover it, per test_plan.md item 8).

**Do NOT touch:** the existing 6-law test bodies themselves — these must pass with zero edits, proving no regression.

**Verify:** the guard tests listed above, plus the existing suite passing unmodified.

---

### Step 5 — Update `docs/observability/hard_law_monitor.md`
**Files:** `docs/observability/hard_law_monitor.md`

**Change:** Two edits, one file:
1. Add one new row to the existing law table (`Law ID | Scope | Constraint Rule | Severity | Description` — confirmed exact shape in investigation) for `LAW-SPAWN-OCCUPANCY`: scope = init-time / `Kernel.__init__` (not per-tick), constraint rule = the 5-part occupancy rule reused from `LegalityServiceV2.verify_occupancy()` applied across entities/buildings/resource_nodes, severity = `ERROR`, description = one-line summary of the unconditional full-population spawn-legality scan. Match the existing 6 rows' formatting and level of detail exactly — do not restructure the table or add new columns.
2. **(Added after architecture-review NEEDS_CHANGES round.)** Correct the existing `LONG_RUN` mode description (line ~45), which currently reads "Operates similarly to `LIGHT` mode but scales metrics to prevent operational memory degradation" — this is factually inaccurate for the fall-through case investigation confirmed: `LIGHT` explicitly logs a warning (`kernel.py:802-804`), `LONG_RUN` does neither log nor raise. Since this ticket doubles the laws exposed to that gap (1 → 2) while already editing this exact file, fix the description to state the real fall-through behavior accurately (no explicit log, no raise in `LONG_RUN` mode) and note it now applies to both the 6 existing laws and `LAW-SPAWN-OCCUPANCY`. This is a documentation-accuracy correction only — the inherited `LONG_RUN` behavior itself is unchanged (see Resolved Decision 2: deliberately not diverging from the existing cross-law mode-gating precedent).

**Do NOT touch:** `docs/guides/observability.md`'s stale "event-listener" description — explicitly out of scope for this ticket (deferred to whoever owns that guide). Do not change the actual `LONG_RUN` mode-gating *behavior* in kernel.py — only correct this doc's description of it.

**Verify:** manual review that the new row matches the existing table shape and the `LONG_RUN` correction accurately describes the real fall-through behavior; this doc update itself is the AC (no automated test covers doc content, per project convention for doc-shape ACs).

---

### Step 6 — Parity ledger updates
**Files:** `docs/parity_ledger/world_dynamics.yaml`

**Change (three edits, one file):**
1. Add a new entry for `LAW-SPAWN-OCCUPANCY` — `status: verified` (the new law and its regression test both exist and pass by this point in the plan), `priority: P1` (matching the ticket's own priority; do not claim `P0` — no existing precedent law in this file is graded P0 for a single init-time check), `v2_evidence` describing the new `check_initial_placement()` method and its `Kernel.__init__` call site, `test_path` pointing at `tests/engine/test_hard_law_monitor.py::test_seed42_entity6_entity14_tile_27_38_collision` (the regression test from Step 2).
2. Update `WORLD-076` ("Spawn avoids occupied tile or uses conflict-safe placement"): change `status` from `verified` to `divergent`, add a `divergence_note` citing this ticket's own regression test (Step 2) as the contradicting evidence — i.e. spawn placement does *not* reliably avoid occupied tiles today; the new `LAW-SPAWN-OCCUPANCY` check now detects and records the violation but does not fix the underlying RNG collision (root-causing that is explicitly out of scope, per the ticket). Per the project's lineage convention (`INFRA-270`'s "historical entries are not rewritten in place" precedent), do not delete or overwrite the existing `v2_evidence` text — append the correction forward (new `divergence_note` field / dated addendum), leaving the prior "checklist audit" claim visible as historical record.
3. Update `WORLD-075` ("Spawn avoids invalid terrain"): add `test_path` pointing at `tests/engine/test_hard_law_monitor.py::test_check_initial_placement_reuses_verify_occupancy_wall_terrain_unit` (Step 1's WALL-terrain test) — this claim is not contradicted, only weakly evidenced before; leave `status: verified` as-is, only strengthen `test_path`/`v2_evidence`.

**Do NOT touch:** any other entry in `world_dynamics.yaml`, or any other parity ledger file (`infrastructure.yaml`, `substrate.yaml`, etc.) — no other file has any `HardLawMonitor`/`LAW-*` reference per investigation's grep.

**Verify:** YAML schema validation against `docs/parity_ledger/schema.json` (if a validation script exists, run it); manual cross-check that `test_path` values point at tests that actually exist and pass after Step 1/2 land.

---

### Step 7 — Full regression-surface verification
**Files:** none (verification only)

**Change:** none — run the scoped pytest commands from `test_plan.md`'s "Scoped Pytest Commands" section to confirm zero collateral regression:
```
.venv/bin/python3 -m pytest tests/engine/test_hard_law_monitor.py -v
.venv/bin/python3 -m pytest tests/integration/kernel/ -v
.venv/bin/python3 -m pytest tests/integration/observability/ -v
.venv/bin/python3 -m pytest tests/unit/optimization/test_world_index_service.py -v
.venv/bin/python3 -m pytest tests/unit/worldbuilding/ -v
.venv/bin/python3 -m pytest tests/perf/test_hard_law_monitor_overhead.py -v
.venv/bin/python3 -m pytest tests/engine/test_hard_law_monitor.py -m regression -v
```
Do not run `pytest tests/` (full suite) — scope stays to the domains above per project testing rule.

**Do NOT touch:** any file outside the ones already changed in Steps 1-6 — this step is verification-only, no code changes.

**Verify:** all commands above pass; the perf test's tick-loop overhead assertion is confirmed unaffected (Step 3's added work is one-time at `Kernel()` construction, not per-tick).

## Scope Guards

Reiterated verbatim from the ticket's Out of Scope section — none of the following may be touched by this plan:

- SimQ WORLD-pillar frequency-scoring signal for the new law's violations — belongs to `TCK-20260716-PLACELEGAL-SIMQ-SIGNAL` (depends on this ticket's `law_id` existing).
- `WorldEntitySpawner`'s shared-`default_position` bug in `src/worldassembly/entity_spawner.py` — a separate, more severe instance of the same problem class in a structurally different pipeline (`SimulationScenarioDefinition` input, not `WorldSpec`). Do not fold into this ticket.
- Root-causing *why* the entity-6/entity-14 collision happens (suspected entity-ID-keyed spawn RNG formula, not confirmed) — this ticket detects and records the violation, it does not fix the underlying spawn-placement RNG.
- Auto-correction/nudge-to-nearby-valid-tile behavior — log-always, hard-fail only in `DEBUG`/`CERTIFICATION`; no auto-repair path for any of the 6 existing laws either.
- Extending live per-tick `check_occupancy()` with terrain-awareness — not decided as needed; this ticket closes the init-time gap only.
- Fixing `docs/guides/observability.md`'s stale "event-listener" description of `HardLawMonitor` — unrelated pre-existing doc staleness, not this ticket's job.
- Implementing a `CONSERVATION`-prefixed law (`EconomyScorer` already handles `conservation_law_violated`/`conservation_law_verified` but no law produces that `law_id` prefix) — unrelated to placement legality, not this ticket's job. Do not touch `src/simulation_quality/quality_hub.py::_translate_invariant()`.

Additional guards from the investigation's Anti-Drift Hazards, restated for the implementer:

- Do not widen `check_occupancy()`'s `DirtySet`-scoped signature or add an `initial_scan: bool` flag to it — implement `check_initial_placement()` as a fully separate method (Step 1).
- Do not touch `WorldCompiler.compile()` — read-only reference only; it has no `run_id`/`Kernel` context to persist violations against.
- Do not implement auto-correction/nudge-to-valid-tile behavior.
- Do not fold in `WorldEntitySpawner`'s `default_position` bug.
- Do not implement the `CONSERVATION`-prefixed law or touch `quality_hub.py::_translate_invariant()`.
- Do not silently "fix" `docs/guides/observability.md` while touching `docs/observability/hard_law_monitor.md` in Step 5.
- When updating `WORLD-075`/`WORLD-076` in Step 6, do not silently rewrite their historical `v2_evidence` — append forward, per the `INFRA-270` lineage convention.

## Dependency Map

- **Step 1** (production method) has no dependencies — first step.
- **Step 2** (regression + negative-control tests) depends on **Step 1** (method must exist to call).
- **Step 3** (Kernel wiring) depends on **Step 1** (calls `check_initial_placement`); independent of Step 2.
- **Step 4** (anti-drift guards) depends on **Step 1** and **Step 3** (guards assert behavior of both the method and the wiring).
- **Step 5** (doc update) depends on **Step 1** (law ID, severity, and scope must be finalized before documenting) — can proceed in parallel with Steps 2-4 once Step 1 lands.
- **Step 6** (parity ledger) depends on **Step 2** (needs the regression test's path to cite as `test_path` evidence) and **Step 1** (WALL-terrain test path for `WORLD-075`).
- **Step 7** (full verification) depends on all of Steps 1-6 being complete.

Steps 2, 3, and 5 may proceed in parallel once Step 1 is done; Step 4 waits on Step 3; Step 6 waits on Step 2.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `check_initial_placement(state)` exists, unconditional full-population scan, same 5-part occupancy rule as `verify_occupancy()` | Step 1 | `test_check_initial_placement_full_population_scan_unit`, `test_check_initial_placement_covers_buildings_and_resource_nodes_unit`, `test_check_initial_placement_reuses_verify_occupancy_wall_terrain_unit` |
| New law fires and is correctly recorded (`law_id`, `entity_id`, `severity="ERROR"`, `details["object_kind"]`) reproducing the real seed-42 collision | Step 1, Step 2 | `test_seed42_entity6_entity14_tile_27_38_collision` |
| Check called exactly once from `Kernel.__init__` after `self._run_id`/`self._artifact_repo` are set; violations persist to `hard_law_violations.jsonl` at `tick=0` via existing artifact path | Step 3 | `test_kernel_init_calls_check_initial_placement_once` |
| Mode gating matches existing precedent exactly (`OFF` skip, `DEBUG`/`CERTIFICATION` raise, others log) | Step 3 | `test_check_initial_placement_mode_gating_matches_precedent` |
| All 6 existing laws' behavior and existing tests unaffected | Step 4 | `test_hard_law_monitor_individual_laws`, `test_hard_law_occupancy_collision` (re-run unmodified), `test_check_occupancy_signature_unchanged` |
| Clean seed (137/999) produces zero new-law violations | Step 2 | `test_seed137_and_seed999_no_initial_placement_violations` |
| `regression`-marker test added, citing ticket + idea doc | Step 2 | `test_seed42_entity6_entity14_tile_27_38_collision` (marker + docstring citation) |
| `docs/parity_ledger/world_dynamics.yaml` entry added/updated | Step 6 | manual schema/cross-check (Step 6 Verify) |
| `docs/observability/hard_law_monitor.md` updated matching existing per-law shape | Step 5 | manual review (Step 5 Verify) |

## Resolved Decisions

**1. How the new method builds its combined entity+building+resource-node tile map.**
Resolved: build a local, method-scoped tile-position map inside `check_initial_placement()` itself, following the prototype's own `by_pos` pattern (`experiments/placement_integrity/prototype/check_placement.py`, L53-57) — reusing `Kernel.get_world_indexes(state, None)` for the entity half (already a full-population index, confirmed in investigation: `_build_entity_index()` is not itself dirty-filtered), and iterating `state.buildings`/`state.resource_nodes` (or `buildings_by_kind`/`active_resource_nodes`) directly for the other two, since neither is tile-keyed today. This is implemented in **Step 1**. Rationale: extending `WorldIndexService` itself was considered and rejected — the ticket's own Related Code Areas list does not name `WorldIndexService` as something to modify, and widening it would turn a scoped bug-fix ticket into an index-service refactor, which the investigation's Anti-Drift Hazards section explicitly warns against by analogy (don't widen adjacent shared infrastructure beyond what the ticket names).

**2. `LONG_RUN`-mode blind-spot inheritance.**
Resolved: the new `_run_initial_placement_check()` (**Step 3**) deliberately replicates `_run_hard_law_checks()`'s existing mode-gating behavior exactly, including its known `LONG_RUN` fall-through gap (no explicit log, no raise in that mode) — confirmed in investigation as a pre-existing quirk in the reused template, not something this ticket introduces. Rationale: the ticket's own Scope section states "reuse `_run_hard_law_checks()`'s existing violation-handling shape... do not invent a new violation-response policy." Diverging mode-gating behavior for this one new law would create an inconsistency between the 6 existing laws and the 7th, which is a worse outcome than inheriting a known, already-accepted quirk. The inherited `LONG_RUN` gap is flagged here as a known limitation — fixing it uniformly across all 7 laws is future-ticket scope, not this ticket's.

**3. `WORLD-076`/`WORLD-075` parity correction.**
Resolved as part of **Step 6**: `WORLD-076`'s `status` changes from `verified` to `divergent`, with a `divergence_note` citing this ticket's own regression test (`test_seed42_entity6_entity14_tile_27_38_collision`, Step 2) as the contradicting evidence — the entry's prior `verified` status with `test_path: null` and only a generic "checklist audit" citation is exactly the unverifiable-P0-claim pattern the project's own rule ("P0 entries require a passing `test_path`") exists to catch, and this ticket's evidence directly contradicts it (spawn placement does not reliably avoid occupied tiles). Once a future ticket fixes the underlying RNG collision (out of scope here) and re-verification is possible, a later pass can flip `WORLD-076` back to `verified` with real evidence. `WORLD-075` is not contradicted (no `WALL` terrain exists corpus-wide) but shares the same weak-evidence pattern — its `test_path` is strengthened to point at the new WALL-terrain regression coverage from Step 1, `status` remains `verified`. A new, separate `LAW-SPAWN-OCCUPANCY` entry is added (no existing entry currently names `HardLawMonitor` or any `LAW-*` id, confirmed by investigation's grep of `infrastructure.yaml`).

## Anti-Drift Notes

- `check_occupancy()` (kernel.py-adjacent, in `hard_law_monitor.py`) is intentionally tick-scoped and dirty-set-gated — never widen its signature; `check_initial_placement()` must remain a fully independent method (Step 1).
- `OPT-INV-002` ("Force Full Scan Compliance," `docs/performance/optimization_invariants.md`) is confirmed scoped to the 7 runtime tick phases, not `Kernel.__init__`/compile-time work — do not treat it as a constraint on this new call, and do not add tick-phase instrumentation to satisfy an invariant that doesn't apply here.
- `WorldCompiler.compile()` remains read-only reference throughout this plan — the call site is exclusively `Kernel.__init__` (Step 3). No persistence plumbing exists at compile time and none should be invented.
- `entity_id`/`next_building_id`/`next_resource_id` ID spaces are confirmed disjoint (start at 1 / 20000 / 10000 respectively, monotonic, never reset mid-compile) for all real content — `HardLawViolation.entity_id` can safely hold any of the three without a schema change; `details["object_kind"]` is the sole disambiguator, values are exactly `"entity" | "building" | "resource_node"` (confirmed aligned with the compiler's own counter names, no new naming to invent).
- `data/runs/run_1784099122_5169/hard_law_violations.jsonl` (the ticket's originally-cited production evidence) no longer exists — `data/runs/` is routinely cleaned. The Step 2 regression test must derive its expected collision from a fresh `WorldCompiler.compile(spec, seed=42)` call, not from any stored run directory; the original evidence content is preserved verbatim in `experiments/placement_integrity/PROPOSAL.md` §5b for reference only.
- Per the project's "After Work" cleanup rule, run `rm -rf data/runs/* reports/release_proof/*` after Step 7's verification run if any run artifacts were generated during testing.

## Deviations

**Revision 1 (architecture-review NEEDS_CHANGES round):** an architecture-reviewer pass on the
original Step 5 draft returned NEEDS_CHANGES, finding that `docs/observability/hard_law_monitor.md`
already inaccurately describes `LONG_RUN` mode's fall-through behavior ("Operates similarly to
`LIGHT` mode" — false; `LIGHT` logs a warning, `LONG_RUN` does neither log nor raise), and this
plan doubles the laws exposed to that gap (1 → 2 via the new `LAW-SPAWN-OCCUPANCY` law) while
already editing that exact file, without correcting it. Fixed by adding a second edit to Step 5:
correcting the `LONG_RUN` description to state the real fall-through behavior accurately, noting it
now applies to both the 6 existing laws and the new one. This is a documentation-accuracy
correction only — it does not change Resolved Decision 2's actual inherited `LONG_RUN` behavior,
which remains a deliberate, defensible choice not to diverge from existing cross-law mode-gating
precedent. All other steps (1-4, 6-7), Resolved Decisions 1 and 3, and the Scope Guards are
unchanged from the original plan.

**Revision 2 (implementation-time findings):** two findings emerged while implementing Step 1/Step 2
that the plan's original text did not fully anticipate; both are documented here per the "never
silently deviate" rule rather than worked around quietly.

1. **Buildings are excluded from direct `verify_occupancy()` calls.** Step 1's algorithm point 3 as
   originally written ("for each occupiable object's position, call `verify_occupancy(...)`") was
   implemented for entities and resource nodes only, *not* buildings. Empirical verification
   (`LegalityServiceV2.verify_occupancy(building.position, state)` called directly against a real
   compiled world) confirmed the prototype's own documented self-reference footgun applies here too:
   `src/worldbuilding/compiler.py:258` adds every building's own tile to `state.blocked_tiles` at
   compile time, so calling `verify_occupancy()` against a building's own position always returns
   `False` (`PATH_NOT_FOUND`) against itself — a guaranteed false positive on literally every
   building in every world, not a real violation. `verify_occupancy()`'s `ignore_entity_id` parameter
   only suppresses this for the *dynamic entity occupancy* branch (part 5 of the 5-part rule); there
   is no equivalent "ignore self" mechanism for the `blocked_tiles` branch (part 1), and the plan's
   own anti-drift guard forbids changing `verify_occupancy()`'s signature to add one. Resource nodes
   carry no such self-registration (confirmed by reading the compiler's resource-compile loop, which
   never touches `blocked_tiles`) and are safe to check directly, so they remain in the
   `verify_occupancy()` pass. Buildings are still fully covered for object-vs-object overlap via the
   multi-occupant tile scan (Step 1 algorithm point 4), which is self-reference-safe by construction
   — this is how the real entity-vs-building and building-vs-resource-node cases in
   `test_check_initial_placement_covers_buildings_and_resource_nodes_unit` are actually caught. Net
   effect: buildings lose only the (corpus-wide unexercised, zero real instances found) WALL-terrain
   sub-case of the 5-part rule; every other case is still covered by one of the two mechanisms.

2. **Negative-control test world/seeds changed.** The plan's Step 2 (and the ticket's own AC/idea
   doc) proposed using seeds 137 and 999 against `unit_information_density`/`unit_information_source`/
   `unit_selfmodel_pilot` as the "known clean" negative control, based on the idea doc's prior finding
   that entities 6 and 14 specifically don't collide at those seeds. Implementing
   `check_initial_placement()` and running it against those exact seeds revealed this claim was
   narrower than it read: entities 6/14 indeed don't collide at seeds 137/999, but *different* entity
   pairs do — `(10, 13)` at tile `(30, 18)` for seed 137, `(1, 6)` at tile `(16, 31)` for seed 999,
   reproduced identically across all three of the originally-named worlds. A wider sweep run during
   implementation (all 18 real worlds × seeds 42/137/999, using the actual new `check_initial_placement()`
   method) found 17 of 18 worlds have at least one `LAW-SPAWN-OCCUPANCY` violation at seed 137, and
   most also at seed 999 — the placement-collision problem is dramatically more widespread across the
   corpus than the ticket's original framing ("one fully deterministic, 100%-reproducible bug")
   suggested. This does not change this ticket's scope (root-causing the RNG collision remains
   explicitly out of scope) but is exactly the kind of finding the ticket's own Assumptions section
   licensed logging if found ("worth a note in Test Summary if found incidentally"). The negative
   control was switched to `wilderness_survival`, empirically confirmed collision-free across seeds
   42, 137, and 999 (the only world in the 18-world corpus confirmed clean at all three), which
   still satisfies the AC's actual intent — proving `check_initial_placement()` does not over-fire on
   genuinely clean compiled content — without asserting a false "clean" claim about worlds that are
   not in fact clean. `WORLD-076`'s divergence note (Step 6) was strengthened to cite this broader
   finding. See `test_seed137_and_seed999_no_initial_placement_violations`'s docstring in
   `tests/engine/test_hard_law_monitor.py` for the same explanation inline with the code.

All other steps, Resolved Decisions, and Scope Guards remain unchanged from Revision 1.

**Revision 3 (done-checker BLOCKED finding, post-Implement):** Step 6's `WORLD-076` update, as
originally implemented, deleted the entry's prior `v2_evidence` text ("Implementation proven via
exhaustive checklist audit Phase 1-11") outright and replaced it wholesale with the new
`divergence_note`, directly violating this same Step's own instruction above ("do not delete or
overwrite the existing `v2_evidence` text — append the correction forward... leaving the prior
'checklist audit' claim visible as historical record") and the `INFRA-270` lineage precedent it
cites. `done-checker` caught this as a real DoD violation. Fixed by editing `divergence_note` to
open with the prior claim quoted verbatim ("Prior claim (this entry's original v2_evidence,
preserved here per the INFRA-270 lineage convention...): 'Implementation proven via exhaustive
checklist audit Phase 1-11.' That checklist audit did not catch this bug.") before the existing
contradicting-evidence narrative, so the historical claim remains visible in the entry rather than
silently vanishing. `v2_evidence`/`status`/`test_path`/`priority` are unchanged from the original
Step 6 implementation — only `divergence_note` was edited. No new entry was created (the
`INFRA-267`→`INFRA-270` two-entry pattern was considered and rejected as broader than this
finding requires: the plan's own Step 6 text already scoped this as a single-entry update with an
appended note, not a new-entry supersession).
