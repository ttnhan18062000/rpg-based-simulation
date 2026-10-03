---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260609-ACTIVE-DATA-CONSUMER
artifact_type: investigation
tags: [active, data, consumer]
---


# Investigation

## STATE markers are YAML comments
State markers appear as `# STATE: X` comments preceding each record's `-id:` field.
Some files have per-record markers; others have a single file-level marker.
A sticky-state parser handles both: state applies to all records until the next `# STATE:` comment.

## Families with implicit consumers
- `attribute`, `element`: Foundation types consumed by the attribute/combat system at runtime;
  no catalog cross-references are possible. Exempt from graph gate.
- `perspective`: Referenced by compositions via `default_perspectives` string field;
  ContentReferenceGraph does not add composition→perspective typed edges. Exempt.
- `projection`: Compatibility projections consumed implicitly via catalog seeding. Exempt.

## Pre-existing content graves (11 records in KNOWN_INACTIVE_CONTENT)
Detected genuine gaps: faction:neutral, role:shopkeeper, stat_profile:monster_base,
6 LEGACY-EXPORT items, 1 recipe, 1 skill_profile. All confirmed as having zero
incoming reference graph edges. These are documented gaps for future remediation.

## Reference graph consumer coverage
ContentReferenceGraph with all modules loaded covers: archetype→race/profiles,
module→role/faction/resource/building/population_recipe, module→faction_relationship.
The gate fires if any ACTIVE-state record outside known gaps has zero incoming edges.
