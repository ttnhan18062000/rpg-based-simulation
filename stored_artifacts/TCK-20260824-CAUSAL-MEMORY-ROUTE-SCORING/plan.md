---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING
artifact_type: plan
tags: [adventure, cognition]
---

# Implementation Plan — TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING

## Summary

Wire `MemoryUpdatePhase` into `AuthoritativeApplyPipeline.refine()` so causal memory finally
reaches `AdventureRouteScorer.score()`'s already-built `memory_adjustment` term. This requires four
independent architectural additions plus one behavior-changing rename: (1) redesign
`MemoryUpdatePhase.run()`'s single `trigger_event` dict into a `trigger_events` list matched by
`entity_id`, updating the 2 confirmed existing test call sites; (2) give `entity.cognition` its
first-ever authoritative write path — a new `EntityUpdate.cognition_bundle_set` field, a new
`CognitionPatch`, and a `MemoryUpdatePhase.apply(state, update) -> StateUpdate` wrapper mirroring
`SelfModelUpdatePhase.apply()` exactly, never mutating `state.entities` directly; (3) register the
new phase in `refine()` between `actor_validity` (PP-02) and `self_model` (PP-03), gated by a new
default-OFF `ENABLE_MEMORY_UPDATE` flag, sourcing `trigger_events` from the existing one-tick-lag
`state.recent_world_events` channel; (4) build the one real trigger producer — a new
`WorldEventCategory.COMBAT_LOSS` emitted whenever a defender survives and takes damage, deliberately
NOT tied to `NearDeathHardeningPhase`'s near-death threshold (that would make the `avoid_enemy`
fallback branch AC3 depends on structurally unreachable). Investigation flagged one open question
(bulk vs. per-entity `run()` call) with its own clear recommendation and rationale — this plan
adopts that recommendation directly (bulk call) since it is a pure efficiency choice with no
acceptance-criteria-visible behavior difference, so no items are left as genuinely unresolved
questions requiring a separate human decision.

One correction to the investigation's Design (b): `CombatActions.execute_attack()`
(`src/engine/domain/combat_actions.py:21-116`) returns `Dict[int, EntityUpdate]`, not a
`StateUpdate` — it has no `world_events_add` channel to append to, and `EntityUpdate` itself has no
world-event field (confirmed by reading `src/core/updates.py:619-651` in full). The investigation's
literal suggestion to build the `WorldEvent` "in `combat_actions.py`'s `defender_up` construction"
is therefore not directly implementable at that exact call site. This plan instead builds the
`WorldEvent` one level up, in `ActionRoutingPhase.route()` (`src/engine/pipeline_phases/actions.py`),
which already holds the `StateUpdate` object and already reads `action_updates[target.id].combat`
(same `CombatUpdate` object the investigation's condition inspects) — see Step 4 for the exact
citation trail and the accumulation hazard this location creates with two earlier same-tick writers
of `update.world_events_add`.

## Steps

### Step 1 — `MemoryUpdatePhase.run()` signature: `trigger_event` (dict) → `trigger_events` (list)

**Files:** `src/domains/memory/phase.py`;
`tests/integration/domains/memory/test_phase13_memory_update_phase.py`;
`tests/integration/scenarios/test_phase13_temporal_causal_spatial_memory_scenarios.py`

**Change:** In `MemoryUpdatePhase.run()` (`src/domains/memory/phase.py:30-100`), change the
parameter `trigger_event: Optional[dict] = None` (line 34) to
`trigger_events: Optional[List[dict]] = None`. At the top of the method body, build
`trigger_by_entity = {t["entity_id"]: t for t in (trigger_events or [])}`. Replace the linear check
at line 57 (`if trigger_event and trigger_event.get("entity_id") == entity.id:`) with
`trigger = trigger_by_entity.get(entity.id)` / `if trigger:`, and use `trigger.get(...)` in place of
`trigger_event.get(...)` for `evt_kind`/`evt_id`/`region_id` (lines 58-60). No other logic in `run()`
changes — the causal-attribution call (line 63-69), capacity eviction (lines 72-74, preserving
`CausalMemory.capacity` default of 30, confirmed `src/core/cognition.py:260`), spatial danger
tagging (line 76-82), and region-visit update (lines 84-90) are untouched.

Update the two confirmed existing call sites (verified by direct read, not assumed):
`tests/integration/domains/memory/test_phase13_memory_update_phase.py:18`
(`phase.run([entity], tick=10, trigger_event=trigger)` → `trigger_events=[trigger]`) and
`tests/integration/scenarios/test_phase13_temporal_causal_spatial_memory_scenarios.py` (same
`phase.run([entity], tick=150, trigger_event=trigger)` pattern, near line 25) → `trigger_events=[trigger]`.
`test_phase13_memory_update_phase.py`'s second test (`test_phase_updates_temporal_staleness_after_old_fact`,
no trigger argument at all) needs no change — `trigger_events=None` still produces an empty
`trigger_by_entity` dict.

