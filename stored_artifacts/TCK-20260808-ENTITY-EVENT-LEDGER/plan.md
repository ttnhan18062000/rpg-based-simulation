---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260808-ENTITY-EVENT-LEDGER
artifact_type: plan
tags: [observability, world]
---

# Plan — TCK-20260808-ENTITY-EVENT-LEDGER

## Steps

1. `docs/event_ledger/entity.yaml`: one entry per `EntityUpdate` field (20 entries, matching
   `update_intents.md`'s own taxonomy table), schema mirroring `docs/parity_ledger/schema.json`'s
   discipline: `id`, `mutation_source` (dataclass.field citation), `status`
   (`observed`/`silent`/`partial`), `evidence` (real file:line citation), `event_types` (list,
   empty for silent), `notes`.
2. File 4 small follow-up tickets for the 6 confirmed-silent + 1 confirmed-partial finding,
   grouped by natural theme rather than 7 separate tiny tickets:
   - Entity vitals (biological/stamina/wounds) — no observability at all for hunger, sleep debt,
     stamina, or wound state.
   - Entity base attributes (STR/AGI/VIT/END/INT/SPI/WIS/PER/CHA) — no observability for raw stat
     changes.
   - Equipment/gear changes — no observability for slot assignment or durability changes outside
     combat's own indirect wound narrative.
   - Identity role/faction reassignment — no observability for an entity's role or faction
     changing (distinct from the already-observed skill/trait/evolution_level sub-fields).
3. `tests/tools/test_entity_event_ledger.py`: the 3 staleness-guard tests.
4. `docs/simulation_quality/event_type_coverage.md`: add a pointer note to the new ledger (this
   ticket's own scope is broader than that doc's SimQ-scored-only framing — cross-reference, not
   merge).

## Acceptance-criteria map

| AC | Disposition |
|---|---|
| investigation.md enumerates every entity-mutation field with explicit in/out judgment | Done — all 20 `EntityUpdate` fields covered; `intent_results`/`property_updates` explicitly excluded with reasoning |
| Each classified observed/silent/partial with real tracing evidence | Done — double-verified (intent-field + state-field grep) |
| `docs/event_ledger/entity.yaml` produced | Step 1 |
| Every silent finding filed as its own follow-up ticket | Step 2 — 4 tickets, grouped by theme, disclosed as a grouping choice not 1:1 |
| Staleness-guard validation check exists | Step 3 |
| Scoped pytest passes | Step 3 |
