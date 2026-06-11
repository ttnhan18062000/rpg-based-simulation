---
status: active
layer: engine
authority: P1
audience: developer
---

# Authoritative Apply Contract

This document defines the **Apply** stage of the `src` authoritative mutation pipeline.

## 1. Overview
The Apply stage is the singular point where the refined `StateUpdate` is committed to the `AuthoritativeState`. It marks the transition from "proposed truth" to "authoritative truth."

## 2. The Singular Mutation Point
- **Law**: Authoritative world mutation MUST occur only within `ApplyPath.apply_generation`.
- **Enforcement**: Direct mutation of state objects is prevented via frozen dataclass constraints.

## 3. Deterministic Commit Order & ComponentPatch Hierarchy
Before application, results are processed through the `ComponentPatch` model (`src/engine/patches.py`) and applied in a fixed dependency order:
1.  **ComponentPatch Extraction**: Monolithic `EntityUpdate` objects are decomposed into non-noop component patches via `extract_patches(entity_id, update)`.
2.  **Sequential Patch Application**: Patches are applied to entity component dictionaries sequentially (`patch.apply(entity, changes)`), replacing legacy monolithic conditional blocks.
3.  **Order Sensitivity**: Fundamental properties (`KindPatch`, `IdentityPatch`, `EquipmentPatch`, `WoundPatch`) are extracted and evaluated before derived stat recalculation.
4.  **Derived Stat Tracking**: If any stat-impacting patch modifies entity attributes or modifiers, `stats_dirty` tracking triggers an isolated, deterministic derived stat recalculation at the end of the entity update cycle.

## 4. Update Consumption Rules
- **Atomic Application**: All updates within a domain (Entity, World, Building) are applied together or not at all (in case of total tick failure).
- **Domain Independence**: Rejection of a navigation update must not corrupt an unrelated inventory update (See [Partial Rejection Proof](tests/engine/test_partial_rejection.py)).

## 5. Traceability (Replay-Visible Truth)
- Every applied update must be emitted as a `REFINED_UPDATE` trace event.
- Replay truth is sourced exclusively from the **post-apply state**, ensuring that "what the world became" is what the observer sees.

## 6. Verification
- `src/engine/patches.py`: Component-level patch hierarchy and extraction.
- `src/engine/apply.py`: Authoritative ApplyPath implementation.
- `tests/unit/optimization/test_component_patches.py`: Unit verification of no-op detection, patch merging, and dependency extraction.
- `tests/integration/optimization/test_component_patch_apply_parity.py`: Integration proof of exact hash parity with legacy state application.
