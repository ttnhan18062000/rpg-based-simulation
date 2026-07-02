---
ticket_id: TCK-20260619-E31B-OBJECTIVE-FSM
phase: investigation
date: 2026-06-20
---

# Investigation — TCK-20260619-E31B-OBJECTIVE-FSM
## Epic 3.1B · Objective State Machine + Stall Detector

---

## Current Behavior

### ScenarioRuntimeService (`src/engine/scenario_runtime.py`)

Implemented by E31A. Key facts for E31B:

- **`__slots__`** (line 55): `("_spec", "_kernel", "_state", "_tick", "_paused")`. New fields
  for stall tracking (`_stall_counter`, `_last_event_tick`) must be added here — omitting
  them will raise `AttributeError` at assignment time on CPython with `__slots__`.
- **`_run_loop()`** (lines 153–161): the tick loop that E31B must extend. After each
  `self._kernel.tick_once()` call, this is where `ObjectiveEvaluator.evaluate()` and the
  stall detector must be called.
- **`step()`** (lines 98–112): advances exactly one tick. E31B should wire objective/stall
  evaluation here too, so `step()` is consistent with `_run_loop()` — otherwise manually
  stepping to exactly `tick_limit` ticks will not trigger OBJECTIVE_MET.
- **`objective_state` property** (lines 132–139): currently reflects only ABORTED (set by
  `abort()`) or the initial RUNNING. Its docstring explicitly defers evaluation to E31B.
- **`alive_entity_count` property** (line 142–149): returns
  `len(self._kernel.state.entities)` — counts all entity dict entries, not live ones. The
  `entity_count` victory condition must count `e.combat.alive` entities, not raw dict size.

### ScenarioObjectiveState (`src/engine/scenario_runtime.py`, lines 23–30)

Already complete. All five values exist: `RUNNING`, `OBJECTIVE_MET`, `OBJECTIVE_FAILED`,
`STALLED`, `ABORTED`.

### VictoryCondition / SimulationScenarioDefinition (`src/scenarios/schema.py`)

- `VictoryCondition` (lines 22–42): frozen Pydantic model with `kind: str` and `value: int`.
  Allowed kinds validated via `ALLOWED_VICTORY_CONDITION_KINDS = {"tick_limit", "entity_count"}`.
- `SimulationScenarioDefinition.victory_conditions` (line 67): `Optional[List[VictoryCondition]]`,
  default `None`. No victory conditions = no evaluation; service stays RUNNING until abort or
  tick_limit in `_run_loop()`.

### ObjectiveStatus (`src/core/strategic.py`, line 26)

This is the *strategic project* objective status enum (`UNRESOLVED/ACTIVE/RESOLVED/FAILED`).
It is **unrelated** to `ScenarioObjectiveState`. The context scan hint was misleading — do not
conflate them.

### AuthoritativeState (`src/core/state.py`, lines 985–1019)

Key fields for evaluators:
- `state.tick: int` — current completed tick count (line 994).
- `state.entities: Dict[int, EntityState]` — all entity instances (line 999).
- `EntityState.combat.alive: bool` — the correct alive predicate (state.py line 270).
  The ticket pseudocode at line 45 uses `e.is_alive` which does **not exist** on `EntityState`.
  The correct expression is `e.combat.alive`.

### Kernel Event Count (`src/engine/kernel.py`)

- `self._current_tick_event_count` (line 764): set after every `tick_once()` call to the
  count of `SimulationEvent` objects generated in that tick. This is accessible on the kernel
  instance as `self._kernel._current_tick_event_count` after each tick.
- `tick_once()` (line 278): synchronous, no return value. The event count must be read from
  the field, not a return value.
- `kernel.shutdown()` (line 827): takes optional `timeout_s: float = 5.0`. Returns
  `ShutdownResult`. Called by `abort()` already; E31B calls it via the existing `abort()`
  indirection — or directly in `_run_loop()` before setting the terminal state, then guards
  against double-shutdown in `abort()`.

