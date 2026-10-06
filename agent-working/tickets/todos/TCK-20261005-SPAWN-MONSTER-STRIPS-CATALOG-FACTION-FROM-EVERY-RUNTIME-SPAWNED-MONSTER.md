---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261005-SPAWN-MONSTER-STRIPS-CATALOG-FACTION-FROM-EVERY-RUNTIME-SPAWNED-MONSTER
phase: open
date: 2026-10-05
tags: [world, combat]
---

# TCK-20261005-SPAWN-MONSTER-STRIPS-CATALOG-FACTION-FROM-EVERY-RUNTIME-SPAWNED-MONSTER

## Title
`spawn_monster` hard-codes the `MONSTER_HORDE` legacy bucket for every runtime-spawned monster, so goblins,
orcs and bosses lose their catalog faction — and with it the hazard endurance the catalog declares for them

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
**This is the general defect the boss respawn loop was one symptom of.** Hypothesis raised by the planner,
confirmed by `rpg-implementer-2` across all 24 corpus worlds (10,000 ticks, seed 42, `audit_mode`, budget
disabled), recorded in the P0's `investigation.md`.

**The code** (planner-verified): `src/systems/world_systems/generator.py:61`, `spawn_monster`, builds every
spawned entity with `.identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE, ...)` — **the legacy
enum bucket, whatever the monster's `kind`**. No catalog `faction_id` is assigned.

**The measurement:** across every pre-fix run, **every runtime-spawned monster carries no catalog
`faction_id`**: 1,392 `world_boss`, 328 `orc_warrior`, 322 `goblin_warrior` (+6 other). **Only compiled
initial populations carry one.**

**Why it kills them.** `goblin_warband` is a catalog faction immune to `NATURAL_TERRAIN`
(`factions.yaml:43,51`), and both loop regions declare `hazard_kind: "NATURAL_TERRAIN"`
(`goblin_camp` 3.0, `bandit_road` 2.0). A goblin spawned at runtime is stripped of that faction, so it takes
drain it is declared to endure. On `frontier_living_world` a `goblin_warrior` at (110,38) and an `orc_warrior`
at (87,50) respawn every 300 ticks from t1 and die of drain — **68 deaths per loop world**, faction at death
= the `MONSTER_HORDE` bucket.

**Why this is legitimate to fix and the rejected option was not.** The owner's 2026-07 ruling
(`TCK-20260701-HAZARD-NATIVE-IMMUNITY`) forbids *deriving* endurance — from location, hostility, or by
granting it to the legacy bucket. This fix derives nothing: it **restores the catalog faction the monster
already has in content**, and with it the endurance that faction *declares*. A goblin is `goblin_warband`;
the spawn path simply forgot.

**Why P1 and not P0.** Owner decision 15 (`ENV-07`, trauma counts only violent-cause deaths) already stops
these drain deaths feeding trauma, so the trauma corruption is neutralised by a ratified rule. What remains is
live and wrong in fiction — runtime goblins dying of their own camp's terrain — and possibly wrong in
legality (see Assumptions).

**Bosses are explicitly NOT in scope.** A boss has **no** catalog faction to restore; giving it one is boss
feature design, deferred by owner decisions 10 and 14. This ticket fixes monsters whose catalog faction exists.

## Scope
1. For every `kind` `spawn_monster` is called with, establish the catalog faction it should carry. Report any
   kind with **no** catalog counterpart rather than inventing one (the orc's catalog counterpart is unchecked).
2. Restore the catalog `faction_id` on spawn for every kind that has one. Bosses excluded.
3. Re-measure, under `audit_mode` with the budget disabled: runtime goblin/orc hazard deaths per loop world
   (expect ~68 -> ~0 if endurance is restored), and per-region trauma with and without the fix.
4. Check every consumer of a spawned monster's faction — legality, hostility, appraisal, targeting — for
   behaviour that changes once it stops being the bucket. **Report changes; do not suppress them.**
5. Disabling-control test; divergence entry; parity-ledger update.

## Out of Scope
- World bosses (deferred, decisions 10 and 14).
- Granting any immunity to the `MONSTER_HORDE` bucket — **rejected by the 2026-07 ruling.**
- Retiring the legacy bucket. Separate, larger migration.

## Acceptance Criteria
- [ ] Every spawned `kind` mapped to its catalog faction, or reported as having none.
- [ ] Runtime-spawned monsters with a catalog faction carry it; bosses unchanged.
- [ ] Runtime goblin/orc hazard deaths re-measured as values, before and after.
- [ ] Every faction consumer checked; behaviour changes reported.
- [ ] Disabling control; divergence; parity ledger.
- [ ] **Re-baseline every figure that cites the 2,112 hazard deaths** (and the per-world death counts) from
      `TCK-20261005-REGIONAL-TRAUMA-IS-PRODUCED-BY-A-BOSS-RESPAWN-AND-HAZARD-DEATH-LOOP-NOT-BY-FIGHTING`. Once
      runtime goblins and orcs carry their catalog faction they stop dying of their own terrain, so those counts
      fall. `ENV-07` is unaffected, because drain deaths do not count toward trauma anyway, but any document
      quoting the totals as current must be updated (raised by `rpg-designer`).

## Related Tickets
- `TCK-20261005-REGIONAL-TRAUMA-IS-PRODUCED-BY-A-BOSS-RESPAWN-AND-HAZARD-DEATH-LOOP-NOT-BY-FIGHTING` (P0) —
  the loop this generalises.
- `TCK-20261005-TACTICAL-HOSTILE-LIST-AND-LEGALITY-DISAGREE-ABOUT-WHO-IS-HOSTILE` — **possible shared cause**,
  see Assumptions.
- `TCK-20260701-HAZARD-NATIVE-IMMUNITY` — the ruling that makes this the right fix and the bucket immunity the
  wrong one.

## Related Docs
- Bible 05's native-endurance clause; catalog `ENV-02`.

## Related Stored Artifacts
- The P0's `investigation.md` — victim faction at death vs catalog faction, all 24 worlds.

## Related Code Areas
- `src/systems/world_systems/generator.py:61` — `spawn_monster`, `faction=Faction.MONSTER_HORDE`.
- `data/content/social/factions.yaml` — catalog factions and their `hazard_immunities`.
- `src/engine/legality.py:252-272` — the `has_clean` probe and raw-faction fallback.

## Assumptions / Open Questions
- **Lane.** Lane B (world).
- **Hypothesis for the hostility ticket, not established:** `legality.py:252-272` consults `is_hostile_compat`
  only when a `has_clean` probe finds a perspective or relationship for the attacker's faction, and otherwise
  compares raw `identity.faction`. Every runtime monster shares `Faction.MONSTER_HORDE`, so two of them compare
  **equal** under the fallback. That would produce `FRIENDLY_FIRE_ILLEGAL` between monsters that are hostile in
  the catalog — plausibly some of the 751 verdicts that ticket is investigating. Test there, not here.
- Open: is `MONSTER_HORDE` meant to mean anything at all now, or is it purely a pre-catalog residue?

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
