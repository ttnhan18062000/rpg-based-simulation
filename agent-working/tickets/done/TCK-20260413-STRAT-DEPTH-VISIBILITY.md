---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260413-STRAT-DEPTH-VISIBILITY
phase: done
date: 2026-04-13
tags: [strat, depth, visibility]
---

# TCK-20260413-STRAT-DEPTH-VISIBILITY

## Title
Strategic Lifecycle & Observability Hardening

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Expand the strategic cognition layer's depth and visibility by hardening transport stability, ensuring debug rendering safety, and enriching the cognition graph with durable narrative elements (turning points, attachments).

## Scope
- [x] Strategic update transport and merge stability tests (M1 Task 3).
- [x] Inspector smoke tests for empty/populated strategic state (M1 Task 2).
- [x] Finalize Milestone 6 by adding Turning Points and Place Attachments to the cognition graph export.
- [x] Implement history-sensitive (thresholded) reprioritization scenarios (M5 Task 1).

## Out of Scope
- Global consequence propagation (Phase 4).
- Cooperation E2E scenarios (Milestone 4 Task 1).

## Acceptance Criteria
- [x] ActionSystem.apply_strategic_update proven idempotent and stable under repeated IDs.
- [x] EntityInspector proven crash-free for all strategic population depths.
- [x] Cognition graph contains TurningPoints and PlaceAttachments with deterministic edges.
- [x] Strategic integration tests cover thresholded reprioritization (e.g. repeated near-death).
- [x] 100% stability in the new test suite.

## Related Tickets
- TCK-20260413-STRAT-REPLAY-DETERMINISM (Completed)

## Related Docs
- strategy_implementation_updated.md

## Related Code Areas
- src/systems/gameplay/action_system.py
- src/ui/cli/inspector.py
- src/core/logic/cognition_graph_exporter.py
- src/core/models/base.py

## Implementation Notes
- Resolved a critical Python 3.13 pickling error for MappingProxyType in Snapshot generation.
- Hardened EntityInspector against None fields by implementing robust fallback rendering.
- Expanded graph edges to include narrative causality (TurningPoint -> Project).

## Test Summary
- tests/integration/strategy/test_strategic_transport.py (3 PASSED)
- tests/ui/test_inspector_strategy_smoke.py (4 PASSED)
- tests/integration/strategy/test_strategic_continuity.py (2 PASSED)
- tests/e2e/strategy/test_strategic_regression.py (Full regression verified)

## Files Changed
- src/core/models/base.py
- src/core/logic/cognition_graph_exporter.py
- src/ui/cli/inspector.py
- src/systems/gameplay/action_system.py
- tests/integration/strategy/test_strategic_transport.py
- tests/integration/strategy/test_strategic_continuity.py
- tests/ui/test_inspector_strategy_smoke.py

## Completion Summary
Sub-project 4 is complete. The strategic cognition layer is now structurally hardened for observational safety and narrative continuity. The critical MappingProxyType pickling bug in Python 3.13 has been resolved, securing the snapshot pipeline.
