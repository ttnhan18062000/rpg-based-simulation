---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261016-GRIEF-AS-STATE-GRIEF-TRIGGERS-ARE-DETECTED-AND-CARRIED-IN-AUTHORITATIVE-STATE-D80
phase: open
date: 2026-10-16
tags: []
---

# TCK-20261016-GRIEF-AS-STATE-GRIEF-TRIGGERS-ARE-DETECTED-AND-CARRIED-IN-AUTHORITATIVE-STATE-D80

## Title
Grief triggers are detected in the observability phase and held in a kernel list outside the world, so turning observability OFF changes the authoritative outcome; detect them in the authoritative pipeline and carry them as a typed record in authoritative state.

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Owner decision 80 (ii), via rpg-planner 2026-10-16: a hard bug that goes before v1. `EventExtractor.detect_grief_triggers` runs in `Kernel._phase_observability` (kernel.py ~986-990) and appends `(griever_id, dead_id, urgency)` to `Kernel._pending_grief_triggers`; the next tick's `_phase_resolution` drains it into `StrategicUpdate`s (`_drain_pending_grief_triggers`, kernel.py ~634 and 678-715). With `ObservabilityMode.OFF`, `_phase_observability` returns early (kernel.py ~968), detection is skipped, and the authoritative outcome changes. The pending list is hidden durable state outside the world (survives a tick, no typed model, not in the fingerprint, not in a snapshot).

## Scope
- Detect grief triggers in the authoritative pipeline from typed state (the death record, the bond/trust history), not from the observability extractor.
- Carry the pending triggers as a typed record in `AuthoritativeState`, written through an update and the apply path, drained by a later tick's authoritative step, with a defined lifecycle (written the tick of the death, consumed once, cleared).
- The observability layer only reports them (the `GriefUrgencyTriggeredEvent` is emitted from the state record).
- The episode-teardown flush (`drain_pending_triggers_at_teardown`, `scenario_runtime.flush_pending_grief_triggers`, campaigns orchestrator) reads the state record.
- Docs: Bible/engine contract line for the record, a divergence entry, parity ledger row.

## Out of Scope
- Changing the grief urgency formula (`min(1.0, trust * 0.8)`) or `ALLY_TRUST_THRESHOLD`.
- Other observability-dependent authoritative paths (list any found in the investigation as follow-ups).

## Acceptance Criteria
- (a) The full state fingerprint with exactly the named new fields projected out is byte-identical to base on 3 worlds (frontier_living_world, urban_political, crowded_frontier) x seeds 42-46 x 5000 ticks with observability ON (pattern: `tests/helpers/death_field_projection.py`).
- (b) Counts (deaths by kind, grief triggers) are identical to base.
- (c) The new full fingerprints are recorded as the base.
- (d) Every moved digest test is listed, before and after, and sent to rpg-planner before any is changed.
- NEW test: observability OFF and ON give the same authoritative outcome (same projected digest) on one seed.
- No observability import in the authoritative detection path (lint-imports kept).

## Related Tickets
TCK-20260824-GRIEF-NEMESIS-REACHABILITY (the path being corrected); TCK-20261014-EVERY-DEATH-CARRIES-A-TYPED-CAUSE-RECORDED-AT-DEATH (the death record this reads).

## Related Docs
docs/engine/kernel.md; docs/mechanics/05_world_evolution.md; docs/guidelines/intentional_divergences.md.

## Related Stored Artifacts
None.

## Related Code Areas
src/engine/kernel.py (_phase_observability, _drain_pending_grief_triggers, drain_pending_triggers_at_teardown); src/observability/event_extractor.py (detect_grief_triggers); src/engine/scenario_runtime.py (flush_pending_grief_triggers); src/domains/campaigns/grief_urgency.py, orchestrator.py; src/core/state.py; src/core/updates.py; tests/helpers/death_field_projection.py.

## Assumptions / Open Questions
- Queued after TCK-20261014-SOME-MOVE-STEPS-LOSE-THEIR-STEP-TIME-BETWEEN-RESOLVE-MOVE-AND-APPLY (rpg-planner).
- Whether the record is a state-level queue or per-entity (on the griever) is a design choice for the plan; the grief cause is the death record's `last_attacker`-independent ally death.

## Implementation Notes
TBD

## Test Summary
TBD

## Files Changed
TBD

## Completion Summary
TBD
