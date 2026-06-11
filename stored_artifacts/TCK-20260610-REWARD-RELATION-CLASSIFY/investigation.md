---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260610-REWARD-RELATION-CLASSIFY
artifact_type: investigation
tags: [reward, relation, classify]
---

# Investigation — TCK-20260610-REWARD-RELATION-CLASSIFY

## Problem

`CombatRewardClassificationService.classify_defeated_target()` (combat_rewards.py:86):
```python
defender_faction = Faction(defender.identity.faction)
if defender_faction == Faction.MONSTER_HORDE:
    return cls._HOSTILE_CREATURE_CLASSIFICATION  # source="hostile_relation"
```
This hardcode means ANY entity with Faction.MONSTER_HORDE is classified as a hostile reward source
regardless of whether the combat context was actually hostile.

## FactionSemanticsService Interface

`src/content_semantics/faction.py`:
- `FactionSemanticsService.is_hostile_compat(source, target, context=None)` — tries catalog relation
  projection first (perspectives + faction_relationships), falls back to legacy bucket hostility
  (`is_hostile()`). This is the same path used by combat legality checks.
- `get_faction_id_str(entity)` — returns faction ID string from identity.properties["faction_id"]
  or identity.faction enum name (lowercased). For Faction.MONSTER_HORDE → "monster_horde".
- `get_faction_semantics_service()` — process-level singleton, lazy-loads catalog once.

## Legacy Bucket Fallback

For legacy enum-based entities (no catalog entries for their faction IDs):
- `is_hostile_compat("hero_guild", "monster_horde")` → falls back to `is_hostile()` →
  `get_legacy_faction_bucket()` → HERO_GUILD vs MONSTER_HORDE → True
- `is_hostile_compat("monster_horde", "hero_guild")` → True (same: bucket_a == MONSTER_HORDE → return != check)
- `is_hostile_compat("neutral", "hero_guild")` → False (NEUTRAL vs HERO_GUILD → no MONSTER_HORDE → False)

## Behavior Change in HERO_KILL path

Current: attacker=MONSTER_HORDE, defender=HERO_GUILD → step 1 checks defender faction (HERO_GUILD ≠ MONSTER_HORDE) → falls through to EntityRole.HERO → HERO_KILL.

New: step 1 calls `is_hostile_compat("monster_horde", "hero_guild")` → True → HOSTILE_CREATURE.

**This is correct behavior**: a monster getting a "hero kill" reward with rebirth_eligible=True made
no semantic sense. With relation semantics, it's a hostile encounter → HOSTILE_CREATURE.

The existing test `test_classify_defeated_target_hero_defender_returns_hero_kill` must be updated:
change attacker faction to NEUTRAL so `is_hostile("neutral", "hero_guild")` → False → EntityRole
fallback → HERO_KILL is still reachable for the neutral-attacker scenario.

## Parity Ledger COMB-280

Status: `verified`. After change, v2_evidence should mention FactionSemanticsService as primary step.
The HERO_KILL path for monster→hero scenario changes — add divergence note.

## _HOSTILE_CREATURE_CLASSIFICATION class constant

Only used on line 87. After refactor, the new code creates a RewardClassification inline with
source="relation_projection". The class-level constant is no longer returned from the main path;
it remains as a named fallback constant (source="hostile_relation") but is unused from the method.