---

## Mechanics / Engine Constraints

### Tick Loop Integration Point

The authoritative location for post-tick side effects is **after PERSISTENCE phase** (phase 7).
`tick_once()` is atomic — it runs all 7 phases synchronously. The correct hook is immediately
after `self._kernel.tick_once()` returns in `_run_loop()` and `step()`.

Phase domain permissions (`docs/engine/kernel.md`, Phase Domain table): PERSISTENCE is the
last phase; it emits `replay` and `events` but does not write entity/world state. Objective
evaluation is read-only with respect to world state, so it is safe to run after PERSISTENCE
without violating phase contracts.

### Shutdown Contract

`kernel.shutdown()` is idempotent via the `_stopped` guard (`tick_once()` line 283):
`if getattr(self, "_stopped", False): return`. Once shutdown is called, subsequent `tick_once()`
calls are no-ops. The implementation should:
1. Set `self._state` to the terminal `ScenarioObjectiveState`.
2. Call `self._kernel.shutdown()` (or rely on the existing `abort()` path).
3. Set `self._paused = True` to break the `_run_loop()` while condition (as `abort()` does).

Avoid calling `kernel.shutdown()` twice — `abort()` already calls it. If `_run_loop()` detects
a terminal condition and sets `_paused = True`, the while loop exits naturally and the caller
can call `abort()` if needed, or the service can self-shutdown inline.

### Stall Detector — "Meaningful Events"

The ticket defines meaningful events as: combat, quest, harvest, death events — not idle ticks.
`_current_tick_event_count` counts **all** generated `SimulationEvent` objects. With an empty
world (no entities), the kernel emits zero events per tick. This makes the stall detector
trivially fire after `STALL_THRESHOLD` ticks in the zero-entity scenario — which overlaps with
the OBJECTIVE_FAILED (entity_count) condition.

Evaluation order matters: check `ObjectiveEvaluator.evaluate()` before the stall detector.
If entities are all dead, OBJECTIVE_FAILED fires first; STALLED is for the case where
simulation is running but producing no meaningful activity.

The ticket does not define a filtering predicate for "meaningful" events beyond listing
categories. A pragmatic implementation: any `_current_tick_event_count > 0` resets the stall
counter. This avoids needing to import and inspect `SimulationEvent.kind` on the hot path.
Document this simplification in `Implementation Notes`.

### STALL_THRESHOLD Default

Ticket specifies default 50 ticks. Define as a module-level constant in `scenario_runtime.py`:
`STALL_THRESHOLD: int = 50`. Do not hard-code in-line.

---

## Parity Ledger Overlap

### INFRA-214 (`docs/parity_ledger/infrastructure.yaml`, line 2419)

Current status: `verified`. Current text describes E31A (ScenarioRuntimeService lifecycle).
The text explicitly notes: "evaluation deferred to E31B."

**Required update after E31B completion:**
- Update `text` to include: `ObjectiveEvaluator` class, stall detector, wiring into `_run_loop()`
  and `step()`.
- Update `v2_evidence` to add: `src/engine/scenario_runtime.py::ObjectiveEvaluator`.
- Update `test_path` to add the integration test for `test_scenario_reaches_objective_met`.
- Status remains `verified`.

No other parity ledger entries are implicated — this feature is entirely new and has no legacy
counterpart outside INFRA-214.

---

## Prior Work (E31A Findings)

From `tickets/done/TCK-20260619-E31A-SCENARIO-SERVICE.md` and
`stored_artifacts/TCK-20260619-E31A-SCENARIO-SERVICE/`:

1. `ScenarioRuntimeService` is complete and tested (30 unit tests,
   `tests/unit/engine/test_scenario_runtime_service.py`).
2. `__slots__` is the blocking constraint for adding stall-tracking fields.
3. The service uses a minimal-profile Kernel (`HardwareClass.CLASS_B`, `no_replay: True`,
   `AuthoritativeState(tick=0, seed=0)` with zero entities). Tests confirm this starts and runs
   100 ticks without error — but produces zero events per tick because there are no entities.
