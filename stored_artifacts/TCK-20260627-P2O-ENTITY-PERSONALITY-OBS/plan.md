---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260627-P2O-ENTITY-PERSONALITY-OBS
artifact_type: plan
tags: [observability, personality, snapshot, jsonl, light-mode]
---

# Plan — TCK-20260627-P2O-ENTITY-PERSONALITY-OBS

## Goal
Add a JSONL file writer that emits per-entity personality snapshots on `active_project_kind`
changes (LIGHT+ mode) or every tick (DEBUG mode), producing
`data/runs/{run_id}/entity_personality_snapshots.jsonl`.

## Architecture Decision
Create a new module `src/observability/personality/recorder.py` following the exact pattern
of `ObservabilityCognitionRecorder`. Do NOT extend the cognition recorder — personality
snapshots have a different trigger (project kind change vs. strategic graph change) and
different output data. Separation keeps each recorder focused and independently testable.

## Changes

### 1. New module: `src/observability/personality/__init__.py`
Empty init file to make the package importable.

### 2. New file: `src/observability/personality/recorder.py`
Class: `PersonalitySnapshotRecorder`
- `__init__(run_id, run_dir=None)`: sets paths, initialises `_prev_project_kind: Dict[int, str | None]`
- `record_tick(state: AuthoritativeState, tick: int)`: iterates strategic entities, resolves
  `active_project_kind`, emits on change (LIGHT) or unconditionally (DEBUG), writes JSONL

Sentinel: `_prev_project_kind` defaults to `"__SENTINEL__"` for unseen entities so the
**first observation always emits** regardless of mode — ensures ≥1 snapshot per entity.

### 3. `src/engine/kernel.py`
Two changes:
a) In `__init__`, alongside `_cognition_recorder = None`, add `_personality_recorder = None`
   and in the `obs_mode != OFF` block, instantiate `PersonalitySnapshotRecorder`.
b) After step 5 (cognition recorder call) in the post-tick section, add step 6 that calls
   `self._personality_recorder.record_tick(state=self._state, tick=tick)`.

### 4. New test: `tests/unit/observability/test_entity_personality_snapshot.py`
7 tests covering: LIGHT-mode change trigger, DEBUG every-tick, field correctness,
entity-without-strategic skipped, None active_project_kind, regression.

### 5. Parity ledger: `docs/parity_ledger/infrastructure.yaml`
Append INFRA-229 entry for personality snapshot emission policy.

## Risk Assessment
Low. The recorder is purely additive and post-commit read-only. No mutations to AuthoritativeState.
Failure is caught by a try/except in the kernel matching the cognition recorder pattern.

## Unresolved Questions
None. All fields confirmed present and accessible.
