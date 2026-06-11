---
status: historical
layer: testing
authority: P2
audience: developer
---

# Phase 2 Self-Model Test Coverage Map

This document catalogs all test suites covering the Bottom-Up Entity Self Model implementation for Phase 2.

## Covered Components & Services

| Feature / Area | Component / Service under Test | Unit Test File | Status | Key Coverage Scenarios |
| :--- | :--- | :--- | :--- | :--- |
| **Component Schemas** | `SelfAwarenessComponent`, `NeedInterpretationComponent`, `CapabilityEstimateComponent`, `KnowledgeModelComponent`, `SelfModelBundle`, `V2EntityBuilder` | `tests/unit/entity/test_phase2_self_model_components.py` | **100% PASS** | Default construction, canonical serialisation stability, equality determinism, and builder integration |
| **Self-Assessment** | `SelfAssessmentService` | `tests/unit/cognition/test_phase2_self_assessment_service.py` | **100% PASS** | Low HP weaknesses, stamina exhaustion, biological pressure (hunger/sleep), weapon gaps, composite stress/confidence |
| **Need Interpretation** | `NeedInterpretationService` | `tests/unit/cognition/test_phase2_need_interpretation_service.py` | **100% PASS** | Healing priority, hunger urgency, sleep recovery, weapon improvement, full inventory pressure, gold constraints, knowledge gaps |
| **Capability Estimates** | `CapabilityEstimateService` | `tests/unit/cognition/test_phase2_capability_estimate_service.py` | **100% PASS** | Scoped estimates for combat (rat vs wolf), travel safety, tool-based gathering, item-based crafting, and missing recipe handling |
| **Knowledge Model** | `KnowledgeModelService` | `tests/unit/cognition/test_phase2_knowledge_model_service.py` | **100% PASS** | Recipe learning from blacksmith, information opacity preservation, guide partial clues (leads), danger ratings, unknowns, gold limits |
| **Update Phase** | `SelfModelUpdatePhase` | `tests/unit/cognition/test_phase2_self_model_phase.py` | **100% PASS** | First-run execution, dirty-check skip for unchanged entities, HP-triggered updates, event-driven knowledge assimilation, trace events |
| **Integration Scenarios** | Full Interpretation Pipeline | `tests/integration/scenarios/test_phase2_self_model_scenarios.py` | **100% PASS** | Vulnerability prioritization (2.1), Recipe gaps (2.2), Equipment capability delta (2.3), Damage impact (2.4), Information opacity (2.5) |
| **Performance Budgets** | Phase execution timing | `tests/perf/test_phase2_self_model_budget.py` | **100% PASS** | Timing verification of 100 entity updates, clean dirty-check skip performance verification (>5x speedup) |

## Strategic Baseline Regression

To ensure no existing features were broken:
* **Command**: `pytest tests/unit/strategic/ -m "not slow" -q`
* **Baseline Status**: **166+ PASS** (Verified no regressions in arena, combat, movement, or strategic reasoning)
