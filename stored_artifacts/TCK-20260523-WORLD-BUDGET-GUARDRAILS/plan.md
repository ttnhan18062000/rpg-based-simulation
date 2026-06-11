---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260523-WORLD-BUDGET-GUARDRAILS
artifact_type: plan
tags: [world, budget, guardrails]
---

# Implementation Plan — Milestone 74 Resource and Storage Guardrails

We will implement robust budget specifications, runtime validation guardrails, and artifact storage estimations across execution profiles.

## Proposed Changes

### Worldbuilding Component

#### [MODIFY] [schema.py](file:///home/vboxuser/Work/rpg-based-simulation/src/worldbuilding/schema.py)
- Create `BudgetSpec` Pydantic class:
  ```python
  class BudgetSpec(BaseModel):
      model_config = ConfigDict(frozen=True)
      max_entities: Optional[int] = Field(None, ge=0)
      max_regions: Optional[int] = Field(None, ge=0)
      max_resource_nodes: Optional[int] = Field(None, ge=0)
      max_buildings: Optional[int] = Field(None, ge=0)
      max_expected_artifact_mb: Optional[float] = Field(None, ge=0.0)
  ```
- Add `budgets: Optional[BudgetSpec] = Field(None)` to `WorldSpec` class.

#### [MODIFY] [validator.py](file:///home/vboxuser/Work/rpg-based-simulation/src/worldbuilding/validator.py)
- Implement `BudgetProfile` configuration representing default thresholds:
  - `local_dev`: 1,000 entities, 50 regions, 500 resource nodes, 100 buildings, 500.0 MB expected artifact size.
  - `ci`: 500 entities, 20 regions, 100 resource nodes, 20 buildings, 100.0 MB expected artifact size.
  - `long_run_lab`: 10,000 entities, 200 regions, 2,000 resource nodes, 500 buildings, 2,000.0 MB expected artifact size.
- Implement pluggable validator rules:
  - `BudgetGuardrailRule`: Enforces maximum counts for entities, regions, resources, buildings, and total map area (area > 1,000,000 is WARNING).
  - Checks are compared against the custom limits declared in `WorldSpec.budgets` or the active `BudgetProfile`.
  - Exceeding profile budgets raises `ERROR` or `WARNING` depending on configuration.
- Implement an estimated artifact size calculator:
  - Artifact Size Estimate = `(Total Entities * Expected Ticks * 0.0001) + (Total Resource Nodes * Expected Ticks * 0.00005)` MB.
  - Ticks defaults to 1,000 if not specified.
  - Flags WARNING if estimate exceeds `max_expected_artifact_mb`.

### Tests

#### [NEW] [test_world_budget_guardrails.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/worldbuilding/test_world_budget_guardrails.py)
- Unit tests verifying:
  - Oversized entities rejection under `local_dev`.
  - Expansion capacity under `long_run_lab`.
  - Expected artifact warnings execution.
  - Valid budget report metadata integration.
