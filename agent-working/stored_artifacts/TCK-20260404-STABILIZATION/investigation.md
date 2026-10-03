---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260404-STABILIZATION
artifact_type: investigation
tags: [stabilization]
---

# Investigation: AI State Regressions & Model Freezing

## Context
Following the Aspect-Oriented Architecture (AOA) pivot, several regressions have been identified in AI decision-making and core model freezing. This ticket (TCK-20260404-STABILIZATION) aims to resolve these final blockers to achieve 100% test pass rate.

## Current Findings

### 1. AI State Regressions
- `UnboundLocalError: Perception` in `navigation.py`: Likely a missing import or a variable being used before assignment.
- `NameError: HeroClass` in `base.py`: Likely a missing import or circular dependency issues common in AOA transitions.
- `AttributeError: Perception.get_faction_registry` in `combat.py`: Perception model might have changed its API or not being initialized correctly.

### 2. Core Model Freezing (`SimulationModel.freeze()`)
- `SimulationModel.freeze()` needs to handle:
    - Slotted models.
    - Already-frozen models (e.g., `Vector2`).
- Recursive freezing must use `object.__setattr__` to bypass Pydantic's frozen checks.

## Codebase Analysis

### AI Navigation (`navigation.py`)
I need to check where `Perception` is used and why it causes `UnboundLocalError`.

### AI Base (`base.py`)
I need to check where `HeroClass` is referenced.

### AI Combat (`combat.py`)
I need to check the `Perception` attribute access.

### Core Models (`src/core/models.py` or similar)
I need to find `SimulationModel.freeze()` implementation.

## Risks & Assumptions
- Circular dependencies might be introduced while fixing imports.
- Pydantic's `frozen=True` might conflict with manual freezing if not handled carefully.
