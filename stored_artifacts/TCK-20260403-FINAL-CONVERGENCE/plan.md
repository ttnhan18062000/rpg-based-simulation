---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260403-FINAL-CONVERGENCE
artifact_type: plan
tags: [final, convergence]
---

# Implementation Plan: Final Architectural Stability & Convergence (TCK-20260403-FINAL-CONVERGENCE)

Complete the remaining items in `final_implementation_plan_3.md` to achieve full architectural convergence and stability.

## Proposed Changes

### Core Models & Immutability

#### [MODIFY] [base.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/models/base.py)
- Refactor `freeze()` to recursively handle nested standard collections (`list`, `tuple`, `dict`) of non-`SimulationModel` items.
- Ensure that `freeze()` on a `SimulationModel` results in its entire structure being immutable.

### Action System & Typed Records

#### [MODIFY] [base.py](file:///home/vboxuser/Work/rpg-based-simulation/src/actions/base.py)
- Audit `TargetUnion` and `IntentUpdate` subclasses to ensure no `Any` types remain in core simulation paths.
- (Note: `intent_metadata` appears already purged from `src/`, but I will double-check for legacy shims in `systems/`).

### Infrastructure & Serialization

#### [MODIFY] [engine_manager.py](file:///home/vboxuser/Work/rpg-based-simulation/src/api/engine_manager.py)
- Finalize and unify the transport payload caching. Ensure it is effectively used by all protocols (REST/WS).

### Test Recovery & Stabilization

#### [FIX] Resolve 26 failures
- Resolve errors in:
    - [test_hero_lifecycle.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/integration/test_hero_lifecycle.py)
    - [test_invariants.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/integration/test_invariants.py)
    - [test_snapshot_safety.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/integration/test_snapshot_safety.py)
- (Hypothesis dependency needs to be addressed).

## Verification Plan

### Automated Tests
- `pytest tests/integration/test_snapshot_safety.py tests/integration/test_invariants.py tests/integration/test_hero_lifecycle.py`
- `pytest tests/unit/core/test_aoa_integrity.py`

### Manual Verification
- None required.