**Do NOT touch:** `CausalAttributionService.attribute()` (`src/domains/memory/attribution.py`) —
its 4-branch `event_kind` logic and the `avoid_enemy`-only-on-fallback behavior stay byte-identical.
`SpatialMemoryUpdateService` and `TemporalPressureService` — unchanged.

**Verify:** existing 2 call-site-updated tests pass; new
`test_run_updates_multiple_entities_with_distinct_trigger_events_same_tick`
(`tests/integration/domains/memory/test_phase13_memory_update_phase.py`, per test_plan.md AC4) proves
3 entities with 2 distinct simultaneous triggers are each independently and correctly matched.

---

### Step 2 — Typed-update integration: `EntityUpdate.cognition_bundle_set`, `CognitionPatch`, `MemoryUpdatePhase.apply()`

**Files:** `src/core/updates.py`; `src/engine/patches.py`; `src/domains/memory/phase.py`

**Change:**

1. `src/core/updates.py` — `EntityUpdate` (`@dataclass(frozen=True, slots=True)`, lines 618-651) has
   no field for `entity.cognition`; only `self_model_bundle_set: Optional[Any] = None` (line 649)
   exists for the structurally distinct `entity.self_model` field (confirmed `entity.self_model` and
   `entity.cognition` are two separate top-level `EntityState` fields at `src/core/state.py:689-690`).
   Add `cognition_bundle_set: Optional[Any] = None` immediately after line 649, mirroring
   `self_model_bundle_set` exactly. Add it to `is_noop()` (line 672's boolean chain — append
   `and self.cognition_bundle_set is None`) and to `merge()` (after line 706's
   `self_model_bundle_set` clause, add
   `if other.cognition_bundle_set is not None: changes["cognition_bundle_set"] = other.cognition_bundle_set`).
   **Other writer analysis (shared-resource requirement):** `EntityUpdate.merge()` is called by
   multiple call sites across the same tick — e.g. `ActionRoutingPhase.route()`
   (`src/engine/pipeline_phases/actions.py:226`, `existing_upd.merge(action_upd)`), which runs
   later in the same tick than the new `memory_update` phase (PP-02.5, Step 3). Traced concretely:
   when `action_routing` merges a combat-produced `action_upd` (which never sets
   `cognition_bundle_set`) into an `existing_upd` that already carries the value written by
   `MemoryUpdatePhase.apply()` earlier in the tick, `other.cognition_bundle_set is None` so the new
   merge clause contributes nothing to `changes`, and `replace(self, **changes)` retains `self`'s
   (i.e. `existing_upd`'s) already-set value automatically — no data loss occurs even without the
   merge clause, because `self` is always the side carrying the earlier write in every currently
   traced call path. The merge clause is added anyway, purely for structural parity with
   `self_model_bundle_set`'s identical clause and to guard against any future code path where a
   `cognition_bundle_set`-bearing update becomes the `other` side of a merge.
2. `src/engine/patches.py` — add `CognitionPatch(ComponentPatch)` immediately after `SelfModelPatch`
   (lines 641-658), copying its shape exactly: `cognition_bundle_set: Optional[Any] = None`,
   `is_noop()` returns `self.cognition_bundle_set is None`, `merge()` prefers `other`'s non-None
   value, `apply(self, entity, changes)` sets `changes["cognition"] = self.cognition_bundle_set`.
   Register it in `extract_patches()` (`src/engine/patches.py:661-720`) after the `SelfModelPatch`
   registration (lines 717-719):
   `if update.cognition_bundle_set is not None: patches.append(CognitionPatch(entity_id, cognition_bundle_set=update.cognition_bundle_set))`.
   **Other writer analysis:** `extract_patches()` builds a single shared `changes: Dict[str, Any]`
   dict per entity that every registered patch's `.apply(entity, changes)` writes into
   (`src/engine/patches.py:661-720`); no other patch writes the `"cognition"` key (each patch owns a
   distinct key — `"self_model"`, `"combat"`, `"navigation"`, etc.) so there is no collision.
   `ApplyPath._fast_replace_entity(entity, changes)` (cited by investigation at
   `src/engine/apply.py:440-456`) performs the single authoritative `dataclasses.replace(entity, **changes)`
   consuming this dict — confirmed by the same call graph the investigation traced
   (`_apply_entity_update_to_dict` → `extract_patches` → `patch.apply` → `_fast_replace_entity`).
3. `src/domains/memory/phase.py` — add `MemoryUpdatePhase.apply(state, update) -> StateUpdate` as a
   `@staticmethod`, mirroring `SelfModelUpdatePhase.apply()` (`src/cognition/self_model_phase.py:32-74`)
   structurally. **Important implementation detail not explicit in investigation.md, confirmed by
   reading the class**: `MemoryUpdatePhase.run()` is an *instance* method (`def run(self, entities, ...)`,
   `src/domains/memory/phase.py:30`), unlike `SelfModelUpdatePhase.run()` which is a `@staticmethod`
   — every existing test call site instantiates first (`phase = MemoryUpdatePhase(); phase.run(...)`,
   confirmed at `tests/integration/domains/memory/test_phase13_memory_update_phase.py:17-18` and the
   scenario test). `apply()` must therefore do `phase = MemoryUpdatePhase()` before calling `.run()`.
   Adopting investigation's own recommended resolution to its flagged (non-blocking) open question:
   call `run()` once in bulk rather than per-entity. Concretely:
   ```
   active_entities = [e for e in state.entities.values() if e.lifecycle.active and e.combat.alive]
   updated = MemoryUpdatePhase().run(active_entities, tick=state.tick, trigger_events=trigger_events)
   new_entity_updates = dict(update.entity_updates)
   for new_entity in updated:
       entity_up = new_entity_updates.get(new_entity.id, EntityUpdate(entity_id=new_entity.id))
       new_entity_updates[new_entity.id] = dataclasses.replace(entity_up, cognition_bundle_set=new_entity.cognition)
   return dataclasses.replace(update, entity_updates=new_entity_updates)
   ```
   This filters to active/alive entities before calling `run()` (matching
   `SelfModelUpdatePhase.apply()`'s loop-skip at `self_model_phase.py:53`,
   `if not entity.lifecycle.active or not entity.combat.alive: continue`) rather than passing
   `state.entities.values()` wholesale — `run()` already independently re-checks this same condition
   internally (`phase.py:40`) and would no-op skipped entities anyway, but pre-filtering avoids
   writing a non-`None` (hence non-noop) `cognition_bundle_set` for every inactive/dead entity in the
   world every tick, which would otherwise force `extract_patches()`/`_fast_replace_entity()` to do
   pointless work for entities this phase does not act on. `trigger_events` itself is sourced by
   Step 3, not here — `apply()` takes it as a parameter built by the caller.

**Do NOT touch:** `SelfModelPatch`, `SelfModelUpdatePhase.apply()`, or the `self_model_bundle_set`
field/clauses themselves — copy the pattern, do not modify the original.

**Verify:** new `test_memory_update_phase_apply_does_not_mutate_state_entities` (architecture guard,
`tests/unit/domains/memory/test_memory_update_phase_apply.py`) and
`test_cognition_bundle_set_applies_to_entity_cognition_field` (unit, same file or
`tests/unit/engine/test_patches.py` if that file already exists — check before creating a new one)
per test_plan.md AC1b/AC1c.

---

### Step 3 — Register the phase call site in `refine()`, add `ENABLE_MEMORY_UPDATE`, source `trigger_events`

**Files:** `src/engine/pipeline.py`; `src/domains/optimization/feature_flags.py`; `src/engine/phase_graph.py`

**Change:** In `AuthoritativeApplyPipeline.refine()`, insert the new phase call after
`costs["trust_validity"] = ...` (`src/engine/pipeline.py:138`) and before the
`# --- Enhanced RPG Phase 2: Self Model Cognition ---` comment block (line 140), i.e. strictly
between the `actor_validity` `run_phase` call (line 136) and the `self_model` `run_phase` call
(line 143) — this is the exact gap the ticket's AC1 and investigation's confirmed insertion point
both name. Add:
```
# --- Enhanced RPG Phase 2.5: Causal Memory Update ---
t_start = time.perf_counter_ns()
from src.domains.memory.phase import MemoryUpdatePhase
from src.domains.world_emergence.schema import WorldEventCategory
_recent_events_for_memory = getattr(state, "recent_world_events", [])
_memory_trigger_events = [
    {"entity_id": int(e.subject), "kind": "combat_loss", "id": f"combat_loss_{e.tick}_{e.subject}", "region_id": e.region_id}
    for e in _recent_events_for_memory
    if e.category == WorldEventCategory.COMBAT_LOSS and e.subject is not None
]
update = run_phase("memory_update", update, lambda u: MemoryUpdatePhase.apply(state, u), "ENABLE_MEMORY_UPDATE")
costs["memory_update"] = (time.perf_counter_ns() - t_start) / 1e6
```
This mirrors the already-documented `faction_awareness` one-tick-lag pattern
(`src/engine/pipeline.py:184-193`, "recent_world_events reflects last tick's window — one-tick lag is
inherent"): a `COMBAT_LOSS` event produced during tick N's `action_routing` (which runs strictly
after this insertion point, `pipeline.py:237`) is only visible in `state.recent_world_events`
starting tick N+1, after `apply.py:320-325` merges it in. `WorldEvent.subject`
(`src/domains/world_emergence/schema.py:52-58`) is typed `Optional[str]`, but `entity.id`/
`EntityUpdate.entity_id` are `int` throughout `src/core/updates.py` and `src/core/state.py` — the
`int(e.subject)` conversion above is required, or Step 1's `trigger_by_entity = {t["entity_id"]: t ...}`
dict-keyed lookup by `entity.id` (an int) will never match a string key and every trigger will be
silently dropped. `MemoryUpdatePhase.apply(state, u)` (Step 2) reads `trigger_events` — since the
lambda closes over `_memory_trigger_events` computed above, `apply()`'s signature needs a third
param: `apply(state, update, trigger_events=None)` (update Step 2's signature accordingly — call as
`lambda u: MemoryUpdatePhase.apply(state, u, _memory_trigger_events)`).

**Feature flag:** add `"ENABLE_MEMORY_UPDATE": FeatureMode.OFF` to `FeatureFlagManager`'s registry
in `src/domains/optimization/feature_flags.py`, alongside the confirmed sibling entry
`"ENABLE_SELF_MODEL_COGNITION": FeatureMode.OFF` (line 19) — every other Enhanced-RPG phase added in
this stretch of `refine()` (`self_model`, `information_belief`, `information_intent_execution`,
`cooperation`, `combat_engagement`) is registered `OFF` by default in this same file (lines 19, 26,
37 confirmed by direct read), and `get_flag_mode()`'s own fallback (line 121,
`return self._flags.get(flag, FeatureMode.OFF)`) already defaults unregistered flags to OFF — adding
the explicit entry is for documentation/consistency, not strictly required for the OFF default to
hold, but is required if a corpus profile ever wants to turn it ON via name lookup.

