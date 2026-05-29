# Cognition Hierarchy Migration & Deprecation Plan

This document details deprecated legacy aspect fields, temporary whitelisted accessors, and the clear removal target to achieve full structural compliance with the nested `CognitionModel` hierarchy.

## 1. Migration Map

| Legacy Aspect Field | New Nested Hierarchy Path | Whitelisted Compatibility Accessor | Removal Target |
| :--- | :--- | :--- | :--- |
| `entity.self_awareness` | `entity.cognition.subjective.self.awareness` | Yes (Internal) | v2.2 |
| `entity.need_interpretation`| `entity.cognition.subjective.self.needs` | Yes (Internal) | v2.2 |
| `entity.knowledge_model` | `entity.cognition.subjective.knowledge` | Yes (Internal) | v2.2 |
| `entity.causal_memory` | `entity.cognition.memory.causal` | Yes (Internal) | v2.2 |
| `entity.spatial_memory` | `entity.cognition.memory.spatial` | Yes (Internal) | v2.2 |

---

## 2. Hard Deprecation Rule

> [!WARNING]
> No downstream domain service or presentation layer may directly read or write to flat aspects whitelisted above after version v2.2. All access must use fully canonical nested paths.
