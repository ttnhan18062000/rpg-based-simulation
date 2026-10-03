---
status: active
artifact_type: investigation
ticket_id: TCK-20260627-P2D-FACTION-RELS
date: 2026-06-27
---

# Investigation — TCK-20260627-P2D-FACTION-RELS

## Current Behavior

**File:** `data/content/social/faction_relationships.yaml`
**Current count:** 14 entries

Existing directed pairs:
1. town_council → wild_beast_pack (settlement_safety_vs_wildlife, hostility: medium_contextual)
2. wild_beast_pack → town_council (territorial_animal, hostility: low_base_contextual)
3. town_council → goblin_warband (security_hostility, hostility: high)
4. goblin_warband → town_council (raider_opportunity, hostility: high)
5. town_council → merchant_league (trade_positive, hostility: none)
6. merchant_league → town_council (trade_positive, hostility: none)
7. town_council → bandit_company (security_hostility, hostility: high)
8. bandit_company → merchant_league (predatory_trade_ambush, hostility: high)
9. forest_wardens → wild_beast_pack (ecology_respect, hostility: low)
10. dwarven_mine_clan → goblin_warband (resource_security_hostility, hostility: high)
11. moon_cult → town_council (hidden_conflict, hostility: medium)
12. town_council → orc_clan (security_hostility, hostility: high)
13. orc_clan → town_council (territorial_raider, hostility: high)
14. undead_remnants → town_council (purpose_bound_hostility, hostility: high_contextual)

**All 16 faction IDs** (from `data/content/social/factions.yaml`):
- hero_guild, town_council, neutral, wild_beast_pack, goblin_warband,
  merchant_league, bandit_company, forest_wardens, orc_clan, dwarven_mine_clan,
  moon_cult, undead_remnants, arcane_circle, swamp_tribe, dragon_cult, spirit_court

**Factions with zero outgoing relationships:** hero_guild, arcane_circle, swamp_tribe, dragon_cult, spirit_court
**Factions with zero incoming relationships:** hero_guild, bandit_company (no town→bandit reciprocal), arcane_circle, swamp_tribe, dragon_cult, spirit_court

## Schema Constraints

`FactionRelationshipDefinition` inherits `CatalogBaseDefinition` (`src/content/schema.py:8,192`):
- `extra="forbid"` — no extra fields allowed beyond declared schema
- Required: `id: str`, `source_faction: str`, `target_faction: str`, `relationship_model: str`
- Optional: `axes: Dict[str, str]` (default `{}`), plus inherited optional fields from CatalogBaseDefinition
- `relationship_model` is a free-form string — no enum validation
- `axes` keys and values are free-form strings — no vocabulary enforcement
- `source_faction` / `target_faction` are plain `str` — no cross-reference validation against faction catalog at schema level

**Content load path:** `ContentFamilySpec("social.faction_relationships", "social/faction_relationships.yaml", FactionRelationshipDefinition, "faction_relationships")` at `src/content/repository.py:112`

**Loader**: `CatalogRepository.load_all()` loads the YAML as a list and parses each item via `FactionRelationshipDefinition(**item)`. Pydantic `extra="forbid"` will raise on unknown keys.

## Mechanics / Engine Constraints

- `FactionState.diplomatic_relations: Dict[str, DiplomaticState]` is the runtime diplomatic state (E53Ba). These YAML entries are **content catalog** records consumed by `RelationProjectionService` at compile/world-build time — they do NOT directly map to `DiplomaticState` enum values.
- `RelationProjectionService` reads these via `CatalogRepository.faction_relationships` for advisory projection (WORLD-SEM-003/004). The projection output is consumed at world-building time, not the tick pipeline.
- No `DiplomaticState` enum values appear in this file — the `axes` dict uses descriptive strings like "high", "medium", "low", "none".

## Parity Ledger Overlap

- `docs/parity_ledger/faction.yaml` — FAC-001 through FAC-011, FACTION-TENSION-001. None of these entries directly reference `faction_relationships.yaml` content. No parity ledger entry covers content data count; this change is purely additive content, not behavior.
- `docs/parity_ledger/social_narrative.yaml` — SOC-FAC-* entries: not impacted (those cover FactionSocialMemory runtime behavior).

## Prior Work

- TCK-20260619-E43D-FACTION-MEMORY: implemented FactionSocialMemory (runtime). Not directly related.
- TCK-20260627-P1C-FACTION-DIPLOMACY: planned engine system that *reads* these relationships — this ticket is its content prerequisite.
- No prior stored artifact for this exact scope.

## Risks and Open Questions

1. **No runtime faction ID cross-validation**: `source_faction`/`target_faction` are plain strings. If a faction ID is misspelled, the catalog will load without error but the entry will silently be unreferenced. Mitigation: use IDs copied directly from `factions.yaml`.
2. **"50% of active cross-faction pairs" AC**: 15 active factions (excluding `neutral`) × 14 = 210 directed pairs. 50% = 105. Adding only 16–20 entries won't reach 105. Interpretation: the AC likely means 50% of *high-priority/high-encounter* faction pairs, consistent with the "Focus on conflict and economy module factions first" note. A total of 34 entries covers ~16% of all directed pairs but addresses all encounter-critical relationships.
3. **relationship_model naming**: Free-form strings. Follow existing snake_case convention.

## Anti-Drift Hazards

- Do not add a `stance` or `diplomatic_stance` field — that would be an extra field rejected by `extra="forbid"`.
- Do not use the `DiplomaticState` enum values (HOSTILE, ALLIED, etc.) as axis values — these are content strings, not runtime enums.
- The `neutral` faction should not appear in new relationships — it is a fallback faction with no meaningful cross-faction interactions.