**Additional consistency finding (not raised in investigation.md, found by reading
`src/engine/phase_graph.py:36-69`):** every other Enhanced-RPG phase from this stretch
(`self_model`, `information_belief`, `information_intent_execution`, `cooperation`,
`combat_engagement`, `progression_conversion`, `world_emergence`) has a `PhaseMetadata` entry in
`PhaseDependencyGraph.PHASES` (lines 62-68) governing dirty-set/cadence-based skip eligibility.
`PhaseDependencyGraph.should_run_phase()` returns `True` unconditionally for any `phase_name` not in
`PHASES` (`phase_graph.py:81-82`), so omitting a `"memory_update"` entry does not break correctness —
the phase will simply always run (subject only to the `ENABLE_MEMORY_UPDATE` flag) whenever the
dirty-set/cadence optimization layer is active. For consistency with every sibling phase in this
stretch, add `"memory_update": PhaseMetadata("memory_update", {"combat", "strategic"}, {"strategic"})`
to `PHASES` (reads: combat/strategic state relevant to causal attribution's hp/stamina/weapon checks
and temporal urgency; writes: `strategic`-tagged dirty set, matching `self_model`'s own write-set at
line 62, since `entity.cognition` feeds strategic route scoring). This is an additive, low-risk
consistency fix; if the planner/reviewer judges it out of scope for this ticket, it can be dropped
without affecting any acceptance criterion — `should_run_phase()`'s default-True fallback makes it
optional, not required.

