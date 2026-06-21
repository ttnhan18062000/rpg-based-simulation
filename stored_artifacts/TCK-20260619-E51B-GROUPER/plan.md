---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E51B-GROUPER
artifact_type: plan
tags: [chronicle, grouper, event-hierarchy]
---

# Plan — TCK-20260619-E51B-GROUPER

## Implementation Steps

1. Create `src/domains/chronicle/grouper.py`:
   - Frozen dataclasses: `Incident`, `Episode`, `Era`, `ChronicleHierarchy`
   - `ChronicleGrouper` class with `INCIDENT_TICK_WINDOW=50`, `ERA_EPISODE_MIN=3`
   - `group()`, `_group_incidents()`, `_group_episodes()`, `_group_eras()`

2. Add tests to `tests/unit/chronicle/test_chronicle_compiler.py`:
   - `test_event_grouping_produces_incident_clusters` (AC-1: ≥2 incidents from 15 events)
   - `test_chronicle_hierarchy_contains_all_four_levels` (AC-2: all 4 levels non-empty)
   - Additional edge case tests for robustness

3. Add parity ledger entry `SOC-CHRON-002` to `docs/parity_ledger/social_narrative.yaml`

4. Finalize ticket, working log, monitoring records, commit.

## No Other Files Changed
- `significance.py` — no changes needed
- `state.py` — no changes needed
- No doc updates needed (no user-facing behavior change)
