---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260904-FACTION-EXPAND-DIRECTIVE
artifact_type: plan
tags: [faction, grand-strategy]
---

# Implementation Plan — TCK-20260904-FACTION-EXPAND-DIRECTIVE

## Summary

Add a 4th faction directive kind, `EXPAND_TERRITORY`, to `FactionDecisionPhase.execute()`
(`src/engine/faction_decision.py:121-169`), gated purely on a population-pressure signal computed
from `src/domains/demographics/cohort.py`'s `compute_population_density`/`compute_regional_scarcity`
over each faction's `fs.territory` regions, with the target resolved deterministically to a
faction-less region (`RegionState.owner_faction_id is None`, sorted by region id). The directive
stays transient scratch per FAC-003 — no new `StateUpdate`/`AuthoritativeState` field. Thread the
directive list one hop further than any existing directive kind ever has: `pipeline.py`'s
`faction_directives` local (already computed at line 230, previously unconsumed downstream) is
passed into `WorldDynamicsSystem.resolve_dynamics()` (new trailing optional param) which passes it
into `CampService.process_camps()` (new trailing optional param), where a new branch reads any
`EXPAND_TERRITORY` directive whose `target_region` matches a camp's region and applies a maturity
boost to that camp. Both new params are backward-compatible trailing optionals defaulting to `None`,
verified against every real call site enumerated in Steps 4 and 6 — 16 `resolve_dynamics()` call sites
(1 production + 15 test) and 17 `process_camps()` call sites (1 production + 16 test), re-confirmed by
direct grep, none of which pass a 4th (`resolve_dynamics`) or 3rd (`process_camps`) positional
argument today. The
material-possession predicate (`recipe_materials()`) is deliberately NOT consulted anywhere in this
plan — population-pressure alone is the hard gate, per the investigation's confirmed near-inertness
finding. Camp/Nest-as-target and City-ownership resolution are explicitly out of scope and untouched.
This is the 6th and final ticket in the m4-place-material-expansion batch.

## Steps

### Step 1 — Add the `EXPAND_TERRITORY` constant

**Files:** `src/engine/faction_constants.py`

**Change:** Add `EXPAND_TERRITORY = "EXPAND_TERRITORY"` as a 4th module-level string constant,
directly below `COMMISSION_QUEST = "COMMISSION_QUEST"` (currently the last line,
`faction_constants.py:10`). Matches the exact existing pattern — plain string constants, no enum,
same file docstring rationale ("avoid circular imports with scoring.py").

**Do NOT touch:** `DEFEND_BORDER`, `TRADE_ROUTE`, `COMMISSION_QUEST` values or the file's docstring
beyond what's needed to list the new constant if the docstring enumerates them (it currently does
not — `faction_constants.py:1-6` is generic, no per-constant listing, so no docstring edit is
required).

**Verify:** `test_faction_constants_expand_territory_value` (test_plan.md item 6).

---

### Step 2 — Add the population-pressure gate helper and the `EXPAND_TERRITORY` branch in `FactionDecisionPhase.execute()`

**Files:** `src/engine/faction_decision.py`

**Change:**
- Import `EXPAND_TERRITORY` alongside the existing import at `faction_decision.py:29`:
  `from src.engine.faction_constants import DEFEND_BORDER, TRADE_ROUTE, COMMISSION_QUEST, EXPAND_TERRITORY`.
- Import `compute_population_density` and `compute_regional_scarcity` from
  `src.domains.demographics.cohort` (module-level import, matching the existing pattern of importing
  `FactionUpdate`/`DiplomaticState` at module scope in this file — `faction_decision.py:31-32`; these
  two cohort functions are pure and side-effect-free per `cohort.py:122` and `:153`, so a module-level
  import introduces no new coupling risk beyond the existing `world_emergence`/`updates`/`enums`
  imports already at the top of this file).