**Do NOT touch:** any other `run_phase(...)` call in `refine()` — insertion is additive only, no
existing phase's position, flag, or lambda changes.

**Verify:** new `test_memory_update_phase_registered_between_actor_validity_and_self_model`
(architecture guard, `tests/architecture/test_memory_update_phase_pipeline_ordering.py` — check
`tests/architecture/` first for an existing generic phase-ordering-guard pattern to extend instead of
writing a new file from scratch, per test_plan.md).

---

### Step 4 — Real `combat_loss` producer: `WorldEventCategory.COMBAT_LOSS` in `ActionRoutingPhase.route()`

**Files:** `src/domains/world_emergence/schema.py`; `src/engine/pipeline_phases/actions.py`

**Change:** Add `COMBAT_LOSS = "COMBAT_LOSS"` to `WorldEventCategory`
(`src/domains/world_emergence/schema.py:15-49`) — a small, additive, precedented change (the enum
has grown incrementally by epic tag in comments, e.g. `# E52A`, `# E53Bd`). Do **not** reuse the
existing unused `NEAR_DEATH` member (line 17) — confirmed by grep that neither `NEAR_DEATH` nor
`PARTY_ABANDONED` is ever constructed anywhere in `src/`, and reusing `NEAR_DEATH`'s name for a
broader "took damage and survived" condition would misdescribe it and block future genuine
near-death-signal work.

