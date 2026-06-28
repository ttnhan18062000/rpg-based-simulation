---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260627-P2J-PATCHES-TYPE
phase: done
date: 2026-06-27
tags: [p2, type-safety, engine, patches, merge, return-type]
---

# TCK-20260627-P2J-PATCHES-TYPE

## Title
Narrow `patches.py merge()` return type from `Any`

## Status
DONE

## Tier
hotfix

## Type
refactor

## Priority
P2

## Request Summary
`src/engine/patches.py:29` — the `merge()` function is the only `Any`-return in an engine-tier module that is not a serialization helper. A type error in a merged patch value is invisible until the downstream pipeline consumer processes it. Source: D13 F5, Risk 6/15.

## Scope
- Read `merge()` at `src/engine/patches.py:29` to understand its inputs and output shape.
- Narrow the return type from `Any` to the actual merged type (likely the same type as its inputs, or a `MergedPatch` TypedDict / dataclass).
- Update callers if the type narrowing causes downstream type errors.

## Out of Scope
- Changes to merge logic or behavior.
- Other type issues in `patches.py`.

## Acceptance Criteria
- [ ] `merge()` return annotation is no longer `Any`.
- [ ] The return type accurately reflects what `merge()` actually produces.
- [ ] `mypy src/engine/patches.py` passes.
- [ ] Existing `ComponentPatch` / patches tests pass.

## Related Tickets
- TCK-20260627-P2I-WORKFLOW-TYPES (parallel typing cleanup sprint)
- TCK-20260627-P1F-ABANDONMENT-TYPE (parallel typing cleanup sprint)

## Related Docs
- `docs/audits/D13_type_safety.md` F5
- `docs/engine/authoritative_apply_contract.md` §3 (ComponentPatch hierarchy)

## Related Stored Artifacts
- N/A

## Related Code Areas
- `src/engine/patches.py:29` (primary)
- `tests/unit/optimization/test_component_patches.py` (reference test)

## Assumptions / Open Questions
- `merge()` likely takes two `ComponentPatch`-typed arguments and returns a merged `ComponentPatch` — confirm by reading the function.
- If inputs are generic (merge of any patch type), a TypeVar-bound approach may be needed.

## Implementation Notes
- Added `Self` to the `typing` import in `src/engine/patches.py` (available Python 3.11+; project runs 3.13).
- Changed `ComponentPatch.merge(self, other: Any) -> Any` to `merge(self, other: Self) -> Self`.
- All concrete subclasses (`KindPatch`, `LifecyclePatch`, etc.) already had properly typed overrides; no caller changes required.
- No behavior change — annotation only.

## Test Summary
- Regression: `pytest tests/unit/optimization/ -m "not slow"`.
- Type check: `mypy src/engine/patches.py`.

## Files Changed
- `src/engine/patches.py` — added `Self` to typing import; changed `ComponentPatch.merge()` signature from `(other: Any) -> Any` to `(other: Self) -> Self`
- `docs/parity_ledger/infrastructure.yaml` — added INFRA-226

## Completion Summary
Added `typing.Self` to `src/engine/patches.py` imports and narrowed `ComponentPatch.merge()` base class signature from `(other: Any) -> Any` to `(other: Self) -> Self`. All 16 concrete subclasses already had properly typed overrides; no callers required changes. Annotation-only — zero behavior change. 89 tests passed. Parity ledger entry INFRA-226 added. Resolves D13 F5 (Risk 6/15).
