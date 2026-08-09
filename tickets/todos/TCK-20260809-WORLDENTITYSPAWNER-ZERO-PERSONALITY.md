---
status: active
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260809-WORLDENTITYSPAWNER-ZERO-PERSONALITY
phase: open
date: 2026-08-09
tags: [combat, simulation-quality]
---

# TCK-20260809-WORLDENTITYSPAWNER-ZERO-PERSONALITY

## Title
`WorldEntitySpawner`/`ArchetypeEntityFactory` (`src/worldassembly/`) never sets `PersonalityComponent`
on any entity it spawns — the same class of bug already fixed once for `WorldCompiler.compile()`
(`TCK-20260619-P0-ENTITY-INIT`), but for a separate, newer entity-construction path that fix never
covered — **confirmed real, but confirmed to have zero current effect on real combat outcome,
SimQ scoring, or entity-lifecycle metrics**

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found during `TCK-20260809-COMBAT-PERSONALITY-RACE-CORRELATION` (same session) while tracing
which real entity-construction paths exist. `ArchetypeEntityFactory.build_entity()`
(`src/entities/archetype_factory.py`) never calls `.identity(personality=...)` in its builder
chain, so every entity spawned through it keeps the builder's default `PersonalityComponent()`
(all traits 0.0) — regardless of the real `race_id`/`archetype_id`/`faction_id` data available in
its own `ResolvedEntityRuntimeContract`. `WorldEntitySpawner._spawn_legacy_guard()` (same file's
sibling path) has the identical gap.

**Real impact, confirmed via direct tracing (not assumed)**: `WorldEntitySpawner`'s only real
caller is `CatalogScenarioStateBuilder` (`src/scenarios/catalog_state_builder.py`), which itself
has **zero callers anywhere in `src/` or `tools/`** — only its own test files reference it
(`tests/unit/certification/test_catalog_scenario_state_builder.py`,
`tests/integration/certification/test_catalog_vs_legacy_scenario_semantics.py`,
`tests/integration/certification/test_catalog_arena_smoke.py`,
`tests/integration/worldassembly/test_world_entity_spawner.py`). The real SimQ world loader
(`tools/calibrate_simq.py`'s `_load_world_state`) goes directly through `WorldCompiler.compile()`
against `data/worlds/{name}/resolved/world.resolved.yaml` and never touches this path. **This bug
does not currently affect any real, scored combat outcome, SimQ grade, or entity-lifecycle
metric** — it is real, but isolated to a certification/integration test harness, not live
production or scoring code.

## Scope
1. **Investigate**: confirm this ticket's own "zero current impact" claim still holds (re-check
   for any new real callers of `WorldEntitySpawner`/`CatalogScenarioStateBuilder` introduced since
   this ticket was filed); confirm the real fix shape (likely: seed `PersonalityComponent` in
   `ArchetypeEntityFactory.build_entity()` using the same `DeterministicRNG`-based approach
   `WorldCompiler.compile()` already uses, plus the real `get_bravery_bias()`/
   `get_action_style_for_bravery()` helpers this session's sibling tickets added — but
   `ArchetypeEntityFactory.build_entity()` currently has no `seed`/RNG parameter threaded in at
   all, which is itself part of the real fix shape, not a trivial addition).
2. **Plan**: decide whether to thread a seed through `WorldEntitySpawner.spawn_from_context()` →
   `_spawn_one()` → `ArchetypeEntityFactory.build_entity()` (3 function signatures across 2
   files), or a different approach.
3. **Implement**: the real, minimal fix, re-verified against the certification/integration tests
   that actually exercise this path.

## Out of Scope
- Any change to `WorldCompiler.compile()`'s own already-correct personality seeding.
- Wiring `WorldEntitySpawner`/`CatalogScenarioStateBuilder` into the real SimQ scoring pipeline —
  a separate, much larger architectural question not implied by this ticket.

## Acceptance Criteria
- [ ] investigation.md re-confirms the zero-current-impact finding (or reports if it's changed)
- [ ] Real fix lands: entities spawned via `ArchetypeEntityFactory`/`WorldEntitySpawner` get real,
      non-zero, race/faction-correlated personality (matching the sibling ticket's own approach)
- [ ] Scoped pytest passes (`tests/unit/certification/`, `tests/integration/certification/`,
      `tests/integration/worldassembly/`)

## Related Tickets
- TCK-20260809-COMBAT-PERSONALITY-RACE-CORRELATION (DONE, same session — found this while
  tracing the real entity-construction architecture; fixed the confirmed-live path only)
- TCK-20260619-P0-ENTITY-INIT (DONE — the earlier, different all-zero-personality bug for
  `WorldCompiler.compile()`'s own path)

## Related Docs
None yet.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/entities/archetype_factory.py` (`ArchetypeEntityFactory.build_entity`)
- `src/worldassembly/entity_spawner.py` (`WorldEntitySpawner`, both `_spawn_archetype_native` and
  `_spawn_legacy_guard`)
- `src/scenarios/catalog_state_builder.py` (the only real caller, itself uncalled)

## Assumptions / Open Questions
- Whether this path is intended to become real/live in the future (in which case this bug matters
  more) or is legacy/abandoned test infrastructure (in which case fixing it is lower value) — not
  determined here; flagged for Investigate.

## Implementation Notes
(To be filled during implementation.)

## Test Summary
(To be filled during implementation.)

## Files Changed
(To be filled during implementation.)

## Completion Summary
(To be filled during implementation.)
