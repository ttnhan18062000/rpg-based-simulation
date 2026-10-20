---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261020-ENTITY-LIST-RETURNS-A-BOUNDED-SUMMARY-NOT-THE-FULL-DETAIL
phase: done
date: 2026-10-20
tags: []
---

# Investigation: TCK-20261020-ENTITY-LIST-RETURNS-A-BOUNDED-SUMMARY-NOT-THE-FULL-DETAIL

See /mnt/data/scratch-rpg-implementer-2/entities_payload.md. Measured on an aged-entity fixture (no live run): a finished quest costs about 176 B, a resolved blocker 104 B, a closed contract 76 B, item properties about 52 B each, and none of them was capped (terminal projects are records that nothing removes, strategic.py:336-361). An entity with 500 of each serialised to 89 KB (500 quests alone), the platform measurement of about 57 KB per entity equals roughly 320 finished quests. After the change the same entity is 4.1 KB as detail and 408 B as a list row. Which record dominates in a live world was not measured (no live run); quests dominate per record.
