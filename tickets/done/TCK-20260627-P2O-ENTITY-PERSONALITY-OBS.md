---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260627-P2O-ENTITY-PERSONALITY-OBS
phase: done
date: 2026-06-27
tags: [observability, personality, entity-snapshot, light-mode, dx]
---

# TCK-20260627-P2O-ENTITY-PERSONALITY-OBS

## Title
Add per-entity personality snapshot in LIGHT observability mode

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
D05 §Recommended Follow-Up (P2) identified that LIGHT observability mode does not surface per-entity personality traits or scoring weights. Developers analyzing entity differentiation must use direct `AuthoritativeState` introspection. A lightweight entity snapshot (role, class, personality vector, active_project_kind) would make D05-type analysis routine. Source: D05 P2 recommendation.

## Scope
Emit a lightweight per-entity snapshot when the entity's active_project_kind changes (in LIGHT+ mode). Each snapshot record contains:
- `entity_id`, `tick`, `role`, `class_id`
- `personality`: `{bravery, greed, industry, sociability}`
- `active_project_kind`

Output: `data/runs/{run_id}/entity_personality_snapshots.jsonl` (append-only, one JSON line per change event).

In DEBUG mode: emit every tick (not just on change).

## Out of Scope
- Changing other LIGHT-mode observability capture behavior
- A new REST API endpoint for personality snapshot queries
- Personality calibration analysis (tracked by P3-A deferred epic)

## Acceptance Criteria
- [x] `entity_personality_snapshots.jsonl` written per run in LIGHT+ mode
- [x] Each record contains: entity_id, tick, role, class_id, personality vector, active_project_kind
- [x] Snapshots emit on active_project_kind change in LIGHT mode
- [x] Snapshots emit every tick in DEBUG mode
- [x] Unit test: 100-tick run produces ≥1 snapshot record per entity with correct fields
- [x] Parity ledger entry added to `docs/parity_ledger/infrastructure.yaml`

## Related Tickets
- TCK-20260627-P1H-GOAL-RUNNERUP (decision_trace.jsonl runner-up scores — related observability artifact)
- TCK-20260627-P3A-DEFERRED-EPICS (Personality Long-Run Calibration depends on this data)

## Related Docs
- `docs/audits/D05_entity_differentiation.md` §Recommended Follow-Up P2
- `docs/audits/D15_entity_decision_inspection.md` (observability pattern reference)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260627-P2O-ENTITY-PERSONALITY-OBS/`

## Related Code Areas
- `src/observability/personality/recorder.py` (new module)
- `src/engine/kernel.py` (slot + init + post-tick hook)
- `src/core/state.py` (IdentityComponent, PersonalityComponent fields)

## Assumptions / Open Questions
None.

## Implementation Notes
- Created `src/observability/personality/recorder.py` with `PersonalitySnapshotRecorder`
  following the exact pattern of `ObservabilityCognitionRecorder`.
- Uses a sentinel `"__UNSEEN__"` to distinguish first observation (always emits) from
  stable None (no active project).
- Access path: `entity.identity.personality.to_canonical_dict()` — matches E11B pattern.
- Active project kind: `entity.strategic.projects[current_project_id].kind.value`.
- Added `_personality_recorder` to Kernel `__slots__` (line 48), initialized in the
  `obs_mode != OFF` block, called as step 6 in the post-tick section.
- Kernel missing-slot error would have silently broken 2 existing observability tests
  (Sweeper/index-builder); fixing the slot restored those tests too.

## Test Summary
7 new tests in `tests/unit/observability/test_entity_personality_snapshot.py`:
- `test_light_mode_emits_on_first_observation_and_change` — first tick emits, stable unchanged, then changed kind emits again
- `test_light_mode_stable_kind_emits_once` — 100 ticks, stable kind → exactly 1 record
- `test_debug_mode_emits_every_tick` — 5 ticks → 5 records
- `test_record_schema_correct_fields` — all 7 top-level keys + 4 personality sub-keys
- `test_entity_without_strategic_skipped` — no file created
- `test_no_active_project_emits_none_kind` — active_project_kind=None
- `test_off_mode_emits_nothing` — no file created

All 7 new tests pass. 484 observability unit tests pass (was 482 before slot fix).

## Files Changed
- `src/observability/personality/__init__.py` — new package
- `src/observability/personality/recorder.py` — PersonalitySnapshotRecorder
- `src/engine/kernel.py` — __slots__, __init__, post-tick step 6
- `tests/unit/observability/test_entity_personality_snapshot.py` — 7 tests
- `docs/parity_ledger/infrastructure.yaml` — INFRA-229

## Completion Summary
`PersonalitySnapshotRecorder` added to `src/observability/personality/recorder.py`. Emits
per-entity personality records to `entity_personality_snapshots.jsonl` on project-kind
change (LIGHT+) or every tick (DEBUG). Wired into `Kernel.__slots__` and post-tick pipeline.
INFRA-229 parity entry added. 7 new unit tests pass; 484 observability tests pass total.
