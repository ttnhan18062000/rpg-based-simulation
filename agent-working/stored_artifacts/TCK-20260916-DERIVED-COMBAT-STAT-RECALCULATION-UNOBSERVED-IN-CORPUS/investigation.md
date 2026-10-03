---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS
artifact_type: investigation
tags: [progression, simulation-quality, testing]
---

# Investigation — TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS

## The discriminating measurement (run first, per this ticket's own instruction)

Instrumented `CombatRewardClassificationService.classify_defeated_target` (the real gate on any
XP grant existing at all — `src/engine/combat.py`'s `if new_hp <= 0:` branch) with a call counter,
and read `identity.evolution_points`/`evolution_level` directly from final state. Ran the same
three real, compiled, catalog-driven corpus worlds the original ticket used
(`crowded_frontier`, `quest_dense_frontier`, `hero_guild_routing`), seed 42, 1000 ticks each,
through the real `Kernel.tick_once()` loop — not a synthetic scenario.

| World | Entities (final) | Kills | XP granted (total) | Max single-entity XP held |
|---|---|---|---|---|
| `crowded_frontier` | 42 | 10 | 100 | 50 (one entity, 5 kills) |
| `quest_dense_frontier` | 9 | 0 | 0 | 0 |
| `hero_guild_routing` | 35 | 3 | 30 | 20 (one entity, 2 kills) |

Result: **meaningful, nonzero, correctly-computed XP** (10 per level-1 monster kill, matching
`defender.identity.evolution_level * 10` exactly per `docs/mechanics/attribute_progression_contract.md`),
sitting **below the level-2 threshold (100 XP)** in every case — the busiest single entity across
all three worlds reached only 50. Per this ticket's own discrimination rule, this result points at
pacing, not a broken chain: real XP is landing.

None of the entities present at world-compile time (`was_present_at_start: True`) changed
`evolution_level` at all across any of the three 1000-tick runs. Entities with high
`evolution_level` (10–15) in the final state are all newly-spawned entities not present at tick 0
(their level is a compile-time property of the archetype that spawned them later, not a level they
earned during the run).

## A false lead, caught and corrected before reporting

A first attempt to determine *why* XP never crosses the threshold constructed a positive control by
calling `ApplyPath._apply_entity_update()` directly with `EntityUpdate(identity=IdentityUpdate(evolution_points_delta=500))`
(the same field combat's real reward path writes) against a fresh level-1 entity. Result: XP
accumulated to 500, but `evolution_level` stayed at 1 — no level-up fired. A second control using
`EntityUpdate(reward=RewardUpdate(xp_gain=500))` (the field the quest-reward path writes) correctly
produced `evolution_level=2`, `evolution_points=400` (500 carried over minus the 100 threshold).

This looked like a genuine wiring gap: `IdentityPatch.apply()` (`src/engine/patches.py:206-215`)
applies `evolution_points_delta` with a plain `ep += u_id.evolution_points_delta` and **no**
threshold check anywhere in that patch. The only code that calls
`LevelingService.process_progression()` — the sole evaluator of the level-up threshold — is
`RewardPatch.apply()` (`src/engine/patches.py:626-649`), gated on `self.reward.xp_gain`, which is
populated only by the two quest-reward call sites (`src/engine/quests.py:213`,
`src/engine/pipeline_phases/quest_opportunity_rewards.py:87`) — never by combat
(`src/engine/combat.py`'s kill-reward construction only ever sets `xp_reward=`, never
`reward_upd=`).

**This reading was wrong, and specifically wrong because the control tested the wrong layer.**
`ApplyPath._apply_entity_update()` applies a single `EntityUpdate` in isolation — it never runs
`src/engine/evolution.py::EvolutionSystem.evaluate()`, a real, unconditional pipeline phase
(`src/engine/pipeline.py:381`, `run_phase("evolution", ...)` — no feature-flag argument) that runs
**after** `resource_transactions` (`:377`, where combat's kill-reward XP lands in
`ent_upd.identity.evolution_points_delta`) and **before** the identity/reward patches apply.
`EvolutionSystem.evaluate()` explicitly consolidates `ent_upd.identity.evolution_points_delta` and
`ent_upd.reward.xp_gain` together (`src/engine/evolution.py:32-36`), evaluates the threshold in a
loop that can fire multiple level-ups in one call (`:55-62`, unlike `LevelingService._execute_level_up`'s
own single-fire-per-call limit), and **unconditionally rewrites** `evolution_level_set` back into
the entity's own update (`:136-144`) — regardless of whether combat or quests supplied the XP.

Redoing the control through the real pipeline (a real `Kernel.tick_once()`, staging a goblin at
`evolution_points=95` who then force-kills an orc worth 10 XP) settled it decisively:

```
Before: goblin level=1 xp=0        (then staged to xp=95 pre-tick)
Before: orc hp=120 level=1
After 1 tick: goblin level=2 xp=5
After 1 tick: orc alive=False
```

`95 + 10 = 105`, threshold for level 2 is `int(100 * 1**1.5) = 100`, carry-over `105 - 100 = 5` —
exactly matching the documented formula
(`docs/mechanics/attribute_progression_contract.md`'s own worked example shape). **The
combat-XP-to-level-up chain is real, correctly wired, and fires correctly the moment enough XP
exists** — this is not a wiring gap.

This false lead is recorded here in full, not quietly dropped, per this epic's own standing
discipline of surfacing a wrong hypothesis before it becomes a reported verdict (the same
discipline that caught two real detector bugs in
`TCK-20260916-MECHANISM-STATE-CALLER-MISMATCH-DETECTION` and a false verification verdict in
`TCK-20260916-MECHANISM-ORPHAN-STATE-BATCH-VERIFICATION`).

## Verdict: content-composition / pacing gap, not a wiring gap

Per this ticket's own scope item 3 acceptance criterion (state plainly which family this is, with
evidence either way):

- The XP-to-level-up chain is directly confirmed correct (positive control above).
- Real corpus combat volume never comes close to the level-2 threshold: 0–10 kills per 1000-tick
  world, 10 XP per typical (level-1) kill, ~10 kills needed for one level-up, and the busiest single
  entity across all three worlds accumulated only 5 kills (50 XP) — half of one threshold, in the
  entire tested window.
- This matches the `camp` family exactly
  (`docs/plans/world_composition_precondition_gap_finding.md`): correct, wired code, defeated by
  real-world data/volume, not a defect in the mechanism itself.
- The low kill volume itself is very likely downstream of the already-ticketed, evidence-backed
  `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION` (low cross-faction combat volume
  generally, root-caused there to a region-name resolution gap in at least one corpus world) — not
  independently re-investigated here, since that's already a real, separately-scoped ticket.

This explains and supersedes the original "zero of 75 entities ever triggered `stats_dirty`"
finding precisely: `stats_dirty` (`src/engine/apply.py`) is gated on attribute/equipment/level
changes, and the only way combat XP produces one of those is a level-up — which the corpus's own
combat volume never produces within the tested window, for a real content/pacing reason, not
because the code path is broken.

## `true_power()`'s `evolution_level` exclusion (AC #5)

Flagged, not resolved, per the original ticket's own scope. The follow-up ticket
(`TCK-20260917-XP-LEVEL-UP-THRESHOLD-VS-CORPUS-COMBAT-VOLUME`) carries this forward in its own
Related Docs section so it isn't lost once this ticket is historical.

## Registry and consumer-artifact propagation

- `registries/mechanisms.yaml`: `xp_leveling` moved `done` → `partial` with a `verified` block
  (instrument: scenario, verdict: observed) recording both the positive-control confirmation and
  the corpus-pacing caveat. `evolution` gained `implemented_by: [src/engine/evolution.py::EvolutionSystem]`
  and its own `verified` block (the code that was actually positive-controlled).
  `progression_conversion` gained a `verified` note connecting its own `ALLOCATE_AP` AP-spend
  branch to the same pacing scarcity (AP is granted by level-ups, which are now confirmed rare from
  combat). `action_pacing_readiness`'s own note — which explicitly named this ticket as "filed, not
  yet root-caused as content-gap vs wiring-gap" — is updated to close that open thread: pacing, not
  wiring, so its own `partial` state and `observed` gate verdict do not need to change.
- `docs/brainstorm/rpg_feature_atlas.html`: `xp_leveling`'s mapped badge (`entity-profile#10`,
  "XP, Attribute Points, Breakthrough & Mastery") regenerated via
  `tools/mechanism_registry/mechanism_atlas_regenerate.py` from `done` to `partial` `cls`. Its own
  badge *label* ("XP/Classes done") and the card's longer `desc` prose are left untouched
  deliberately — that tool's own documented contract touches only the `cls` leaf value, reserving
  label/prose review for the not-yet-built `TCK-20260916-ATLAS-CARD-DESCRIPTION-EFFECT-CAVEAT-AUDIT`
  (now sequenced inside `tickets/todos/mechanism-verification/`). Flagged here as a concrete,
  ready-made example for that ticket rather than hand-edited now.
- `docs/brainstorm/simulation_capabilities.html`: re-checked via
  `mechanism_capabilities_regenerate.py --check` — zero drift, no mapped card cites `xp_leveling`
  or `evolution` directly.
- No parity ledger change: the code matches the Mechanics Bible's documented formula exactly (the
  positive control reproduces the doc's own worked example bit-for-bit); this is a registry-level
  verification finding about corpus-play frequency, not a Bible/code divergence.

## Not investigated in this pass (stated plainly, not left ambiguous)

- `attributes_biology` was not directly traced in this investigation — the only touchpoint seen was
  `EvolutionSystem.evaluate()`'s own `well_rested_until` XP multiplier check, which is too narrow to
  stand in for verifying the whole mechanism. No `verified` block was added for it; it stays
  unverified rather than receiving an unearned one.
- Why cross-faction combat volume is low in general was not re-investigated — that is
  `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`'s own scope, already filed.
- Whether the pacing conclusion holds at a longer tick count (the original ticket's own open
  question) was not re-checked here either; 1000 ticks was reused to match the original
  measurement's own window.
