---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260716-PLACELEGAL-HARDLAW
phase: done
date: 2026-07-16
tags: [observability, determinism, world, bug]
---

# TCK-20260716-PLACELEGAL-HARDLAW

## Title
New `HardLawMonitor` law for initial-spawn placement legality (compile-time occupancy collisions never checked)

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`src/worldbuilding/compiler.py::WorldCompiler.compile()` never validates entity/building/resource-node placement against terrain or occupancy — confirmed by direct grep (zero hits for `walkable`/`LegalityService`/`occupancy` in that file). Live per-tick occupancy IS checked (`HardLawMonitor.check_occupancy()` → `LegalityServiceV2.verify_occupancy()`), but only against `dirty_set.movement_entities` — entities that moved *that specific tick*. Initial spawn state is never checked by anything.

This is a real, reproduced, independently-corroborated bug, not a hypothetical gap (full evidence trail in `docs/plans/idea_placement_legality_check.md`):
- A standalone prototype (`experiments/placement_integrity/prototype/check_placement.py`) swept all 18 real worlds in `data/worlds/` and found entities 6 and 14 spawning on the identical tile `(27, 38)` at seed 42, in three structurally similar worlds. Confirmed seed-dependent (no collision at seeds 137/999).
- Corroborated independently in production observability data: a real completed `Kernel` run (`data/runs/run_1784099122_5169/`, seed 42) shows the identical collision in its own `hard_law_violations.jsonl`, first logged at tick 7 — a quantified 7-tick detection lag after the violation existed from tick 0.
- Corpus-wide sweep of all retained runs under `data/runs/` (re-verified 2026-07-16): 20 of 255 runs (7.8%) show a hard-law violation, all 39 instances are this exact same tile/entity-pair — one fully deterministic, 100%-reproducible bug, re-triggered repeatedly across independent runs, each discovery 7+ ticks late.