**Location correction from investigation.md**, confirmed by direct read of both files: the
investigation recommended building this `WorldEvent` inside `CombatActions.execute_attack()`'s
`defender_up` construction (`src/engine/domain/combat_actions.py:96-108`). `execute_attack()`'s
return type is `Dict[int, EntityUpdate]` (`combat_actions.py:27`), and `EntityUpdate`
(`src/core/updates.py:619-651`, read in full for Step 2) has no field capable of carrying a
`WorldEvent` — there is no `StateUpdate.world_events_add` channel reachable from inside
`execute_attack()`. Tracing the call chain confirms this is structural, not an oversight:
`CombatActions.execute_attack()` → `ActionRouter.execute_action()`
(`src/engine/domain/action_router.py:61-62`) → `SimulationDomainLogic.execute_action()`
(`src/engine/domain_logic.py:42-56`, a pure passthrough) → `ActionRoutingPhase.route()`
(`src/engine/pipeline_phases/actions.py:162-166`, `action_updates = SimulationDomainLogic.execute_action(...)`)
— only `ActionRoutingPhase.route()` holds the `StateUpdate` (`update`, the function parameter) that
has a real `world_events_add` field. Build the `WorldEvent` there instead, immediately after
`action_updates = SimulationDomainLogic.execute_action(...)` is computed (`actions.py:162-166`), for
the `action == "ATTACK"` case: for each `action_eid, action_upd in action_updates.items()` where
`action_eid != eid` (i.e. the defender, since `action_updates` for `ATTACK` is
`{entity.id: attacker_up, target.id: defender_up}` per `combat_actions.py:114`) and
`action_upd.combat is not None`, check
`action_upd.combat.alive_set is not False and action_upd.combat.damage_taken > 0`
(both fields confirmed to exist on `CombatUpdate`, `src/core/updates.py:98,102`) and construct
`WorldEvent(category=WorldEventCategory.COMBAT_LOSS, tick=state.tick, region_id=<defender's current region>, subject=str(action_eid))`.
The defender's region is not directly available inside `route()` without a lookup — use
`state.entities.get(action_eid)`'s `.navigation.region_id` (field confirmed to exist at
`src/core/state.py:377`, same field `MemoryUpdatePhase.run()` itself already reads at
`phase.py:85`) if the entity is still present in `state.entities`.

**Shared-resource / other-writer analysis (`update.world_events_add`):** by the time
`action_routing` runs (`pipeline.py:237`), `update.world_events_add` may already contain events from
two earlier same-tick writers: `diplomatic_transitions` (`pipeline.py:219-222`,
`u.merge(_SU_dt(..., world_events_add=_diplo_world_events))`) and `military_conflict`
(`pipeline.py:229-232`, `u.merge(MilitaryConflictPhase.execute(state))`). `ActionRoutingPhase.route()`
itself currently never touches `world_events_add` at all (confirmed by grep — no such reference in
`actions.py`), so this ticket's change is the first writer inside this specific phase. The new logic
must accumulate onto the existing list, not overwrite it, and must be threaded through every
intermediate `update = replace(update, ...)` call inside `route()`'s per-actor loop
(`actions.py:141, 159, 187, 245`) and the final `return replace(update, entity_updates=refined_entity_updates)`
(`actions.py:247-250`) exactly the way `rejection_events`/`rejections_delta` are already
accumulated per-iteration (`actions.py:134-135, 149-150, 181-182`) — build a local
`new_world_events_add = list(update.world_events_add)` at the top of the function (mirroring
`refined_entity_updates = dict(update.entity_updates)` at line 86), `.append(...)` to it inside the
`ATTACK` branch, and include `world_events_add=new_world_events_add` in the final `replace(...)` at
line 247-250 (and any intermediate `replace(update, ...)` call made after an append, so a later
iteration's read of `update.world_events_add` sees prior iterations' additions — same reasoning
`rejection_events` already follows).

**Do NOT touch:** `damage_taken`, `alive_set`, `outcome_kind`, or any other existing `CombatUpdate`
field/value — this step only reads them to decide whether to emit a `WorldEvent`, never writes them.
Do not emit `COMBAT_LOSS` when `action_upd.combat.alive_set is False` (defender died — no future
entity to receive the memory) or when `damage_taken == 0` (miss/no-op). Do **not** couple this
condition to `NearDeathHardeningPhase`'s `projected_hp <= 10%` threshold
(`src/engine/pipeline_phases/hardening.py:71-74`) — this is the single highest-risk mistake per
investigation.md, since it would make `hp_pct < 0.3` true by construction on every firing and
permanently starve `CausalAttributionService.attribute()`'s `avoid_enemy` fallback branch
(`src/domains/memory/attribution.py:50-52`), making AC3 unsatisfiable for that path.

