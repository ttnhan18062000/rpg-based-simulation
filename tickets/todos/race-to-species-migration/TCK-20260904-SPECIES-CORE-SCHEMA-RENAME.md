---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260904-SPECIES-CORE-SCHEMA-RENAME
phase: open
date: 2026-09-04
tags: [content, schema]
---

# TCK-20260904-SPECIES-CORE-SCHEMA-RENAME

## Title
Rename RaceDefinition/race_id to a species-named schema in core content plumbing

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
Child 1/4 of `TCK-20260904-EPIC-RACE-TO-SPECIES-TERMINOLOGY`. Renames the foundational schema/entity
plumbing that every other child ticket's rename depends on: `RaceDefinition`
(`src/content/schema.py:134`) to a species-named class, and the `race_id` field to `species_id`
everywhere it is read/written in this ticket's file list. Base content catalog
`data/content/living/races.yaml` renames to `species.yaml`.

## Scope
- `src/content/schema.py` — `RaceDefinition` class rename (confirm the exact target name with a
  plan-owner sanity check before starting, per the epic's own Assumptions/Open Questions).
- `src/content/{resolver,repository,matrix,reference_graph,validator}.py` — `race_id`/`race`
  parameter, variable, and error-context renames.
- `src/entities/{archetype_factory,contract_builder,identity_resolver}.py` — `race_id` field renames.
- `src/worldbuilding/compiler.py` — `race_id` property renames (lines ~532-533 at investigation time).
- `data/content/living/races.yaml` -> `species.yaml`, updating every path reference to it.
- `entity.identity.properties["race_id"]` -> `["species_id"]` — the actual stored key on live entity
  state; confirm no serialized/replay data depends on the old key name in a way that breaks replay
  determinism for existing recorded runs (check `docs/core/state.md`'s durable-state rules before
  touching this).

## Out of Scope
- The race-relations subsystem (`race_relations.yaml`, combat/tactical/diplomacy consumers) — child 2.
- Remaining cross-cutting consumers (kernel, cognition, observability, quests, api/ws) — child 3.
- Docs/mechanics/parity sweep — child 4, and only after this ticket's real final names are settled.

## Acceptance Criteria
- [ ] `RaceDefinition` renamed with a plan-owner-confirmed target name.
- [ ] `race_id` renamed to `species_id` everywhere in this ticket's file list, including the stored
      `entity.identity.properties` key.
- [ ] `data/content/living/races.yaml` renamed to `species.yaml`; every consumer's path reference
      updated.
- [ ] Existing tests in this ticket's scope (`tests/unit/content/`, `tests/unit/core/
      test_catalog_fallback.py`, `test_hardening_e5.py`, `test_registry_bridge.py`,
      `tests/unit/worldassembly/test_archetype_preservation.py`,
      `tests/unit/worldbuilding/test_world_compiler.py`) pass unchanged.
- [ ] Replay/determinism impact of the stored-property-key rename explicitly checked, not assumed
      safe.

## Related Tickets
- TCK-20260904-EPIC-RACE-TO-SPECIES-TERMINOLOGY (parent epic)
- TCK-20260904-SPECIES-RELATIONS-SUBSYSTEM-RENAME (depends on this ticket)
- TCK-20260904-SPECIES-CROSSCUTTING-CONSUMERS-RENAME (depends on this ticket)

## Related Docs
- `docs/core/state.md` (durable-state rules to check before renaming a stored property key)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/content/schema.py`, `src/content/resolver.py`, `src/content/repository.py`,
  `src/content/matrix.py`, `src/content/reference_graph.py`, `src/content/validator.py`
- `src/entities/archetype_factory.py`, `src/entities/contract_builder.py`,
  `src/entities/identity_resolver.py`
- `src/worldbuilding/compiler.py`
- `data/content/living/races.yaml`

## Assumptions / Open Questions
- Exact replacement class name for `RaceDefinition` not finally locked — proposed but not decided in
  the parent epic.
- Whether renaming the stored `race_id` property key breaks any existing recorded replay/checkpoint
  fixture that references it by name — needs a direct check, not an assumption.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
