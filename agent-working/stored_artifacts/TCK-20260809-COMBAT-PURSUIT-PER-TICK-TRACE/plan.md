---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE
artifact_type: plan
tags: [combat, simulation-quality]
---

# Plan — TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE

## Real fix: live-refresh a stale entity-tracking navigation target

**Location**: `src/engine/pipeline_phases/movement.py::MovementPhase.route_movement_intent()`,
right after `nav_target` is first computed from either this tick's fresh decision or the
persisted `entity.navigation.target` snapshot.

**Change**: when relying on the persisted snapshot (no fresh decision this tick) and
`entity.task.payload.get("target_id")` references a real, alive, active entity, override
`nav_target` with that entity's live, current-tick `navigation.position` instead of the stale
snapshot.

```python
has_fresh_decision = bool(ent_upd and ent_upd.navigation and ent_upd.navigation.target_set is not None)
nav_target = ent_upd.navigation.target_set if has_fresh_decision else entity.navigation.target

if not has_fresh_decision:
    tracked_id = entity.task.payload.get("target_id")
    if tracked_id is not None:
        tracked_entity = state.entities.get(tracked_id)
        if tracked_entity is not None and tracked_entity.lifecycle.active and tracked_entity.combat.alive:
            nav_target = tracked_entity.navigation.position

if not nav_target or entity.navigation.position == nav_target:
    continue
```

**Why this is safely scoped**: `task.payload["target_id"]` is only ever set by the real
entity-tracking tactical branches (`PURSUE`, `INTERCEPT`ing, `KITING`, `BRACKETING`,
`GUARDING_ALLY`) — confirmed via direct read of every `tactical.py` branch that sets
`payload_set`. Fixed-point errands (`WANDER`, `PANIC_RETREAT`/`SAFETY_PRESSURE_RETREAT`,
`LEASH_RETURN`, `STALEMATE_BREAK`, objective-pursuit `reach_location`) never include `target_id`
in their own `payload_set`, and `TaskUpdate.payload_set` **replaces** (does not merge into) the
entity's persisted `task.payload` (confirmed via `src/engine/patches.py:538`), so a decision that
doesn't set `target_id` correctly clears any stale one from a prior, unrelated engagement. The fix
is therefore a no-op by construction for every non-entity-tracking movement mode.

## What is deliberately NOT touched
- `scheduler.py`'s own `SystemCadence.strategic_intelligence` cadence gate — untouched. It serves
  many real, unrelated purposes (general AI decision-making load) and weakening it for all
  entities/all reasons would be a much larger, riskier change than this ticket's own narrow,
  well-evidenced fix.
- `find_intercept_position()`'s own prediction math — untouched. With live tracking now in place
  for the *movement execution* phase, the intercept-point prediction (used only for the specific
  `dist_to_target > 3` branch at *decision* time) becomes less load-bearing, since the pursuer no
  longer blindly walks to a stale prediction for many ticks in between.
- Any change to `resolve_attack()`/`calculate_damage()`/combat resolution itself.

## Rejected alternative
- **Weakening `scheduler.py`'s own cadence gate for actively-engaged entities** (e.g. bypass
  cadence entirely whenever `task.payload` has a real `target_id`): rejected — this would touch
  a shared, performance-critical, widely-exercised component (`TCK-20260512-PERF-STAGGERED-
  SCHEDULER`'s own explicit optimization), with real risk of reintroducing the "all entities spike
  every tick" problem that ticket was built to prevent, for a benefit already achieved more safely
  by the movement-routing-side fix.

## Verification plan
1. New unit tests in `tests/unit/movement/test_pursuit_target_refresh.py` — live-refresh works,
   fixed-point errands are unaffected, dead/missing `target_id` falls back safely to the stale
   snapshot without crashing.
2. Full scoped pytest: `tests/unit/movement/`, `tests/unit/tactical/`, `tests/unit/combat/`,
   `tests/unit/kernel/`, `tests/unit/strategic/`.
3. Real corpus re-verification (2000-tick live `Kernel.tick_once()` loop,
   `dungeon_crawl_seed42`/`urban_political_seed42`, corpus-default flags): the real, direct,
   falsifiable measure is the `is_attack_legal` rate for genuinely hostile pairs (the same metric
   this whole investigation chain has used throughout), not the aggregate kill count alone (a
   noisier, further-downstream metric also affected by other, still-open factors this ticket does
   not claim to fix).

## Acceptance-criteria map
| AC | How satisfied |
|---|---|
| Per-tick trace captured, included in investigation.md | Done |
| Trace distinguishes cadence starvation vs. prediction divergence | Done — resolved to a third, more precise mechanism (stale static target, confirmed via source read of scheduler.py + movement.py) |
| Concrete, evidence-backed recommendation | Done — fix implemented |
| If a fix lands: real corpus re-verification shows non-zero combat_damage/entity_killed | Partially — legal rate improved dramatically (0%→44% dungeon_crawl); aggregate kill count in this specific short run stayed flat, honestly disclosed |