**Verify:** new `test_combat_loss_world_event_emitted_when_defender_survives_and_takes_damage` and
`test_combat_loss_world_event_not_emitted_when_defender_takes_no_damage_or_dies` (per test_plan.md
AC2) — locate the existing `execute_attack`/`action_routing` test file first via
`grep -rl "execute_attack\|ActionRoutingPhase" tests/` (test_plan.md flags this as an
implementer-time discovery step since the exact file was not enumerated in investigation.md).

---

### Step 5 — End-to-end scenario: causal memory populates and scoring reflects it, next tick

**Files:** `tests/integration/scenarios/test_causal_memory_route_scoring_e2e.py` (new)

**Change:** A ≥2-tick integration test (per test_plan.md AC3), driven through
`AuthoritativeApplyPipeline.refine()` with `ENABLE_MEMORY_UPDATE` explicitly enabled (no other new
flag is required — `action_routing` itself runs unconditionally, unflagged, per
`pipeline.py:237`):
- **Tick N:** construct an attacker/defender pair where the attack resolves via `action_routing`
  such that the defender survives and takes damage but does **not** cross `hp_pct < 0.3` /
  `stamina < 20` / `weapon_dur < 0.2` (a healthy defender, modest damage), so Step 4's `COMBAT_LOSS`
  event fires and, next tick, `CausalAttributionService.attribute()`'s fallback branch
  (`attribution.py:50-52`) is the one that fires — `strong_enemy`/`avoid_enemy`, not
  `low_health`/`heal_first` etc.
- **Tick N+1:** assert `state.entities[defender_id].cognition.memory.causal.entries` is non-empty and
  contains an entry whose `future_advice` includes `"avoid_enemy"` (field/path confirmed live at
  `src/domains/adventure/scoring.py:242,245`).
- Call `AdventureRouteScorer.score()` on the defender for a `HUNT_WEAK_ENEMY`-family route and assert
  `memory_adjustment == -1.0` (constant and condition confirmed live at `scoring.py:244,250-251`).

**Do NOT touch:** `AdventureRouteScorer.score()` itself (`src/domains/adventure/scoring.py`) — this
step only calls it, per the ticket's Out-of-Scope decision (see Scope Guards below).

**Verify:** this step *is* the test — `test_combat_loss_end_to_end_produces_nonzero_memory_adjustment_next_tick`.

---

### Step 6 — Doc corrections (implementer-owned subset only)

**Files:** `docs/simulation/domains/memory_contract.md`; `docs/mechanics/04_strategic_cognition.md`;
`docs/engine/authoritative_pipeline.md`

**Change:**
- `docs/simulation/domains/memory_contract.md` — correct the Adventure-domain Domain Interactions row
  (investigation cites line 173) that currently states "this is not yet observable in any live run:
  `MemoryUpdatePhase`... has zero call sites" — describe the new live wiring (pipeline insertion point,
  the `ENABLE_MEMORY_UPDATE` flag default-OFF, and the one-tick-lag semantics of the `COMBAT_LOSS`
  producer, since that lag is new, non-obvious behavior).
- `docs/mechanics/04_strategic_cognition.md` §6.11 — update the "Not yet live" callout (investigation
  cites line 546, "measurement is possible until `MemoryUpdatePhase` is wired into the pipeline") to
  reflect live-reachability; the fallback-branch constraint description itself (line 535) does not
  change, only its live status.