## Scope
- New `HardLawMonitor` method, e.g. `check_initial_placement(state: AuthoritativeState) -> List[HardLawViolation]` (`src/observability/hard_law_monitor.py`) — an **unconditional full-population scan** (not `DirtySet`-gated; nothing has "moved" yet at init time), reusing the existing full 5-part occupancy rule from `LegalityServiceV2.verify_occupancy()` (`src/engine/legality.py`): `WALL` terrain, OR `blocked_tiles`, OR `building_tiles`, OR `transient_claims`, OR live entity/building/resource-node occupancy. Do not reuse or repurpose `check_occupancy()`'s `DirtySet`-scoped signature — it is intentionally tick-scoped (see `docs/performance/optimization_invariants.md` OPT-INV-002, confirmed scoped to the 7 runtime tick phases, not compile/init time — do not treat that invariant as covering this new call).
- New law, working name `LAW-SPAWN-OCCUPANCY` (confirm exact naming against `docs/observability/hard_law_monitor.md`'s existing vocabulary during Investigate), `severity="ERROR"` — matching all 6 existing laws' severity convention (no law currently uses `WARNING`).
- Call site: **`Kernel.__init__`**, not `WorldCompiler.compile()`. Confirmed via direct read: `self._run_id` is assigned at `kernel.py:120-123` and `self._artifact_repo` is available by `kernel.py:180` — both well before `__init__` returns — so a full run context already exists by the time `__init__` runs, letting the new check reuse the existing per-run `hard_law_violations.jsonl` persistence path unmodified. `WorldCompiler.compile()` itself has no run context (no `run_id`, no `Kernel` instance) and is not a valid call site for anything that needs to persist a violation record. Add the new check as a new private method (e.g. `self._run_initial_placement_check()`) called once near the end of `__init__`, after `self.validate(flags)` and the `ContentWarmupService.warmup()` block (`kernel.py:311-319`) — that block is the direct architectural precedent for "one-time, non-fatal, pre-first-tick work" (see its own `WORLD-CAT-004` comment tag).
- Reuse `_run_hard_law_checks()`'s existing violation-handling shape (`kernel.py:738-804`) as the implementation template for the new method: mode-gate via `ObservabilityConfig.get_mode()` (skip entirely if `OFF`, matching `kernel.py:742-744`); write violations to `hard_law_violations.jsonl` via `self._artifact_repo.resolve_path(self._run_id, "violations")` with `tick=0` (matching `kernel.py:770-788`); route through `AlertsManager` (matching `kernel.py:790-798`); raise `HardLawViolationError` only in `DEBUG`/`CERTIFICATION` modes (matching `kernel.py:800-801`) — do not invent a new violation-response policy, this precedent already answers the hard-fail-vs-log-only question the idea doc raised.
- `HardLawViolation.entity_id: int` schema: **no field change needed.** Confirmed entity IDs start at 1 (`next_entity_id = 1`, `compiler.py:264`), resource-node IDs start at 10000, building IDs start at 20000 (`compiler.py`, confirmed by grep) — all three ID spaces are disjoint, so `entity_id` can safely hold whichever object's real ID triggered the violation. Add `details["object_kind"] = "entity" | "building" | "resource_node"` (the existing free-form `details: Dict[str, Any]` field, already used by other laws) to disambiguate which ID space `entity_id` refers to — this is the resolution to the idea doc's open schema question, not a new one.
- Add a `regression`-marker test reproducing the real seed-42 / entities-6-and-14 / tile-(27,38) collision (per `docs/testing/test_taxonomy.md`'s stated purpose for that marker — proving a previously-identified, reproduced bug doesn't return), citing this ticket and `docs/plans/idea_placement_legality_check.md` as originating evidence.
- Parity ledger entry: add/update `docs/parity_ledger/world_dynamics.yaml` (new law = new behavior).

## Out of Scope
- SimQ WORLD-pillar frequency-scoring signal for the new law's violations — `TCK-20260716-PLACELEGAL-SIMQ-SIGNAL` (depends on this ticket's `law_id` existing; see `SEQUENCE.md`).
- `WorldEntitySpawner`'s shared-`default_position` bug in `src/worldassembly/` (`entity_spawner.py`) — a separate, more severe instance of the same problem class in a structurally different pipeline (`SimulationScenarioDefinition` input, not `WorldSpec`), explicitly excluded per the idea doc's scope-boundary finding. Do not fold into this ticket.
- Root-causing *why* the entity-6/entity-14 collision happens (suspected entity-ID-keyed spawn RNG formula, not confirmed) — this ticket detects and records the violation, it does not fix the underlying spawn-placement RNG.
- Auto-correction/nudge-to-nearby-valid-tile behavior — out of scope per the reused severity/mode-gating precedent (log-always, hard-fail only in DEBUG/CERTIFICATION; no auto-repair path exists for any of the 6 existing laws either).
- Extending live per-tick `check_occupancy()` with terrain-awareness — not decided as needed; this ticket closes the init-time gap only.
- Fixing `docs/guides/observability.md`'s stale "event-listener" description of `HardLawMonitor` — unrelated pre-existing doc staleness, flagged in the idea doc for whoever owns that guide, not this ticket's job.
- Implementing a `CONSERVATION`-prefixed law (a separate, precisely-located, independently-confirmed gap found during this idea's investigation — `EconomyScorer` already fully handles `conservation_law_violated`/`conservation_law_verified` but no law produces that `law_id` prefix) — unrelated to placement legality, not this ticket's job.

## Acceptance Criteria
- [x] New `HardLawMonitor.check_initial_placement(state)` method exists, performs an unconditional full-population scan (entities + buildings + resource nodes) using the same 5-part occupancy rule as `LegalityServiceV2.verify_occupancy()`.
- [x] New law fires and is correctly recorded (`law_id`, `entity_id`, `severity="ERROR"`, `details["object_kind"]`) when reproducing the real seed-42 collision (entities 6 and 14, tile `(27, 38)`, worlds `unit_information_density`/`unit_information_source`/`unit_selfmodel_pilot`).
- [x] Check is called exactly once, from `Kernel.__init__`, after `self._run_id`/`self._artifact_repo` are set; violations persist to that run's `hard_law_violations.jsonl` at `tick=0`, using the existing per-run artifact path (no new persistence/lifecycle code).
- [x] Mode gating matches existing precedent exactly: skipped entirely when `ObservabilityConfig.get_mode() == OFF`; raises `HardLawViolationError` only in `DEBUG`/`CERTIFICATION`; logs (no raise) in all other modes.
- [x] All 6 existing laws' behavior and existing tests are unaffected (no shared-state regression from adding the new init-time call).
- [x] A world with no placement collisions produces zero new-law violations — confirms the check isn't over-firing. (See Implementation Notes: the ticket's originally-suggested seed 137/999 example against `unit_information_density`/etc. was found NOT clean once checked with the full-population scan — a different entity pair collides at those seeds. `wilderness_survival` at seeds 42/137/999 is used instead, empirically confirmed clean.)
- [x] `regression`-marker test added, citing this ticket and the idea doc as originating evidence.
- [x] `docs/parity_ledger/world_dynamics.yaml` entry added/updated for the new law.
- [x] `docs/observability/hard_law_monitor.md` (P1, authoritative) updated with the new law's entry, matching its existing per-law documentation shape exactly.

