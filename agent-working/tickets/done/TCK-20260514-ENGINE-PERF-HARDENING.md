---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260514-ENGINE-PERF-HARDENING
phase: done
date: 2026-05-14
tags: [engine, perf, hardening]
---

# TCK-20260514-ENGINE-PERF-HARDENING

## Title
V2 RPG Engine Performance Hardening - Phase 3

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Optimize V2 Engine performance for 1,000+ entities by reducing object churn and improving lookup efficiency.

## Scope

- Implement lazy dictionary reconstruction in `AuthoritativeState` and `ApplyPath`.
- Cache regional lookups via `NavigationComponent.region_id`.
- Optimize spatial checks in `LegalityServiceV2.has_line_of_sight`.
- Fix determinism regression in replay tests.
- Optimize `AuthoritativeState.to_readonly` to reuse the read-only entities cache.
- Optimize `ApplyPath.apply_partial` to avoid redundant dictionary creation.
- Optimize `LegalityServiceV2.has_line_of_sight` to use `building_tiles` spatial index.
- Optimize `ApplyPath.apply_passive` to use cached `region_id` for entities.

## Out of Scope
- Major architectural changes to the worker protocol.
- Changes to the frontend or non-engine systems.

## Acceptance Criteria
- `IDLE_1000` scenario compute time reduced further (goal: < 40ms).
- Total `replace()` and dictionary creation calls reduced.
- All core integrity and unit tests pass.

## Related Tickets
- TCK-20260514-CORE-STABILIZATION (Previous phase)

## Related Docs
- logic_checklist_exhaustive_v2.md

## Related Code Areas
- src/core/state.py
- src/engine/apply.py
- src/engine/legality.py

## Implementation Notes
- Use `slots=True` for any new components.
- Maintain authoritative determinism and immutability.

## Test Summary

- `tests/unit/kernel/test_performance_integrity.py`: New suite covering cache validity and lazy reconstruction.
- `tests/unit/kernel/test_replay_determinism.py`: Fixed audit mode regression.
- `scripts/profile_engine.py`: Verified idle performance with 1,000 entities.

## Files Changed

- `src/core/state.py`
- `src/engine/apply.py`
- `src/engine/legality.py`
- `tests/unit/kernel/test_replay_determinism.py`
- `tests/unit/kernel/test_performance_integrity.py`

## Completion Summary

Successfully implemented Phase 3 optimizations. Core simulation tick (idle) now achieves ~45ms for 1,000 entities, meeting the 50ms budget (excluding persistence overhead).