- `docs/engine/authoritative_pipeline.md` (layer: engine, authority: P1) — this file's "The 37 Phases
  of Refinement" table (lines 15-58, confirmed by direct read) is the by-name, by-number phase
  registry CLAUDE.md names under Engine Contracts as authoritative for `refine()`'s phase sequence,
  and it currently enumerates `actor_validity` as row `#2` and `self_model` as row `#3`
  (lines 22-23) with no `memory_update` row between them — the exact gap Step 3 fills by inserting
  `memory_update`/`ENABLE_MEMORY_UPDATE` at that point in `refine()`. Insert a new table row
  immediately after the `actor_validity` row (line 22) and before the `self_model` row (line 23):
  `| 3 | \`memory_update\` | Enhanced RPG: updates causal/temporal/spatial memory from prior-tick
  trigger events (\`ENABLE_MEMORY_UPDATE\`). |` — matching the existing row format and phrasing style
  of the other Enhanced-RPG rows (e.g. the `self_model` row's `"Enhanced RPG: updates cognitive
  self-model (ENABLE_SELF_MODEL_COGNITION)."` pattern, line 23). Renumber every subsequent row's `#`
  column by +1: `self_model` becomes `4`, `information_belief` becomes `5`, `information_intent_execution`
  becomes `6`, `cooperation` becomes `7`, `contracts` becomes `8`, `blacksmith` becomes `9`,
  `faction_awareness` becomes `10`, `diplomatic_transitions` becomes `11`, `military_conflict`
  becomes `12`, `action_routing` becomes `13`, `position_swaps` becomes `14`, `movement_routing`
  becomes `15`, `combat_engagement` becomes `16`, `interaction_routing` becomes `17`,
  `interaction_enforcement` becomes `18`, `building_sabotage` becomes `19`, `town_resolution` becomes
  `20`, `gold_sink` becomes `21`, `world_dynamics` becomes `22`, `world_emergence` becomes `23`,
  `quest_rewards` becomes `24`, `guild_visit` becomes `25`, `shop` becomes `26`, `paid_information`
  becomes `27`, `resource_transactions` becomes `28`, `evolution` becomes `29`,
  `progression_conversion` becomes `30`, `strategic_intelligence` becomes `31`,
  `near_death_hardening` becomes `32`, `occupancy_resolution` becomes `33`, `lifecycle` becomes `34`,
  `groups` becomes `35`, `active_contracts` becomes `36`, `expired_offers` becomes `37`, and
  `capacity_enforcement` becomes `38` (previously 2-37 and 37 respectively, per the current table
  read above). Also update the `## The 37 Phases of Refinement` heading (line 15) to `## The 38
  Phases of Refinement`, and the `> [!IMPORTANT]` callout's count language (line 11, "must pass
  through this pipeline... refined through these 37 phases") to say "38 phases", so the heading/count
  language matches the new total everywhere it appears in this file.

**Do NOT touch:** `docs/parity_ledger/strategic_cognition.yaml` (STRAT-227) — per test_plan.md's
explicit Gate Integrity note, the parity-updater agent re-verifies and updates ledger `v2_evidence`/
`test_path` entries at the dedicated Parity phase of the pipeline; the implementer must not touch
this file directly. `docs/engine/kernel.md` — investigation confirms it documents the 7-phase kernel
loop at a level of abstraction that does not enumerate `refine()`'s internal sub-phases by name, so
adding `memory_update` alongside `self_model`/`information_belief`/etc. creates no new inconsistency
requiring a change there.

**Verify:** no test — doc-only step; reviewed for accuracy against the finished Steps 1-5 code.

## Scope Guards

- Do **not** extend the `future_advice → RouteFamily` mapping in `AdventureRouteScorer.score()`
  (`src/domains/adventure/scoring.py:236-253`) beyond the current 2 mapped values (`avoid_enemy`,
  `boost_party_trust`) — this ticket's Out-of-Scope section frames this as a binary choice and
  investigation's Risks section recommends against extending it here; that work belongs to
  `TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING`'s own continuation lineage. AC3 is satisfiable without
  it via Step 4's producer design reaching the existing `avoid_enemy` fallback branch.
- Do **not** touch the 7 mechanisms owned by `TCK-20260824-WIRE-ORPHANED-MECHANISMS` — that ticket's
  scope explicitly excludes `MemoryUpdatePhase`, confirming this ticket is its sole owner; do not
  reach into that ticket's territory for unrelated orphaned-mechanism wiring.
- Do **not** modify `CausalAttributionService.attribute()`'s 4-branch logic
  (`src/domains/memory/attribution.py:18-77`) — the `avoid_enemy` fallback-only condition is load
  bearing for AC3 and must stay byte-identical.
- Do **not** couple the `COMBAT_LOSS` producer to `NearDeathHardeningPhase`'s threshold
  (`src/engine/pipeline_phases/hardening.py:71-74`) — see Step 4.
- Do **not** widen `MemoryUpdatePhase.run()`'s existing skip condition
  (`not entity.lifecycle.active or not entity.combat.alive`, `phase.py:40`) — an entity that died in
  the same tick's `action_routing` must not receive a `combat_loss` memory update next tick if it is
  no longer active.
- Do **not** write `MemoryUpdatePhase.apply()` to mutate `state.entities` directly — all writes must
  flow through `EntityUpdate.cognition_bundle_set` → `CognitionPatch` → `changes["cognition"]` →
  `_fast_replace_entity`, exactly like `self_model_bundle_set`.
- Do **not** edit `docs/parity_ledger/strategic_cognition.yaml` as part of this plan's steps — that
  is the Parity phase's (parity-updater agent's) job, not the implementer's.

## Dependency Map

- Step 1 (signature redesign) and Step 2 (typed-update wrapper) are independent of each other and
  can be implemented in either order.
- Step 3 (pipeline registration) depends on **both** Step 1 (needs the `trigger_events` list
  signature) and Step 2 (needs `EntityUpdate.cognition_bundle_set`, `CognitionPatch`, and
  `MemoryUpdatePhase.apply()` to exist and accept a `trigger_events` argument).
