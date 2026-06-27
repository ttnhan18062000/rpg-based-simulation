---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260627-P2O-ENTITY-PERSONALITY-OBS
artifact_type: investigation
tags: [entity-differentiation, observability, personality, project-kind, light-mode]
---

# Investigation — TCK-20260627-P2O-ENTITY-PERSONALITY-OBS

## Prior Work Check

search_docs surface: **TCK-20260619-E11B-OBS-SNAPSHOT** (done) added `role`, `class_id`,
and `personality` dict to `EntityInspectionSnapshot` (the live API snapshot dataclass in
`src/observability/live/entity_inspector.py`). That ticket is **complete and different**:
it exposes personality on the real-time inspector API endpoint. The current ticket asks for
a persistent JSONL file artifact written per-run, triggered by `active_project_kind` changes.
These are two separate concerns and there is no overlap.

## Code Structure

### PersonalityComponent (`src/core/state.py:L413`)
Fields: `greed`, `bravery`, `sociability`, `industry` (all `float`).
Method: `to_canonical_dict()` returns `{greed, bravery, sociability, industry}`.
Accessed via `entity.identity.personality` (not `entity.personality`).

### ProjectKind (`src/core/strategic.py:L134`)
Enum with `.value` as string: CRAFTING, QUEST, EXPLORATION, COMBAT, SOCIAL, RECOVERY,
PREPARATION, TRAINING, HARVESTING, INFORMATION, INFORMATION_SEEKING, TRAVEL.

Active project kind resolution:
```
entity.strategic.current_project_id
→ entity.strategic.projects[id].kind.value  # str
```
Null when no active project.

### Pattern: ObservabilityCognitionRecorder (`src/observability/cognition/recorder.py`)
- Instantiated in `Kernel.__init__` when `obs_mode != OFF`
- Called: `self._cognition_recorder.record_tick(state, tick, events, event_recorder)`
- Writes JSONL to `data/runs/{run_id}/cognition_graph_snapshots.jsonl`
- Maintains per-entity prev-state dict for change detection

### Kernel Hook Points
- Init block (`kernel.py:L234`): `if obs_mode != ObservabilityMode.OFF:` — where recorders
  are created. Add `PersonalitySnapshotRecorder` alongside cognition recorder.
- Post-tick block (`kernel.py:L825`): step 5 calls `_cognition_recorder.record_tick()`.
  Add step 6 immediately after for `_personality_recorder.record_tick()`.

## Emission Policy

| Mode   | Emission trigger                             |
|--------|----------------------------------------------|
| OFF    | Never                                        |
| LIGHT+ | On `active_project_kind` change per entity   |
| DEBUG  | Every tick for every strategic entity        |

Note: The sentinel `"__SENTINEL__"` is used in `_prev_project_kind` to distinguish "first
tick seen" (should emit on first observation) from `None` (entity has no active project).
After first tick, `None` is a valid stable state.

## Record Schema

```json
{
  "run_id": "...",
  "entity_id": 1,
  "tick": 42,
  "role": 0,
  "class_id": "WARRIOR",
  "personality": {"greed": 0.8, "bravery": 0.3, "sociability": 0.5, "industry": 0.9},
  "active_project_kind": "combat"
}
```

## No Conflicts Found
- No existing `entity_personality_snapshots.jsonl` writer
- No existing `src/observability/personality/` module
- Prior work (E11B) only touched the live inspector, not a file recorder
- No architectural issues — read-only access to AuthoritativeState, post-commit
