---
status: active
layer: mechanics
authority: P2
audience: agent
ticket_id: TCK-20260808-PROGRESSION-GROWTH-ECONOMY-UNREACHABLE-IN-PRACTICE
artifact_type: investigation
phase: investigate
date: 2026-08-08
tags: [progression, combat, feature-flags]
---

# Investigation — TCK-20260808-PROGRESSION-GROWTH-ECONOMY-UNREACHABLE-IN-PRACTICE

## Method disclosure

All findings below come from direct, real execution: a live `Kernel` driven tick-by-tick
(`tools.calibrate_simq._load_world_state` + `Kernel.tick_once()`), with targeted monkeypatch
instrumentation on real engine methods (`ResourceTransactionResolver.resolve`,
`CombatResolutionSystem.resolve_attack`/`resolve_multi_attack`/`resolve_opportunity_attack`/
`resolve_skill_usage`/`resolve_aoe_attack`, `CombatActions.execute_attack`) to observe exactly
which code paths real gameplay exercises, plus direct before/after inspection of
`entity.identity.evolution_points`/`evolution_level` across 2000 real ticks. No hypothesis below
is asserted without a corresponding real run. Subagent spawning was unavailable this session
(200/200 cap) — all investigation was done via direct tool calls.

## Root cause (confirmed, not hypothesized)

**The dominant real combat-kill path in this corpus is not the `ATTACK` action — it's the
opportunity-attack-on-retreat mechanic in `src/engine/movement.py:193-204` — and that path's own
reward wiring silently drops 100% of the XP/gold it computes.**

### Step 1: `ATTACK` actions essentially never fire in practice

Instrumented `CombatActions.execute_attack` (the handler for the `ATTACK` action, reached via
`ActionRoutingPhase.route` → `SimulationDomainLogic.execute_action` → `ActionRouter.execute_action`)
across a real 2000-tick run of `sandbox_world` (seed 42, `SIM_OBS_MODE=NORMAL`):

```
TOTAL kills via resolve_attack: 0, ATTACK action calls: 0
```

Zero calls in 2000 ticks. Whatever AI-selection logic decides entity actions is not, in this
world/config, choosing `ATTACK` as a deliberate action often enough to matter (out of scope to
root-cause the action-selection policy itself here — see Related Tickets).

### Step 2: real deaths happen through a completely different path

Instrumenting all 5 `CombatResolutionSystem.resolve_*` methods on the same run:

```
resolve_multi_attack: 560 calls
resolve_multi_attack:DEFEAT: 9
```

All engine-level call volume and all real outcome resolutions in this run went through
`resolve_multi_attack` — never `resolve_attack`, `resolve_opportunity_attack`,
`resolve_skill_usage`, or `resolve_aoe_attack`. Tracing the single call site
(`src/engine/movement.py:193-204`, inside `MovementSystem.resolve_move`):

```python
if engaged_hostiles and not skip_oa:
    entities = getattr(state_or_context, 'entities', {})
    attackers = []
    for eid in engaged_hostiles:
        attacker = entities.get(eid)
        if attacker: attackers.append(attacker)

    if attackers:
        combat_update = CombatResolutionSystem.resolve_multi_attack(
            attackers, entity, state_or_context, is_opportunity_attack=True, is_lethal=False
        )
        updates[entity.id] = EntityUpdate(entity_id=entity.id, combat=combat_update)
```

This is the "opportunity attack" triggered when `entity` (the subject of `resolve_move`, i.e. the
entity that is moving/retreating) tries to move away while `engaged_hostiles` are attached to it.
`attackers` are the hostiles; `entity` is the one taking the hit and dying. This is a real,
frequently-exercised mechanic (560 calls / 2000 ticks in this one world) — not a rare edge case.

### Step 3: the reward is computed correctly, then discarded — two separate defects in the same call site

`resolve_multi_attack` (`src/engine/combat.py:328-434`) computes `xp_gain`/`gold_gain` and builds
`resource_transfers` identically to `resolve_attack`'s own logic (line 389:
`if not alive and defender.combat.alive:` → `xp_gain = defender.identity.evolution_level *
classification.xp_multiplier`, wrapped into a `ResourceTransferIntent(source_kind="COMBAT",
xp_reward=xp_gain, ...)`), returned on `CombatUpdate.resource_transfers`. **This part is correct
and not the bug.**

The bug is entirely in the caller (`movement.py:204`):

```python
updates[entity.id] = EntityUpdate(entity_id=entity.id, combat=combat_update)
```

1. **Wrong beneficiary.** `combat_update.resource_transfers` was built to reward whoever
   defeated `entity` — i.e. the `attackers`. But it is attached to `entity`'s own `EntityUpdate`
   (`entity` here is the victim, not an attacker). Even in the best case this would credit the XP
   to the wrong side of the fight.
2. **Never lifted to where it would be read at all.** `ResourceTransactionSystem.resolve_all()`
   (`src/engine/economy.py:58`) only reads the **top-level** `EntityUpdate.resource_transfers`
   field (`if not ent_upd.resource_transfers: continue`). `movement.py:204` never extracts
   `combat_update.resource_transfers` out of the nested `CombatUpdate` — contrast with the
   correct pattern in `src/engine/domain/combat_actions.py:62-67`
   (`CombatActions.execute_attack`), which explicitly does
   `resource_transfers=combat_up.resource_transfers` on the returned `EntityUpdate`. Confirmed by
   direct grep that nothing in the codebase ever reads `.combat.resource_transfers` back out —
   `grep -rn "\.combat\.resource_transfers" src/` returns zero matches. The reward is written into
   a dead field and never read by anything, on every single occurrence.

