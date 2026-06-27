# Investigation — TCK-20260627-P1A-REJECTION-BACKOFF

## Current Behavior (file:line refs)

**Root cause confirmed (D03 audit, line 153):** After the P0A adventure-routing fix enables the
opportunity pipeline, entities with stale initial-spawn projects keep retrying objectives that fail
legality/movement/economy checks every tick. Each failure writes to `rejections_delta[reason]`
(accumulated in `state.rejection_registry` via `apply.py:261-263`).

Writers of `rejections_delta`:
- `src/engine/interaction.py:87` — INTERACTION_RESET
- `src/engine/pipeline_phases/movement.py:270` — movement rejection
- `src/engine/economy.py:150,224` — economy rejections

Observed rate: ~650 rejections/tick → 550K cumulative at tick 1,000 (D06 F3).

### The dead-code guard

`ProjectState` at `src/core/strategic.py:L243-254` has:
```python
failure_count: int = 0
```

`evaluate_strategic_intent` at `src/systems/strategic_systems/intelligence.py:L1147` checks:
```python
if project.failure_count >= 3:
    # abandon
```

But **`failure_count` is NEVER incremented anywhere in the codebase**. The abandonment guard
is permanently dead code. This is the missing wire-up.

### How intent failures are already tracked

- `entity.identity.latest_intent_results: List[IntentResult]` — per-entity intent results
  (set in `apply.py:516`, `economy.py:80-273`, `information/phase.py:100`)
- `IntentResult.accepted: bool` — False when the action was rejected
- `StrategicWorkQueue.build()` at `work_queue.py:55` already routes entities with
  `intent_fail = any(not r.accepted for r in entity.identity.latest_intent_results)` to tier1

`evaluate_strategic_intent` is then called for those entities and has full access to
`entity.identity.latest_intent_results`.

## Mechanics/Engine Constraints

- `ProjectStatus.ABANDONED` is a valid status value (`strategic.py:L22`)
- `replace()` from `apply.py` is the correct way to produce updated frozen dataclasses
- Durable state changes must go through `StrategicUpdate.projects_add_or_update`
- No raw mutation of `entity.strategic` is permitted
- D03 audit recommendation (line 294): "Add a max-retry count or tick-expiry to `ProjectState`
  such that a project is abandoned after N consecutive rejections or M ticks without progress."

## Parity Ledger Overlap

- STRAT-002: current project/objective continuity — not affected (abandonment exits project)
- STRAT-003: project switching uses interruption resistance — not affected (abandonment bypasses switch)
- No existing entry covers rejection-based abandonment → will add STRAT-234

## Prior Work

- TCK-20260627-P0A-ADVENTURE-FLAG: Fixed adventure routing flag (prerequisite — DONE)
- TCK-20260618-AUDIT-D03-BEHAVIOR: Identified the cascade (DONE, see stored_artifacts/)
- TCK-20260619-AUDIT-D06-LONGRUN: Quantified 550K rejections at tick 1000 (DONE)
- TCK-20260427-PH6-STRATEGIC-COGNITION: Added `failure_count` field and stub guard (DONE,
  but left the increment unwired)

## Risks and Open Questions

- **Threshold calibration**: N=20 is the AC-mandated starting point. D06 data shows seeds with
  4.8× variation in rejection rates (seed 137 vs seed 42). N=20 provides margin even for
  high-rejection seeds.
- **Empty `latest_intent_results`**: When no intents were emitted (entity idle/cadence skip),
  results list is empty — in this case, `failure_count` must NOT be changed (no progress either
  direction). This avoids spurious resets.
- **Success/failure mix**: If any intent is accepted in the same tick, reset to 0 (entity made
  progress). This is conservative and correct — the cascade only happens when ALL intents fail.
- **Determinism**: `replace()` is deterministic. The increment/reset logic depends only on
  `entity.identity.latest_intent_results` which is set deterministically per tick.

## Anti-Drift Hazards

- Do not introduce a new field when `failure_count` already exists — avoids schema churn and
  backwards-compat issues
- Keep the constant `_MAX_CONSECUTIVE_REJECTIONS = 20` at module level (not hardcoded inline)
- The early return with just the project update must still include `memory_upd` leads (follow
  the pattern already used in the abandonment early return at L1155-1158)
