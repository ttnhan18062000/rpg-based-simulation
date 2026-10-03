# Implementation Sequence — race-to-species-migration

Tickets must be implemented in this order. Generated from the dependency analysis in
`TCK-20260904-EPIC-RACE-TO-SPECIES-TERMINOLOGY`'s own plan.md.

tracking_doc: docs/plans/rpg_design_roadmap/rpg_design_roadmap.md

## Order

1. TCK-20260904-SPECIES-CORE-SCHEMA-RENAME  (no deps in this batch — the foundation every other
   ticket's rename builds on: `RaceDefinition`/`race_id`/`races.yaml`)
2. TCK-20260904-SPECIES-RELATIONS-SUBSYSTEM-RENAME  (depends on: TCK-20260904-SPECIES-CORE-SCHEMA-RENAME)
3. TCK-20260904-SPECIES-CROSSCUTTING-CONSUMERS-RENAME  (depends on: TCK-20260904-SPECIES-CORE-SCHEMA-RENAME)
4. TCK-20260904-SPECIES-DOCS-MECHANICS-PARITY-SWEEP  (depends on: TCK-20260904-SPECIES-CORE-SCHEMA-RENAME,
   TCK-20260904-SPECIES-RELATIONS-SUBSYSTEM-RENAME, TCK-20260904-SPECIES-CROSSCUTTING-CONSUMERS-RENAME
   — cites the real final names, doesn't guess ahead of the code)

## Why This Order Matters

Tickets 2 and 3 both read the base schema/field names ticket 1 renames — running them first would
mean renaming a field that doesn't exist yet under the new name. Ticket 4 documents the real outcome
of 1-3, so it must run last or its prose could describe a rename that hasn't actually landed yet.
