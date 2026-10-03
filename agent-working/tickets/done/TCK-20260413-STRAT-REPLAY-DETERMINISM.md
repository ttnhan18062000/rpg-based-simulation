---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260413-STRAT-REPLAY-DETERMINISM
phase: done
date: 2026-04-13
tags: [strat, replay, determinism]
---

# TCK-20260413-STRAT-REPLAY-DETERMINISM

## Title
Strategic Replay & Determinism: Snapshot Safety and Graph Hardening

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Harden simulation replay stability by ensuring snapshot deep isolation and refine strategic observability through enhanced cognition graph exports.

## Scope
- [x] Milestone 4: Strategic Replay Stability (Snapshot deep isolation fix)
- [x] Milestone 5: Graph Export Hardening (Structural links: Lead -> Obj, Blocker -> Obj)
- [x] Milestone 6: Outcome Grounding (Verify lead resolution provenance)

## Out of Scope
- Infrastructure changes (Sub-project 1 complete)
- Structural security fixes (Sub-project 2 complete)

## Acceptance Criteria
- [x] WorldStrategicRegistry.copy() performs a deep copy to ensure snapshot isolation.
- [x] EntityCognitionExporter includes edges between Leads and the Objectives they support.
- [x] EntityCognitionExporter includes edges between Blockers and the Objectives they block.
- [x] Deterministic simulation replay yields byte-identical graph exports from recovered snapshots.
- [x] "Solved" leads correctly identify their world-state source (provenance check).

## Related Tickets
- TCK-20260413-STRAT-INFRA-REMEDIATION (Completed)
- TCK-20260413-STRAT-STRUCTURAL-SECURITY (Completed)

## Related Docs
- docs/specs/2026-04-13-trust-boundary-remediation-design.md

## Related Code Areas
- src/core/models/world_strategy.py
- src/core/logic/cognition_graph_exporter.py
- tests/integration/strategy/test_cognition_graph_regression.py

## Implementation Notes
- Fixed deep isolation bug in WorldStrategicRegistry by enforcing model_copy(deep=True).
- Implemented edge factory for strategic narrative links (Leads/Blockers) in the Cytoscape adapter.

## Test Summary
- tests/integration/strategy/test_strategic_replay_determinism.py (Passed)
- tests/integration/strategy/test_cognition_graph_regression.py (Updated & Passed)

## Files Changed
- src/core/models/world_strategy.py
- src/core/logic/cognition_graph_exporter.py
- tests/integration/strategy/test_strategic_replay_determinism.py
- tests/integration/strategy/test_cognition_graph_regression.py

## Completion Summary
Sub-project 3 is complete. The strategic snapshot pipeline is now byte-identical and isolation-safe. Cognition graphs now expose the causal links between uncertainty (leads/blockers) and strategic intent (objectives).