## Related Tickets
TCK-20260716-PLACELEGAL-SIMQ-SIGNAL (depends on this ticket's `law_id`; see `SEQUENCE.md` in this folder)

## Related Docs
docs/plans/idea_placement_legality_check.md (originating investigation), docs/observability/hard_law_monitor.md (P1, authoritative — target for the new law's documentation), docs/testing/test_taxonomy.md (`regression` marker), docs/parity_ledger/world_dynamics.yaml, docs/performance/optimization_invariants.md (OPT-INV-002 — confirmed NOT applicable to this compile/init-time call, cited to preempt a future misreading)

## Related Stored Artifacts
none yet — `experiments/placement_integrity/PROPOSAL.md` and `experiments/placement_integrity/prototype/check_placement.py` are the pre-ticket investigation trail this idea distills (not staged artifacts of this ticket)

## Related Code Areas
src/observability/hard_law_monitor.py, src/engine/kernel.py (`__init__` lines ~120-123, ~180, ~300-319 call-site precedent, `_run_hard_law_checks` lines 738-804 implementation template), src/engine/legality.py (`LegalityServiceV2.verify_occupancy`), src/worldbuilding/compiler.py (entity/building/resource-node ID assignment — read-only reference, no changes needed here), docs/parity_ledger/world_dynamics.yaml

## Assumptions / Open Questions
- Exact `law_id` string: working name `LAW-SPAWN-OCCUPANCY`; confirm during Investigate it doesn't collide with or duplicate `LAW-OCCUPANCY-COLLISION`'s naming pattern.
- Whether the new law needs its own dedicated method or can be expressed as a parameterized variant of `check_occupancy()` (e.g. an `initial_scan: bool` flag) — leaning toward a dedicated method given the semantic difference (unconditional full scan vs. dirty-set-filtered), but this is a real implementation-time call, not decided here.
- Whether `AlertsManager` routing at init time is desirable (an init-time alert fires before any user/operator is necessarily watching a live run) — reuse the existing routing call for consistency unless Investigate finds a concrete reason to skip it for this one call site.
- A wider seed sweep (idea doc notes only 3 seeds × 3 affected worlds tested; 54+ untested compiles across all 18 worlds) might surface additional distinct violations beyond the one recurring bug — not required for this ticket's acceptance criteria, but worth a note in Test Summary if found incidentally.

## Implementation Notes
Implemented per `staging_artifacts/TCK-20260716-PLACELEGAL-HARDLAW/plan.md` (Revision 1, plus this
ticket's own Revision 2 addendum recorded in that file's Deviations section).

**Step 1 — `HardLawMonitor.check_initial_placement(state)`** (`src/observability/hard_law_monitor.py`):
new `@staticmethod`, signature `(state) -> List[HardLawViolation]`, no `DirtySet`. Builds a local,
method-scoped `by_pos` tile map across `state.entities` (active/alive only), `state.buildings`, and
`state.resource_nodes`. Two detection passes: (1) a multi-occupant tile scan over `by_pos` — the
primary, self-reference-safe mechanism that catches all object-vs-object overlaps (this is what
reproduces the real entity-6/entity-14 bug); (2) for entities and resource nodes only (NOT buildings
— see deviation below), a call to `LegalityServiceV2.verify_occupancy()` reusing its WALL/
`blocked_tiles`/`building_tiles`/`transient_claims`/dynamic-occupancy 5-part rule, skipped for tiles
already reported by pass 1 (mirrors `check_occupancy()`'s `reported_tiles` dedupe convention). Every
violation uses `law_id="LAW-SPAWN-OCCUPANCY"`, `severity="ERROR"`, `details["object_kind"]` in
`{"entity", "building", "resource_node"}`.

**Deviation (documented in plan.md Deviations, Revision 2):** buildings are excluded from the direct
`verify_occupancy()` pass. `src/worldbuilding/compiler.py:258` adds every building's own tile to
`state.blocked_tiles` at compile time, so calling `verify_occupancy()` against a building's own
position always self-flags (`PATH_NOT_FOUND`) — confirmed empirically against a real compiled world
before writing the fix. `verify_occupancy()`'s `ignore_entity_id` only suppresses this for the
dynamic-entity branch, not `blocked_tiles`, and its signature cannot be changed (anti-drift guard).
Buildings remain fully covered for overlap detection via the multi-occupant scan; only the
(corpus-wide unexercised) WALL-terrain sub-case is not directly exercised for buildings specifically.

**Step 2 — regression + negative control** (`tests/engine/test_hard_law_monitor.py`): 3 unit tests for
Step 1's mechanics, `test_seed42_entity6_entity14_tile_27_38_collision` (`@pytest.mark.regression`,
compiles `unit_information_density` fresh at `seed=42`, asserts the exact entities-6/14 tile-(27,38)
violation), and `test_seed137_and_seed999_no_initial_placement_violations`.

**Deviation (documented in plan.md Deviations, Revision 2):** the negative-control test could not use
the ticket's originally-suggested seeds 137/999 against `unit_information_density` — implementing and
running `check_initial_placement()` against those seeds found they are NOT collision-free; a
*different* entity pair collides at each (`(10,13)`@`(30,18)` for seed 137, `(1,6)`@`(16,31)` for seed
999, reproduced identically across all 3 originally-named worlds). A corpus-wide sweep (all 18 worlds
× seeds 42/137/999) run during implementation found 17/18 worlds have ≥1 violation at seed 137 — the
placement-collision problem is far more widespread than the ticket's original framing suggested. Not
fixed (root-causing the RNG is explicitly out of scope) but flagged here per the ticket's own
Assumptions section, which licensed exactly this kind of incidental finding. Negative control switched
to `wilderness_survival` (empirically confirmed clean across seeds 42/137/999 — the only corpus world
confirmed clean at all three).

**Step 3 — `Kernel._run_initial_placement_check()`** (`src/engine/kernel.py`): new private method,
placed immediately before `_run_hard_law_checks()`; mirrors its mode-gate/accumulate/persist(`tick=0`
explicit)/route/raise-or-log shape exactly, including the inherited `LONG_RUN` fall-through (neither
logs nor raises). Called once, as the last statement in `__init__`, immediately after the
`ContentWarmupService.warmup()` try/except block. New integration tests in a new file
`tests/integration/observability/test_initial_placement_check.py` (per test_plan.md's own noted
contingency — `test_kernel_boundaries.py`'s fixtures build a clean state and don't need a colliding
one): `test_kernel_init_calls_check_initial_placement_once` (monkeypatches
`HardLawMonitor.check_initial_placement` with a call-counting spy, asserts exactly 1 call and exactly
1 JSONL record at `tick=0`) and `test_check_initial_placement_mode_gating_matches_precedent` (OFF/
DEBUG/CERTIFICATION/LIGHT/LONG_RUN, matching Step 3's spec).

**Test-authoring note (not a plan deviation, scoped to the test file only):** constructing a `Kernel`
with a pre-existing violation in `DEBUG`/`CERTIFICATION` mode raises `HardLawViolationError` from
inside `__init__` itself — the constructor never returns, so there is no `kernel` variable to call
`.shutdown()` on, and the `EventRecorder`/`QueueDrainWorker` thread already started earlier in
`__init__` leaks (tripped the session-scoped `tests/conftest.py` thread-leak sentinel on first run).
This is a pre-existing gap in `Kernel.__init__`'s exception safety (any exception raised after
`EventRecorder` construction and before return already had this property, e.g. `ProfileValidator`
errors in `self.validate(flags)`) that this ticket's new call site was simply the first to exercise in
tests. Fixing `__init__`'s exception safety is a separate, unrelated concern, out of this ticket's
scope; the test instead reclaims the leaked `EventRecorder` via `gc.get_objects()` and calls
`.shutdown()` on it directly (see the test file's inline comment).

**Step 4 — anti-drift guards** (`tests/engine/test_hard_law_monitor.py`): all 4 specified guard tests
added; `test_hard_law_monitor_individual_laws` and `test_hard_law_occupancy_collision` re-run
unmodified and pass.

**Step 5 — `docs/observability/hard_law_monitor.md`**: added the `LAW-SPAWN-OCCUPANCY` row (matching
the existing 6 rows' shape) and updated the "six authoritative laws" intro to "seven"; corrected the
`LONG_RUN` description from the inaccurate "Operates similarly to `LIGHT` mode" to the real
fall-through behavior (persists + routes, but neither logs nor raises), noting it applies to all 7
laws. `LONG_RUN` *behavior* itself was not touched — doc-accuracy fix only, per the plan.

**Step 6 — `docs/parity_ledger/world_dynamics.yaml`**: added `WORLD-112` (new, `status: verified`,
`priority: P1`, `test_path` → the Step 2 regression test); `WORLD-076` flipped `verified` → `divergent`
with a `divergence_note` citing the regression test and the wider seed-137/999-are-not-clean finding
above (`v2_evidence` text left untouched, per the `INFRA-270` lineage convention cited in the plan);
`WORLD-075` `test_path` strengthened to point at the Step 1 WALL-terrain test, `status` left
`verified`. Verified YAML parses and the 3 touched/new entries pass `docs/parity_ledger/schema.json`
individually (the file as a whole has one pre-existing, unrelated schema violation — `WORLD-CULT-003`'s
non-conforming `id` pattern — not touched by this ticket).

**Step 7 — full regression-surface verification**: all 7 scoped pytest commands from `test_plan.md`
run. 3 pre-existing failures found, none caused by this ticket's change — each independently
reproduced identically on the unmodified base branch via `git stash`:
`tests/integration/kernel/test_long_run_determinism.py::test_1000_tick_determinism` (wall-clock
timeout under this machine's tick-budget watchdog during a 1000-tick run — persistence-phase
slowness, unrelated to `Kernel.__init__`), `tests/integration/observability/test_export_flow.py`'s 2
Parquet-export tests (missing optional `pyarrow` dependency in this environment), and
`tests/perf/test_hard_law_monitor_overhead.py::test_hard_law_monitor_overhead` (pre-existing ~33-34%
relative-overhead perf-noise failure on this machine against a 5% threshold, identical on base branch
— my check runs once at `Kernel()` construction, not per-tick, so it cannot be the cause of a
per-tick-loop overhead regression). See exact commands/output in the implementer's session; all
`HardLawMonitor`/kernel-init/worldbuilding-compiler/observability-init-check tests pass.

## Test Summary
- `tests/engine/test_hard_law_monitor.py`: 12/12 passed (3 pre-existing + 9 new: 3 unit, regression,
  negative control, 4 anti-drift guards).
- `tests/integration/observability/test_initial_placement_check.py` (new file): 2/2 passed.
- `tests/integration/kernel/`: 93 passed, 1 pre-existing failure (unrelated, confirmed on base branch).
- `tests/integration/observability/`: 94 passed, 3 skipped, 2 pre-existing failures (unrelated,
  confirmed on base branch — missing `pyarrow`).
- `tests/unit/optimization/test_world_index_service.py`: 6/6 passed.
- `tests/unit/worldbuilding/`: 114/114 passed.
- `tests/perf/test_hard_law_monitor_overhead.py`: 1 pre-existing failure (unrelated, confirmed on base
  branch).
- `tests/engine/test_hard_law_monitor.py -m regression`: 1/1 passed.
- Zero collateral regression: every failure above independently reproduced on the unmodified base
  branch via `git stash`.

## Files Changed
- `src/observability/hard_law_monitor.py` — added `HardLawMonitor.check_initial_placement(state)`.
- `src/engine/kernel.py` — added `Kernel._run_initial_placement_check()`; added its call site as the
  last statement in `__init__`.
- `tests/engine/test_hard_law_monitor.py` — added 9 tests (3 unit, regression, negative control, 4
  anti-drift guards); added `BuildingState`/`ResourceNodeState`/`inspect` imports.
- `tests/integration/observability/test_initial_placement_check.py` — new file, 2 integration tests.
- `docs/observability/hard_law_monitor.md` — added `LAW-SPAWN-OCCUPANCY` row; corrected `LONG_RUN`
  mode description.
- `docs/parity_ledger/world_dynamics.yaml` — added `WORLD-112`; updated `WORLD-075`/`WORLD-076`.
- `staging_artifacts/TCK-20260716-PLACELEGAL-HARDLAW/plan.md` — added Revision 2 Deviations entry.
- `tickets/inprogress/TCK-20260716-PLACELEGAL-HARDLAW.md` — this file.

## Completion Summary
Added the 7th `HardLawMonitor` law, `LAW-SPAWN-OCCUPANCY`: an unconditional full-population
placement-legality scan (entities + buildings + resource nodes) run once at `Kernel.__init__`,
reusing `LegalityServiceV2.verify_occupancy()`'s existing 5-part occupancy rule for entities/resource
nodes plus a self-reference-safe multi-occupant tile scan that also covers buildings. Closes the gap
where `WorldCompiler.compile()` never validated spawn placement and the live, `DirtySet`-gated
`LAW-OCCUPANCY-COLLISION` check could never see entities that never moved. Reproduced and regression-
tested the real seed-42 `unit_information_density` entities-6/14 tile-(27,38) collision from a fresh
compile (no dependency on now-deleted `data/runs/` evidence). Mode-gating, persistence, and alert
routing exactly mirror `_run_hard_law_checks()`'s existing template, including its `LONG_RUN`
fall-through gap (deliberately inherited, not fixed, per the plan's Resolved Decision 2). Discovered
during implementation that the placement-collision problem is substantially more widespread across
the world corpus than previously documented (17/18 worlds show a violation at seed 137) — flagged in
Implementation Notes and in `WORLD-076`'s new `divergent` status/`divergence_note`, but root-causing
it remains out of this ticket's scope. All 7 steps from the plan completed; all Acceptance Criteria
satisfied; zero collateral regression across the full scoped regression surface (all 3 observed test
failures independently confirmed pre-existing on the unmodified base branch).
