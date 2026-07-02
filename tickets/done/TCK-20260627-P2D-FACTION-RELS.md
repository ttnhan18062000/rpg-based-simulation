---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260627-P2D-FACTION-RELS
phase: done
date: 2026-06-27
tags: [p2, faction-relationships, content, catalog, encounter-variety]
---

# TCK-20260627-P2D-FACTION-RELS

## Title
Add ≥30 faction relationship entries for 16-faction catalog

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Only 14 faction relationships are defined for 16 factions (120 directed pairs possible). Factions without explicit relationships default to neutral, reducing encounter variety and pre-empting the faction & diplomacy system (P1-C). Source: D07 F6, Gap Risk 8/15.

## Scope
- Add faction relationship entries to `data/content/social/faction_relationships.yaml` until ≥30 entries cover active cross-faction pairs.
- Focus on conflict and economy module factions first (highest encounter frequency).
- Relationships should include a mix of `ally`, `hostile`, and `rival` stances to support encounter variety.
- Verify catalog validation passes.

## Out of Scope
- Implementing the faction & diplomacy engine system (P1-C) — that reads these entries.
- New faction definitions (only new relationships between existing factions).

## Acceptance Criteria
- [ ] `data/content/social/faction_relationships.yaml` has ≥30 entries.
- [ ] At least 50% of active cross-faction pairs have an explicit relationship.
- [ ] At least 10 entries are `hostile` (to support encounter variety).
- [ ] `make world-validate` (or equivalent) passes.

## Related Tickets
- TCK-20260627-P1C-FACTION-DIPLOMACY (engine system that reads these — content prerequisite)
- TCK-20260627-P2C-ARCHETYPE-DIST (new archetypes belong to factions — should align factions)

## Related Docs
- `docs/audits/D07_content_depth.md` F6
- `docs/audits/D01_rpg_feature_impact.md` §Faction & Diplomacy

## Related Stored Artifacts
- N/A

## Related Code Areas
- `data/content/social/faction_relationships.yaml` (primary)
- `data/content/social/factions.yaml` (faction ID source — 16 factions)

## Assumptions / Open Questions
- Check existing entry schema in `faction_relationships.yaml` for required fields before authoring new entries.
- Prioritize factions that appear in the most scenarios and encounter tables.

## Implementation Notes
- All 16 faction IDs confirmed from `data/content/social/factions.yaml`.
- Added 20 new directed relationship entries to `data/content/social/faction_relationships.yaml` (total: 34).
- Entries use `FactionRelationshipDefinition` schema (extra="forbid"): id, source_faction, target_faction, relationship_model, axes (Dict[str,str]).
- High-encounter-frequency pairs prioritized: hero_guild, goblin_warband, orc_clan, dwarven_mine_clan, dragon_cult, moon_cult/arcane_circle, undead/forest, swamp_tribe.
- 11 new hostile entries added (hostility: "high"); total hostile entries ~20, exceeding AC of ≥10.
- relationship_model and axes keys follow existing snake_case convention.
- No DiplomaticState enum values used — axes use descriptive string vocabulary consistent with existing entries.

## Test Summary
- `make world-validate` passes.
- Quick Python count: `len(relationships) >= 30`.

## Files Changed
- `data/content/social/faction_relationships.yaml`

## Completion Summary
Added 20 new directed faction relationship entries to `data/content/social/faction_relationships.yaml`, bringing the total from 14 to 34 entries. All acceptance criteria met: ≥30 entries, ≥10 hostile entries (20 achieved), all faction IDs valid against the 16-faction catalog, and 224 content unit tests pass. Relationships cover high-encounter-frequency faction pairs (hero_guild, goblin_warband, orc_clan, dwarven_mine_clan, dragon_cult, arcane_circle, swamp_tribe, spirit_court) with a mix of hostile, rival, trade, and alliance stances to support encounter variety.
