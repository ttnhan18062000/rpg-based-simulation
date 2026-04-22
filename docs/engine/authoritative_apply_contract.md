# Authoritative Apply Contract

This document defines the **Apply** stage of the `src_v2` authoritative mutation pipeline.

## 1. Overview
The Apply stage is the singular point where the refined `StateUpdate` is committed to the `AuthoritativeState`. It marks the transition from "proposed truth" to "authoritative truth."

## 2. The Singular Mutation Point
- **Law**: Authoritative world mutation MUST occur only within `ApplyPath.apply_generation`.
- **Enforcement**: Direct mutation of state objects is prevented via frozen dataclass constraints.

## 3. Deterministic Commit Order
Before application, results are sorted by the **Frozen Commit Key**:
1.  **Class Priority**: (e.g., CRITICAL > PERIODIC).
2.  **Local Priority**: System-specific weighting.
3.  **Entity ID**: The final tie-breaker for absolute determinism.

## 4. Update Consumption Rules
- **Atomic Application**: All updates within a domain (Entity, World, Building) are applied together or not at all (in case of total tick failure).
- **Domain Independence**: Rejection of a navigation update must not corrupt an unrelated inventory update (See [Partial Rejection Proof](tests_v2/engine/test_partial_rejection.py)).

## 5. Traceability (Replay-Visible Truth)
- Every applied update must be emitted as a `REFINED_UPDATE` trace event.
- Replay truth is sourced exclusively from the **post-apply state**, ensuring that "what the world became" is what the observer sees.

## 6. Verification
- `src_v2/engine/apply.py`: Authoritative implementation.
- `tests_v2/engine/test_authoritative_apply.py`: Apply-path proof.
