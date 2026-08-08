---
status: active
layer: mechanics
authority: P1
audience: agent
ticket_id: TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD
artifact_type: investigation
tags: [progression, combat, simulation-quality]
---

# Investigation — TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD

## Update: chosen fix reverted, real root cause traced deeper — split into new tickets

Per explicit user decision, this ticket's own scoping was unified with
`TCK-20260808-GROWTH-PACING-STALL-DETECTOR-IMBALANCE` (closed as superseded). The chosen lever
(raise `CombatRewardClassificationService`'s `xp_multiplier` 4x, then 6x) was implemented and
**empirically re-tested against real corpus data** — and found insufficient: even at 6x, the
maximum real XP gain among the *original* population (not newly-spawned boss entities, which a
first, flawed probe had conflated with genuine leveling) across a full 2000-tick `urban_political`
run was **60 XP against a 100 XP level-2 threshold — zero original entities leveled up.**

Per further user direction ("keep going, finish tracing the real bottleneck"), traced the real
mechanism instead of continuing to escalate the multiplier arbitrarily:

1. **Not hostile scarcity**: a real probe found hostiles within `radius=10.0` in 100% of sampled
   ticks (50/50) for the original population.
2. **Not goal-competition failure**: `CombatEngageScorer`'s own `GoalKind.COMBAT_ENGAGE` wins the
   goal competition in 325/330 real samples (98.5%) when available — entities are actively trying
   to engage hostiles, not choosing other goals instead.
3. **Not a dead code path**: `tactical.py`'s own real "ATTACK" branch routes through
   `ActionRouter` → `CombatActions.execute_attack()` → `CombatResolutionSystem.resolve_attack()`
   with a real, non-None `context` at the real pipeline call site — the wiring is intact.
4. **The real, decisive cause**: `is_attack_legal` (`tactical.py:397`, via
   `LegalityServiceV2.verify_attack_legality()`) was **FALSE in 100% of 330 real samples**,
   splitting into `ReasonCode.FRIENDLY_FIRE_ILLEGAL` (150, 45%) and
   `ReasonCode.INSUFFICIENT_READINESS` (180, 55%). Because it's always false, entities perpetually
   `MovementMode.PURSUE` their target and never emit a real ATTACK — and since PURSUE is the
   opposite of the egress movement that triggers the corpus's other real kill mechanism
   (opportunity-attack), they never land a hit through that path either.

**This is the real root cause of the low corpus-wide kill rate** this whole session's growth/
progression investigation chain has been building on — a genuine combat-legality mechanism gap,
not a reward-magnitude or XP-curve problem. Given the scope and depth this required, per explicit
user guidance ("create tickets for the combat only, study deeply"), the real fix is **not**
implemented in this ticket — reverted the multiplier change (`git checkout -- 
src/engine/combat_rewards.py`, confirmed clean) and filed the real, dedicated follow-up:
`TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION`. A related, distinct feature idea
raised during this same investigation (personality/race-driven flee-vs-fight outcomes,
pursuit-prevents-escape) was filed separately:
`TCK-20260809-COMBAT-OUTCOME-FLEE-VS-FIGHT-PERSONALITY`.

## Real XP curve, confirmed

`LevelingService.get_xp_required(level)` (`src/progression/leveling.py:10-18`):
`int(100 * (level ** 1.5))` — reaching level 2 from level 1 requires **100 XP**. Real per-kill XP
grant (established earlier this session, `TCK-20260808-GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX`):
10 XP per MONSTER kill. Real corpus-wide kill rate: 3-5 XP-granting kills population-wide per
2000 ticks. At that rate, reaching even level 2 requires roughly 20-33x the real observed kill
volume of an entire 2000-tick run — `level_up` is not merely rare, it is essentially unreachable
at any tick length this session has tested (up to 5000 ticks, the established long-run tier).

## `attribute_changed`'s other real producers — traced, not assumed zero

Found 3 additional real producers beyond `EvolutionSystem`'s own level-gated non-HERO branch:

1. **`AllocateAttributeAction.execute()`** (`src/actions/attributes.py:14-47`) — a real "spend AP
   on an attribute" action. **Also gated by `unspent_ap`** (line 17-18:
   `if entity.identity.unspent_ap <= 0: return EntityUpdate(entity_id=entity.id)`) — the exact
   same field `EvolutionSystem`'s own level-gated block is the only real producer of. This
   **reinforces**, not contradicts, the original shared-cause finding: it's a second real consumer
   blocked by the same upstream gate, not an independent cause.
2. **`CoreActions.execute_allocate_ap()`** (`src/engine/domain/core_actions.py:146-172`) — same
   pattern: requires `entity.identity.unspent_ap >= amount`, otherwise returns a no-op
   `INSUFFICIENT_AP` failure. Same shared cause.
3. **`compute_elder_attribute_update()`** (`src/domains/demographics/cohort.py:68-107`) — a real,
   genuinely *independent* producer (age-based attribute decay for "elder" entities), gated by
   `get_age_bracket(age_ticks) == "elder"`, which requires `age_ticks >= 7000`
   (`src/domains/demographics/cohort.py:50-65`, spec `TCK-20260619-E52C-AGE-ADVANCEMENT`) — a
   threshold that exceeds even this session's own established long-run tier (5000 ticks). **Also
   confirmed to have zero real callers anywhere in `src/`** (direct grep) — dead-but-correct code,
   the same "built but never wired" pattern found in the sibling
   `TCK-20260808-ITEM-EQUIPPED-DORMANT-PATH-INVESTIGATION`'s own `auto_equip()` finding. Disclosed,
   not fixed here — wiring it in, and whether 7000+ ticks is ever a realistic real-play window,
   are real design questions outside this ticket's own scope.

**Conclusion**: `attribute_changed`'s dormancy is now more completely explained — 2 of its 3 extra
producers share the exact same root cause as `skill_unlocked`/`progression_conversion_applied`
(the `unspent_ap`/`levels_gained` gate), and the 1 genuinely independent producer is real but
separately unreachable (age threshold) AND separately dead (no caller) — two distinct reasons
compounding, neither fixed by this ticket's own scope.

## Re-checked `TCK-20260701-SIMQ-EMIT-PROGRESSION`'s own AC claim — does not hold up today

That ticket's own Acceptance Criteria claimed "dungeon_crawl 200-tick run produces > 0
skill_unlocked events." Re-ran this exact scenario for real, today:
`tools/calibrate_simq.py --name dungeon_crawl --seed 42 --ticks 200 --profile dungeon_crawl` →
**`PROGRESSION grade=C norm=+0.0000 events=0`** — zero real PROGRESSION-pillar events of any kind,
directly contradicting that historical claim. Given `calibrate_simq.py`'s own default synthetic
entity count (10, not the real compiled `dungeon_crawl` world's own population), the most likely
explanation is that ticket's own 2026-07-01 AC was verified against a narrow/synthetic calibration
scenario rather than real corpus gameplay — not necessarily a regression since that date. Not
fully resolved (would require git-archaeology into that ticket's own real test artifacts, out of
this ticket's proportionate scope) — disclosed as a real, current, re-confirmed data point rather
than left unchecked.

## Docs Requiring Update
- `docs/audits/D21_entity_lifecycle_foundation_layers.md`: record the `attribute_changed`
  producer-tracing results and the re-confirmed empirical zero-event finding.