- Step 4 (combat_loss producer) is independent of Steps 1-3 and can be implemented in parallel with
  them — it only depends on the new `WorldEventCategory.COMBAT_LOSS` enum member it adds itself.
- Step 5 (end-to-end test) depends on **all** of Steps 1, 2, 3, and 4 being complete — it is the
  integration point that exercises the full chain.
- Step 6 (docs) depends on Steps 1-5 being complete and correct, since it documents the finished live
  behavior.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| pipeline.py registers MemoryUpdatePhase's call site between actor_validity (PP-02) and self_model (PP-03) | Step 3 | `test_memory_update_phase_registered_between_actor_validity_and_self_model` |
| At least one real, live trigger_event producer feeds a genuine in-tick event, not just test dicts | Step 4 | `test_combat_loss_world_event_emitted_when_defender_survives_and_takes_damage`, `test_combat_loss_world_event_not_emitted_when_defender_takes_no_damage_or_dies` |
| After a real triggering event, entity.cognition.memory.causal.entries becomes non-empty and AdventureRouteScorer.score() produces a nonzero memory_adjustment | Steps 1, 2, 3, 4, 5 | `test_combat_loss_end_to_end_produces_nonzero_memory_adjustment_next_tick` |
| MemoryUpdatePhase.run()'s signature is redesigned/looped so multiple entities triggering in the same tick are all updated | Step 1 | `test_run_updates_multiple_entities_with_distinct_trigger_events_same_tick` (plus the 2 updated existing tests) |

## Anti-Drift Notes

- The single highest-risk mistake is coupling the `COMBAT_LOSS` producer to
  `NearDeathHardeningPhase`'s `hp_pct < 0.3`-guaranteed threshold — this looks like free reuse of
  existing detection logic but structurally starves the `avoid_enemy` fallback branch that AC3
  depends on. Step 4 explicitly forbids this.
- `WorldEvent.subject` is `Optional[str]`; `entity.id` and `EntityUpdate.entity_id` are `int`. Step 3
  performs an explicit `int(e.subject)` conversion when building `trigger_events` — omitting this
  makes the Step 1 dict-keyed lookup silently match nothing, and every real trigger would be dropped
  with no error raised.
- The one-tick lag (`recent_world_events` reflects last tick's window) is by design, matching the
  `faction_awareness` precedent — an end-to-end test asserting `memory_adjustment != 0` in the *same*
  tick as the triggering combat resolution will fail even with a fully correct implementation.
- `MemoryUpdatePhase.run()` is an instance method, not `@staticmethod` (unlike
  `SelfModelUpdatePhase.run()`) — `apply()` must instantiate `MemoryUpdatePhase()` before calling
  `.run()`.
- `ActionRoutingPhase.route()` (Step 4) is not currently a `world_events_add` writer at all; two
  earlier same-tick phases (`diplomatic_transitions`, `military_conflict`) already populate
  `update.world_events_add` before `action_routing` runs — the new logic must accumulate onto the
  existing list via every intermediate `replace(update, ...)` call in the per-actor loop, not
  overwrite it, mirroring the existing `rejection_events` accumulation pattern in the same function.
- `extract_patches()`'s `changes` dict is shared across all registered `ComponentPatch` subclasses per
  entity; `CognitionPatch` must use the `"cognition"` key exclusively — no other patch writes that key
  today, so there is no collision, but a future patch must not be given the same key.

## Deviations

- **AC2b test file location**: test_plan.md's AC2b named
  `tests/integration/domains/memory/test_memory_update_phase_apply.py` as the (new-or-appended)
  location. That exact basename collides at pytest collection time with the AC1b/AC1c unit file
  the same test_plan names for `tests/unit/domains/memory/test_memory_update_phase_apply.py` —
  neither `tests/unit/domains/memory/` nor `tests/integration/domains/memory/` has an `__init__.py`,
  so pytest's rootdir-relative module naming collides on identical basenames in different
  directories (`import file mismatch`, confirmed by running the scoped suite). Implemented the
  AC1b/AC1c file at the named path and renamed the AC2b file to
  `tests/integration/domains/memory/test_memory_update_phase_apply_trigger_events.py` — same
  content/purpose, no ticket-ID/phase-number in the name, only a unique basename.
- **Step 3's optional `PhaseMetadata` addition**: plan.md flagged the `"memory_update"` entry in
  `PhaseDependencyGraph.PHASES` as "additive... if the planner/reviewer judges it out of scope for
  this ticket, it can be dropped without affecting any acceptance criterion." Implemented it anyway
  for consistency with every sibling Enhanced-RPG phase in that stretch of `refine()` — not a
  deviation from the plan's own recommended path, noted here only because the plan explicitly
  called out the choice as open.
