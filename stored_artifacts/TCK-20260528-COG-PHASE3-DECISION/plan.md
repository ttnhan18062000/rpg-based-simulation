# Implementation Plan - Phase 3: Adventure Decision Layer

This plan outlines the architecture, logic, and test suites for building the **Adventure Decision Layer** under `src/domains/adventure/`. This layer translates interpreted entity self-models and dynamic world options into structured adventure route choices, mapping the selected route to strategic projects and executable action intents.

## User Review Required

> [!NOTE]
> **Key Design Decision**: The core entity models (`EntityState`, `SelfAwarenessComponent`, etc.) remain completely clean and generic. There is **no** `AdventureReadinessComponent` or hardcoding of adventure-specific aspects. All adventure logic is kept isolated in the domain service.

> [!TIP]
> **Imperfect Personality Bias**: Entities will select their adventure routes based on subjective preferences rather than a globally perfect mathematical optimum. A brave entity accepts higher risks, while a cautious one prioritizes recovery.

## Proposed Changes

### Adventure Domain Layer

#### [NEW] [schema.py](file:///home/vboxuser/Work/rpg-based-simulation/src/domains/adventure/schema.py)
- Defines primitive frozen dataclasses:
  - `AdventureRouteOption`: Models a candidate route (family, score, risk, expectations, requirements, blockers).
  - `RejectedRoute`: Tracks alternatives with score and specific rejection reasons.
  - `AdventureDecisionResult`: Holds the chosen option, rejected routes, posture, proposed project/objective, and trace map.

#### [NEW] [generator.py](file:///home/vboxuser/Work/rpg-based-simulation/src/domains/adventure/generator.py)
- Implements `AdventureRouteGenerator`: converts entity aspects (needs, capabilities, knowledge facts) + dynamic opportunities (service and resource options) into scoped route candidates.

#### [NEW] [scoring.py](file:///home/vboxuser/Work/rpg-based-simulation/src/domains/adventure/scoring.py)
- Implements route scoring including personality biases (bravery, caution, greed, curiosity, industry, sociability).

#### [NEW] [service.py](file:///home/vboxuser/Work/rpg-based-simulation/src/domains/adventure/service.py)
- Implements `AdventureDecisionService`: evaluates generator candidates and returns the best explainable choice.

#### [NEW] [mapper.py](file:///home/vboxuser/Work/rpg-based-simulation/src/domains/adventure/mapper.py)
- Implements `RouteToProjectMapper`: maps a selected route option to standard strategic projects (`ProjectState`) and objectives (`ObjectiveState`).

#### [NEW] [resolver.py](file:///home/vboxuser/Work/rpg-based-simulation/src/domains/adventure/resolver.py)
- Implements `ObjectiveIntentResolver`: translates first objectives to immediate action intents (e.g. `MOVE_TO` or `HARVEST`).

#### [NEW] [phase.py](file:///home/vboxuser/Work/rpg-based-simulation/src/domains/adventure/phase.py)
- Implements `AdventureDecisionPhase`: runtime system phase with strict cadences and skips to protect execution budgets.

---

### Core & Tests

#### [MODIFY] [entity_base.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/entity/entity_base.md)
- Documents Phase 3 design decisions, vocabulary, and architectures.

#### [NEW] Unit and Scenario Test Suites
- Adds 10 new test files covering all units, integration phases, strategic scenarios, and performance timing gates as specified in the Phase 3 document.

---

## Verification Plan

### Automated Tests
We will run all Phase 3 tests to ensure complete success:
```bash
pytest tests/unit/domains/adventure/ tests/integration/domains/adventure/ tests/integration/scenarios/test_phase3_adventure_decision_scenarios.py tests/perf/test_phase3_adventure_decision_budget.py -v
```

### Strategic Regression Check
Ensure no existing behavioral patterns are broken:
```bash
pytest tests/unit/strategic/ -m "not slow" -q
```
