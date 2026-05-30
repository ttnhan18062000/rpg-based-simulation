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
| **`DerivedViews`** | *N/A (Computed transiently)* | `src/views/` |
| **`DecisionTrace`** | *N/A (Observability pipeline)* | `src/observability/` |
