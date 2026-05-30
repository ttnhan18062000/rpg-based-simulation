# Implementation Plan - Detour Depth (Task 10)

## Proposed Changes

- Rename `detour_depth` config parameter to `reserved_detour_depth` in:
  - `src/core/strategic.py`
  - `src/core/builder.py`
  - `src/strategy/cognition_capacity.py`
  - `tests/unit/strategic/test_cognition_capacity.py`

## Verification Plan

Run capacity unit tests:
`pytest tests/unit/strategic/test_cognition_capacity.py`