Combined with Step 1 (the `ATTACK` action path — the one code path that *does* lift
`resource_transfers` correctly — essentially never fires), the result is: **the only combat path
that reliably produces kills in this corpus is also the only one whose reward output is
orphaned.** This is sufficient on its own to explain the corpus-wide `growth_trajectory` ≈ 0
finding — it isn't that kills are simply rare (9 real deaths in 2000 ticks in this one world is
non-trivial), it's that literally none of them can produce XP regardless of volume.

### Secondary, related gap: `is_lethal=False` is hardcoded on this path too

`movement.py:202` hardcodes `is_lethal=False` for the opportunity-attack call. In
`resolve_multi_attack`, `outcome = "KILL" if is_lethal else "DEFEAT"` (line 383) — so this path
can *never* produce `outcome_kind == "KILL"`, only `"DEFEAT"`. `src/observability/
event_shapers.py:157` gates `entity_killed` (and `hero_death_unrecorded`) specifically on
`outcome_kind == "KILL"` — so even independent of the resource_transfers bug, this entire class of
real deaths is invisible to the `entity_killed` event, and to any lifecycle-score/SimQ signal that
relies on it. Whether `is_lethal=False` here is itself intentional (e.g. "opportunistic strikes
during a retreat shouldn't be outright kills, only defeats/knockdowns") or a second defect is a
Plan-phase design decision, not resolved here — flagged as an open question, not assumed either
way.

## Investigate scope item 1: `RewardPatch`/`EvolutionSystem` dual-consumer question — RESOLVED, not a bug

Both consume `ent_upd.reward.xp_gain`, but cleanly separated in practice:

- `src/engine/evolution.py::EvolutionSystem.evaluate()` runs as pipeline phase `evolution`
  (position 24, after `resource_transactions` at 23). It reads `ent_upd.reward.xp_gain` into its
  `raw_delta` consolidation (line 39), then **zeroes it** before returning its own updated
  `EntityUpdate` (lines 79-82: `if ent_upd.reward and ent_upd.reward.xp_gain != 0: new_reward =
  replace(ent_upd.reward, xp_gain=0)`, written back at line 146).
- `src/engine/patches.py::RewardPatch` is constructed later, during `ApplyPath.apply_generation`'s
  per-entity patch-building pass (`patches.py:698-700`, live/real code — confirmed via grep it's
  reachable, not dead), from the **same, already-evolution-processed** `EntityUpdate.reward`
  field. By the time this runs, `reward.xp_gain` is already 0 (if `EvolutionSystem` consumed it
  this tick), so `RewardPatch.apply()`'s own `if self.reward and self.reward.xp_gain > 0:` guard
  never re-triggers `LevelingService.process_progression()` for the same XP. Confirmed: **not a
  double-application bug** — `EvolutionSystem` and `RewardPatch` are cleanly sequenced consumers
  of the same field, not competing ones.

## Investigate scope item 2: real kill rate — measured directly

`sandbox_world`, seed 42, 2000 ticks, `NORMAL` mode: **9 real deaths** (`resolve_multi_attack`
DEFEAT outcomes), **0** via the `ATTACK` action path. This is the real, current measurement
(supersedes the ticket's own initial "kills specifically... are rare" framing — kills are not
categorically rare, they are structurally unrewarded on the path that actually produces them).

## Investigate scope item 3: quest completion rate — re-confirmed with fresh data

Fresh real runs, 1000 ticks each, `NORMAL` mode, this session (2026-08-08), `dropped_count=0` on
both:

| World | quest_* events | combat_damage | combat_initiated | xp_granted/level_up/skill_unlocked |
|---|---|---|---|---|
| `sandbox_world` | **0** | 128 | 14 | **0** |
| `urban_political` | **0** | 48 | 12 | **0** |

Matches `TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE`'s historical finding — quest
completion is still genuinely zero corpus-wide, not stale. Root-causing quest dormancy itself
remains out of scope per this ticket's own Out of Scope section (substantial enough for its own
follow-up ticket).

## Docs Requiring Update

None. — no Mechanics Bible formula changes are implied by this finding (the XP/threshold formulas
themselves are correct and already documented; the bug is a wiring defect in how a reward gets
attributed and propagated, not a change to any documented law). If Plan decides to also change
`is_lethal=False`'s semantics on the opportunity-attack path, that would newly touch
`docs/mechanics/02_combat_laws.md`'s Victory Outcomes section — deferred to Plan/Implement, not
assumed here.

## Real code areas confirmed relevant (supersedes ticket's original list)

- `src/engine/movement.py:193-204` — **the real bug site**: wrong-entity attribution + missing
  `resource_transfers` lift, inside `MovementSystem.resolve_move`'s opportunity-attack branch.
- `src/engine/combat.py:328-434` (`resolve_multi_attack`) — reward computation itself is correct;
  confirms this is a caller-side bug, not a combat-math bug.
- `src/engine/domain/combat_actions.py:62-67` (`CombatActions.execute_attack`) — the CORRECT
  reference pattern for lifting `resource_transfers` out of a nested `CombatUpdate`, to mirror in
  the fix.
- `src/engine/evolution.py:79-82`, `src/engine/patches.py:588-598,698-700` — dual-consumer
  question, resolved not-a-bug.
- `src/engine/quests.py`, `src/engine/pipeline_phases/quest_opportunity_rewards.py` — quest path,
  re-confirmed still dormant, not touched by this ticket's fix.
