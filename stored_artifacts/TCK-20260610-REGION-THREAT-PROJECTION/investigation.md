---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260610-REGION-THREAT-PROJECTION
artifact_type: investigation
tags: [region, threat, projection]
---

# TCK-20260610-REGION-THREAT-PROJECTION — Investigation

## Key Findings

No existing `RegionThreatClassifier` exists. Region threat is currently tracked as `RegionState.trauma_score` and `retaliation_pressure` (numerical values, not perspective-relative classification). `ThreatService` only handles decay/cooling, not classification.

## Relevant Data

- `RegionState.owner_faction_id: Optional[int]` — legacy int enum, not clean faction_id
- `RuntimeRegionDefinition.controlling_faction: Optional[str]` — clean faction string (catalog)
- `EcologyDefinition.dominant_factions: List[str]`, `populations: List[str]` — clean faction lists
- `hero_guild_perspective.ally_groups: ["town_council", ...]`
- `hero_guild_perspective.hostile_groups: ["goblin_warband", "bandit_company", ...]`
- `hero_guild_perspective.contextual_threat_groups: ["wild_beast_pack", ...]` → label="threat"

## Classification Design

New file: `src/world/region_threat_classifier.py`

Inputs: `perspective_faction_id`, `controlling_faction_id`, `population_faction_ids`, optional `RelationContext`

Output label: `safe | neutral | contested | threatened | hostile | unknown`

Derivation rules:
- Controlling = enemy → "hostile"
- Controlling = threat → "threatened" (escalates to "hostile" if any population is enemy)
- Controlling = ally/protected + no hostile populations → "safe"
- Controlling = ally/protected + population threat → "threatened"
- Controlling = ally/protected + population enemy → "contested"
- Controlling = neutral + any population enemy → "contested"
- Controlling = neutral + any population threat → "threatened"
- Controlling = neutral (only) → "neutral"
- No factions → "unknown"

Fallback: no perspective/relationship in catalog → `FactionSemanticsService.get_legacy_faction_bucket()` determines safety.