4. `alive_entity_count` counts raw `state.entities` dict size, not `combat.alive` entities.
   This is intentional for E31A's scope but the `entity_count` evaluator in E31B must use
   `e.combat.alive` directly.
5. The unit test file (`tests/unit/engine/test_scenario_runtime_service.py`) uses mock kernels
   and real kernels. Integration tests (`tests/integration/scenarios/`) do not yet contain
   `test_scenario_runtime_service.py` — it must be created by E31B per the ticket AC.

---

## Risks and Open Questions

### Risk 1 — `__slots__` breakage (HIGH)
`ScenarioRuntimeService.__slots__` at line 55 must be extended with `_stall_counter` and
`_last_event_tick` (or equivalent). Forgetting this causes `AttributeError` on first assignment.
Mitigation: extend `__slots__` as the first code change; test will catch it immediately.

### Risk 2 — `e.is_alive` pseudocode bug (MEDIUM)
Ticket pseudocode (line 45) uses `e.is_alive` which does not exist. Correct attribute is
`e.combat.alive`. If implemented verbatim, every `entity_count` check raises `AttributeError`.

### Risk 3 — `step()` not wired (MEDIUM)
If objective evaluation is only added to `_run_loop()` and not `step()`, manually stepping
a scenario to the tick limit will never transition to OBJECTIVE_MET. The AC test
`test_scenario_reaches_objective_met` uses `start()` which calls `_run_loop()`, so the
integration test would pass — but the behavior would be inconsistent for callers using `step()`.
Recommend wiring both.

### Risk 4 — Stall fires before OBJECTIVE_FAILED (LOW)
If evaluation order is stall-first, a scenario with all-dead entities also triggers STALLED
rather than OBJECTIVE_FAILED. Evaluation order must be: objective conditions first, stall second.

### Risk 5 — Terminal state re-entry (LOW)
If `_run_loop()` sets a terminal state but does not break immediately, or if `step()` is called
on a service already in OBJECTIVE_MET/FAILED/STALLED, behavior is undefined. Add guard: if
`self._state != RUNNING`, return early from `_run_loop()` (already handled by while condition)
and raise or no-op from `step()`.

### Open Question 1
Should `step()` on a non-RUNNING service raise `RuntimeError` (consistent with ABORTED guard)
or silently no-op? The ticket is silent. Recommend: raise `RuntimeError` for OBJECTIVE_MET,
OBJECTIVE_FAILED, STALLED — same message pattern as the ABORTED guard.

### Open Question 2
Should the service call `kernel.shutdown()` immediately on terminal transition, or leave cleanup
to the caller? Ticket says "call `kernel.shutdown()`" — but `abort()` already calls it.
Recommend: set `_paused = True` to break the loop, let `_state` reflect the terminal value,
and document that callers should call `abort()` for cleanup (which calls shutdown idempotently).
This avoids double-shutdown and keeps `abort()` as the single cleanup path.

---

## Anti-Drift Hazards

1. **Do not add new fields to `ScenarioRuntimeService` without extending `__slots__`.**
2. **Do not use `len(state.entities)` as alive count** — use `e.combat.alive` filter.
3. **Do not read `_current_tick_event_count` before calling `tick_once()`** — it reflects
   the previous tick until updated at kernel.py line 764.
4. **Do not call `kernel.shutdown()` in the tick loop** — only set `_paused = True` and let
   the caller drive cleanup via `abort()`, or call shutdown once and guard against double calls.
5. **`ObjectiveEvaluator` is a pure static utility — no state, no kernel reference.** Keep it
   stateless; stall tracking belongs on `ScenarioRuntimeService`, not the evaluator.
6. **`victory_conditions` may be `None`** (default). The evaluator must guard: if `None` or
   empty list, return `RUNNING` immediately.
