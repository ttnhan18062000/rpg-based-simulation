# Implementation Plan: World Validation Layer

Build the pluggable validation rules framework and `WorldValidator` component.

## Proposed Changes

### Worldbuilding Framework

#### [NEW] [validator.py](file:///home/vboxuser/Work/rpg-based-simulation/src/worldbuilding/validator.py)
- Define `ValidationIssue` (dataclass or namedtuple) with `rule_id`, `severity`, `message`, `path`.
- Define base class `WorldValidationRule`.
- Implement specific rules:
  - `EntityFactionExistRule` (`WORLD-REF-001`, ERROR)
  - `EntitySpawnRegionExistRule` (`WORLD-REF-002`, ERROR)
  - `ResourceRegionExistRule` (`WORLD-REF-003`, ERROR)
  - `BuildingRegionExistRule` (`WORLD-REF-004`, ERROR)
  - `RegionBoundsWithinTopologyRule` (`WORLD-TOPO-001`, ERROR)
  - `NoResourcesWarningRule` (`WORLD-WARN-001`, WARNING)
  - `HighEntityDensityWarningRule` (`WORLD-WARN-002`, WARNING)
- Implement `WorldValidator`:
  - `validate(self, spec: WorldSpec, raw_data: dict = None, strict: bool = False) -> list[ValidationIssue]`
  - Aggregates issues, validates unknown sections, and raises `InvalidWorldSpecError` if any ERROR is found (or if `strict=True` and any WARNING/ERROR is found).

#### [MODIFY] [__init__.py](file:///home/vboxuser/Work/rpg-based-simulation/src/worldbuilding/__init__.py)
- Export `WorldValidator`, `ValidationIssue`, and related rules/exceptions.

#### [NEW] [test_world_validation_rules.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/worldbuilding/test_world_validation_rules.py)
- Test suite validating individual rule logic.

#### [NEW] [test_world_validator.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/worldbuilding/test_world_validator.py)
- Test suite validating validator orchestration, strict mode, unknown sections, and determinism.

---

## Verification Plan

### Automated Tests
Run unit tests with pytest:
```bash
pytest tests/unit/worldbuilding/test_world_validator.py tests/unit/worldbuilding/test_world_validation_rules.py
```
Ensure all tests execute cleanly with zero errors.
