---
status: active
layer: architecture
authority: P1
audience: developer
---

# Cognition Domain Ownership Map

This document establishes the official ownership mapping between core `CognitionModel` sub-components and their authoritative domain service logic packages.

| Cognition Sub-Model | Stored Path | Domain Service Owner Package |
| :--- | :--- | :--- |
| **`PerceptionModel`** | `cognition.subjective.perception` | `src/domains/perception/` |
| **`TemporalModel`** | `cognition.subjective.time` | `src/domains/time/` |
| **`CausalMemory`** | `cognition.memory.causal` | `src/domains/memory/` |
| **`SpatialMemory`** | `cognition.memory.spatial` | `src/domains/memory/` |
| **`MotivationModel`** | `cognition.motivation` | `src/domains/motivation/` |
| **`CommitmentModel`** | `cognition.commitment` | `src/domains/commitment/` |
| **`RelationshipModel`** | `cognition.relationships` | `src/domains/cooperation/` |
| **`RoleModelBundle`** | `cognition.role_model` | `src/strategy/` (`role_model_phase.py`, `role_model_imitation.py`; TCK-20260831-ROLE-MODEL-IMITATION) |
| **`DerivedViews`** | *N/A (Computed transiently)* | `src/views/` |
| **`DecisionTrace`** | *N/A (Observability pipeline)* | `src/observability/` |

## Decisions

### `SelfModel` / `SubjectiveModel.self` — CUT (TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION, 2026-09-01)

`core/cognition.py::SelfModel` (formerly `cognition.subjective.self`) was removed. It had zero
production constructions anywhere in `src/` — the only writer path for entity self-model data is
the real, distinct `entity.self_model` field (`SelfModelBundle`, `src/core/self_model.py`), owned by
`src/cognition/` (`SelfModelUpdatePhase`, gated by `ENABLE_SELF_MODEL_COGNITION`) and already
documented in `docs/cognition/README.md`. `entity.self_model` and `entity.cognition` are genuinely
distinct `EntityState` fields with confusingly identical component class names
(`SelfAwarenessComponent`, `NeedInterpretationComponent`, `CapabilityEstimateComponent`) — do not
reintroduce a second self-model representation under `cognition.py`.
