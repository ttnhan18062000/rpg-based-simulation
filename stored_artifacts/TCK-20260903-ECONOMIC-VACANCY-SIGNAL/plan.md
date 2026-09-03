---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20260903-ECONOMIC-VACANCY-SIGNAL
artifact_type: plan
tags: [economy, lifecycle]
---

# Implementation Plan — TCK-20260903-ECONOMIC-VACANCY-SIGNAL

## Summary

This plan implements "The Empty Chair" vacancy signal using the real durable/apply-path pattern
confirmed in investigation.md: `StateUpdate.world_events_add` → `AuthoritativeState.recent_world_events`,
capped at the **last 500 `WorldEvent` objects appended anywhere across the whole world (all
categories, all regions combined) — a count-based ring buffer, not a 500-tick time window**
(re-confirmed by direct read, `src/engine/apply.py:335-338`: `WORLD_EVENT_WINDOW = 500`;
`merged_events = prior_events + update.world_events_add`; `new_recent_world_events =
merged_events[-WORLD_EVENT_WINDOW:]` — a plain list-slice on the merged event list, with no
tick-based filtering anywhere in that block), not `EconomyHealthMonitor`'s read-only
`_event_listeners` side-channel. See "Review Revision" below for why this correction matters and
how the plan now handles it. Occupancy is defined per **Option 1** from investigation.md
(region-scoped `EntityRole` uniqueness, reusing `OccupationChangeGoalScorer`'s region-matching scan
pattern) — no new durable schema field is added. The death check is invoked from
`LifecycleSystem.resolve_lifecycle` (PP-33, `src/systems/lifecycle_systems/lifecycle.py`), which I
re-read in its current branch state (lines 40-184, confirmed no role/production logic exists there
yet). Per Review Revision point 3 below, the actual scan/emit logic is **extracted** into a new
`EconomicVacancyService.check_and_emit(state, recent_deaths) -> StateUpdate`
(new file `src/economy/vacancy.py`), mirroring the exact signature shape and call-site pattern of
`FactionInfluenceService.process_influence_shift(state, recent_deaths) -> StateUpdate`
(`src/world/influence.py:31`, confirmed by direct read), which is already called from the same
`if recent_deaths:` aggregate block in `resolve_lifecycle` (lines 160-164) — not inlined inside the
per-entity death loop. The signal is wired to a real consumer at PP-20
(`TownResolutionSystem.resolve`, `src/engine/town_resolution.py`), which reads
`state.recent_world_events` (one-tick-lagged, same law as `FactionAwarenessService`) and reacts via
`StateUpdate.metric_counters` — deliberately **not** by gating `BlacksmithSystem` (PP-07), because I
independently re-verified `TOWN-017` (`docs/parity_ledger/town_resource.yaml:193-201`) is
**`priority: P0`**, not the non-P0 status investigation.md guessed from an excerpt — gating crafting
would put a P0-protected verified entry at risk and drift toward the explicitly out-of-scope
"recovery mechanism" territory. Per the task's point 4, this plan also formally revises the
ticket's AC4 ("measurable production-throughput delta") to "measurable vacancy-detection delta,"
documented below as a deviation, because `BlacksmithSystem.enforce` stays entity-agnostic under
this design and a literal throughput-delta test would pass or fail independently of whether the
vacancy signal is wired at all.

## Review Revision (architecture review, NEEDS_CHANGES → addressed)

The architecture review returned three required fixes against the prior version of this plan. All
three are addressed below; nothing else in the plan changed (the review explicitly approved the
TOWN-017 P0 handling, the AC4 revision, the durable-state/apply-path pattern, `replace()`-based
mutation, and determinism as-is).

