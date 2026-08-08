---
status: active
layer: mechanics
authority: P1
audience: agent
ticket_id: TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD
artifact_type: plan
tags: [progression, combat, simulation-quality]
---

# Plan — TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD

## Final outcome: chosen fix reverted — real cause is deeper, redirected to new tickets

The `xp_multiplier` fix below was implemented, re-tested against real corpus data at 4x and then
6x, and found insufficient even at 6x: zero *original*-population entities ever leveled up (max
real XP gain 60 against a 100 XP threshold). Per explicit user direction, the investigation
continued past "raise the multiplier further" and traced the real bottleneck: entities almost
never land a real ATTACK because `LegalityServiceV2.verify_attack_legality()` returns FALSE in
100% of a real 330-sample probe (`FRIENDLY_FIRE_ILLEGAL` 45%, `INSUFFICIENT_READINESS` 55%) — see
`investigation.md`'s own "Update: chosen fix reverted..." section for the full evidence chain
(hostile-scarcity, goal-competition, and dead-code-path hypotheses all ruled out first with real
data before reaching this one).

`git checkout -- src/engine/combat_rewards.py` cleanly reverted the multiplier change — **no net
`src/` change lands from this ticket.** The real fix now belongs to the newly-created, dedicated
follow-up `TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION`; a related but distinct
feature idea raised during the same investigation (personality/race-driven flee-vs-fight,
pursuit-prevents-escape) was filed separately as
`TCK-20260809-COMBAT-OUTCOME-FLEE-VS-FIGHT-PERSONALITY`. The below sections document the
originally-chosen (and since-abandoned) approach for the record.

## Scoping decision (resolved with the user)
Unified with `TCK-20260808-GROWTH-PACING-STALL-DETECTOR-IMBALANCE`, which is now closed as
superseded — this ticket is the single real fix.

## Real data gathered to choose the fix lever
A real, controlled 2000-tick probe (`urban_political`, seed 42) measured actual per-entity XP
accumulation, not just the population total: **80 total XP across only 5 entities; the single
best-performing entity accumulated 30 XP** (at the current `xp_multiplier=10` for MONSTER kills,
implying ~3 real kills). `LevelingService.get_xp_required(1) == 100` — even the luckiest real
entity in this run fell 70 XP short of leveling up even once.

## Chosen fix: raise `CombatRewardClassificationService`'s `xp_multiplier`, not the XP curve

Considered and rejected 3 alternatives:
- **Lower `LevelingService.get_xp_required()`'s curve**: this is a Certified-Level-1 Mechanics
  Bible formula (`docs/mechanics/01_entity_anatomy.md:93`, `XP_Required = int(100 * (level **
  1.5))`) — changing it means a real divergence entry, parity ledger update, and re-verification
  across every world's own level-progression assumptions. Higher blast radius than needed for the
  real, narrow bottleneck found (reaching level 2 at all, not the shape of the whole curve).
- **Raise real combat/kill frequency corpus-wide** (AI targeting, hostile density): the highest
  blast radius of the 3 — would ripple into COMBAT/AGENCY pillar grades unpredictably, the same
  category of risk `TCK-20260808-ROUTING-FLAG-FACTION-INFORMATION-RNG-COUPLING` found a real,
  unrelated regression from touching a shared pipeline path. Not chosen.
- **Add non-combat XP sources (quest completion)**: quest-completion dormancy is a separate,
  already-disclosed, unrelated gap (this session's own earlier findings) — bundling its own fix in
  here would violate this ticket's own established scoping discipline (see the sibling
  `ITEM-EQUIPPED`/`TRAIT-EXPRESSED` tickets' own splits). Not chosen.

**Chosen**: raise `xp_multiplier` in `CombatRewardClassificationService`
(`src/engine/combat_rewards.py:38,46,65,103`) — MONSTER 10→40, HERO 20→80 (preserving the existing
2:1 HERO:MONSTER ratio). Real, structural rate change (not the already-rejected "just tweak the
multiplier slightly" — this is a 4x change, chosen with a real margin over the observed 30 XP
top-entity accumulation, not a marginal nudge). Confirmed via direct read: `xp_gain =
defender.identity.evolution_level * classification.xp_multiplier`, and `gold_multiplier` is a
**separate** field (5/50, untouched) — no ECONOMY-pillar ripple. Confirmed via grep: `xp_multiplier`
is not documented anywhere in the Mechanics Bible (`docs/mechanics/`) — a tuning constant, not a
certified formula, so no divergence-doc/parity-ledger-for-the-formula-itself update is required
for the constant change alone (the parity ledger entry for THIS fix's own real effect, i.e.
level_up becoming reachable, is still required per Parity phase).

## Verification plan
Re-run the real 2000-tick `urban_political` probe post-fix, confirm: (a) `level_up` fires at least
once for the real top-performing entity, (b) `skill_unlocked`/`progression_conversion_applied`
correspondingly fire (cascading from the unblocked gate), (c) `capability_growth_stalled`'s own
fire count measurably drops relative to real growth events (the original sibling ticket's own
concern), (d) no COMBAT/ECONOMY pillar grade regression in the same run (gold_multiplier
untouched, kill *frequency* untouched — only reward *magnitude* per kill changed).

## Acceptance-criteria map
| AC | How satisfied |
|---|---|
| investigation.md confirms real producer/gate for each event | Investigate phase, already done |
| Scoping resolved with user before Plan | Done — unified |
| Fix re-verified against real 2000-tick corpus data | Verification plan above |
| Scoped pytest passes | Test phase |
