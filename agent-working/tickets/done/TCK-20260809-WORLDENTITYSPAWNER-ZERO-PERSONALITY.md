---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260809-WORLDENTITYSPAWNER-ZERO-PERSONALITY
phase: done
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
DONE

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
- [x] investigation.md re-confirms the zero-current-impact finding (or reports if it's changed) —
      re-confirmed accurate: `CatalogScenarioStateBuilder`'s only real caller is certification/
      integration test infrastructure, no live SimQ scoring caller found
- [x] Real fix lands: entities spawned via `ArchetypeEntityFactory`/`WorldEntitySpawner` get real,
      non-zero, race/faction-correlated personality (matching the sibling ticket's own approach) —
      verified both at unit level and via a real, live end-to-end `CatalogScenarioStateBuilder`
      run (15/15 entities, real bravery correlation confirmed)
- [x] Scoped pytest passes (`tests/unit/certification/`, `tests/integration/certification/`,
      `tests/integration/worldassembly/`) — 1185 passed across the full scoped surface

## Related Tickets
- TCK-20260809-COMBAT-PERSONALITY-RACE-CORRELATION (DONE, same session — found this while
  tracing the real entity-construction architecture; fixed the confirmed-live path only)
- TCK-20260619-P0-ENTITY-INIT (DONE — the earlier, different all-zero-personality bug for
  `WorldCompiler.compile()`'s own path)

## Related Docs
- `docs/world/assembly_contract.md` (updated — corrected its own now-inaccurate "no randomness"
  determinism claim)
- `docs/mechanics/content_usage_matrix.md` (regenerated)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260809-WORLDENTITYSPAWNER-ZERO-PERSONALITY/`

## Related Code Areas
- `src/entities/archetype_factory.py` (`ArchetypeEntityFactory.build_entity`)
- `src/worldassembly/entity_spawner.py` (`WorldEntitySpawner`, both `_spawn_archetype_native` and
  `_spawn_legacy_guard`)
- `src/scenarios/catalog_state_builder.py` (the only real caller, itself uncalled)
- `src/content_semantics/personality.py` (new — shared bravery-bias/`ActionStyle`/personality
  helpers, extracted from `src/worldbuilding/compiler.py`)

## Assumptions / Open Questions
- Whether this path is intended to become real/live in the future (in which case this bug matters
  more) or is legacy/abandoned test infrastructure (in which case fixing it is lower value) — not
  determined here; flagged for Investigate. **Resolved for this ticket's own purposes**: fixed
  regardless, since it's real, disclosed technical debt worth closing correctly either way, and
  the real fix cost was small once the seed-threading path was traced.

## Implementation Notes
**Step 1 (architecture)**: extracted `_load_personality_bias_config`, `_PERSONALITY_BIAS_FALLBACK`,
`get_bravery_bias`, `get_action_style_for_bravery` out of `src/worldbuilding/compiler.py` into a
new `src/content_semantics/personality.py`, matching this repo's own established precedent for
cross-cutting semantic helpers (`content_semantics/faction.py`, `relation.py`, `role.py`) — avoids
a backward dependency from `src/entities/` onto a specific `worldbuilding` compiler module.
`compiler.py` re-imports the 2 public functions; zero behavior change to its own existing,
already-shipped callers (confirmed: all 38 of `compiler.py`'s own existing personality/
`ActionStyle` tests still pass unmodified).

**Step 2**: added `build_personality_for_entity(entity_id, faction_id, seed)` to the same new
module — the exact same `DeterministicRNG`/`Domain.WORLD`/`sub_id` convention
`WorldCompiler.compile()` already uses (10=greed, 11=bravery, 12=sociability, 13=industry), shared
by both real construction branches rather than duplicated.

**Step 3**: `ArchetypeEntityFactory.build_entity()` gained a `seed: int = 42` parameter (default
matches `CatalogScenarioStateBuilder.build()`'s own existing default exactly — backward-compatible
for all 12 pre-existing direct-call tests), calls `build_personality_for_entity()`, sets
`.identity(personality=...)` and `.combat(action_style=get_action_style_for_bravery(bravery))`.
`WorldEntitySpawner._spawn_legacy_guard()` got the identical treatment (the second, separate real
construction branch — confirmed via a dedicated new test file it wasn't accidentally skipped).

**Step 4**: threaded the seed through `spawn_from_context()`'s own signature →
`_spawn_one()` → both `_spawn_archetype_native()`/`_spawn_legacy_guard()`, and wired
`CatalogScenarioStateBuilder.build()`'s own already-existing `seed: int = 42` parameter down into
`spawn_from_context()` — previously computed but never passed through at all.

**Step 5**: corrected `docs/world/assembly_contract.md`'s own real, authoritative "No randomness
is introduced during spawning" claim — now accurately describes seed-parameterized determinism.

**2 real regressions caught and fixed during this ticket's own Test phase** (not silently patched
around): extracting the shared helpers broke 2 pre-existing tests in `test_world_compiler.py` that
referenced `compiler._load_personality_bias_config` directly — moved them to the real, new owner
(`test_personality.py`) rather than reverting the extraction. `src/content/matrix.py`'s own
`social/personality_bias` content-usage-matrix `evidence_tests` field still pointed at the old,
moved test location — `test_content_usage_evidence.py`'s own real gate caught this; updated and
regenerated `docs/mechanics/content_usage_matrix.md`.

**Real, live end-to-end verification** (not unit-test-only, per this session's own established
discipline): ran `CatalogScenarioStateBuilder.build()` directly against the real
`wolf_territory_pressure` scenario (`frontier_living_world` composition, `wolf_den_near_forest`
module) — 15/15 real entities got non-zero personality; the 3 real `wild_beast_pack` wolf/spider
entities showed bravery 0.617-0.989 (correctly biased high, matching the sibling ticket's own
established bias values) with 2/3 landing `AGGRESSIVE` `ActionStyle`.

## Test Summary
New: `tests/unit/content_semantics/test_personality.py` (9 tests), 4 new tests in
`tests/unit/entities/test_archetype_entity_factory.py`, `tests/unit/worldassembly/
test_entity_spawner_legacy_guard.py` (4 tests, new), 4 new tests in `tests/integration/
worldassembly/test_world_entity_spawner.py`. Full scoped pytest (`tests/unit/entities/`,
`tests/unit/worldassembly/`, `tests/unit/content_semantics/`, `tests/unit/worldbuilding/`,
`tests/unit/scenarios/`, `tests/integration/entities/`, `tests/integration/worldassembly/`,
`tests/unit/certification/`, `tests/integration/certification/`, `tests/unit/combat/`,
`tests/unit/core/`, `tests/unit/tactical/`, `tests/unit/movement/`, `tests/unit/strategic/`,
`tests/unit/content/`): 1185 passed, 2 pre-existing failures already confirmed unrelated to this
or any prior ticket this session.

## Files Changed
- `src/content_semantics/personality.py` — new, shared personality/bravery-bias/`ActionStyle`
  helpers (extracted from `compiler.py`).
- `src/worldbuilding/compiler.py` — re-imports the 2 public functions instead of defining them.
- `src/entities/archetype_factory.py` — real personality/`ActionStyle` seeding, `seed` parameter.
- `src/worldassembly/entity_spawner.py` — `seed` threading, legacy-guard personality seeding.
- `src/scenarios/catalog_state_builder.py` — wires its own existing `seed` through.
- `src/content/matrix.py` — corrected the `social/personality_bias` entry's `evidence_tests`.
- `tests/unit/content_semantics/test_personality.py` — new.
- `tests/unit/entities/test_archetype_entity_factory.py`,
  `tests/unit/worldassembly/test_entity_spawner_legacy_guard.py` (new),
  `tests/integration/worldassembly/test_world_entity_spawner.py`,
  `tests/unit/worldbuilding/test_world_compiler.py` (2 tests moved out) — test coverage.
- `docs/world/assembly_contract.md`, `docs/mechanics/content_usage_matrix.md` — updated.

## Completion Summary
Closed the second, previously-disclosed-but-unfixed half of the "personality is uncorrelated with
race/faction" gap: entities spawned through `ArchetypeEntityFactory`/`WorldEntitySpawner` now get
the same real, race-correlated personality and `ActionStyle` mechanism this session's sibling
combat tickets already shipped for the live `WorldCompiler.compile()` path — implemented via a
real architecture improvement (extracting shared logic into `content_semantics/`, matching this
repo's own established precedent) rather than duplicating or cross-importing backward. Real impact
remains honestly confirmed limited to certification/integration test infrastructure today — this
ticket closes real technical debt, it does not change any currently-scored combat outcome. Two
real regressions introduced by the refactor were caught by existing tests/gates and fixed properly
(not silently worked around) before this ticket's own closure.
