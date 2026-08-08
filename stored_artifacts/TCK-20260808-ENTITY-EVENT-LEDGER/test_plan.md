---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260808-ENTITY-EVENT-LEDGER
artifact_type: test_plan
tags: [observability, world]
---

# Test Plan — TCK-20260808-ENTITY-EVENT-LEDGER

## New tests (`tests/tools/test_entity_event_ledger.py`) — staleness guard

1. `test_entity_ledger_mutation_sources_exist` — every ledger entry's `mutation_source` (a
   `dataclass.field` citation) references a real class in `src/core/updates.py` (via `getattr`/
   `dataclasses.fields()`), not a stale/renamed reference.
2. `test_entity_ledger_evidence_citations_are_real_files` — every ledger entry's `evidence` field
   (a file path, optionally with a line number) points at a file that actually exists.
3. `test_entity_ledger_covers_every_entity_update_field` — cross-check the ledger's own
   `mutation_source` values against `EntityUpdate`'s real dataclass fields (via
   `dataclasses.fields(EntityUpdate)`) — every field has at least one ledger entry, catching future
   drift if a new field is added to `EntityUpdate` without a corresponding ledger update.

## Scoped pytest command

`.venv/bin/python3 -m pytest tests/tools/test_entity_event_ledger.py -q`
