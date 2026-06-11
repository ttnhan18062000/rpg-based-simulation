---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260610-SENSE-PERCEPTION-GATE
phase: done
date: 2026-06-10
tags: [sense, perception, gate]
---

# TCK-20260610-SENSE-PERCEPTION-GATE

## Title
Add PerceptionGate consuming sense_profile from catalog for entity perception gating

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Phase 42.2. Entity archetypes carry `sense_profile_id` in `identity.properties` (set by `worldassembly/archetype_factory.py`). Currently no behavior consumer reads this. This ticket adds `PerceptionGate.can_perceive(source_entity, target_or_event, context) -> PerceptionResult` that uses the source entity's sense profile to determine whether it can detect a target. This is distinct from the existing `PerceptionFilterService` (which gates attention budget) — this gates raw detection capability.

## Scope
- Add `src/world/perception/gate.py` with `PerceptionGate` class
- Add `PerceptionResult(BaseModel)` with: `perceived: bool`, `confidence: float`, `signals_used: list[str]`, `profile_source: str`
- Supported sense categories: `vision`, `hearing`, `smell`, `magic_sense`, `life_sense`, `vibration`, `social_reading`
- Inputs: `sense_profile` (from catalog via `sense_profile_id`), distance, terrain/region context, target visibility/noise/scent/magic signal, current alertness
- Do not bypass relation projection — perception gating is upstream of relation classification, not a replacement
- Explicit fallback: entity with no `sense_profile_id` uses baseline humanoid perception defaults
- Tests: wolf detects scent better than normal humanoid; spider detects vibration; arcane profile detects magic signal; normal humanoid cannot detect magic signal without profile

## Out of Scope
- Complex sensory physics or ray-casting
- Connecting to decision points (that is TCK-20260610-PRESSURE-PERCEPTION-CONSUMERS)
- Changing existing `PerceptionFilterService` (attention budget gating)

## Acceptance Criteria
- [x] `PerceptionGate.can_perceive()` exists and returns `PerceptionResult`
- [x] Sense profiles consumed from catalog
- [x] `PerceptionResult` includes `profile_source` field
- [x] Perception is deterministic for same inputs
- [x] Perception does not bypass or replace relation projection
- [x] Existing movement/combat tests still pass
- [x] No race-specific perception scripts inside gate
- [x] 4 archetype test cases pass

## Related Tickets
- TCK-20260610-MOTIVATION-PRESSURE-RESOLVER (companion — pressure inputs)
- TCK-20260610-PRESSURE-PERCEPTION-CONSUMERS (downstream — connects to decisions)

## Related Docs
- `docs/mechanics/04_strategic_cognition.md`

## Related Code Areas
- `src/world/perception/gate.py` — new
- `src/content/repository.py` — catalog source for sense profiles
- `worldassembly/archetype_factory.py` — where sense_profile_id is set on entity

## Assumptions / Open Questions
- Do `sense_profile` YAML files exist in `data/content/`? If not, minimal fixture files needed alongside need/drive profiles.

## Implementation Notes
Created `src/world/perception/` package with `gate.py`. `PerceptionGate.can_perceive()` evaluates 7 sense channels (vision, hearing, smell, magic_sense, life_sense, vibration, social_reading) by multiplying sense strength × signal strength × distance_factor × terrain_modifier × alertness_factor. Score ≥ 0.2 threshold triggers perception. Entities without `sense_profile_id` or with an unrecognised id fall back to `_BASELINE_SENSE` (normal_humanoid_senses equivalent). Sense strengths loaded from `CatalogRepository.get_sense_profile()`. All channel mapping is table-driven; no race-specific scripts.

## Test Summary
11 tests in `tests/unit/world/test_sense_perception_gate.py`. Covers: wolf scent detection, wolf vs human scent confidence comparison, spider vibration, arcane magic detection, humanoid magic blindness, baseline fallback (no profile), unknown profile fallback, determinism, catalog immutability, distance confidence reduction, no-signal no-perception. All 11 pass.

## Files Changed
- `src/world/perception/__init__.py` (new)
- `src/world/perception/gate.py` (new)
- `tests/unit/world/test_sense_perception_gate.py` (new)

## Completion Summary
PerceptionGate added as read-only, data-driven gate. Sense profiles from catalog (6 profiles covering humanoid, predator, goblin, spider, arcane, undead). All 11 unit tests pass. No mutations to catalog or entity. Upstream of relation projection as specified. Ready for consumers in TCK-20260610-PRESSURE-PERCEPTION-CONSUMERS.
