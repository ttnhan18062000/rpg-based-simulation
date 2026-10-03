# Investigation — TCK-20260911-CAMPAIGN-SURVIVOR-EARNED-PROGRESSION-NOT-CARRIED-FORWARD

## Root cause: the missing mechanism is carry-forward, not recompute

The ticket, as originally filed, framed this as "the recompute path never fires at reconstruction
time" and proposed calling `SkillScalingService.get_effective_stats()` once at reconstruction as a
narrow, hotfix-tier fix. Traced `get_effective_stats()` → `LevelingService.
recalculate_combat_stats()` (`src/progression/leveling.py:76-`) in full before implementing
anything: combat stats are **not** a function of `evolution_level` at all.

```
max_hp   = base_hp   + (attributes.vitality * 2) + (attributes.endurance * 0.5) + gear_hp
atk      = base_atk  + (attributes.strength * 0.5) + gear_atk
def_stat = base_def  + (attributes.vitality * 0.3) + gear_def
evasion  = base_evasion + (attributes.agility * 0.001) + gear_evasion + skill_passive
```

No `level` parameter anywhere in the chain. Level only enters indirectly: leveling up grants
`unspent_ap_delta` (5 AP/level, `LevelingService._execute_level_up()`) that gets spent on specific
attributes via a separate, path-dependent mechanism. `EntityCarryForward` did not carry
`AttributeComponent`. So calling the recompute function at reconstruction with default (level-1)
attributes would have produced stats close to the bare default regardless of the survivor's real
carried level — the recompute function had nothing real to recompute from. Confirmed this via a
real counterfactual (see below), not assumed.

## Real, direct confirmation (counterfactual, not code-read reasoning alone)

Per this ticket's own AC. Captured the pre-fix bug via a genuine counterfactual: saved this
ticket's own implementation diff (`git diff` of `orchestrator.py`/`state.py`), reverted both files
to `origin/main`'s HEAD (`git checkout HEAD -- <files>`), ran the exact test scenario
(`test_reconstructed_survivor_with_no_carried_progression_gets_default_attribute_stats_not_bare_combat_defaults`,
a level=20 survivor with no carried attributes/equipment), confirmed it produced
`combat.max_hp=100, atk=10, def_stat=5` — `EntityState`'s own bare `CombatComponent` defaults,
identical for a level-20 and a level-1 entity. Then restored the implementation via `git apply` on
the saved diff and re-ran: the same scenario now produces `max_hp=112, atk=12, def_stat=6` — the
correct `get_effective_stats()` output for default (level-1-equivalent) attributes, proving the
recompute call now genuinely executes at reconstruction (though a survivor with real carried
attributes produces materially higher numbers — see the dedicated test below).

## Full earned-progression audit (per peer review's explicit request)

Every field checked against its real mid-episode mutation path (`src/engine/patches.py`, the
leveling/veterancy/breakthrough services), not guessed from its name — the same standard of
evidence this whole audit arc has used throughout:

| Field | Confirmed via | Direct `get_effective_stats()` input? |
|---|---|---|
| `AttributeComponent` (9 fields) | Dominant driver of `max_hp`/`atk`/`def_stat`/`evasion` (formula above) | Yes |
| `unspent_ap` | `LevelingService._execute_level_up()` grants `+5`/level, banked | No — real earned progression, lost if not carried |
| `learned_skills` | Live-mutated via `IdentityUpdate.learned_skills`, not a static archetype default | Yes — passive skill bonuses |
| `active_breakthroughs` | Live-mutated via `patches.py`; consumed by `BreakthroughService.apply_bonuses()` | Yes |
| `class_id` | Live-mutated via `class_id_set`; defaults to `"NOVICE"` otherwise; consumed by `ClassTierService.apply_bonuses()` | Yes |
| `veterancy_points`/`veterancy_rank` | Accumulated via `VeterancyService.process_points()`, wired live through `patches.py`/`apply.py` | No — see finding below |
| `known_recipes` | Real, player-earned progression by the same test as the above | No (crafting-relevant, not combat) |

**Veterancy finding, filed separately**: `VeterancyService.get_stat_multiplier(rank)` — the
function that would apply rank as a real +5%/rank combat bonus — has zero real callers anywhere
in `src/`. Veterancy accumulates correctly but never affects combat stats today. Filed as
`TCK-20260912-VETERANCY-STAT-MULTIPLIER-NEVER-APPLIED` (P2), not this ticket's to fix. Carrying
`veterancy_points`/`veterancy_rank` forward is still correct regardless — preserving real earned
state is right even while its downstream mechanical application is separately incomplete.

**Checked and explicitly excluded** (recorded, not silently omitted, per peer review — an implicit
decision a later reader can't distinguish from an oversight is the same failure this whole batch
keeps finding from the other direction):
- `craft_target` — transient in-progress intent, not accumulated progression.
- `territory_maturity` — confirmed via `src/world/creature_territory.py` to be a creature/NPC
  territorial mechanic, not survivor/hero-relevant.
- `wounds`/`scars` — **a deliberate divergence, not an oversight.** Scars are arguably earned too
  under the "retains what it earned" invariant, but reconstruction intentionally keeps them reset
  to fresh (`V2EntityBuilder().build()`'s own defaults) — survivors are narratively recovered
  between episodes. Recorded explicitly (both in the ticket and via a dedicated test) so a future
  reader sees a documented choice, not a gap.
- `cooldowns` — tick-scoped transient state, meaningless across an episode boundary.

## Implementation

`EntityCarryForward` (`src/domains/campaigns/state.py`) extended with `attributes` (dict, all 9
`AttributeComponent` fields), `unspent_ap`, `learned_skills`, `active_breakthroughs`, `class_id`,
`veterancy_points`, `veterancy_rank`, `known_recipes` — following the exact pattern the identity
ticket already established (unconditional, not gated by a `carry_forward_rules` flag; empty/default
for pre-existing records). `to_dict()`/`from_dict()` extended symmetrically, sets sorted for
determinism matching `traits`' own precedent.

`_extract_entity_carry_forwards()` populates the new fields from `entity.attributes`/
`entity.identity.*`. `_build_initial_state()`'s survivor-reconstruction branch: extended the
`V2EntityBuilder(eid)....identity(...)` call with the 7 new identity fields, added a
`.attributes(...)` call (values pass through as `None` when `cf.attributes` is empty — the
builder's own established no-op-on-None pattern, so pre-existing records fall back to component
defaults exactly like every other field in this block already does). After equipment resolution,
calls `SkillScalingService.get_effective_stats()` — the same function the live tick-time
`stats_dirty` path in `apply.py` uses, unmodified — using the survivor's real carried attributes,
equipment, learned_skills, traits, class_id, and active_breakthroughs, and applies the result to
`combat`. `hp` is explicitly set to the newly-derived `max_hp` (full health), consistent with the
wounds/scars-reset framing (recovered between episodes, not left at a stale default).

## Test evidence

Per peer review's explicit acceptance note: an equipment-only or attributes-only test would pass
on a half-fix. `test_reconstructed_survivor_combat_stats_reflect_both_earned_attributes_and_carried_equipment`
uses a survivor with both (`iron_sword`/`iron_plate` equipped, `strength=50`/`vitality=50`/
`endurance=20` attributes) and asserts **exact** expected values (`max_hp=210`, `atk=45`,
`def_stat=35`), computed independently from the documented formula — only possible if both
contributions are present and correctly summed. A wrong value on either axis (e.g. `35` for
`atk` would mean only gear landed, `20` would mean only attributes) is called out explicitly in
each assertion's own failure message.