1. **`WORLD_EVENT_WINDOW` mischaracterization (blocking).** The prior plan repeatedly called
   `recent_world_events` a "500-tick bounded window." Direct re-read of `src/engine/apply.py:335-338`
   confirms it is a cap on the **last 500 `WorldEvent` objects globally** (every category, every
   region, merged from every phase that writes `world_events_add` in a tick), not a 500-tick clock.
   At least one other confirmed emitter alone can plausibly exhaust much of that budget well inside
   500 ticks in a populated world: `DemographicCycleService.process_demographics`
   (`src/domains/demographics/cohort.py:337-418`) appends one `WorldEvent` per changed cohort
   *bracket* per *region* every `COHORT_INTERVAL = 200` ticks (line 335), plus a further batch from
   its own migration pass (lines 397-406) — a world with, say, 10 regions × 3 brackets each easily
   produces 30+ events every 200 ticks from this one source alone, before counting the
   `contracts`/`blacksmith`, `diplomatic_transitions`, `military_conflict`,
   `interaction_enforcement`, and `town_resolution` phases that also write `world_events_add` every
   tick (enumerated in Step 2 below). **Decision (not left as an open question): keep
   `recent_world_events` as the emission/consumption mechanism (option (a) from the review), and
   explicitly accept the weaker "last-500-events-globally" guarantee for AC3, rather than building a
   new durable-until-filled registry (option (b)).** Reasoning:
   - This ticket's own Out of Scope explicitly excludes any "filled" detection/resolution mechanism
     (`filled_by_entity_id`, apprentice promotion, auto-refill — see investigation.md's Anti-Drift
     Hazards). A durable open-vacancies registry (option (b)) would need exactly such a mechanism to
     ever clear an entry — without one, it becomes state that is never programmatically removed,
     which is a bigger and more permanent durable-state commitment than a "signal" ticket should
     make, and drifts toward the same out-of-scope "recovery mechanism" territory the ticket already
     warns against.
   - `recent_world_events` is the only existing durable, apply-path-committed, cross-tick-readable
     mechanism in this codebase for this class of event-shaped signal (investigation.md, "Current
     Behavior"). Building a second parallel durable registry purely to get a longer/unbounded memory
     window is disproportionate machinery for what the ticket scopes as a signal, not a tracking
     system.
   - AC3's actual words are "vacancy remains detectable... across a subsequent tick if unfilled" —
     i.e., nothing auto-resolves it early. That guarantee holds under the real mechanism: the event
     is never evicted *because time passed* or *because the vacancy was implicitly resolved*: it is
     evicted only by genuine, unrelated world activity crowding it out of a 500-slot global buffer.
     This is a real, bounded, and now honestly-stated limitation of the delivered signal — not a
     silent one.
   - All "500-tick" language below is corrected to describe the real mechanic, and Step 4's boundary
     test is redesigned to exercise the actual count-based eviction (constructing a merged event list
     directly), not a 501-tick simulation loop standing in as a false proxy for it.
2. **Liveness-filter mismatch (needs correction).** The prior plan's Step 2 pseudocode filtered on
   both `entity.lifecycle.active` and `entity.combat.alive`, while claiming this "mirrors
   `OccupationChangeGoalScorer`... exactly" — `occupation_change_scorer.py:47-48` filters only on
   `other.combat.alive`. That claim was false and is removed. **Decision: keep both filters
   (intentionally stricter than the scorer), documented, not silently dropped.** Reasoning, newly
   verified by direct read: nothing in `resolve_lifecycle`'s death-marking block
   (`src/systems/lifecycle_systems/lifecycle.py:109-121`) ever sets `combat.alive_set=False` — a
   repo-wide grep for `alive_set\s*=` confirms it is written only in `src/engine/combat.py` (KILL
   outcomes) and `src/engine/world_dynamics.py:39` (HAZARD outcomes). An entity that dies via
   `death_reason = "OLD_AGE"` (the same `if is_dead:` branch this ticket's check lives beside) gets
   `lifecycle.active` set `False` but **never** gets `combat.alive_set` written at all, so
   `combat.alive` stays `True` on that entity forever afterward. `OccupationChangeGoalScorer`'s
   `combat.alive`-only filter therefore already has this latent staleness quirk for its own
   citizen-retraining purpose (out of scope to fix here). But this ticket's vacancy check would
   inherit the same staleness bug in a way that defeats its own purpose: a region whose sole
   SHOPKEEPER died of old age in an earlier tick, leaving a second, already-dead-of-old-age
   SHOPKEEPER corpse still sitting in `state.entities` with stale `combat.alive=True`, would
   incorrectly read as "still occupied" and never emit the vacancy event at all. Filtering on
   `lifecycle.active` too — the field this exact function reliably sets `False` on every death
   regardless of reason — closes that gap. This is documented in the new service's code comment
   (Step 2 below), not left as an unexplained divergence from the cited precedent.
3. **Inline aggregate scan violated the extraction precedent (needs correction).** The prior Step 2
   inlined ~25 lines of nested-loop region-wide scan logic directly inside the per-entity death
   branch of `resolve_lifecycle`. Direct re-read confirms `resolve_lifecycle` already draws this
   exact line: local, per-entity-death logic (heir/heirloom transfer, lines 123-158) stays inline;
   aggregate/cross-entity/region-wide logic is extracted and called once, after the main per-entity
   loop, from the `if recent_deaths:` block (lines 160-164) —
   `FactionInfluenceService.process_influence_shift(state, recent_deaths)`
   (`src/world/influence.py:31`), imported from `src.world.influence`. Step 2 is rewritten below to
   extract the vacancy scan into `EconomicVacancyService.check_and_emit(state, recent_deaths) ->
   StateUpdate` (new file `src/economy/vacancy.py`, mirroring `FactionInfluenceService`'s exact
   signature shape), called from the same `if recent_deaths:` block the same way, not inlined in the
   per-entity loop.

## Occupancy Definition (Acceptance Criterion 5)

**"Occupies a production-relevant role" = an entity is the only *living* entity
(`entity.lifecycle.active and entity.combat.alive`) in its *region*
(`LegalityServiceV2.get_region_for_position(entity.navigation.position, state).id`,
`src/engine/legality.py:44-46`) whose `entity.identity.role` is in the production-relevant role set
`{EntityRole.SHOPKEEPER, EntityRole.WORKER}`.**

- **Role set rationale**: `EntityRole` (`src/core/enums.py:6-12`) has no dedicated `BLACKSMITH`
  role. `src/systems/world_systems/routine.py:138` pairs `SHOPKEEPER` with the `SHOPKEEPING`
  task-kind and `src/entities/identity_resolver.py:15` labels `EntityRole.SHOPKEEPER` as
  `"shopkeeper"` — the closest match to the schema doc's "a City's only blacksmith" example
  (`docs/brainstorm/rpg_expected_schemas.html:934-940`). `routine.py:142` pairs `WORKER` with
  `HARVESTING`, which is equally production. `GUARD` (`routine.py:144`, `PATROLLING`) is excluded —
  not production. This is a **new, minimal, module-level constant** in the new
  `src/economy/vacancy.py` (`_PRODUCTION_RELEVANT_ROLES = (EntityRole.SHOPKEEPER, EntityRole.WORKER)`,
  per Review Revision point 3's extraction), not a reuse of `OccupationChangeGoalScorer`'s
  `_CANDIDATE_ROLES` (`occupation_change_scorer.py:14`), because that tuple also includes `GUARD`,
  which is not production-relevant here.
- **Region scope, not world scope**: reuses `OccupationChangeGoalScorer.score`'s *scan pattern*
  (`occupation_change_scorer.py:42-52`) — one pass over `state.entities`/`state.entities.values()`,
  region-matched via `LegalityServiceV2.get_region_for_position`. This directly satisfies the
  anti-drift hazard against a global/world-wide role count. **Correction (Review Revision point 2):
  this is not an exact mirror of the scorer's liveness filter.** The scorer filters only on
  `other.combat.alive` (`occupation_change_scorer.py:47-48`); this ticket's check filters on both
  `other.lifecycle.active` and `other.combat.alive`, deliberately stricter — see Review Revision
  point 2 for the verified reason (`combat.alive_set` is never written for `OLD_AGE` deaths, only
  `lifecycle.active` is, so a `combat.alive`-only filter would treat an old-age corpse as a
  permanent occupant).
- **Option 3 (`PlaceState.occupant_entity_id`) is ruled out** — confirmed by investigation.md: not
  merged into this branch, and LAIR-kind-only (monster/boss anchor) even once merged, structurally
  unrelated to City worker staffing.
- **Option 2 (new durable per-building/region occupant field) is ruled out** — bigger schema
  surface than necessary, and risks pre-empting idea 66's own future `building_ids`/`entity_ids`
  Place-membership shape. Nothing in `BuildingState` (`src/core/state.py:1101-1127`, confirmed by
  investigation.md — `id, kind, position, hp, max_hp, functional, inventory, price_modifiers`, no
  occupant field) requires this ticket to add one: the region+role headcount scan needs no new
  durable state at all.
- **Known simplification, documented not silently**: if two production-relevant entities in the
  same region die in the *same* tick, each is evaluated against the frozen `state.entities` snapshot
  (pre-death), so both may independently see "1 other living peer" and neither emits a vacancy event
  even though the region ends the tick with zero. This mirrors how `OccupationChangeGoalScorer`
  itself reads only the frozen snapshot, and is an accepted edge case, not a bug to silently ignore —
  called out in Anti-Drift Notes below, not in scope to solve (would require a second pass over
  `recent_deaths` after the main loop, itself scope creep beyond a "signal" ticket).

## Steps

### Step 1 — Add `PRODUCTION_ROLE_VACATED` to `WorldEventCategory`
**Files:** `src/domains/world_emergence/schema.py`
**Change:** Add one new member to `WorldEventCategory` (str Enum, `schema.py:15-51`), following the
existing style of grouped, commented additions (e.g. `COMBAT_LOSS` at line 50-51):
```python
    # TCK-20260903-ECONOMIC-VACANCY-SIGNAL: sole production-relevant occupant died, region left
    # with zero living holders of that role.
    PRODUCTION_ROLE_VACATED = "PRODUCTION_ROLE_VACATED"
```
No change to `WorldEvent` itself (`schema.py:53-60`) — its existing fields (`category, tick,
region_id, subject, severity, payload: Dict[str, float]`) are sufficient; do not add a new field.
`vacated_role` is carried in `payload` as `{"vacated_role": float(int(role))}` since `payload` is
typed `Dict[str, float]` (schema.py:60) and cannot hold a string or enum directly — confirmed by
reading the dataclass definition, not assumed. The vacating entity id is carried in `subject` (str);
`region_id` uses the existing top-level field.
**Do NOT touch:** Any other `WorldEventCategory` member, `WorldEventAggregate`, or any other class in
this file — this is a single additive enum member.
**Verify:** No dedicated test needed for the enum addition alone; covered implicitly by Step 2/3's
tests asserting `event.category == WorldEventCategory.PRODUCTION_ROLE_VACATED`.

### Step 2 — `EconomicVacancyService` (new, extracted) + call site in `LifecycleSystem.resolve_lifecycle` (PP-33)
**Files:** new `src/economy/vacancy.py`; edit `src/systems/lifecycle_systems/lifecycle.py`
**Change (rewritten per Review Revision points 2 and 3 — extraction + corrected filter):**

**2a. New file `src/economy/vacancy.py`** — mirrors `FactionInfluenceService`'s exact shape
(`src/world/influence.py:22-31`: a plain class with a `@staticmethod` taking
`(state: AuthoritativeState, recent_deaths: List[EntityState]) -> StateUpdate`), placed in
`src/economy/` alongside the existing `EconomyHealthMonitor` (`src/economy/health_monitor.py`) since
this is economy-domain aggregate logic, not lifecycle-local logic:
```python
from __future__ import annotations
from typing import List
from src.core.state import AuthoritativeState, EntityState
from src.core.updates import StateUpdate
from src.core.enums import EntityRole

# TCK-20260903-ECONOMIC-VACANCY-SIGNAL. Role set rationale: see plan.md's Occupancy Definition
# section -- SHOPKEEPER (routine.py:138, SHOPKEEPING) and WORKER (routine.py:142, HARVESTING) are
# production-relevant; GUARD (routine.py:144, PATROLLING) is not. Deliberately narrower than
# OccupationChangeGoalScorer's _CANDIDATE_ROLES (occupation_change_scorer.py:14), which also
# includes GUARD for retraining purposes unrelated to production.
_PRODUCTION_RELEVANT_ROLES = (EntityRole.SHOPKEEPER, EntityRole.WORKER)


class EconomicVacancyService:
    """
    Detects when a death leaves a region with zero living holders of a production-relevant role
    and emits a PRODUCTION_ROLE_VACATED WorldEvent. Mirrors FactionInfluenceService's shape
    (src/world/influence.py) -- called once per tick from LifecycleSystem.resolve_lifecycle's
    aggregate `if recent_deaths:` block, after the main per-entity death loop, over the same
    recent_deaths list FactionInfluenceService.process_influence_shift already consumes there.
    """

    @staticmethod
    def check_and_emit(state: AuthoritativeState, recent_deaths: List[EntityState]) -> StateUpdate:
        from src.engine.legality import LegalityServiceV2  # local import, mirrors
                                                             # occupation_change_scorer.py:36 and
                                                             # influence.py's own local import style
        from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory

        events = []
        for entity in recent_deaths:
            if entity.identity.role not in _PRODUCTION_RELEVANT_ROLES:
                continue
            region = LegalityServiceV2.get_region_for_position(entity.navigation.position, state)
            if region is None:
                continue

            still_occupied = False
            for other_id, other in state.entities.items():
                if other_id == entity.id:
                    continue
                # Deliberately stricter than OccupationChangeGoalScorer's combat.alive-only filter
                # (occupation_change_scorer.py:47-48). Verified: resolve_lifecycle's death-marking
                # block (lifecycle.py:109-121) sets lifecycle.active=False on every death regardless
                # of reason, but never writes combat.alive_set for OLD_AGE deaths -- alive_set is
                # only ever written in src/engine/combat.py (KILL) and
                # src/engine/world_dynamics.py:39 (HAZARD). An old-age-dead entity's combat.alive
                # therefore stays True forever. Filtering on combat.alive alone would count that
                # stale corpse as a permanent occupant and this check would never fire for a region
                # whose real occupants all died of old age. lifecycle.active is the reliable
                # liveness signal here.
                if not other.lifecycle.active or not other.combat.alive:
                    continue
                if other.identity.role != entity.identity.role:
                    continue
                other_region = LegalityServiceV2.get_region_for_position(
                    other.navigation.position, state
                )
                if other_region is not None and other_region.id == region.id:
                    still_occupied = True
                    break

            if not still_occupied:
                events.append(WorldEvent(
                    category=WorldEventCategory.PRODUCTION_ROLE_VACATED,
                    tick=state.tick,
                    region_id=region.id,
                    subject=str(entity.id),
                    severity=1.0,
                    payload={"vacated_role": float(int(entity.identity.role))},
                ))

        if not events:
            return StateUpdate()
        return StateUpdate(world_events_add=events)
```
Known same-tick co-death simplification (unchanged from the Occupancy Definition section): each
`entity` in `recent_deaths` is checked against the frozen `state.entities` snapshot, so two
production-relevant entities of the same role dying in the same region in the same tick may each
see the other as still `combat.alive` and neither emits an event. Accepted, documented, not fixed
here (see Anti-Drift Notes).

**2b. Call site — `src/systems/lifecycle_systems/lifecycle.py`, inside the existing
`if recent_deaths:` aggregate block (lines 160-183)**, alongside (not inside) the existing
`FactionInfluenceService` calls:
```python
        if recent_deaths:
            from src.world.influence import FactionInfluenceService
            from src.economy.vacancy import EconomicVacancyService
            # Influence Shift
            inf_update = FactionInfluenceService.process_influence_shift(state, recent_deaths)
            # Conquest/Stronghold Lifecycle (Requires generator)
            from src.systems.world_systems.generator import EntityGenerator
            generator = EntityGenerator(state.seed + state.tick)
            inf_update = FactionInfluenceService.process_conquest_lifecycle(state, inf_update, generator)
            # Economic Vacancy Signal (TCK-20260903-ECONOMIC-VACANCY-SIGNAL)
            vac_update = EconomicVacancyService.check_and_emit(state, recent_deaths)

            # Merge world updates and new entities
            new_world_updates = dict(update.world_updates)
            for r_id, extra_upd in inf_update.world_updates.items():
                if r_id in new_world_updates:
                    new_world_updates[r_id] = new_world_updates[r_id].merge(extra_upd)
                else:
                    new_world_updates[r_id] = extra_upd

            update = replace(update,
                world_updates=new_world_updates,
                entities_add=list(update.entities_add) + list(inf_update.entities_add),
                entities_remove=list(update.entities_remove) + list(inf_update.entities_remove),
                world_events_add=list(update.world_events_add) + list(vac_update.world_events_add),
            )

        return replace(update, entity_updates=refined_entity_updates)
```
The only change to the existing block is adding `vac_update = EconomicVacancyService.check_and_emit(...)`
and the new `world_events_add=...` keyword to the existing `replace(update, ...)` call already in
this block — **this block today does not merge `world_events_add` at all** (confirmed by direct
read: it only names `world_updates`, `entities_add`, `entities_remove`); adding the
`world_events_add` keyword is additive to that `replace()` call, not a change to any of its existing
three fields. The function's final line (`return replace(update, entity_updates=refined_entity_updates)`)
is **unchanged** — since `replace()` only overwrites named fields, `update.world_events_add` (already
carrying the vacancy events from the block above) passes through it untouched. This composes safely
with pre-existing `update.world_events_add` content from phases that ran earlier in the same tick
(see the enumerated writers below) because `list(update.world_events_add) + list(vac_update.world_events_add)`
is copy-forward-then-append, never a bare overwrite — matching every other in-place
`replace(update, ...)` writer to `world_events_add` in this codebase (`src/engine/economy.py:276,290`,
`src/engine/pipeline_phases/actions.py:87,142,160,209,267,272`, `src/engine/world_dynamics.py:112-115`,
`src/engine/pipeline_phases/quest_opportunity_rewards.py:118`).

**Enumerated other writers to `world_events_add` in the same tick's pipeline** (grep-confirmed,
`src/engine/pipeline.py`): `contracts`/`blacksmith` (before lifecycle, PP order 223),
`diplomatic_transitions` (270, via `.merge()`), `military_conflict` (via `.merge()`),
`interaction_enforcement`, `town_resolution` (323, this ticket's own Step 3, before lifecycle), plus
`_route_action_intent`'s `actions.py` writes, plus `demographics`
(`DemographicCycleService.process_demographics`, `src/domains/demographics/cohort.py:337-418`,
which appends `POPULATION_BIRTH`/`POPULATION_DEATH` events every `COHORT_INTERVAL=200` ticks — see
Review Revision point 1 for why this matters for the window-size claim). All of these run **before**
`lifecycle` (pipeline order 389) in phase order within the same tick and therefore already sit
inside `update.world_events_add` by the time `resolve_lifecycle` runs — the copy-forward-then-append
in 2b preserves every one of them. No writer runs *after* lifecycle in the same tick that could
overwrite what this step adds (confirmed via `pipeline.py` phase ordering around line 389).

**Do NOT touch:** heir/heirloom transfer logic (lines 123-158), the existing
`FactionInfluenceService`/conquest calls or their `world_updates`/`entities_add`/`entities_remove`
merging (only the `world_events_add` keyword is added to that same `replace()` call), life-stage
transition logic (lines 55-90), or `_select_default_heir` — none of these interact with the vacancy
check. Do not inline the scan logic back into the per-entity `if is_dead:` loop — it belongs in
`EconomicVacancyService`, called once over the full `recent_deaths` list, per Review Revision point 3.
**Verify:** `tests/unit/progression/test_lifecycle.py::test_sole_shopkeeper_death_emits_vacancy_event`,
`::test_non_sole_occupant_death_does_not_emit_vacancy_event`,
`::test_role_and_region_scope_of_sole_occupant_check` (test_plan.md items 1, 2, 7), plus a new
`tests/unit/economy/test_vacancy.py::test_old_age_death_of_prior_occupant_does_not_mask_vacancy`
covering the `lifecycle.active`-vs-`combat.alive` divergence directly (construct a region with one
live SHOPKEEPER and one already-`OLD_AGE`-dead SHOPKEEPER whose `combat.alive` is still `True`; kill
the live one; assert the event still fires). Also re-run the full existing
`tests/unit/progression/test_lifecycle.py` file (`test_death_by_old_age`,
`test_combat_death_classification`, `test_permadeath_death_classification`,
`test_succession_and_heirloom_transfer`, `test_default_heir_*`) unchanged, per test_plan.md's
Regression Surface.

### Step 3 — Wire `TownResolutionSystem.resolve` (PP-20) as the reading consumer
**Files:** `src/engine/town_resolution.py`
**Change:** In `TownResolutionSystem.resolve` (lines 21-178), add a read-only reaction near the top
of the function (after the early-exit checks at lines 41-42, before the entity loop at line 64):
```python
new_metric_counters = dict(update.metric_counters)
for event in getattr(state, "recent_world_events", []):
    if event.category != WorldEventCategory.PRODUCTION_ROLE_VACATED:
        continue
    key = f"economic_vacancy_detected_region_{event.region_id}"
    new_metric_counters[key] = new_metric_counters.get(key, 0) + 1
```
(`WorldEventCategory` imported locally at the top of `resolve`, alongside the existing local imports
at lines 27-29.) Add `metric_counters=new_metric_counters` to the function's existing final
`return replace(update, entity_updates=..., resource_updates=..., building_updates=...)`
(lines 174-178).

This reads `state.recent_world_events` — the previous tick's already-applied, bounded window
(`src/engine/apply.py:335-338`) — the same one-tick-lag law documented for
`FactionAwarenessService.compute_tension_updates` (`src/engine/faction_decision.py:177-179`) and the
same call-site pattern used at `src/engine/pipeline.py:236-241`
(`_recent_events = getattr(state, "recent_world_events", [])`). Deliberately **does not** touch
`BuildingState.functional` or gate `BlacksmithSystem.enforce` — the reaction is purely additive
metrics, preserving `TOWN-017`'s verified **P0** parity entry (`town_resource.yaml:193-201`,
re-confirmed priority by direct read, correcting investigation.md's non-P0 guess) untouched.

**Enumerated other writers to `metric_counters` in the same tick** (grep-confirmed across `src/`):
`src/domains/cooperation/phase.py:165-167` (`cooperation_evaluations`, `cooperation_phase_ms`),
`src/domains/world_emergence/phase.py:129-132` (`world_emergence_ms`, `aggregates_generated`,
`quest_opportunities_rejected`), `src/engine/pipeline_phases/movement.py:219-220`
(`movement_candidates`), `src/systems/strategic_systems/intelligence.py:810-812`
(`strategic_candidates`), and `src/engine/pipeline.py:97-132` itself (`raw_entity_updates`,
`compacted_entity_updates`, `phase_runs`, `skip_<phase>`, `run_<phase>`, `phase_skips`). All of these
follow the identical `dict(update.metric_counters)` copy-forward pattern before setting their own
keys, then return via `replace(update, metric_counters=...)` — the same pattern this step follows.
Because every writer namespaces its own keys (no other writer uses the
`economic_vacancy_detected_region_*` prefix), and `StateUpdate.merge()` sums same-key values
additively across separately-constructed `StateUpdate`s (`src/core/updates.py:1146-1148`) rather than
overwriting, there is no collision risk between this key and any existing metric. `metric_counters`
is a per-tick observability snapshot (re-set at `pipeline.py:425-427` at the end of each tick's phase
run), not durable cross-tick state — the actual cross-tick "remains detectable" guarantee for the
vacancy signal comes from `recent_world_events`'s last-500-events-globally window (Step 2, corrected
per Review Revision point 1 — a count of `WorldEvent` objects across the whole world, not a 500-tick
clock), not from this counter; this counter only proves Step 3's reaction re-fires every tick the
underlying event is still in that window, which is what AC2/AC3 require of the *consumer*.
**Do NOT touch:** the entity loop (lines 64-136), building taxation/maintenance block (lines
138-172), or any `BuildingState.functional` write — those stay exactly as they are today
(faction-maintenance-insolvency-only, per investigation.md's confirmed current behavior).
**Verify:** new tests in `tests/integration/economy/test_economic_vacancy_signal.py` (Step 4):
`test_vacancy_signal_readable_by_consuming_system`,
`test_vacancy_remains_detectable_across_subsequent_tick_if_unfilled`. Also re-run
`tests_v2/parity/test_town_resolution_parity.py -k "blacksmith or shop"` to confirm `TOWN-017`
crafting stays entity-agnostic (test_plan.md's Anti-Drift Test Guard).

### Step 4 — New integration tests
**Files:** new `tests/integration/economy/test_economic_vacancy_signal.py`
**Change:** Add, in this order (each independently runnable):
1. `test_vacancy_event_committed_through_authoritative_apply_path` — build a minimal state with one
   `SHOPKEEPER` in a region, run the death through the real apply cycle
   (`src.engine.apply.ApplyPipeline.apply_generation`, `src/engine/apply.py:189`, or
   `apply_partial`, line 463 — whichever the existing test helpers in this suite already use for a
   single-phase-equivalent apply; consult `tests/unit/domains/faction/test_faction_awareness.py` for
   the closest existing apply-cycle-driven test harness pattern before writing a new one from
   scratch), assert the `PRODUCTION_ROLE_VACATED` event is present in the post-apply
   `AuthoritativeState.recent_world_events`. Satisfies test_plan.md item 3 and AC1's
   "through the authoritative apply path" language concretely.
2. `test_vacancy_signal_readable_by_consuming_system` — construct a state where
   `recent_world_events` already contains a `PRODUCTION_ROLE_VACATED` event for a region, call
   `TownResolutionSystem.resolve(state, StateUpdate())`, assert
   `result.metric_counters["economic_vacancy_detected_region_<id>"] == 1`. Satisfies AC2 and
   test_plan.md item 4 (reads from state, not constructed in isolation).
3. `test_vacancy_remains_detectable_across_subsequent_tick_if_unfilled` — same as above, but run
   `TownResolutionSystem.resolve` twice across two simulated ticks with the event still in the
   window both times; assert the counter increments each time (still-detected). **Redesigned per
   Review Revision point 1** — the eviction boundary is a count of `WorldEvent` objects, not a tick
   count, so it must be tested at the actual mechanism (`src/engine/apply.py:335-338`), not via a
   501-tick simulation loop standing in as a false proxy for it. Split into two assertions, both
   exercising `ApplyPipeline` (or the equivalent apply-path helper used in Step 4 item 1) directly
   rather than ticks:
   - **Still-in-window case**: construct `prior_state.recent_world_events` as a list of 499 filler
     `WorldEvent`s (any category) plus the `PRODUCTION_ROLE_VACATED` event at the end (500 total,
     i.e. exactly at the cap with the vacancy event as the newest), apply a `StateUpdate` carrying
     zero new events, and assert the vacancy event is still present in
     `new_recent_world_events` afterward (the 500-slot cap does not evict something already inside
     it when nothing new is added).
   - **Evicted case**: construct `prior_state.recent_world_events` as the vacancy event followed by
     499 filler `WorldEvent`s (i.e. the vacancy event is now the *oldest* of exactly 500), apply a
     `StateUpdate` carrying **one** new filler `WorldEvent` in `world_events_add`, and assert the
     vacancy event is **no longer** present in the resulting `new_recent_world_events` — proving the
     window evicts by event count, and that a single additional world event from any other system is
     enough to push it out once the buffer is full, regardless of how many or how few ticks that
     took in wall-clock/tick terms.
   Both assertions run against the real `WORLD_EVENT_WINDOW = 500` slicing logic
   (`src/engine/apply.py:335-338`), not a re-implemented copy of it, and the test's own docstring
   must state explicitly that this is a global event-count cap shared with every other `WorldEvent`
   emitter in the pipeline, not a per-signal 500-tick timer. Satisfies AC3, with the real
   bounded-window mechanic stated and tested explicitly, not left implicit or tested via a
   tick-count proxy that doesn't match the actual code.
4. `test_single_production_entity_town_regression_vacancy_detection_delta` — **replaces** the
   ticket's originally-worded "production-throughput delta" scenario (see AC4 revision below):
   single-production-entity (`SHOPKEEPER`) town, same seed, two runs of N ticks (N ≥ 2): control
   (entity survives) vs. treatment (entity killed at tick 1 via the same death path Step 2 covers).
   Assert control's cumulative `economic_vacancy_detected_region_<id>` metric stays 0 across all N
   ticks, treatment's is > 0 from the tick after death onward. The test's own docstring must state
   explicitly that this measures the vacancy-detection-signal delta (Step 2 emission + Step 3
   consumption), **not** blacksmith crafting throughput, and that `BlacksmithSystem.enforce`
   (`src/engine/blacksmith.py`) remains entity-agnostic by design in this ticket — so this test would
   correctly fail if Step 2 or Step 3's wiring were removed, but is not claiming anything about
   crafted-item counts.
**Do NOT touch:** any existing test file. This is entirely new.
**Verify:** these 4 tests themselves, run via
`pytest tests/integration/economy/test_economic_vacancy_signal.py -v`.

### Step 5 — Parity ledger entry
**Files:** `docs/parity_ledger/town_resource.yaml`
**Change:** Add one new entry. Highest existing `id:` in this file as of this plan's writing is
`TOWN-192` (grep-confirmed, `town_resource.yaml:2280`) — next free id is **`TOWN-193`**, but the
parity-updater step must re-grep immediately before writing, since this is a shared, concurrently-
edited repo (per CLAUDE.md's worktree-isolation note) and another in-flight ticket could claim it
first. Entry shape:
```yaml
- id: TOWN-193
  text: >
    Death of the sole living region-scoped SHOPKEEPER or WORKER emits a PRODUCTION_ROLE_VACATED
    WorldEvent through the authoritative apply path (world_events_add -> recent_world_events, a
    last-500-events-globally window, not a 500-tick timer); TownResolutionSystem reads it back
    one-tick-lagged and increments a per-region detection counter. Crafting itself remains
    entity-agnostic (no change to TOWN-017).
  status: verified
  priority: P2
  legacy_evidence: null
  v2_evidence: '`src/economy/vacancy.py` (`EconomicVacancyService.check_and_emit`),
    `src/systems/lifecycle_systems/lifecycle.py` (`LifecycleSystem.resolve_lifecycle`, call site),
    `src/engine/town_resolution.py` (`TownResolutionSystem.resolve`)'
  proof_type: parity
  test_path: '`tests/integration/economy/test_economic_vacancy_signal.py`'
  divergence_note: null
  support_boundary: null
```
Use `tools/parity_ledger_writer.py` (the sanctioned writer) rather than a raw Edit, per the
established anti-drift lesson on hand-rolled full-file YAML rewrites.
**Do NOT touch:** `TOWN-017` or any of its neighbors (`TOWN-026`, `TOWN-028`, `TOWN-043`) — their
`status`/`text` stay exactly as-is, since crafting behavior is unchanged.
**Verify:** `docs/parity_ledger/schema.json` validation (however the parity-updater agent normally
confirms this — e.g. re-running the parity YAML validator tool if one exists in `tools/`).

### Step 6 — Doc updates (D19 audit inventory)
**Files:** `docs/audits/D19_domain_phase_inventory.md`
**Change:** Update the description cells for the PP-33 row (line ~208) and PP-20 row (line ~175) to
note the new vacancy-signal emission/consumption behavior, in the same short style as the existing
cells. This is a `doc-updater` agent task, run after Steps 1-5 land, not part of the implementer's
own diff.
**Do NOT touch:** the PP-07 row — `BlacksmithSystem`'s behavior is unchanged by this ticket.
**Verify:** N/A (doc-only; no test).

## Scope Guards

- Do not implement `filled_by_entity_id` resolution (apprentice promotion / import / auto-refill) —
  explicitly out of scope. No such field or branch should appear anywhere in the diff.
- Do not add a second `GoalScorer` — `EconomicVacancyService` (Step 2) reuses only the
  region-matching *scan pattern*, is not a `GoalScorer` subclass, is not registered in
  `StrategicIntelligenceSystem`'s goal tiers, and does not touch `OccupationChangeGoalScorer` or its
  tests at all.
- Do not gate `BlacksmithSystem.enforce` on the vacancy signal — this would silently break
  `TOWN-017`'s verified **P0** parity entry. If a future ticket decides to do this deliberately, it
  must update `TOWN-017` in the same session per the Authoritative Mechanics Rule; this ticket does
  not.
- Do not touch `PlaceState`/`PlaceKind`/`occupant_entity_id` or anything under idea 66's Place-model
  work — confirmed not merged into this branch, and structurally irrelevant (LAIR-scoped) even once
  merged.
- Do not add a new field to `BuildingState`, `RegionState`, or any other durable schema — Option 1's
  region+role headcount scan requires none.
- Do not use `location_place_id` anywhere — `region_id` is the interim location identifier per
  ticket scope.
- Do not modify `EconomyHealthMonitor`, its alert classes, or its `_event_listeners` kernel wiring —
  it is referenced only as a shape precedent that this ticket does not reuse for wiring.
- Do not modify heir/heirloom transfer logic, faction influence/conquest shift logic, or life-stage
  transition logic in `lifecycle.py` — the vacancy check is purely additive within `resolve_lifecycle`.

## Dependency Map

- Step 1 (enum addition) must land before Step 2 and Step 3 (both import `WorldEventCategory.PRODUCTION_ROLE_VACATED`).
- Step 2's new file `src/economy/vacancy.py` (`EconomicVacancyService`) must exist before Step 2's
  edit to `lifecycle.py` (2b imports it) — both sub-steps are in the same Step 2 and land together.
- Step 2 (emission) must land before Step 3 can be meaningfully tested end-to-end, though Step 3's
  code change itself does not literally depend on Step 2's code (it reads a category, not a specific
  emitter) — implement in numeric order regardless, since Step 4's tests need both.
- Step 4 (tests) depends on Steps 1-3 all being in place.
- Step 5 (parity ledger) and Step 6 (doc updates) depend on Steps 1-4 being implemented and passing,
  since their `test_path`/description content describes the finished behavior.
- All steps are otherwise independent of any other in-flight ticket in this repo (no shared file
  overlap identified with `TCK-20260824-DEFAULT-HEIR-ASSIGNMENT` or
  `TCK-20260824-OCCUPATION-CHANGE-TRIGGER`, both DONE and read-only reference precedents here).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: death of sole occupant commits a typed vacancy event through the authoritative apply path, carrying vacated_role and vacating entity/region_id | Step 1, Step 2 | `test_sole_shopkeeper_death_emits_vacancy_event`, `test_vacancy_event_committed_through_authoritative_apply_path` |
| AC2: signal actually readable by a consuming system (PP-07 or PP-20), proven by reading from state/events | Step 3 | `test_vacancy_signal_readable_by_consuming_system` |
| AC3: vacancy remains detectable (not auto-resolved) across a subsequent tick if unfilled | Step 2 (event persists in `recent_world_events` until evicted by the real last-500-events-globally count-based cap — see Review Revision point 1), Step 3 (re-reads it each tick) | `test_vacancy_remains_detectable_across_subsequent_tick_if_unfilled` (asserts the real count-based eviction boundary directly, not a tick-count proxy) |
| **AC4 (REVISED)**: originally "measurable production-throughput delta vs. same-seed control." **Revised to**: "measurable vacancy-detection-signal delta vs. same-seed control" — see rationale below. | Step 2, Step 3, Step 4 item 4 | `test_single_production_entity_town_regression_vacancy_detection_delta` |
| AC5: Plan phase produces an explicit, documented definition of "occupies a production-relevant role" | This plan's "Occupancy Definition" section | N/A (plan.md itself is the artifact) |

### AC4 revision rationale (documented deviation, same class as Coming-of-Age's role-gate addition and Clan-Lifecycle's asset_ids inertness note)

Investigation.md flagged that `BlacksmithSystem.enforce` (`src/engine/blacksmith.py:114-248`) is
confirmed fully entity-agnostic — any qualifying entity can craft regardless of the vacancy signal —
so a literal "production-throughput delta" (e.g. crafted-item counts) is **not** something this
ticket's design actually produces, and gating `BlacksmithSystem` to manufacture one would both
violate the ticket's own out-of-scope guard against recovery/refill mechanics and break `TOWN-017`'s
verified P0 parity entry. Rather than silently claim a throughput delta this plan does not build
(prohibited by this planner's own instructions), AC4 is revised to measure the delta this design
*does* honestly produce: the vacancy-detection signal (Step 2 emission → Step 3 consumption) is
present and counting in the treatment run and absent in the control run. **The implementer must
update the ticket's AC4 text and the "Assumptions / Open Questions" section in
`tickets/inprogress/TCK-20260903-ECONOMIC-VACANCY-SIGNAL.md` to reflect this revision explicitly**
(not silently) before moving the ticket to `tickets/done/`, recording the same rationale in the
ticket's own Implementation Notes.

## Anti-Drift Notes

- **TOWN-017 is P0, not non-P0** — investigation.md's Parity Ledger Overlap section states "None of
  the entries actually in this ticket's likely change surface are priority P0 in the excerpts read";
  a direct re-read of `docs/parity_ledger/town_resource.yaml:196` shows `TOWN-017`'s `priority: P0`
  plainly. This raises the real stakes of the "do not gate BlacksmithSystem" scope guard from a
  general good practice to a hard P0-parity-breaking risk — treat it as such.
- **Same-tick co-death edge case** (documented above under Occupancy Definition) — two
  production-relevant entities of the same role dying in the same region in the same tick may both
  independently see the other as "still occupying" (frozen-snapshot read) and neither emits a
  vacancy event. This is an accepted simplification, not silently dropped — do not attempt to fix it
  as part of this ticket (would require a second pass over `recent_deaths`, itself scope creep).
- **`recent_world_events` is bounded by event count, not tick count — corrected per Review Revision
  point 1.** `WORLD_EVENT_WINDOW = 500` (`src/engine/apply.py:335`) caps the last 500 `WorldEvent`
  objects merged from `prior_events + update.world_events_add` **globally, across every category and
  region**, via a plain list slice (`apply.py:337-338`) — there is no tick-based filtering anywhere
  in that code. "Remains detectable... if unfilled" is true only until 500 other `WorldEvent`s (from
  *any* system — demographics, contracts, diplomacy, military, interaction enforcement, town
  resolution, this ticket's own emitter, etc.) have been appended since. In an active, populated
  world this can happen in materially fewer than 500 ticks (see Review Revision point 1's
  `DemographicCycleService` arithmetic). This is a stated, accepted limitation of using
  `recent_world_events` for this signal (see Review Revision point 1 for why a durable-until-filled
  registry was considered and rejected) — do not describe it as "500 ticks" anywhere in code
  comments, docs, or tests; describe it as "last 500 world events" or "count-based window."
  Step 4's tests must assert this real boundary explicitly (via direct event-count construction, not
  a tick-count proxy) rather than leaving it untested or testing the wrong mechanic.
- **`metric_counters` is per-tick, not durable** — re-set at the end of each tick's phase run
  (`src/engine/pipeline.py:425-427`). It is not the mechanism providing cross-tick persistence for
  the vacancy signal (that's `recent_world_events`); it is only proof that the consumer re-detects
  the still-in-window event every tick, which is what AC2/AC3 require of the consumer side.
- **One-tick lag is inherent, not a bug** — the Step 3 consumer sees vacancy events from the
  previous tick's applied window, same as every other `recent_world_events` consumer in this
  codebase. Do not attempt same-tick same-death detection in `TownResolutionSystem` — that would
  require bypassing the established apply-path law.
- **Do not conflate `WorldEventCategory.PRODUCTION_ROLE_VACATED` with existing `POPULATION_DEATH`**
  — `POPULATION_DEATH` (schema.py:34) is emitted by `DemographicCycleService.process_demographics`
  for abstract cohort-count deaths, an entirely separate mechanism from this ticket's
  per-entity, per-death, sole-occupancy check. Do not try to reuse or piggyback on
  `POPULATION_DEATH` events.
- **`combat.alive` alone is not a reliable liveness signal for this check** — verified (Review
  Revision point 2) that `combat.alive_set` is never written for `OLD_AGE` deaths, only for
  `KILL`/`HAZARD` outcomes (`src/engine/combat.py`, `src/engine/world_dynamics.py:39`). Any future
  change to `EconomicVacancyService.check_and_emit` must keep the `lifecycle.active` filter alongside
  `combat.alive` — dropping it to "match `OccupationChangeGoalScorer` exactly" would silently
  reintroduce the old-age-corpse staleness bug this plan explicitly filters out.
- **Do not inline the vacancy scan back into `resolve_lifecycle`'s per-entity `if is_dead:` loop** —
  per Review Revision point 3, it belongs in `EconomicVacancyService.check_and_emit`, called once
  over the full `recent_deaths` list from the aggregate `if recent_deaths:` block, mirroring
  `FactionInfluenceService`. This is the established convention in this exact function for
  aggregate/cross-entity logic versus local per-death logic — do not regress it.

## Unresolved Questions

None blocking. All three investigation-flagged decisions (occupancy definition, role set, AC4
tension) are resolved above with stated rationale, and all three architecture-review findings
(WORLD_EVENT_WINDOW mischaracterization, liveness-filter mismatch, inline-scan extraction) are
resolved above under "Review Revision" with stated rationale and verified evidence. If a reviewer
disagrees with the SHOPKEEPER+WORKER role-set choice, the AC4 revision, or the decision to keep
`recent_world_events`'s weaker guarantee over building a new durable registry, that is a
design-judgment disagreement to raise explicitly during Review, not a fact gap in this plan.

## Deviations (recorded during Implement)

All implementation steps (1-6) landed exactly as specified above — no deviation in the actual
code/data changes. One deviation in **Verify tooling only**: Step 3's Verify section and Step 5's
`TOWN-017` cross-reference both cite `tests_v2/parity/test_town_resolution_parity.py -k "blacksmith
or shop"`. Direct re-check at implementation time (`find`, `git log --all -- tests_v2`) confirms no
`tests_v2/` directory has ever existed anywhere in this worktree's git history — this is a stale
reference predating this ticket, not something this ticket's diff caused or can fix (out of scope:
`TOWN-017`'s own entry is explicitly a Do-Not-Touch per this plan's Scope Guards). Substituted the
real `TownResolutionSystem`/`BlacksmithSystem`-exercising test files that do exist in this repo as
the regression guard instead: `tests/unit/resource/test_resource_v2_boundary.py`
(`test_blacksmith_craft_refactor`), `tests/unit/world/test_building_interaction_contract.py`,
`tests/unit/core/test_interaction_recovery.py`, `tests/integration/pipeline/test_strategic_cadence.py`
(`test_town_resolution_cadence_gating`), `tests/integrity/test_logic_guards.py` — all pass unchanged,
confirming crafting stays entity-agnostic. See the ticket's own Implementation Notes and Assumptions
/ Open Questions sections for the same note.
