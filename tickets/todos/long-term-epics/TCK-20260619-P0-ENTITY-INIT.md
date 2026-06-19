---
status: open
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-P0-ENTITY-INIT
phase: open
date: 2026-06-19
tags: [entity-initialization, personality, world-compiler, class-id, phase-0, p0-foundation]
---

# TCK-20260619-P0-ENTITY-INIT

## Title
P0-4 · Entity Initialization — Seed PersonalityComponent and assign class IDs in WorldCompiler

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P0

## Request Summary
`WorldCompiler.compile()` produces `PersonalityComponent(greed=0.0, bravery=0.0, sociability=0.0, industry=0.0)` for every entity. All entities are also assigned `class_id=NOVICE` regardless of role. The OCEAN system and scoring formula are correctly implemented, but zero variation enters the system at spawn. Every behavioral differentiation measurement in Phase 1+ requires this fix.

Source: `docs/audits/D05_entity_differentiation.md` F1 (personality) and F2 (class assignment).

## Scope
- In `src/worldbuilding/compiler.py`: seed `PersonalityComponent` using `DeterministicRNG` per entity sub-seed so bravery/greed/industry/sociability vary across entities at spawn
- Sub-seed derivation: `rng.sub_seed(f"personality:{entity_id}")` pattern (consistent with engine contract; see `src/platform/rng.py:L10`)
- In `src/worldbuilding/compiler.py` or `src/systems/world_systems/generator.py:L20`: read class assignments from `data/content/spawn_tables.yaml` so class_id is assigned by role: HERO → [WARRIOR, MAGE, ROGUE]; CITIZEN → [WORKER, MERCHANT]; MONSTER → [BEAST, UNDEAD]
- If `spawn_tables.yaml` does not exist, create it with the role→class_id distribution
- ~20 lines total change

## Out of Scope
- Multi-episode personality evolution (Phase 4)
- Class ability differentiation / class-specific scoring weights (Epic 1.1)
- HERO role entity placement in worlds (Epic 1.1)

## Acceptance Criteria
- Direct state inspection at tick 0 shows personality trait variance across entities: no two entities share the same (bravery, greed, industry, sociability) tuple when seeded with different entity sub-seeds
- At least one entity per tested world has `class_id` other than NOVICE after fix
- Determinism preserved: same world seed produces same personality vectors across runs

## Related Tickets
- TCK-20260619-E11-ENTITY-IDENTITY (depends on this; Epic 1.1 measures behavioral differentiation)
- TCK-20260619-P0-HUNGER-SATIATION (sister P0 fix; both must be done before Epic 1.2 balance baseline)

## Related Docs
- `docs/audits/D05_entity_differentiation.md`
- `docs/plans/long_term_development_roadmap.md` § P0-4
- `docs/parity_ledger/substrate.yaml` (entity initialization / spawn — update entries for personality seeding)
- `docs/parity_ledger/progression.yaml` (class_id assignment — update entries for non-NOVICE class spawn)
- `docs/core/entities.md` (update if entity spawn behavior is documented here)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-AUDIT-D05/`

## Related Code Areas
- `src/worldbuilding/compiler.py` (WorldCompiler.compile())
- `src/platform/rng.py:L10` (DeterministicRNG)
- `src/systems/world_systems/generator.py:L20` (EntityGenerator)
- `src/core/state.py:L395` (AttributeComponent — class_id field)
- `data/content/spawn_tables.yaml` (create or update)

## Assumptions / Open Questions
- Personality range: is [0.0, 1.0] correct per trait, or is the range defined differently in `docs/mechanics/01_entity_anatomy.md`? Verify before seeding
- Does `EntityGenerator` or `WorldCompiler` own entity spawn? — graphify shows `EntityGenerator` in community 0 alongside `WorldCompiler`; check which is called at compile time

## Implementation Notes
Read `src/worldbuilding/compiler.py` to locate where `PersonalityComponent` is currently constructed (should be a literal `PersonalityComponent()` call with no args or all zeros). Replace with RNG-seeded values. For class assignment, look up the role in spawn_tables.yaml and pick a class_id using `rng.choice()`.

After implementation: update `docs/parity_ledger/substrate.yaml` for personality seeding entry and `docs/parity_ledger/progression.yaml` for class_id assignment entry — set `status: verified`, add `v2_evidence` and `test_path`. Run `make knowledge-index-update` if any docs/ files change.

## Test Summary
- New file `tests/unit/entity/test_entity_initialization.py`:
  - `test_entity_personality_variance_at_spawn()` — build a world, inspect tick-0 state, assert no two entities share identical (bravery, greed, industry, sociability) tuple
  - `test_class_id_non_novice_by_role()` — assert HERO-role entities have class_id in {WARRIOR, MAGE, ROGUE}; CITIZEN in {WORKER, MERCHANT}
  - `test_personality_seeding_is_deterministic()` — compile same world twice with same seed; assert identical personality vectors
- Run existing `tests/integration/kernel/test_phase2_determinism.py` to verify determinism preserved after change

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
