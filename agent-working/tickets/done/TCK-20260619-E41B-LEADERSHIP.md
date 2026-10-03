---
status: historical
layer: social
authority: P1
audience: agent
ticket_id: TCK-20260619-E41B-LEADERSHIP
phase: done
date: 2026-06-20
tags: [party, leadership-election, lifecycle, sociability, phase-4]
---

# TCK-20260619-E41B-LEADERSHIP

## Title
Epic 4.1B · Sustained Party Lifecycle + Leadership Election

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
No mechanism exists to sustain party leadership or detect leadership transitions. This ticket implements `PartyLifecycleService` with periodic leadership election using `sociability` (OCEAN personality trait) and basic cohesion checks.

**Requires:** TCK-20260619-E41A-GROUP-LIFECYCLE

## Scope

New file `src/systems/social_systems/party_lifecycle.py`:
- `PartyLifecycleService.check_leadership()` static method with deterministic election logic.
- Sociability read from `entity.identity.personality.sociability`.
- Returns `(Optional[GroupRecord], Optional[LeadershipChangedEvent])` tuple.
- Wired into `src/engine/pipeline_phases/groups.py` `GroupPhase.resolve()` after GroupSystem.

## Acceptance Criteria
- [x] `test_leadership_election_picks_highest_sociability` passes (leader change when diff ≥ 0.2)
- [x] Leadership change emits `leadership_changed` SimulationEvent (`LeadershipChangedEvent`)

## Related Tickets
- TCK-20260619-E41-PARTY-LOOP (parent epic)
- TCK-20260619-E41A-GROUP-LIFECYCLE (required — done)
- TCK-20260619-E41C-REWARD-DIST (blocked on this)

## Related Code Areas
- `src/systems/social_systems/party_lifecycle.py` (new)
- `src/engine/pipeline_phases/groups.py` (wired lifecycle pass)
- `src/observability/events.py` (LeadershipChangedEvent added)
- `docs/parity_ledger/social_narrative.yaml` (SOC-228 added)

## Test Summary
```bash
pytest tests/unit/social/test_party_lifecycle.py -x -v
# 6 passed
pytest tests/unit/social/test_group_lifecycle_fields.py tests/unit/social/test_party_coordination.py tests/unit/social/test_groups.py -x -v
# 15 passed (regression)
```

## Files Changed
- `src/systems/social_systems/party_lifecycle.py` — NEW
- `src/observability/events.py` — Added `LeadershipChangedEvent`
- `src/engine/pipeline_phases/groups.py` — Wired `PartyLifecycleService` into `GroupPhase.resolve()`
- `tests/unit/social/test_party_lifecycle.py` — NEW (6 tests)
- `docs/parity_ledger/social_narrative.yaml` — Added SOC-228

## Implementation Notes
- `GroupUpdate` dataclass does not exist; mutations returned as `GroupRecord` via `dataclasses.replace`.
- Sociability field path is `entity.identity.personality.sociability` (not `entity.personality.sociability`).
- Wired in `GroupPhase.resolve()` rather than `kernel.py` — group pipeline phase is the correct injection point per existing architecture.
- `GroupPhase.last_tick_events` list collects events per tick for test inspection and downstream dispatch.
- Determinism: tiebreaker is `min(entity_id)` when multiple members share highest sociability.

## Completion Summary
Implemented `PartyLifecycleService` with periodic sociability-based leadership election (interval=100 ticks). Added `LeadershipChangedEvent` to observability events. Wired into `GroupPhase.resolve()` after cohesion/dissolution processing. All 6 unit tests pass; 15 regression tests pass. SOC-228 parity entry added.
