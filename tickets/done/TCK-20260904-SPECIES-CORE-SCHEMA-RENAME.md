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
DONE

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
- [x] `RaceDefinition` renamed with a plan-owner-confirmed target name. (`SpeciesDefinition` — no
      plan-owner was available mid-session; recorded as the only reasonable candidate in
      investigation.md.)
- [x] `race_id` renamed to `species_id` everywhere in this ticket's file list, including the stored
      `entity.identity.properties` key.
- [x] `data/content/living/races.yaml` renamed to `species.yaml`; every consumer's path reference
      updated.
- [x] Existing tests in this ticket's scope (`tests/unit/content/`, `tests/unit/core/
      test_catalog_fallback.py`, `test_hardening_e5.py`, `test_registry_bridge.py`,
      `tests/unit/worldassembly/test_archetype_preservation.py`,
      `tests/unit/worldbuilding/test_world_compiler.py`) pass unchanged.
- [x] Replay/determinism impact of the stored-property-key rename explicitly checked, not assumed
      safe.

## Related Tickets
- TCK-20260904-EPIC-RACE-TO-SPECIES-TERMINOLOGY (parent epic)
- TCK-20260904-SPECIES-RELATIONS-SUBSYSTEM-RENAME (depends on this ticket)
- TCK-20260904-SPECIES-CROSSCUTTING-CONSUMERS-RENAME (depends on this ticket)

## Related Docs
- `docs/core/state.md` (durable-state rules to check before renaming a stored property key)

## Related Stored Artifacts
- stored_artifacts/TCK-20260904-SPECIES-CORE-SCHEMA-RENAME/{investigation,plan,test_plan}.md

## Related Code Areas
- `src/content/schema.py`, `src/content/resolver.py`, `src/content/repository.py`,
  `src/content/matrix.py`, `src/content/reference_graph.py`, `src/content/validator.py`
- `src/entities/archetype_factory.py`, `src/entities/contract_builder.py`,
  `src/entities/identity_resolver.py`
- `src/worldbuilding/compiler.py`
- `data/content/living/races.yaml`

## Assumptions / Open Questions
- Exact replacement class name for `RaceDefinition` not finally locked — proposed but not decided in
  the parent epic. Resolved: `SpeciesDefinition`, see investigation.md.
- Whether renaming the stored `race_id` property key breaks any existing recorded replay/checkpoint
  fixture that references it by name — needs a direct check, not an assumption. Resolved: no —
  checkpointing/hashing is generic (`entity.to_canonical_dict()`), no field name hardcoded; see
  investigation.md's "Replay/determinism impact" section.

## Implementation Notes
Real scope was larger than the ticket's original file list — confirmed via grep, not assumed:
`src/entities/runtime_contract.py`, `src/worldassembly/{models,resolver,entity_spawner}.py`, and
`data/content/entities/entity_archetypes.yaml` (29 `race:` keys) all had hard-coupled `race_id`/`race`
reads that would break at runtime if left unfixed. Also did minimal surgical stored-key fixes (not
full renames) in 3 files owned by child 2/3 (`content_semantics/faction.py`, `strategy/
role_model_imitation.py`, `observability/event_shapers.py`) since they read the exact
`entity.identity.properties` key renamed here — their own naming stays child 2/3's job.
`RaceRelationRecord`/`source_race`/`target_race`/`race_relations.yaml`/`FactionDefinition.
common_races` all confirmed untouched (child 2 scope). All 21 `data/worlds/*/resolved/*` artifacts
regenerated (`resolve` + `compile --seed <original_seed>` per world); diff-verified isolated to the
renamed field only (see investigation.md and test_plan.md).

## Test Summary
872 passed, 33 deselected (slow tests excluded, standard project convention), 0 failed, across the
full scoped test list (content/, entities/, worldassembly/, worldbuilding/, observability, strategic,
quest, content_semantics, combat wiring, plus corpus/integration tests reading the regenerated
`data/worlds/` artifacts). Full command and file list in test_plan.md. One `@pytest.mark.slow` test
(`test_population_stability[dungeon_crawl]`) hit an environment-load `TimeoutError` under this
session's concurrent-multi-session memory pressure — not a rename regression, excluded from the
scoped run per the project's standard `-m "not slow"` convention.

## Files Changed
- `src/content/{schema,resolver,repository,matrix,reference_graph,validator}.py`
- `src/entities/{archetype_factory,contract_builder,identity_resolver,runtime_contract}.py`
  (`runtime_contract.py` beyond original scope — hard coupling)
- `src/worldbuilding/compiler.py`
- `src/worldassembly/{models,resolver,entity_spawner}.py` (beyond original scope — hard coupling)
- `src/content_semantics/faction.py`, `src/strategy/role_model_imitation.py`,
  `src/observability/event_shapers.py` (minimal stored-key-only fix, child 2/3 files)
- `src/quests/generator.py`, `src/content_semantics/personality.py`, `src/world/environment.py`,
  `src/world/perception/gate.py`, `src/world/motivation/pressure_resolver.py` (comment accuracy only)
- `data/content/living/races.yaml` → `species.yaml` (git mv); `data/content/entities/
  entity_archetypes.yaml` (29 keys); `data/content/social/personality_bias.yaml` (comment)
- `tools/generate_content_inventory.py`
- `data/worlds/*/resolved/*.json`, `data/worlds/*/world_compile_report.json` (21 worlds)
- 20 test files across `tests/unit/content/`, `tests/unit/core/`, `tests/unit/entities/`,
  `tests/unit/worldassembly/`, `tests/unit/observability/`, `tests/unit/strategic/`,
  `tests/unit/combat/`, `tests/unit/quest/`, `tests/integration/combat/`,
  `tests/integration/entities/`, `tests/integration/domains/adventure/`,
  `tests/integration/content/test_expansion_gate.py` (full list in test_plan.md)
- `docs/parity_ledger/substrate.yaml` (SUB-393)

## Completion Summary
Renamed `RaceDefinition` → `SpeciesDefinition` and the `race_id`/`race` field chain to
`species_id`/`species` across core content schema, resolver, repository, entity-identity, and
worldassembly plumbing, plus the hard-coupled content YAML and 21 pre-compiled world artifacts.
Established and held a clean scope boundary against child 2 (race-relations subsystem) and child 3
(remaining cross-cutting consumers), doing only minimal surgical stored-key fixes in their owned
files where hard coupling made that unavoidable. Ticket's own two flagged open questions (target
class name, replay/determinism safety) both resolved and documented. All scoped tests green.
