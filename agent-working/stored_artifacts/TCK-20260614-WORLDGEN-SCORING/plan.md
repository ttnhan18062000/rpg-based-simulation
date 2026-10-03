# Plan — TCK-20260614-WORLDGEN-SCORING

## Goal
Create `src/worldgeneration/scorer.py` with `ModuleScore` dataclass and `ModuleScorer` class.

## Files to Create
1. `src/worldgeneration/scorer.py` — new implementation file
2. `tests/unit/worldgeneration/test_module_scorer.py` — unit tests

## Files to Update
1. `docs/parity_ledger/substrate.yaml` — add SUBSTRATE-NEW-008
2. `tickets/inprogress/TCK-20260614-WORLDGEN-SCORING.md` — ticket copy
3. `tickets/working_log.csv` — append entry

## Implementation Design

### ModuleScore
- Frozen dataclass
- Fields: `module_id: str`, `score: float`, `reasons: list[str]`, `dimensions: dict[str, float]`

### ModuleScorer.score()
- Pure static method: `score(intent, modules) -> Dict[str, ModuleScore]`
- Short-circuit for required_modules: score=1.0, reasons=["required by intent"]
- 4 scoring dimensions for non-required modules:
  1. `module_type`: settlement→high if settlement_style!="none", terrain→1.0, else 0.3
  2. `danger_level`: modules with observability_tags∩{hostile,conflict,danger_zone} or module_type in {conflict,danger_zone} → proportional to danger_level/5.0
  3. `resource_density`: modules with resource_recipes or module_type=="economy" → proportional to resource_density
  4. `population_scale`: settlement/population module_type → proportional to population_scale
- Normalize: avg(dimensions.values()) clamped to [0.0, 1.0], rounded to 4dp

## Sequence
1. Create staging artifacts (this file)
2. Create ticket in inprogress
3. Implement scorer.py
4. Write tests
5. Update parity ledger
6. Verify tests pass
7. Finalize
