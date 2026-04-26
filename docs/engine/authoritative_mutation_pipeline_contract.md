# Authoritative Mutation Pipeline Contract

This document integrates the **Refinement** and **Apply** contracts into a unified specification for the `src` state transition lifecycle.

## 1. The Pipeline Law: "Proposal -> Refine -> Apply"

The engine enforces a strict separation between thought (Proposal), resolution (Refine), and authority (Apply).

1.  **Proposal**: Semantic workers suggest deltas based on isolated snapshots.
2.  **Refine**: The `AuthoritativeApplyPipeline` consolidates deltas and tie-breaks conflicts.
3.  **Apply**: The `ApplyPath` commits the consolidated delta to the live state.

## 2. Refinement stage (The Filter)
Refinement is responsible for:
- Mapping navigation targets to tile steps.
- Checking resource node charges before harvesting.
- Resolving occupancy conflicts between entities.
- Scaling regional hazards based on calamities.

## 3. Apply stage (The Commit)
Apply is responsible for:
- Transforming the frozen `AuthoritativeState` into a new generation.
- Advancing the tick and world-time markers.
- Emitting the final `REFINED_UPDATE` for replay integrity.

## 4. Why This Split Matters
By splitting Refinement from Apply, the engine achieves:
- **Deterministic Rejection**: We can reject a move (Refine) without losing the intent (Proposal) or corrupting the world (Apply).
- **Concurrency Safety**: Workers can run in parallel (Proposal) while resolution (Refine) and commitment (Apply) remain strictly sequential and deterministic.

## 5. Verification Bundle
- [Refinement Contract](authoritative_refinement_contract.md)
- [Apply Contract](authoritative_apply_contract.md)
- `tests/engine/test_pipeline_contract.py`
