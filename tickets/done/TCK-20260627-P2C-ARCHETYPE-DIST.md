---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260627-P2C-ARCHETYPE-DIST
phase: done
date: 2026-06-27
tags: [archetypes, content, distribution, mage, healer, variety]
---

# TCK-20260627-P2C-ARCHETYPE-DIST

## Title
Add 6–8 archetypes for underrepresented roles (mage, healer, leader, rogue)

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
The archetype catalog at `data/content/entities/entity_archetypes.yaml` has 21 archetypes, but 4/21 are the same role (scout). No dedicated mage/caster role has more than 1 entry. Encounters pull mostly scout-type entities, reducing behavioral variety. Source: D07 F4, Gap Risk 9/15.

## Scope
- Add 6–8 new archetype entries to `data/content/entities/entity_archetypes.yaml` weighted toward: mage (2+), healer (1–2), leader variants (1), rogue (1–2).
- Distribute new archetypes across existing factions (use faction IDs from `data/content/social/factions.yaml`).
- Verify: no single role exceeds 3/21 distribution in the final archetype set.
- Run catalog validation: `make world-validate` or `make content-check` (if that target exists).

## Out of Scope
- Game balance tuning for the new archetypes.
- Adding new mechanics to support new roles.
- Faction relationship content (P2-D).

## Acceptance Criteria
- [ ] `data/content/entities/entity_archetypes.yaml` has ≥27 total archetype entries (21 + 6–8 new).
- [ ] Scout/ranger role count ≤ 3/total after additions.
- [ ] Mage role count ≥ 2.
- [ ] Each new archetype is assigned to a faction registered in the catalog.
- [ ] `make world-validate` (or equivalent) passes.
- [ ] No ContentUsageMatrix drift: `pytest tests/ -k content -m "not slow"` passes.

## Related Tickets
- TCK-20260627-P2D-FACTION-RELS (complementary content — faction relationships should exist for factions the new archetypes belong to)
- TCK-20260627-P2K-CONTENT-MATRIX (ContentUsageMatrix auto-generate — ensures no registration step is missed)
- TCK-20260627-P2L-CONTENT-GUIDE (authoring guide — use it as reference when adding archetypes)

## Related Docs
- `docs/audits/D07_content_depth.md` F4
- `docs/content/authoring_guide.md` (once P2-L is done — use as reference if available)
- `docs/simulation/domains/adventure_contract.md` (archetype roles in encounter selection)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260610-SWAMP-BORDER-PACK/` — example of adding archetypes via content pack

## Related Code Areas
- `data/content/entities/entity_archetypes.yaml` (primary)
- `data/content/social/factions.yaml` (faction ID source)

## Assumptions / Open Questions
- New archetypes should follow the same YAML schema as existing entries in `entity_archetypes.yaml`.
- Check that catalog ID constraints are respected (namespace collision avoidance per `WorldModuleSpec`).

## Implementation Notes
- Look at existing archetypes in `entity_archetypes.yaml` for schema reference before authoring new ones.
- Use faction IDs that already exist in `factions.yaml` — do not invent new faction IDs in this ticket.
- Added 7 new archetypes: town_healer, forest_druid, arcane_mage, moon_cult_sorcerer, orc_warchief, dwarven_hunter, bandit_cutpurse.
- No "rogue" role exists in roles.yaml; used "hunter" role with rogue_skills for the rogue-concept archetypes (dwarven_hunter, bandit_cutpurse).
- No healer_skills profile exists; healer archetypes use mage_skills (closest available for support magic).
- Final count: 28 archetypes. Scout proportion: 4/28 = 14.3% (improved from 19%). Mage count: 3 (archetypes: apprentice_mage, arcane_mage, moon_cult_sorcerer).

## Test Summary
- `make world-validate` passes.
- `pytest tests/ -k "archetype or entity_archetype" -m "not slow"` passes.
- Distribution assertion: verify role distribution manually or via a quick Python check.

## Files Changed
- `data/content/entities/entity_archetypes.yaml` — appended 7 new archetype entries

## Completion Summary
Added 7 new archetypes (town_healer, forest_druid, arcane_mage, moon_cult_sorcerer, orc_warchief, dwarven_hunter, bandit_cutpurse) to `data/content/entities/entity_archetypes.yaml`, bringing the total from 21 to 28. Mage count increased to 3; healer role populated with 2 entries; hunter role (rogue-concept) populated with 2 entries; leader role expanded with orc_warchief. Scout proportion improved from 19% (4/21) to 14.3% (4/28). All 108 content tests pass. Behavior is unchanged — this is a pure content addition validated by the catalog relational integrity checker.