- **Population-pressure gate definition** (design decision, per investigation Risk #1): a faction is
  "under population pressure" when the **mean of `compute_regional_scarcity(region_id, state)` over
  `fs.territory`** exceeds `0.7` — reusing the existing `migration_threshold` default already used
  elsewhere in `cohort.py` (confirmed as the pattern `PopulationCohort.migration_threshold` defaults
  to in `_check_migration`, `cohort.py:256`, and directly precedented by
  `src/world/reproduction_humanoid.py:71` and `src/world/camp.py:114-116`, both of which compare a
  single `compute_regional_scarcity(...)` value against a `0.7`-shaped threshold). Mean (not max) is
  chosen because `DEFEND_BORDER`/`TRADE_ROUTE` gates already read faction-aggregate fields
  (`fs.tension_level`, `fs.military_strength`) rather than any single region's value — a mean over
  territory keeps `EXPAND_TERRITORY`'s gate philosophically consistent with "is the faction as a whole
  under pressure," not "does the faction have one crisis region." A faction with empty `fs.territory`
  cannot be under pressure (empty mean is undefined) — treat as not-pressured, matching `DEFEND_BORDER`
  and `COMMISSION_QUEST`'s existing `len(fs.territory) > 0` precondition style.
  - `compute_population_density` is read too (per the ticket's AC requiring "A population-pressure/
    cohort signal from `cohort.py`" — plural signal, not scarcity alone) but only as a **secondary,
    non-blocking condition ORed in for future extensibility is explicitly rejected** — instead, per
    the investigation's instruction to "pick and justify" a single concrete rule: use
    `compute_regional_scarcity` as the sole numeric gate (directly precedented, unlike
    `compute_population_density` which the investigation confirms has **zero** existing faction/
    region-pressure-gate precedent — its only consumer is the unrelated `RegionalPressureModel`,
    `cohort.py:134`, `world_emergence/models.py:109`). To still satisfy the AC's plural "signal"
    framing without inventing an unprecedented density threshold, `compute_population_density` is
    read and attached as `priority` scaling only (see below) — informational, never gating.
- **New branch**, added as a 3rd `if` block after the existing `COMMISSION_QUEST` unconditional block
  (`faction_decision.py:158-167`), inside the same `for faction_id, fs in state.factions.items():`
  loop:
  ```python
  # --- EXPAND_TERRITORY: population-pressure-gated territorial expansion ---
  if fs.territory:
      mean_scarcity = sum(
          compute_regional_scarcity(rid, state) for rid in fs.territory
      ) / len(fs.territory)
      if mean_scarcity > 0.7:
          target = _resolve_expand_territory_target(state, fs)
          if target is not None:
              mean_density = sum(
                  compute_population_density(state.regions[rid])
                  for rid in fs.territory if rid in state.regions
              ) / len(fs.territory)
              directives.append(
                  FactionDirective(
                      faction_id=faction_id,
                      directive_kind=EXPAND_TERRITORY,
                      target_region=target,
                      priority=min(1.0, mean_scarcity + mean_density * 0.1),
                      created_tick=state.tick,
                  )
              )
  ```
  This block is independent of (not `elif`-chained to) the `DEFEND_BORDER`/`TRADE_ROUTE` pair and the
  `COMMISSION_QUEST` block — per test_plan.md's "Mutual-exclusivity non-interference guard," a faction
  qualifying for both `DEFEND_BORDER`/`TRADE_ROUTE` and `EXPAND_TERRITORY` must emit both, which this
  structure (a 3rd independent `if`, same as `COMMISSION_QUEST` already is relative to the first pair)
  satisfies without any new exclusivity logic.
- **New private staticmethod** `_resolve_expand_territory_target(state, fs) -> Optional[str]` on
  `FactionDecisionPhase`, placed directly below `execute()`:
  ```python
  @staticmethod
  def _resolve_expand_territory_target(state: AuthoritativeState, fs: FactionState) -> Optional[str]:
      """Deterministically pick the lowest-id faction-less region not already in fs.territory."""
      candidates = sorted(
          rid for rid, region in state.regions.items()
          if region.owner_faction_id is None and rid not in fs.territory
      )
      return candidates[0] if candidates else None
  ```
  `region.owner_faction_id is None` is the exact field/semantics confirmed at
  `src/core/state.py:273` (`Optional[int]`, "Faction that currently controls the region"). The
  `rid not in fs.territory` defensive check directly addresses investigation Risk #4 (the documented
  `owner_faction_id`/`FactionState.territory` divergence) — even though no current code path can cause
  a region to be simultaneously `owner_faction_id is None` and present in some faction's `territory`
  tuple, this check is cheap and closes the gap defensively per the investigation's suggestion.
  Sorting `state.regions.items()` by `rid` before selection (via `sorted(...)` over the generator, then
  indexing `[0]`) matches the exact determinism idiom `find_adjacent_regions` uses (`cohort.py:202`,
  `sorted(state.regions.items())`) — required because `state.regions` is a plain `Dict[str,
  RegionState]` with no iteration-order guarantee across runs (test_plan.md item 4, determinism guard).
- Add `Optional` to the existing `from typing import TYPE_CHECKING, Optional, Sequence` import if not
  already present (it already is, per `faction_decision.py:21`) — no import change needed there.
- Update the class docstring's "Decision rules" list (`faction_decision.py:112-118`) to add a 4th
  bullet documenting `EXPAND_TERRITORY`'s rule in the same style as the other three.

**Do NOT touch:** the `DEFEND_BORDER`/`TRADE_ROUTE`/`COMMISSION_QUEST` branches' own conditions,
ordering, or `priority`/`created_tick` computation (`faction_decision.py:139-167`) — these must fire
identically before and after this change (test_plan.md's regression-surface requirement that the 11
existing tests in `test_faction_decision_phase.py` must not regress). Do not consult
`recipe_materials()` anywhere in this branch (see Anti-Drift Notes). Do not add Camp/Nest or
City-ownership-aware logic to `_resolve_expand_territory_target`.

**Verify:**
- `test_faction_decision_phase_expand_territory_emitted_under_population_pressure`
- `test_faction_decision_phase_expand_territory_not_emitted_without_pressure`
- `test_faction_decision_phase_expand_territory_not_emitted_without_target`
- `test_faction_decision_phase_expand_territory_target_resolution_deterministic`
- Mutual-exclusivity non-interference guard (extends
  `test_faction_decision_phase_high_tension_emits_defend_and_commission`-style coverage)
- All 11 pre-existing tests in `tests/unit/domains/faction/test_faction_decision_phase.py` unchanged.

---

### Step 3 — Transient-scratch anti-drift guard extension

**Files:** `tests/unit/domains/faction/test_faction_decision_phase.py`

**Change:** Extend (not replace) the existing `test_faction_directive_not_in_state_update` and
`test_faction_decision_phase_returns_list_not_state_update` tests, or add a sibling test
`test_faction_decision_phase_expand_territory_transient_not_persisted`, asserting: (a)
`not hasattr(StateUpdate, "faction_directives")` and no attribute on `StateUpdate` named anything
`expand`/`territory`-related (grep `StateUpdate`'s dataclass fields, confirmed shape at
`src/core/updates.py` — this step does not modify `StateUpdate` itself, only asserts against it); (b)
constructing a state with a faction under population pressure, calling `execute()`, and asserting the
returned value is `list[FactionDirective]` whose `EXPAND_TERRITORY` entries are never merged into any
`StateUpdate`/`AuthoritativeState` object anywhere in the test's own call sequence. This is a test-only
step — no production code changes.

**Do NOT touch:** `src/core/updates.py` (`StateUpdate` dataclass) — this step proves no field was
added there, it does not add one.

**Verify:** `test_faction_decision_phase_expand_territory_transient_not_persisted` (test_plan.md item 5).

---

### Step 4 — Add `faction_directives` trailing optional param to `WorldDynamicsSystem.resolve_dynamics()`

**Files:** `src/engine/world_dynamics.py`

**Change:** Change the signature at `world_dynamics.py:23` from:
```python
def resolve_dynamics(state: AuthoritativeState, update: StateUpdate, generator: EntityGenerator, cadence: SystemCadence | None = None) -> StateUpdate:
```
to:
```python
def resolve_dynamics(state: AuthoritativeState, update: StateUpdate, generator: EntityGenerator, cadence: SystemCadence | None = None, faction_directives: list | None = None) -> StateUpdate:
```
Then at the existing `CampService.process_camps(state, generator)` call site
(`world_dynamics.py:175`, inside the `if should_run(state.tick, None, cadence.world_dynamics):` block
starting at line 131), change it to:
```python
camp_state_update = CampService.process_camps(state, generator, faction_directives=faction_directives)
```

**Every other writer/caller of `resolve_dynamics()` — independently re-verified by direct grep
(`grep -n "resolve_dynamics(" <file>`) against every candidate file, not merely re-stated from the
investigation, since a prior draft of this enumeration under-counted and mischaracterized several of
these call sites. 16 total call sites (1 production + 15 test), none of which pass a 5th positional
argument today, so this trailing-optional addition is additive and non-breaking for every one of
them, regardless of whether each existing call passes `cadence` positionally, as a keyword, or omits
it entirely:**
1. `src/engine/pipeline.py:343` — the sole production call site
   (`WorldDynamicsSystem.resolve_dynamics(state, u, generator, cadence=cadence)`, `cadence=` keyword),
   updated in Step 5 below to also pass `faction_directives=faction_directives`.
2. `tests/unit/world/test_world_dynamics.py` — **5** call sites (lines 15, 37, 58, 68, 419), not 4.
   Lines 15, 37, 58, 68 pass only `(state, update, generator)` — 3 bare positional args, no `cadence`
   argument at all. Line 419 passes `(state, StateUpdate(), generator, cadence)` — `cadence` as a 4th
   **positional** argument, not a `cadence=` keyword. All 5 are unaffected by a new 5th trailing
   optional param.
3. `tests/unit/world/test_sovereignty_events.py` — 1 call site (line 44),
   `resolve_dynamics(state, update, _FakeGen(), cadence=cadence)`, `cadence=` keyword; unaffected.
4. `tests/unit/world/test_creature_territory_lifecycle.py` — 4 call sites (lines 106, 127, 130, 176),
   all `cadence=SystemCadence(...)` keyword; unaffected.
5. `tests/unit/world/test_reproduction_humanoid_cadence.py` — 2 call sites (lines 263, 308), both
   `resolve_dynamics(state, StateUpdate(), generator, cadence)` — `cadence` as a 4th positional
   argument, not a keyword; unaffected.
6. `tests/integration/world/test_phase9_stability.py` — 1 call site (line 36),
   `resolve_dynamics(state, StateUpdate(), generator)` — 3 bare positional args, no `cadence`;
   unaffected.
7. `tests/integration/scenarios/test_demographics.py` — 1 call site (line 333),
   `resolve_dynamics(state, StateUpdate(), generator, cadence)` — `cadence` as a 4th positional
   argument. **This file was entirely omitted from the original enumeration**; it is unaffected by
   the same reasoning as the others.
8. `tests/unit/world/test_camp_lifecycle.py` — 1 call site (line 24),
   `resolve_dynamics(state, StateUpdate(), generator, cadence=SystemCadence(world_dynamics=30))` —
   `cadence=` keyword. **This call site was omitted from the resolve_dynamics() enumeration in an
   earlier revision** (the file was enumerated for `process_camps()` in Step 6 but not cross-checked
   for `resolve_dynamics()` too); it is unaffected by the same reasoning as the others.

No ordering/race concern: `resolve_dynamics()` is called once per tick from a single-threaded
`refine()` call (confirmed by the kernel's deterministic single-phase-at-a-time execution per
`docs/engine/kernel.md`), so there is no concurrent-write hazard introduced by adding this parameter
— it is a plain function argument, not a shared mutable resource.

**Do NOT touch:** the `state, update, generator, cadence` parameter order or any other line inside
`resolve_dynamics()` besides the signature and the one `process_camps(...)` call site.

**Verify:** `tests/unit/world/test_world_dynamics.py` (all 5 existing call sites unchanged behavior)
and `tests/integration/scenarios/test_demographics.py` (its 1 existing call site unchanged behavior)
plus new `test_resolve_dynamics_threads_faction_directives_to_camp_service` (test_plan.md item 10).

---

### Step 5 — Thread `faction_directives` from `pipeline.py` into `resolve_dynamics()`

**Files:** `src/engine/pipeline.py`

**Change:** At `pipeline.py:343`, the existing call:
```python
update = run_phase("world_dynamics", update, lambda u: WorldDynamicsSystem.resolve_dynamics(state, u, generator, cadence=cadence))
```
becomes:
```python
update = run_phase("world_dynamics", update, lambda u: WorldDynamicsSystem.resolve_dynamics(state, u, generator, cadence=cadence, faction_directives=faction_directives))
```
The `faction_directives` local is already computed at `pipeline.py:230`
(`faction_directives: list = FactionDecisionPhase.execute(state, policy=None)`) and is already in
lexical scope at line 343 (both are local variables inside the same `refine()` method body, with
`faction_decision` phase 8b confirmed to run strictly before `world_dynamics` at line 343 in the same
call — no cross-tick or cross-call staleness risk, since `faction_directives` is freshly recomputed
every tick at line 230 and consumed once, same tick, at line 343).

**Every other reader of the `faction_directives` local, enumerated (confirmed via investigation) —
none are affected by this addition, since this step only adds a new consumer, it does not change what
`faction_directives` contains or remove any existing read:**
1. The (disclosed-dead per STRAT-252) `AdventureRouteScorer` urgency-table path — not actually reached
   via this local at all per the investigation (`AdventureGoalScorer` calls
   `AdventureDecisionService.decide()` with `faction_directives=None` unconditionally); unaffected.
2. No other line in `pipeline.py` reads `faction_directives` today (confirmed by investigation: "not
   currently threaded to any other phase").

**Do NOT touch:** any other `run_phase(...)` call in `refine()`, the phase ordering, or the
`faction_decision`/`faction_awareness` blocks (`pipeline.py:226-242`) beyond what Step 2 requires
inside `faction_decision.py` itself (nothing in `pipeline.py`'s faction_decision block needs to
change — it already assigns `faction_directives` correctly for the new directive kind, since
`FactionDecisionPhase.execute()`'s return type doesn't change).

**Verify:** `tests/integration/scenarios/test_faction_campaign.py`,
`tests/integration/world/test_phase9_stability.py` (full `refine()` call still succeeds with the new
argument threaded through).

---

### Step 6 — Add `faction_directives` trailing optional param and consumption branch to `CampService.process_camps()`

**Files:** `src/world/camp.py`

**Change:** Change the signature at `camp.py:23` from:
```python
def process_camps(state: AuthoritativeState, generator: EntityGenerator) -> StateUpdate:
```
to:
```python
def process_camps(state: AuthoritativeState, generator: EntityGenerator, faction_directives: list | None = None) -> StateUpdate:
```
Add a new step inside the existing `for c_id, camp in state.camps.items():` loop
(`camp.py:33-136`), after step "1. Maturity Evolution" (`camp.py:37-45`) and before step
"2. Camp-based Spawning" (`camp.py:47`), reading the camp's own region (already resolved at
`camp.py:41`, `region = LegalityServiceV2.get_region_for_position(camp.position, state)`, reused —
not re-fetched):
```python
# 1b. Faction EXPAND_TERRITORY consumption: a matching directive boosts maturity growth.
if faction_directives and region is not None:
    from src.engine.faction_constants import EXPAND_TERRITORY
    for directive in faction_directives:
        if getattr(directive, "directive_kind", None) == EXPAND_TERRITORY and directive.target_region == region.id:
            existing = camp_updates[c_id]
            camp_updates[c_id] = replace(existing, maturity_delta=existing.maturity_delta + 1.0)
            break
```
This requires importing `replace` from `dataclasses` at the top of `camp.py` (not currently imported
— confirmed via `camp.py:1-6`, only `TYPE_CHECKING, Dict, List` and `StateUpdate, CampUpdate,
WorldUpdate` are imported today; add `from dataclasses import replace`). The `+1.0` maturity boost
value is a deliberately small, explicit constant (documented inline as
`EXPAND_TERRITORY_MATURITY_BOOST = 1.0`, added as a class constant alongside `MATURITY_PER_TICK =
0.05` at `camp.py:17`, and referenced instead of the literal `1.0` in the branch above) — chosen to be
clearly observable in a unit test (20x `MATURITY_PER_TICK`) without materially destabilizing the
existing `RAID_MATURITY_THRESHOLD = 80.0` cadence in any currently-compiled real world (moot in
practice per below, since `state.camps` is `{}` everywhere real today).

**Every other writer to `state.camps`/`camp_updates` inside this same function, enumerated, and how
this branch interacts with each:**
1. Step "1. Maturity Evolution" (`camp.py:37-45`) — writes `camp_updates[c_id] = CampUpdate(id=c_id,
   maturity_delta=m_delta)` unconditionally for every active camp, immediately before this new step
   runs. This new step reads that same `camp_updates[c_id]` entry and `replace()`s it with an
   incremented `maturity_delta`, additively — it does not overwrite the trauma-scaled `m_delta` computed
   there, matching the additive-merge discipline the file already uses elsewhere (e.g. the natural-
   creature-reproduction nudge at `camp.py:131-135` explicitly merges rather than overwrites for the
   same additive-safety reason).
2. Step "3. Raid Trigger / Nest Spread" (`camp.py:67-104`) — conditionally overwrites
   `camp_updates[c_id] = CampUpdate(id=c_id, maturity_delta=-20.0, last_raid_tick_set=...)` later in
   the same loop iteration, **replacing** (not merging) the earlier entry. This is pre-existing
   behavior this ticket does not change — the new EXPAND_TERRITORY boost from step 1b, if applied,
   is silently discarded by this later unconditional overwrite in the same tick a raid/spread also
   triggers. This is an accepted, pre-existing interaction pattern (step 3 already discards step 1's
   maturity_delta the same way whenever it fires) — not a new hazard introduced by this ticket, so no
   additional guard is added for it; documented here for the implementer's awareness only.
3. Step "4. Natural-Creature Reproduction" (`camp.py:106-136`) — writes to `world_updates`, not
   `camp_updates`; no interaction.
4. No other function in the codebase writes to `camp_updates` inside `process_camps()` — this is a
   single-function-scoped local dict, not a shared registry; the only shared resource is `state.camps`
   itself (read-only in this function) and the returned `StateUpdate.camp_updates`, applied
   authoritatively downstream by the apply-path (outside this function's or this ticket's scope).

**Backward compatibility:** `faction_directives` defaults to `None`; the `if faction_directives and
region is not None:` guard short-circuits to a no-op when the caller passes nothing (or an empty
list), so `process_camps(state, generator)` (the pre-existing 2-positional-arg call shape) behaves
byte-identically to before this ticket.

**Every caller of `process_camps()` in the codebase — independently re-verified by direct grep
(`grep -rn "process_camps(" --include="*.py" .`), not merely re-stated from the investigation, since
a prior draft of this enumeration omitted an entire file with 9 call sites. 17 total call sites (1
production + 16 test), all passing exactly `(state, generator)` — the pre-existing 2-positional-arg
shape — so all are unaffected by the new 3rd trailing optional param:**
1. `src/engine/world_dynamics.py:175` — the sole production call site (updated in Step 4 to pass
   `faction_directives=faction_directives`).
2. `tests/unit/world/test_camp_lifecycle.py` — 7 call sites (lines 64, 98, 117, 136, 159, 251, 286);
   unaffected.
3. `tests/unit/world/test_natural_creature_reproduction.py` — 9 call sites (lines 47, 100, 118, 135,
   152, 172, 198, 224, 257). **This file was entirely omitted from the original enumeration**, which
   incorrectly stated `test_camp_lifecycle.py` was the only test file with direct call sites. This
   file's 9 calls sit inside the same `for c_id, camp in state.camps.items():` loop
   (`test_natural_creature_reproduction.py`'s own test bodies construct `state.camps` directly, same
   pattern as `test_camp_lifecycle.py`) that Step 6's new branch is added to — all 9 are unaffected by
   the new optional param, but must be included in this ticket's regression run since they exercise
   the exact loop this step modifies (see test_plan.md's Regression Surface, updated accordingly).

**Real-content reachability note (per investigation, must be disclosed, not silently assumed away):**
`state.camps` is `{}` in every currently-compiled real world (zero world YAML files set
`creature_kind`, confirmed by investigation's `grep -rn "creature_kind" data/worlds/` — no matches),
so this consumption branch is real, tested via direct unit-test construction of a non-empty
`state.camps` dict (matching `test_camp_lifecycle.py`'s existing testing pattern), but has **zero
observable effect in any real compiled world today** — structurally identical to the "wired but inert
against real content" outcome `TCK-20260904-CAMPSTATE-PLACE-BRIDGE` already disclosed for its own
bridge work. This is not a defect; it is the correct, honest scope for this ticket given the current
content-authoring gap.

**Feature-flag decision:** unflagged, matching the existing unconditional style of
`DEFEND_BORDER`/`TRADE_ROUTE`/`COMMISSION_QUEST` (no flag) and `CampService.process_camps()` itself
(also unconditional). Per investigation Risk #3, this carries zero real-world behavioral risk today
since `state.camps` is `{}` everywhere real; if real content ever starts setting `creature_kind`, this
becomes live gameplay behavior with no flag fallback — that tradeoff is accepted here consistently
with how the sibling `CAMPSTATE-PLACE-BRIDGE` ticket treated the same situation, not silently
defaulted.

**Do NOT touch:** `state.camps` construction, `CampState`, `NEST_RACE_KINDS`, `ENABLE_CAMP_NEST_SPREAD`
flag logic, `resolve_camp_clearing()` (camp.py:139-161), or any code in
`src/worldbuilding/compiler.py`. Do not add a `camps_add`-shaped field to `StateUpdate`/`CampUpdate`
— this branch only mutates existing camps' `maturity_delta`, never constructs a new camp.

**Verify:**
- `test_camp_service_consumes_expand_territory_directive`
- `test_camp_service_ignores_expand_territory_directive_for_other_region`
- `test_camp_service_process_camps_backward_compatible_no_directives`
- All existing `test_camp_lifecycle.py` tests (`test_camp_maturity_and_spawn`,
  `test_camp_clearing_reward`, etc.) unchanged.
- All existing `tests/unit/world/test_natural_creature_reproduction.py` tests (14 tests, e.g.
  `test_camp_maturity_threshold_spawns_natural_creature_offspring`,
  `test_two_simultaneous_births_same_region_same_call_both_nudge`) unchanged — required because these
  tests' 9 `process_camps()` calls exercise the same `state.camps.items()` loop this step's new branch
  is added to.

---

### Step 7 — Update `docs/parity_ledger/faction.yaml` FAC-003

**Files:** `docs/parity_ledger/faction.yaml`

**Change:** Update the FAC-003 entry (`faction.yaml:34-49`) `text` field to read: "FactionDecisionPhase
reads state.factions each decision tick and emits transient FactionDirective list (DEFEND_BORDER,
TRADE_ROUTE, COMMISSION_QUEST, EXPAND_TERRITORY); directives are not persisted in
AuthoritativeState. EXPAND_TERRITORY is additionally threaded through
WorldDynamicsSystem.resolve_dynamics() into CampService.process_camps() as a transient,
non-persisted consumption input." Update `v2_evidence` to append
`+ src/domains/demographics/cohort.py (population-pressure gate) + src/engine/world_dynamics.py +
src/world/camp.py (EXPAND_TERRITORY consumption, TCK-20260904-FACTION-EXPAND-DIRECTIVE)`. Keep
`status: verified`, `priority: P2` unchanged. `test_path` stays
`tests/unit/domains/faction/test_faction_decision_phase.py` (already correct per the ticket's own
scope line) — do not add a second `test_path` field (schema is single-valued per
`docs/parity_ledger/schema.json`); the new `CampService`-side tests live in
`tests/unit/world/test_camp_lifecycle.py` and `test_world_dynamics.py` but are cross-referenced in
`text`/`v2_evidence` rather than in `test_path`, consistent with FAC-003 being scoped to the
`FactionDecisionPhase` emission side specifically. Use `tools/parity_ledger_writer.py` (per CLAUDE.md's
"big diff via the sanctioned writer is safe; via raw Edit is real corruption risk") rather than hand-
editing the YAML.

**Do NOT touch:** any other entry in `faction.yaml`, or any entry in `strategic_cognition.yaml`
(FACTION-DIR-001/STRAT-252) or `world_dynamics.yaml` (WORLD-109/WORLD-124) — investigation confirmed
both are conceptually adjacent but out of this ticket's update scope (STRAT-252's dead-path text
remains accurate; WORLD-109/WORLD-124 describe camp *construction*, not consumption, and are
unaffected).

**Verify:** `docs/parity_ledger/faction.yaml` FAC-003 `text`/`v2_evidence` reflect the 4th directive
kind (AC #6, direct text match).

---

### Step 8 — Update `docs/systems/faction_contract.md`

**Files:** `docs/systems/faction_contract.md`

**Change:**
- In the "FactionDirective Schema" section (`faction_contract.md:78-85`), update the
  `directive_kind: str — one of: DEFEND_BORDER | TRADE_ROUTE | COMMISSION_QUEST` line (line 85) to
  add `| EXPAND_TERRITORY`.
- In the "Directive Kinds" table (`faction_contract.md:94-105`), add a 4th row:
  `| `EXPAND_TERRITORY` | `"EXPAND_TERRITORY"` | mean `compute_regional_scarcity` over `fs.territory` >
  0.7 AND a faction-less region exists |`, and a note below the existing "mutually exclusive"/
  "always emitted" sentences (lines 104-105) stating `EXPAND_TERRITORY` is independent of (not
  mutually exclusive with) the other three.
- In the "Pipeline Position" section (`faction_contract.md:155`+), add a sentence noting
  `faction_directives` (including `EXPAND_TERRITORY`) is now additionally threaded into
  `WorldDynamicsSystem.resolve_dynamics()` → `CampService.process_camps()` at the `world_dynamics`
  phase, same-tick, in addition to its existing (disclosed-dead) urgency-scoring consumption.

**Do NOT touch:** the `GUARD`/`HERO` behavior-tree consumption table (`faction_contract.md:142-144`)
— this ticket does not add an `EXPAND_TERRITORY`-triggered behavior-tree entry (out of this ticket's
AC scope; only `CampService` consumption is required).

**Verify:** Doc review only (no automated test) — cross-checked manually against Step 2/6's actual
code.

---

### Step 9 — Update `docs/world/raid_boss_camp_contract.md`

**Files:** `docs/world/raid_boss_camp_contract.md`

**Change:** In the "## Camp — `camp.py`" section (`raid_boss_camp_contract.md:22`+), add a new
subsection (following the precedent of the existing Camp/Nest classification and Nest-spread
subsections already in this section for the two sibling tickets) describing the new
`faction_directives`-consuming branch: what triggers it (an `EXPAND_TERRITORY` directive whose
`target_region` matches the camp's region), its effect (`+1.0` maturity_delta boost via
`EXPAND_TERRITORY_MATURITY_BOOST`), its interaction with the raid-trigger overwrite (Step 6's
"Every other writer" note #2 — the boost is discarded in the same tick a raid/spread also fires), and
the current real-content-inert status (zero `creature_kind`-bearing world files today).

**Do NOT touch:** the Raid/Boss sections of this doc, or the Camp/Nest classification table itself —
this ticket only adds a new input to `process_camps()`, it does not change classification or raid
logic.

**Verify:** Doc review only, cross-checked against Step 6's actual code.

---

## Scope Guards

- No Camp/Nest-as-conquest-target logic in `_resolve_expand_territory_target` or anywhere in target
  resolution — confirmed by investigation that real content still cannot exercise it (zero
  `creature_kind`-bearing world files), even though the underlying `CampState`-construction mechanism
  now technically exists via the two now-landed sibling tickets.
- No City-ownership-aware resolution (idea 35) anywhere in this ticket — idea 35 remains design-only,
  no implementation ticket exists yet.
- No new `camps_add`-shaped field on `StateUpdate`/`CampUpdate` — `CampService` has no camp-
  construction mechanism today and this ticket does not add one; the `EXPAND_TERRITORY` consumption
  branch only mutates `maturity_delta` on existing camps.
- No persistence of `EXPAND_TERRITORY` (or any derived field) into `AuthoritativeState` or
  `StateUpdate` — FAC-003's transient-scratch rule, mechanically enforced by the two existing anti-
  drift tests (kept structurally unmodified, coverage only grows).
- No hard-gating (or any gating at all) of `EXPAND_TERRITORY` emission on `recipe_materials()` — see
  Unresolved Questions / Anti-Drift Notes below for the explicit decision and rationale.
- No signature/parameter-order change to `resolve_dynamics()`'s or `process_camps()`'s existing
  positional parameters — `faction_directives` is added strictly as a new trailing optional on both.
- No changes to `src/world/creature_territory.py`, `src/worldbuilding/compiler.py`'s
  `CampState`-construction branch, `NEST_RACE_KINDS`, `ENABLE_CAMP_NEST_SPREAD` flag logic, or the
  Camp/Nest classification table in `docs/mechanics/05_world_evolution.md` §6 — all are the sibling
  tickets' already-closed, unrelated scope.
- No changes to `src/domains/progression/material_predicate.py` or its own tests — this ticket may
  reference it in commentary only (it does not, per the decision below), never modify it.
- No changes to `docs/mechanics/05_world_evolution.md`, `docs/mechanics/04_strategic_cognition.md`
  §6.10, or `docs/audits/D19_domain_phase_inventory.md` — all explicitly excluded per investigation's
  "Docs Requiring Update" section reasoning (directive-kind vocabulary is documented only in
  `faction_contract.md`; §6.10 covers a different, disclosed-dead consumer; audits are cite-only
  point-in-time snapshots per CLAUDE.md and sibling-ticket precedent).
- No changes to `docs/parity_ledger/strategic_cognition.yaml` (FACTION-DIR-001/STRAT-252) or
  `docs/parity_ledger/world_dynamics.yaml` (WORLD-109/WORLD-124) — conceptually adjacent, confirmed
  out of scope by investigation.

## Dependency Map

- Step 1 (constant) has no dependencies — first.
- Step 2 (branch + gate + target resolution) depends on Step 1 (imports the constant).
- Step 3 (transient guard test) depends on Step 2 (needs the branch to exist to test against it).
- Step 4 (`resolve_dynamics` param) has no dependency on Steps 1-3 — can be done in parallel, but
  numbered after them for narrative order.
- Step 5 (`pipeline.py` threading) depends on Step 4 (needs the new `resolve_dynamics()` param to
  exist) and on `faction_directives` already being computed at `pipeline.py:230` (pre-existing, no
  change needed there).
- Step 6 (`CampService` consumption) depends on Step 1 (imports `EXPAND_TERRITORY`) and is consumed
  by Step 4's call-site change (Step 4 passes `faction_directives` through to `process_camps()`, so
  Step 6's new param must exist before Step 4's call-site edit is meaningful — implement Step 6 before
  or alongside Step 4).
- Step 7 (parity ledger) depends on Steps 2 and 6 being complete (documents both the emission and
  consumption sides).
- Steps 8-9 (docs) depend on Steps 2 and 6 being complete (describe the final shipped behavior).

Suggested implementation order: 1 → 2 → 3 → 6 → 4 → 5 → 7 → 8 → 9 (Step 6 before Step 4 so Step 4's
call-site edit at `world_dynamics.py:175` has a real target parameter to pass into).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| EXPAND_TERRITORY added as 4th directive constant + branch in `FactionDecisionPhase.execute()`, matching if/elif structure, same pipeline position | Steps 1, 2 | `test_faction_constants_expand_territory_value`; all 11 existing `test_faction_decision_phase.py` tests unchanged |
| Target resolution uses only `RegionState.owner_faction_id` (faction-less regions), no Camp/Nest or City-ownership logic | Step 2 (`_resolve_expand_territory_target`) | `test_faction_decision_phase_expand_territory_emitted_under_population_pressure`; No-Camp/Nest/City-ownership scope-creep guard |
| Population-pressure/cohort signal from `cohort.py` gates emission, tested trigger + no-trigger | Step 2 | `test_faction_decision_phase_expand_territory_emitted_under_population_pressure`; `test_faction_decision_phase_expand_territory_not_emitted_without_pressure` |
| Directive reaches `CampService` as real, tested 3-phase integration (signal → FactionDecisionPhase → CampService) | Steps 2, 4, 5, 6 | `test_camp_service_consumes_expand_territory_directive`; `test_resolve_dynamics_threads_faction_directives_to_camp_service` |
| EXPAND_TERRITORY proven NOT persisted in `AuthoritativeState`/`StateUpdate` | Step 3 | `test_faction_decision_phase_expand_territory_transient_not_persisted`; existing `test_faction_directive_not_in_state_update` |
| `docs/parity_ledger/faction.yaml` FAC-003 text/v2_evidence/test_path updated | Step 7 | Doc review (direct text comparison against updated FAC-003 entry) |

## Anti-Drift Notes

- **Material-possession predicate: explicit decision — do NOT reference `recipe_materials()` anywhere
  in this ticket's implementation**, not even as a soft/informational signal. The investigation
  confirms it is structurally near-inert against real `known_recipes` (disjoint `craft_*` namespace vs.
  the predicate's 3-entry catalog, zero shared ids) — even a "soft" consultation would either always
  return an empty tuple in production (making the soft signal permanently absent, dead code dressed up
  as a feature) or require special-casing around its known inertness, adding complexity with no real
  behavioral payoff. The ticket's own Assumptions section already frames this as non-blocking; this
  plan resolves it fully rather than leaving a half-consulted predicate in the code. Idea 52's card
  language ("informed by material possession") is satisfied by population-pressure gating alone per
  the investigation's explicit recommendation — this is a documented, deliberate simplification, not
  an oversight.
- **Camp/Nest conquest-target reasoning must be stated as the investigation's re-verified finding, not
  the ticket's original framing**: the `CampState`-construction mechanism now exists (both sibling
  tickets landed), so the blocker is no longer "not yet in code" — it is a pure content-authoring gap
  (zero real world YAML sets `creature_kind`). This distinction matters for anyone reading this plan
  later without re-reading the investigation; Steps 8-9's doc updates should carry this same corrected
  framing forward if they touch this topic at all (they should not need to — Camp/Nest is out of
  scope for target resolution regardless of the reason).
- **`RegionState.owner_faction_id` vs `FactionState.territory` divergence** (FAC-010 known limitation):
  `owner_faction_id` is set only at world-compile time and never kept in sync with
  `FactionState.territory` by the military-conflict/territory-transfer machinery. Step 2's
  `_resolve_expand_territory_target` defensively excludes any region already in `fs.territory` even
  though no current code path can produce that overlap — this is a cheap, explicit hedge against a
  known divergence, not evidence the divergence is expected to occur.
- **CampService consumption is real but currently unreachable in production** — `state.camps` is `{}`
  for every real compiled world today (confirmed via `grep -rn "creature_kind" data/worlds/`, no
  matches). Step 6's branch must still be genuinely correct and tested via direct unit-test
  construction (matching `test_camp_lifecycle.py`'s existing pattern of constructing a non-empty
  `state.camps` dict), not stubbed or skipped — "wired but inert against real content" is an accepted,
  disclosed outcome for this ticket, identical in kind to `CAMPSTATE-PLACE-BRIDGE`'s own disclosed
  outcome, not a shortcut.
- **Determinism**: `_resolve_expand_territory_target` must use `sorted(state.regions.items())`-style
  iteration (never raw `dict.items()` iteration order) when selecting a target among multiple
  faction-less regions — this matches `find_adjacent_regions`'s existing determinism idiom exactly and
  is directly required by test_plan.md item 4. The population-pressure gate computation (`mean_scarcity`,
  `mean_density`) iterates `fs.territory`, which is a `Tuple[str, ...]` (ordered, per
  `src/core/state.py:714`) — not a dict — so no additional sorting is needed there; iterating it in its
  existing tuple order is already deterministic.
- **Batch completion**: this is the 6th and final ticket in the m4-place-material-expansion batch. Once
  this ticket closes, the `tickets/todos/m4-place-material-expansion/` folder (if all its tickets are
  now done) should be moved to `tickets/done/m4-place-material-expansion/` per CLAUDE.md's folder-
  completion convention — this is Finalize's responsibility for this ticket, not something to act on
  during planning or implementation.

## Unresolved Questions

None. All open questions the investigation raised (population-pressure threshold/aggregation,
CampService consumption semantics, feature-flag gating, material-possession predicate usage) have been
resolved explicitly above with rationale, per the investigation's own instruction that these are real
design decisions this plan must make rather than defer.
