---
ticket_id: TCK-20260619-E23-QUEST-GENERATION
phase: test_plan
date: 2026-06-20
---

# Test Plan: Pressure-Driven Quest Generation

## Unit Tests

### Extend `tests/unit/quest/test_quest_generation.py` (E23A)
- `test_resource_crisis_quest_generated_on_depletion` — inject RESOURCE_DEPLETED event; assert QuestOpportunityGenerator produces a `resource_crisis` QuestOpportunity with correct fields
- `test_quest_generation_determinism` — same depletion signal + same seed → same quest id and parameters

### New `tests/unit/quest/test_quest_lifecycle.py` (E23B)
- `test_quest_lifecycle_transitions` — OFFERED→ACTIVE→PROGRESSED→COMPLETED; assert each transition valid
- `test_quest_expires_after_expiry_ticks` — tick past expiry_ticks; assert EXPIRED state
- `test_quest_registry_contains_active_quest` — after OFFERED, assert quest_registry[id] exists with status OFFERED

### New `tests/unit/quest/test_quest_rewards.py` (E23C)
- `test_quest_completion_adds_gold_and_xp` — apply COMPLETED transition; assert entity receives gold + XP via reward pipeline
- `test_quest_completion_is_authoritative` — assert reward applied through authoritative pipeline (not direct mutation)

### New `tests/unit/domains/adventure/test_hero_quest_scoring.py` (E23D)
- `test_hero_entity_scores_quest_above_harvesting` — HERO entity with matching capability; assert quest route score > GATHER_RESOURCE route score
- `test_non_hero_entity_unaffected` — non-HERO entity; assert quest route score unchanged vs baseline

## Integration Tests

### New `tests/integration/scenarios/test_pressure_quest.py` (E23C/D)
- `test_resource_crisis_quest_starts_after_depletion` (@slow @integration) — 400-tick run; deplete node; assert HERO entity starts `resource_crisis` quest
- `test_quest_completed_produces_gold_and_xp` (@slow @integration) — 1000-tick run; assert ≥1 quest COMPLETED with non-zero reward in entity state

## Validation Commands
```bash
pytest tests/unit/quest/ -x -v
pytest tests/unit/domains/adventure/test_hero_quest_scoring.py -x -v
pytest tests/integration/scenarios/test_pressure_quest.py -x -v -m slow
pytest tests/unit/quest/test_quest_generation.py -x -v  # regression (existing)
```
