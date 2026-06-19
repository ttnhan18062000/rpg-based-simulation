---
status: inprogress
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E11-ENTITY-IDENTITY
phase: scoped
date: 2026-06-19
tags: [entity-differentiation, personality, class-system, observability, behavioral-quality, epic, phase-1]
---

# TCK-20260619-E11-ENTITY-IDENTITY

## Title
Epic 1.1 · Entity Identity & Behavioral Differentiation

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
All entities currently have identical personality vectors and NOVICE class. The scoring formula is architecturally correct but receives identical inputs for every entity. Observable behavioral variation is purely positional. After this epic, two entities with different personality vectors in the same situation make observably different route choices at statistically significant rates.

Score: 9/10 · Effort: M · Source: `docs/audits/D05_entity_differentiation.md`

## Scope
- **Prerequisite:** TCK-20260619-P0-ENTITY-INIT must be complete
- Add HERO role entities (2–3 per world) with distinct archetypes to `sandbox_world` and `urban_political`
- Extend `data/content/spawn_tables.yaml` with class_id distributions: HERO→[WARRIOR, MAGE, ROGUE]; CITIZEN→[WORKER, MERCHANT]; MONSTER→[BEAST, UNDEAD]
- Add per-entity personality snapshot to LIGHT observability mode: role, class_id, personality vector, active_project_kind at tick N
- Build a 400-tick differentiation test harness: measures route-kind distribution variance across entities; fails if all entities produce identical project-kind histograms
- Calibrate personality bias weights in `src/domains/adventure/scoring.py` so high-bravery entities measurably prefer risky routes at ≥2× rate vs. low-bravery entities
- Child tickets should cover: (a) HERO entity authoring, (b) observability snapshot extension, (c) test harness, (d) scoring calibration

## Out of Scope
- Multi-episode personality evolution (Phase 4)
- Campaign-level character arcs (Phase 3)
- Party formation mechanics (Epic 4.1)

## Acceptance Criteria
- In a 400-tick `sandbox_world` run, entities in the top bravery quartile take `combat_engage` routes at ≥2× the rate of entities in the bottom quartile
- Differentiation test harness runs in CI (post-P0-1)
- No two entities in the same world have identical personality vectors at tick 0

## Related Tickets
- TCK-20260619-P0-ENTITY-INIT (prerequisite — DONE)
- TCK-20260619-E12-BALANCE-BASELINE (unlocked by this epic)

## Child Tickets (created 2026-06-19)
- TCK-20260619-E11A-HERO-AUTHORING — Author HERO entities in world files (`tickets/todos/e11-entity-identity/`)
- TCK-20260619-E11B-OBS-SNAPSHOT — Add personality snapshot to LIGHT observability mode
- TCK-20260619-E11C-DIFF-HARNESS — Build 400-tick differentiation test harness
- TCK-20260619-E11D-SCORING-CAL — Calibrate personality bias weights in adventure scoring

## Related Docs
- `docs/audits/D05_entity_differentiation.md`
- `docs/mechanics/01_entity_anatomy.md` § Core Attributes (OCEAN personality trait definitions, valid ranges — calibration must stay within ranges defined here)
- `docs/mechanics/04_strategic_cognition.md` (update personality bias weight documentation; scoring formula references personality traits from 01)
- `docs/core/attributes_and_classes.md` (class archetype definitions — HERO, WARRIOR, MAGE, ROGUE; verify IDs before authoring HERO entities)
- `docs/plans/long_term_development_roadmap.md` § Epic 1.1
- `docs/parity_ledger/strategic_cognition.yaml` (personality scoring entries — update to `verified`)
- `docs/parity_ledger/progression.yaml` (class archetype assignment entries)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-AUDIT-D05/`

## Related Code Areas
- `src/worldbuilding/compiler.py`
- `src/domains/adventure/scoring.py`
- `src/core/state.py:L395` (AttributeComponent)
- `data/content/spawn_tables.yaml`
- `data/worlds/sandbox_world/`, `data/worlds/urban_political/`

## Assumptions / Open Questions
- What observability fields are available in LIGHT mode? Read `src/observability/` before extending
- Is bravery trait already wired to a risk preference term in scoring.py, or does the calibration require adding a new term?

## Implementation Notes
Scope first, then implement as child standard tickets. The test harness is the highest-value deliverable — implement it early so you can measure as you calibrate.

After each child ticket: update `docs/parity_ledger/strategic_cognition.yaml` for personality-scoring entries and `docs/parity_ledger/progression.yaml` for class assignment entries. If `docs/mechanics/04_strategic_cognition.md` is updated with new bias weight rationale, run `make knowledge-index-update`.

## Test Summary
Per child ticket. Key test files:
- New `tests/integration/scenarios/test_entity_differentiation.py`:
  - `test_bravery_quartile_combat_rate_2x()` — 400-tick `sandbox_world`; assert top-bravery-quartile entities take `combat_engage` at ≥2× rate of bottom quartile
  - `test_no_identical_personality_vectors_at_spawn()` — tick-0 inspection; assert all personalities distinct
  - `test_differentiation_harness_runs_in_ci()` — import guard ensuring harness is picked up by `make lane-all-fast`
- New `tests/unit/entity/test_entity_archetypes.py`:
  - `test_hero_archetypes_cover_combat_mage_rogue()` — HERO entities in world have at least one of each archetype class

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
