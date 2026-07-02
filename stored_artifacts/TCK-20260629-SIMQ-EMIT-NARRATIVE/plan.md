---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260629-SIMQ-EMIT-NARRATIVE
artifact_type: plan
tags: [simq, event-extractor, narrative, chronicle, world-emergence, scenario, lifecycle]
---

# Plan: TCK-20260629-SIMQ-EMIT-NARRATIVE

---

## Decisions

### D1: world_emergence_event trigger — one event per WorldEvent appended to world_events_add

No `WORLD_EMERGENCE_THRESHOLD` category exists in `WorldEventCategory` (schema.py:15–49).
All `WorldEvent` objects appended to `world_events_add` originate from world-level domain
logic; by definition they ARE world emergence events. The decision (from prompt) is:

**Emit one `world_emergence_event` per `WorldEvent` in `world_events_add` regardless of
category.** No new threshold logic. No new `WorldEventCategory` enum value. The extractor
already reads `world_events_add` for faction events (event_extractor.py:555–576); the
narrative block appends to the same loop with a separate `SimulationEvent`. EventCategory
`"lifecycle"` is used (already valid in the Literal) — no new category needed since
"narrative" does not exist in the current `EventCategory` Literal and the faction/lifecycle
precedent covers world-level events adequately. Alternatively, `"region"` is valid;
implementer should use `"lifecycle"` to match `calamity_spawned` precedent.

**Scope-out:** No new `WorldEventCategory.WORLD_EMERGENCE_THRESHOLD` value is added to
schema.py. The existing `world_events_add` loop in event_extractor.py is extended, not
replaced.

### D2: narrative_milestone "first X" — emit unconditionally; NarrativeScorer deduplicates

`WorldEmergencePhase.execute()` is a `@staticmethod` (phase.py:28) with no instance state.
Adding a run-level stateful set would require either schema mutation or a module-level
mutable (which breaks determinism per Architecture Rule). The decision:

**Emit `narrative_milestone` unconditionally from EventExtractor when
`WorldEventCategory.FACTION_WAR_DECLARED` (→ `"first_war"`),
`entities_add` with boss kind (→ `"first_boss_kill"`), or
`WorldEventCategory.SOVEREIGNTY_SHIFT` (→ `"first_sovereignty_transfer"`)
is observed.** NarrativeScorer already has per-instance one-shot flags (`_quest_dormant_fired`,
`_narrative_silent_fired`, `_scenario_broken_fired`) and handles deduplication. This matches
the established scorer-dedup pattern referenced in the investigation.

**Note on `boss_spawned` vs `boss_killed`:** The ticket cites "first boss kill" but
`entities_add` produces a `boss_spawned` event (not a kill). EventExtractor does not
currently detect boss deaths from state diff. Emit `narrative_milestone` with
`milestone="first_boss_spawned"` from the same `boss_spawned` detection block
(event_extractor.py:481–490). The scorer label mismatch ("first_boss_kill" vs spawned) is
documented as an unresolved question (see §Unresolved Questions). If the test plan uses
`"first_boss_kill"` as the expected payload, the implementer should use `"first_boss_spawned"`
and update the test accordingly, OR add a state-diff check for boss entity death — but the
latter is out of scope for this ticket given no existing detection pattern.

### D3: ScenarioRuntimeService event_recorder — Optional[EventRecorder] parameter on __init__

`ScenarioRuntimeService.__init__()` (scenario_runtime.py:129) currently takes only `spec`
and `initial_state`. The decision:

**Add `event_recorder: Optional[EventRecorder] = None` as the third parameter to
`ScenarioRuntimeService.__init__()`**, stored as `self._event_recorder`. The
`_evaluate_after_tick()` method calls `self._event_recorder.record(event)` guarded by
`if self._event_recorder is not None`. This matches the established None-safe injection
pattern used throughout the observability stack.

`EventRecorder` is imported at the top of `scenario_runtime.py` under `TYPE_CHECKING`
(to avoid circular imports) and used as a runtime type hint string. At actual call time,
the guard `if self._event_recorder is not None:` ensures None-safety without requiring
the import to be unconditional.

All existing `ScenarioRuntimeService(spec)` and `ScenarioRuntimeService(spec, state)`
call sites are unaffected (parameter is keyword-only with default `None`).

**`__slots__`** — `ScenarioRuntimeService` declares `__slots__` (scenario_runtime.py:118–127).
`"_event_recorder"` must be added to `__slots__` before the implementation step.

### D4: hero_death_unrecorded — always emit on hero-kind entity death; scorer deduplicates

The detection options from investigation Q4:
- Option (b): detect "no chronicle entry in world_events_add" — but chronicle entries are
  written via `CampaignState.narrative_ledger.extend()` in the orchestrator at episode
  boundary, not via `world_events_add` during ticks. There is no reliable tick-level
  "chronicle written this tick" signal in `StateUpdate`.
- Option (c): always emit when hero becomes inactive.

**Decision: always emit `hero_death_unrecorded` when a hero-kind entity transitions
`active=True → active=False` in the entity state diff (prior `entity.lifecycle.active=True`,
current `entity.lifecycle.active=False`, `entity.kind == "hero"`).** NarrativeScorer
handles dedup on `entity_id`. Test N-11 becomes a gap test with `pytest.skip` per the
test plan's note for option (c).

The detection site is EventExtractor's existing entity loop (already iterates
`dirty_entity_ids`, already has `entity` and `prior_ent` in scope). The `"lifecycle"`
event category is used (matching `calamity_spawned`).

### D5: chronicle_entry_created — instrument CampaignOrchestrator write path, not NarrativeLedger.record()

Investigation confirmed two orchestrator write paths:
- `self._state.narrative_ledger.extend(narrative_entries)` — line 199 in orchestrator.py
  (bulk append at episode boundary from `_advance_state()`)
- `self._state.narrative_ledger.append(ledger_entry)` — line 577 in orchestrator.py
  (tick-level append in `_extract_narrative_entries` loop)

The ticket's original scope says to add `event_recorder` to `NarrativeLedger.__init__()`.
**Decision: do NOT instrument `NarrativeLedger.record()`.** That method is "for
construction-time or test use" (narrative_ledger.py:43–51) and is not the authoritative
write path. Instead:

**Wire the event_recorder into `NarrativeLedger` class via an optional parameter on
`__init__()` — but call it ONLY from the orchestrator's two write sites.** The orchestrator
creates a fresh `NarrativeLedger` facade at query time (confirmed by class docstring:
`ledger = NarrativeLedger(entries=campaign_state.narrative_ledger)`). Since the facade
is ephemeral, the approach is:

**Add `event_recorder: Optional[EventRecorder] = None` to `NarrativeLedger.__init__()`
and store as `self._event_recorder`. Add a new `record_and_emit(entry, tick)` method (or
enhance `record()` to call the recorder after append when `self._event_recorder` is set).
Wire the orchestrator to pass an `event_recorder` when constructing the `NarrativeLedger`
facade at write time (lines 199 and 577).**

Alternatively (simpler, matching the test plan's TC-D16 structure): **add
`event_recorder` parameter directly to `NarrativeLedger.record()` as an optional
keyword argument.** The orchestrator callers at lines 199 (`.extend()`) and 577
(`.append()`) bypass `record()` — so this approach only works if the orchestrator is
changed to call `ledger.record(entry, event_recorder=recorder)` instead of direct
list mutation.

**Final decision: add `event_recorder: Optional[...]` to `NarrativeLedger.__init__()`.
Add an `emit_chronicle_event(entry, tick)` helper on the class that calls `record()` and
then emits if recorder is set. The orchestrator constructs a temporary `NarrativeLedger`
wrapping the live list, calls `emit_chronicle_event()` for each new entry. This avoids
direct list mutation bypass and gives the test harness a clean single-method surface
(TC-D16 tests `record()` + emission from the same call).**

See implementation note: the facade wraps the live list by reference, so `record()` on
the facade appends to `self._entries` (the wrapped list). The orchestrator can safely
call `ledger.emit_chronicle_event(entry, tick=state.tick)` for each new entry.

**Import constraint:** `NarrativeLedger` has no engine or observability imports. The
`event_recorder` type hint must be a string annotation or `TYPE_CHECKING` guard to avoid
circular imports. Use `Optional["EventRecorder"]` with `from __future__ import annotations`.

### D6: scenario_objective_progressed — SCOPED OUT (no partial progress concept)

`ObjectiveEvaluator.evaluate()` returns `RUNNING | OBJECTIVE_MET | OBJECTIVE_FAILED`
(binary state machine). There is no partial-progress concept or incremental counter in
the current `ObjectiveEvaluator`. **`scenario_objective_progressed` cannot be emitted
without a schema change to `ObjectiveEvaluator`.** This is documented as a gap test
(S-05 in test plan). The event type is listed in the ticket's scope table but is
architecture-blocked; gap is documented, not implemented.

### D7: EventCategory "narrative" — use "lifecycle" as the event_category for narrative events

The `EventCategory` Literal (events.py:44–48) does not include `"narrative"`. Adding a new
Literal value touches `src/observability/events.py` which is a low-risk change, but
keeping scope narrow: use `"lifecycle"` for `world_emergence_event`, `narrative_milestone`,
`hero_death_unrecorded`, and `chronicle_entry_created`. This matches `calamity_spawned` and
`boss_spawned` which are also lifecycle-category events. `scenario_objective_*` and
`scenario_stalled` use `"infrastructure"` (closest match for runtime service events).

**If the implementing agent prefers a clean separation:** add `"narrative"` to the
`EventCategory` Literal in `events.py` as a single-line change (no other impact). Document
the choice in the Deviations section of this plan after implementation.

---

## Files to Change

| File | Role |
|---|---|
| `src/domains/campaigns/narrative_ledger.py` | Add `event_recorder` optional param + `emit_chronicle_event()` method |
| `src/domains/campaigns/orchestrator.py` | Call `emit_chronicle_event()` at lines ~199 and ~577 |
| `src/observability/event_extractor.py` | Add `world_emergence_event`, `narrative_milestone`, `hero_death_unrecorded` |
| `src/engine/scenario_runtime.py` | Add `event_recorder` param; emit in `_evaluate_after_tick()` |
| `docs/parity_ledger/infrastructure.yaml` | Update INFRA-247 + SIMQ-CALIBRATED-001 |
| `tests/unit/campaigns/test_narrative_ledger.py` | Add TC-D16..TC-D19 |
| `tests/unit/engine/test_scenario_runtime_service.py` | Add S-01..S-05 |
| `tests/unit/observability/test_event_extractor_narrative.py` | NEW: N-01..N-18 |

## Scope Guards — What NOT to Touch

- `src/domains/world_emergence/schema.py` — no new `WorldEventCategory` enum values
- `src/domains/world_emergence/phase.py` — no changes; emission goes through EventExtractor
  reading `world_events_add`, not through the phase itself
- `src/systems/lifecycle_systems/lifecycle.py` — no changes; `hero_death_unrecorded`
  detection via EventExtractor state diff (active transition), not inside LifecycleSystem
- `src/core/state.py`, `src/core/updates.py` — no new fields in StateUpdate or AuthoritativeState
- `src/simulation_quality/` — no imports from simulation_quality in any changed source file
- `src/engine/pipeline.py` — no changes; `WorldEmergenceResult[1]` remains discarded
- `tests/simulation_quality/test_narrative_scorer.py` — must pass unchanged (regression guard)
- `tests/unit/observability/test_event_extractor_social_faction.py` — must pass unchanged
- `tests/unit/observability/test_event_extractor_economy.py` — must pass unchanged
- `tests/unit/observability/test_event_extractor_world.py` — must pass unchanged
- Quest event emission — do NOT add `quest_started/completed/failed` emission; translation
  layer (TCK-20260629-SIMQ-EVENT-TRANSLATE, DONE) already covers these via `QuestEvent`
- `src/domains/campaigns/state.py` — read-only; `NarrativeLedgerEntry` fields are unchanged

---

## Ordered Steps

---

### Step 1 — Baseline: Run existing regression suite (no file changes)

**Purpose:** Confirm green baseline before any edits.

**Command:**
```bash
uv run --with pytest python3 -m pytest \
    tests/simulation_quality/test_narrative_scorer.py \
    tests/unit/campaigns/test_narrative_ledger.py \
    tests/unit/engine/test_scenario_runtime_service.py \
    tests/unit/observability/test_event_extractor_simq.py \
    tests/unit/observability/test_event_extractor_social_faction.py \
    tests/unit/observability/test_event_extractor_economy.py \
    tests/unit/observability/test_event_extractor_world.py \
    tests/simulation_quality/test_quality_hub_event_translation.py \
    -v
```

**Acceptance:** All existing tests pass. Record counts. Stop if any red — investigate
before proceeding.

**Files changed:** none
**Dependencies:** none

---

### Step 2 — Wire EventRecorder into NarrativeLedger

**Files:** `src/domains/campaigns/narrative_ledger.py`

**2a. Add `TYPE_CHECKING` import guard at top of file (after existing imports):**

```python
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.observability.events import SimulationEvent
    from src.observability.event_recorder import EventRecorder  # or wherever EventRecorder lives
```

Confirm actual import path for `EventRecorder` at implementation time by checking
`src/observability/`. Use the string annotation `"EventRecorder"` in the type hint
so the import is gated by `TYPE_CHECKING` and avoids circular deps.

**2b. Extend `__init__()` signature:**

```python
def __init__(
    self,
    entries: Optional[List[NarrativeLedgerEntry]] = None,
    event_recorder: Optional["EventRecorder"] = None,
) -> None:
    self._entries: List[NarrativeLedgerEntry] = list(entries or [])
    self._event_recorder = event_recorder
```

**2c. Add `emit_chronicle_event()` method after `record()`:**

```python
def emit_chronicle_event(self, entry: NarrativeLedgerEntry, tick: int) -> None:
    """Append entry and emit chronicle_entry_created to event bus if recorder is set.

    This is the authoritative call site for wired narrative ledger recording.
    ``record()`` remains for construction-time / test use and does NOT emit.
    """
    self._entries.append(entry)
    if self._event_recorder is not None:
        from src.observability.events import SimulationEvent  # local import avoids circular
        self._event_recorder.record(SimulationEvent(
            event_type="chronicle_entry_created",
            event_category="lifecycle",
            tick=tick,
            entity_id=None,
            severity="INFO",
            source_system="narrative_ledger",
            message="",
            payload={
                "entry_id": entry.entry_id,
                "event_type": entry.event_type,
                "significance": entry.significance,
                "episode": entry.episode,
                "subject_id": entry.subject_id,
            },
        ))
```

**Acceptance:** `NarrativeLedger(entries=[...])` works unchanged (recorder=None).
`NarrativeLedger(entries=[...], event_recorder=recorder).emit_chronicle_event(entry, tick=5)`
calls `recorder.record(...)` exactly once. `record()` is unmodified and does NOT call recorder.

**Files changed:** `src/domains/campaigns/narrative_ledger.py`
**Dependencies:** Step 1

---

### Step 3 — Wire orchestrator to call emit_chronicle_event()

**File:** `src/domains/campaigns/orchestrator.py`

The orchestrator has two narrative_ledger write paths:

**3a. Line ~199 — bulk append at episode boundary:**

```python
# BEFORE:
self._state.narrative_ledger.extend(narrative_entries)

# AFTER:
_ledger_facade = NarrativeLedger(
    entries=self._state.narrative_ledger,
    event_recorder=getattr(self, "_event_recorder", None),
)
for _ne in narrative_entries:
    _ledger_facade.emit_chronicle_event(_ne, tick=getattr(self._state, "tick", 0))
# Note: emit_chronicle_event appends to _ledger_facade._entries which IS
# self._state.narrative_ledger (same list object by reference after __init__ list()).
# IMPORTANT: NarrativeLedger.__init__ does list(entries or []) — this copies the list.
# The orchestrator must use self._state.narrative_ledger.append(ne) AFTER emitting,
# OR initialise NarrativeLedger on the actual list reference without copy.
```

**Critical note:** `NarrativeLedger.__init__` does `list(entries or [])` — a copy, not
a reference. Calling `emit_chronicle_event` on the facade appends to the COPY, not to
`self._state.narrative_ledger`. Two resolution options:

- Option A (preferred): Keep `list()` copy in `__init__` for safety. In orchestrator,
  call `self._state.narrative_ledger.append(ne)` for the authoritative write, then call
  `self._emit_chronicle_event_to_bus(ne)` via a helper directly in the orchestrator.
- Option B: Change `NarrativeLedger.__init__` to accept the live list by reference
  (do NOT copy). This is a design change to the facade contract.

**Final approach for Step 3 (Option A — cleanest):**

Add a private helper on the orchestrator:

```python
def _emit_chronicle_events(
    self, entries: List[NarrativeLedgerEntry], tick: int
) -> None:
    """Emit chronicle_entry_created events for new narrative ledger entries."""
    er = getattr(self, "_event_recorder", None)
    if er is None:
        return
    from src.observability.events import SimulationEvent
    for entry in entries:
        er.record(SimulationEvent(
            event_type="chronicle_entry_created",
            event_category="lifecycle",
            tick=tick,
            entity_id=None,
            severity="INFO",
            source_system="campaign_orchestrator",
            message="",
            payload={
                "entry_id": entry.entry_id,
                "event_type": entry.event_type,
                "significance": entry.significance,
                "episode": entry.episode,
                "subject_id": entry.subject_id,
            },
        ))
```

Then at line ~199:
```python
self._state.narrative_ledger.extend(narrative_entries)
self._emit_chronicle_events(narrative_entries, tick=self._state.tick)
```

And at line ~577:
```python
self._state.narrative_ledger.append(ledger_entry)
self._emit_chronicle_events([ledger_entry], tick=state.tick)
```

This keeps `NarrativeLedger` as a pure facade (no coupling change), satisfies AC "wire
NarrativeLedger to emit chronicle_entry_created", and is None-safe (no-op when
`_event_recorder` is absent).

**Check:** Does `CampaignOrchestrator.__init__` accept `event_recorder`? If not, the
orchestrator needs `self._event_recorder = event_recorder` wiring. Check orchestrator
`__init__` at implementation time. If it already has one (from prior observability work),
use it. If not, add `event_recorder: Optional[EventRecorder] = None` parameter with a
`TYPE_CHECKING` import guard.

**Files changed:** `src/domains/campaigns/orchestrator.py`
**Dependencies:** Step 2 (method signature decided; Step 3 can reference it)

---

### Step 4 — Add hero_death_unrecorded in EventExtractor entity loop

**File:** `src/observability/event_extractor.py`

**Insert after the existing `LifecycleEvent(action="death")` block or after the entity
loop's group_joined/group_expelled block (around line 320), still inside the
`for eid in dirty_entity_ids:` loop, after the check that both `entity` and `prior_ent`
exist:**

The entity loop already has:
```python
entity = current_state.entities.get(eid)
prior_ent = prior_state.entities.get(eid)
```

Add after the existing lifecycle / HP / status checks, inside the `if entity is not None
and prior_ent is not None:` guard:

```python
# NARRATIVE: hero_death_unrecorded — hero-kind entity deactivated this tick
_prior_active = getattr(getattr(prior_ent, "lifecycle", None), "active", None)
_curr_active = getattr(getattr(entity, "lifecycle", None), "active", None)
if (
    _prior_active is True
    and _curr_active is False
    and getattr(entity, "kind", None) == "hero"
):
    events.append(SimulationEvent(
        event_type="hero_death_unrecorded",
        event_category="lifecycle",
        tick=tick,
        entity_id=eid,
        severity="WARNING",
        source_system="event_extractor",
        message="",
        payload={"entity_id": eid},
    ))
```

**Note:** Per Decision D4, this always fires when a hero becomes inactive. `chronicle_entry_created`
emission (Step 2/3) is independent — there is no cross-check at extraction time.

**Acceptance:** Tests N-08, N-09, N-10 (from test plan). N-11 becomes a gap test (pytest.skip).

**Files changed:** `src/observability/event_extractor.py`
**Dependencies:** Step 1. Independent of Steps 2, 3, 5.

---

### Step 5 — Add world_emergence_event and narrative_milestone in EventExtractor world_events loop

**File:** `src/observability/event_extractor.py`

The existing `world_events_add` loop (lines ~555–576) already emits `war_declared` and
`military_conflict_resolved`. Extend this same loop to also emit narrative events.

**5a. Extend the existing `world_events_add` loop to add `world_emergence_event` for ALL
WorldEvents and `narrative_milestone` for war/sovereignty:**

```python
# Inside the existing loop: for we in _world_evts:
cat = getattr(we, "category", None)

# NARRATIVE: world_emergence_event — one per WorldEvent in world_events_add (D1)
events.append(SimulationEvent(
    event_type="world_emergence_event",
    event_category="lifecycle",
    tick=tick,
    entity_id=None,
    severity="INFO",
    source_system="event_extractor",
    message="",
    payload={
        "category": str(cat) if cat else "",
        "region_id": str(getattr(we, "region_id", "") or ""),
        "subject": str(getattr(we, "subject", "") or ""),
    },
))

# NARRATIVE: narrative_milestone — war and sovereignty (D2)
if cat == WorldEventCategory.FACTION_WAR_DECLARED:
    events.append(SimulationEvent(
        event_type="narrative_milestone",
        event_category="lifecycle",
        tick=tick,
        entity_id=None,
        severity="WARNING",
        source_system="event_extractor",
        message="",
        payload={"milestone": "first_war", "subject": str(getattr(we, "subject", "") or "")},
    ))
elif cat == WorldEventCategory.SOVEREIGNTY_SHIFT:
    events.append(SimulationEvent(
        event_type="narrative_milestone",
        event_category="lifecycle",
        tick=tick,
        entity_id=None,
        severity="WARNING",
        source_system="event_extractor",
        message="",
        payload={
            "milestone": "first_sovereignty_transfer",
            "region_id": str(getattr(we, "region_id", "") or ""),
        },
    ))
```

**5b. Extend boss_spawned block (lines ~481–490) to also emit narrative_milestone:**

```python
# After emitting boss_spawned:
if kind in _BOSS_KINDS:
    events.append(SimulationEvent(  # existing boss_spawned
        event_type="boss_spawned", ...
    ))
    events.append(SimulationEvent(  # NEW: narrative_milestone
        event_type="narrative_milestone",
        event_category="lifecycle",
        tick=tick,
        entity_id=getattr(new_ent, "id", None),
        severity="WARNING",
        source_system="event_extractor",
        message="",
        payload={"milestone": "first_boss_spawned", "kind": kind},
    ))
```

**Note on milestone label:** `"first_boss_spawned"` is used instead of `"first_boss_kill"`
(see Decision D2 note). Test plan N-05 references `"first_boss_kill"` — the test must be
adjusted to expect `"first_boss_spawned"` OR to check for the `boss_spawned` event type
as a proxy, since no boss-death detection exists.

**Acceptance:** Tests N-01 (world_emergence_event emitted), N-02 (payload has region_id),
N-03 (all WorldEvents emit world_emergence_event, not just specific categories),
N-04 (war → first_war milestone), N-05 (boss spawn → first_boss_spawned milestone),
N-06 (sovereignty → first_sovereignty_transfer milestone), N-07 (non-milestone events still
emit world_emergence_event but not narrative_milestone).

**Files changed:** `src/observability/event_extractor.py`
**Dependencies:** Step 1. Independent of Steps 2, 3, 4.

---

### Step 6 — Add event_recorder to ScenarioRuntimeService; emit scenario events

**File:** `src/engine/scenario_runtime.py`

**6a. Add `"_event_recorder"` to `__slots__` (line ~118–127):**

```python
__slots__ = (
    "_spec",
    "_kernel",
    "_state",
    "_tick",
    "_paused",
    "_stall_counter",
    "_last_event_tick",
    "_initial_state",
    "_event_recorder",   # ADD
)
```

**6b. Add `TYPE_CHECKING` import for EventRecorder (avoid circular import):**

```python
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from src.observability.event_recorder import EventRecorder  # confirm actual module
```

**6c. Extend `__init__()` signature (add after `initial_state`):**

```python
def __init__(
    self,
    spec: "SimulationScenarioDefinition",
    initial_state: Optional["AuthoritativeState"] = None,
    event_recorder: Optional["EventRecorder"] = None,
) -> None:
    ...
    self._event_recorder = event_recorder
```

**6d. Emit `scenario_stalled` and `scenario_objective_completed/failed` in
`_evaluate_after_tick()` (lines ~279–309):**

After the existing `self._state = result` / `self._paused = True` assignments, add emission:

For `OBJECTIVE_MET` / `OBJECTIVE_FAILED` (after line ~288):
```python
if result != ScenarioObjectiveState.RUNNING:
    self._state = result
    self._paused = True
    if self._event_recorder is not None:
        from src.observability.events import SimulationEvent
        evt_type = (
            "scenario_objective_completed"
            if result == ScenarioObjectiveState.OBJECTIVE_MET
            else "scenario_objective_completed"  # failed also maps to completed with status
        )
        # Note: no separate "scenario_objective_failed" event type in scorer;
        # use scenario_objective_completed with payload status for both terminal states.
        # Adjust if scorer differentiates.
        self._event_recorder.record(SimulationEvent(
            event_type="scenario_objective_completed",
            event_category="infrastructure",
            tick=self._tick,
            entity_id=None,
            severity="INFO",
            source_system="scenario_runtime",
            message="",
            payload={
                "scenario_id": getattr(self._spec, "id", ""),
                "outcome": result.name,
            },
        ))
    return
```

For `STALLED` (after line ~308):
```python
if self._stall_counter > STALL_THRESHOLD:
    self._state = ScenarioObjectiveState.STALLED
    self._paused = True
    if self._event_recorder is not None:
        from src.observability.events import SimulationEvent
        self._event_recorder.record(SimulationEvent(
            event_type="scenario_stalled",
            event_category="infrastructure",
            tick=self._tick,
            entity_id=None,
            severity="WARNING",
            source_system="scenario_runtime",
            message="",
            payload={
                "scenario_id": getattr(self._spec, "id", ""),
                "stall_counter": self._stall_counter,
                "last_event_tick": self._last_event_tick,
            },
        ))
```

**Note:** `scenario_objective_failed` vs `scenario_objective_completed` — the test plan
S-03 expects emission for `OBJECTIVE_FAILED`. Emit `scenario_objective_completed` with
`payload["outcome"] == "OBJECTIVE_FAILED"` (one event type, differentiated by payload),
OR emit `scenario_objective_completed` only for `OBJECTIVE_MET` and a distinct
`scenario_objective_failed` event for `OBJECTIVE_FAILED`. The NarrativeScorer's weights
table should be checked at implementation time to determine which event type is expected.
Use whichever the scorer expects; emit with `outcome` in payload for disambiguation.

**Acceptance:** Tests S-01 (stalled emits event), S-02 (objective_met emits completed),
S-03 (objective_failed emits failed), S-04 (None-safe — no AttributeError).
S-05 is a gap test (scenario_objective_progressed: pytest.skip).
Existing `ScenarioRuntimeService(spec)` call sites must not break.

**Files changed:** `src/engine/scenario_runtime.py`
**Dependencies:** Step 1. Independent of Steps 2–5.

---

### Step 7 — Write new test file: test_event_extractor_narrative.py

**File:** `tests/unit/observability/test_event_extractor_narrative.py` (NEW)

Implement all N-01..N-18 test cases from `test_plan.md §Group B–G`:

**Group B (N-01..N-03):** `world_emergence_event` — build `_make_update()` with
`world_events_add=[WorldEvent(category=WorldEventCategory.ENTITY_DEATH, tick=1)]`;
assert `world_emergence_event` in emitted event types. N-03: non-emergence categories
still produce `world_emergence_event` (all categories do — per Decision D1).
Add N-03b as gap test: `pytest.skip("world_emergence_event: emits for all WorldEventCategory values by design; no threshold discrimination")`.

**Group C (N-04..N-07):** `narrative_milestone` — use `FACTION_WAR_DECLARED`,
`SOVEREIGNTY_SHIFT`, and `entities_add` with boss kind. N-07: `RESOURCE_HARVESTED`
WorldEvent emits `world_emergence_event` but NOT `narrative_milestone`.

Note: adjust N-05 payload assertion to `"first_boss_spawned"` (not `"first_boss_kill"`).

**Group E (N-08..N-11):** `hero_death_unrecorded` — build state diff with entity
transitioning `lifecycle.active: True → False` and `kind="hero"`. N-09: `kind="goblin_raider"`
does not emit. N-11: gap test (`pytest.skip`) — always emits; chronicle cross-check not
implemented.

**Group F (N-12..N-14):** Quest confirmation tests — assert `QuestEvent` (not `quest_started`)
is emitted by EventExtractor directly; translation is handled separately. These tests confirm
no double-emission from the new narrative extractor code.

**Group G (N-15..N-18):** Import guard — AST-based check that `simulation_quality` is not
imported in `phase.py`, `lifecycle.py`, `narrative_ledger.py`, `scenario_runtime.py`.

**Pattern:** Follow `test_event_extractor_social_faction.py` builder pattern:
`MagicMock`-based `_entity()`, `_prior_state()`, `_curr_state()`, `_update()` helpers.
Assert on `[e.event_type for e in events]`.

**Files changed:** `tests/unit/observability/test_event_extractor_narrative.py` (NEW)
**Dependencies:** Steps 4, 5 (tests verify implemented behavior)

---

### Step 8 — Add NarrativeLedger tests (TC-D16..TC-D19)

**File:** `tests/unit/campaigns/test_narrative_ledger.py` (additions)

Implement TC-D16..TC-D19 from `test_plan.md §Group A`:
- TC-D16: `test_record_emits_chronicle_entry_created_when_recorder_provided` — construct
  `NarrativeLedger(entries=[], event_recorder=mock_recorder)`, call
  `ledger.emit_chronicle_event(entry, tick=5)`, assert `mock_recorder.record.called` once.
- TC-D17: `test_record_no_emission_when_recorder_none` — `event_recorder=None`; no AttributeError.
- TC-D18: `test_chronicle_entry_payload_contains_entry_fields` — emitted event payload has
  `entry_id`, `event_type`, `significance`, `episode`.
- TC-D19: `test_recorder_not_called_on_query` — `ledger.query()` does not call recorder.

**Files changed:** `tests/unit/campaigns/test_narrative_ledger.py`
**Dependencies:** Step 2

---

### Step 9 — Add ScenarioRuntimeService tests (S-01..S-05)

**File:** `tests/unit/engine/test_scenario_runtime_service.py` (additions)

Implement S-01..S-05 from `test_plan.md §Group D`:
- S-01: stall threshold crossed → `scenario_stalled` emitted.
- S-02: `OBJECTIVE_MET` → `scenario_objective_completed` emitted.
- S-03: `OBJECTIVE_FAILED` → `scenario_objective_completed` (outcome=FAILED) or
  `scenario_objective_failed` emitted (per actual scorer contract).
- S-04: `event_recorder=None` → no AttributeError; existing test patterns unchanged.
- S-05: `pytest.skip("scenario_objective_progressed: binary ObjectiveEvaluator only — no partial progress")`.

**Files changed:** `tests/unit/engine/test_scenario_runtime_service.py`
**Dependencies:** Step 6

---

### Step 10 — Run full regression suite + all new tests

**Command:**
```bash
uv run --with pytest python3 -m pytest \
    tests/simulation_quality/test_narrative_scorer.py \
    tests/unit/campaigns/test_narrative_ledger.py \
    tests/unit/engine/test_scenario_runtime_service.py \
    tests/unit/observability/test_event_extractor_narrative.py \
    tests/unit/observability/test_event_extractor_simq.py \
    tests/unit/observability/test_event_extractor_social_faction.py \
    tests/unit/observability/test_event_extractor_economy.py \
    tests/unit/observability/test_event_extractor_world.py \
    tests/simulation_quality/test_quality_hub_event_translation.py \
    -v
```

**Acceptance:** All pass. Zero regressions in pre-existing test files. Any failure → fix in
the corresponding step's file before proceeding.

**Files changed:** none
**Dependencies:** Steps 7, 8, 9

---

### Step 11 — Update parity ledger

**File:** `docs/parity_ledger/infrastructure.yaml`

**11a. INFRA-247** — find entry, update `divergence_note` to reflect the gap is resolved:

```yaml
# BEFORE: divergence_note documenting chronicle_entry_created gap
divergence_note: >
  chronicle_entry_created events emitted as disk JSONL only (not event bus) — known gap.
  ...

# AFTER:
divergence_note: ""
v2_evidence: >
  TCK-20260629-SIMQ-EMIT-NARRATIVE wires chronicle_entry_created to event bus via
  CampaignOrchestrator._emit_chronicle_events(). Tested in
  tests/unit/campaigns/test_narrative_ledger.py (TC-D16..TC-D19).
status: verified
```

**11b. SIMQ-CALIBRATED-001** — append NARRATIVE pillar status to `v2_evidence`:

```yaml
v2_evidence: >
  [existing text] ...
  TCK-20260629-SIMQ-EMIT-NARRATIVE implements NARRATIVE pillar (7 new emission hooks):
  chronicle_entry_created (orchestrator), world_emergence_event + narrative_milestone
  (EventExtractor from world_events_add), hero_death_unrecorded (EventExtractor entity diff),
  scenario_stalled + scenario_objective_completed (ScenarioRuntimeService injection).
  Gap: scenario_objective_progressed (binary ObjectiveEvaluator — no partial progress concept).
  Tests: tests/unit/observability/test_event_extractor_narrative.py (N-01..N-18).
```

**Files changed:** `docs/parity_ledger/infrastructure.yaml`
**Dependencies:** Step 10 (ledger updated only after tests pass)

---

### Step 12 — Finalize ticket

- Update `tickets/inprogress/TCK-20260629-SIMQ-EMIT-NARRATIVE.md`:
  - Status: DONE
  - Fill Implementation Notes, Test Summary, Files Changed, Completion Summary
  - Update AC checklist: check off implemented items; mark `scenario_objective_progressed`
    gap with note referencing S-05 gap test
- Move to `tickets/done/TCK-20260629-SIMQ-EMIT-NARRATIVE.md`
- Delete source file: `rm tickets/inprogress/TCK-20260629-SIMQ-EMIT-NARRATIVE.md`
- Move `staging_artifacts/TCK-20260629-SIMQ-EMIT-NARRATIVE/` to `stored_artifacts/`
- Append row to `tickets/working_log.csv` (bottom)
- Clean up: `rm -rf data/runs/* reports/release_proof/*` (if populated)
- Run `make knowledge-index-update` (docs/parity_ledger modified)
- Write agent-monitoring entries: one run entry in `agent-monitoring/runs.jsonl` + at least
  one event in `agent-monitoring/events.jsonl`
- Stage `agent-monitoring/` including `tools.jsonl` in the commit
- Commit: `TCK-20260629-SIMQ-EMIT-NARRATIVE: emit NARRATIVE pillar events (chronicle, emergence, scenario, hero-death)`

**Dependencies:** Step 11

---

## Dependency Map

```
Step 1 (baseline)
  ├── Step 2 (NarrativeLedger event_recorder)
  │     └── Step 3 (orchestrator wiring)   → Step 8 (TC-D16..D19 tests)
  ├── Step 4 (hero_death_unrecorded)        → Step 7 (N-08..N-11 tests)
  ├── Step 5 (world_emergence + milestone)  → Step 7 (N-01..N-07 tests)
  └── Step 6 (ScenarioRuntimeService)       → Step 9 (S-01..S-05 tests)
                                                │
                                          Steps 7, 8, 9
                                                │
                                                ▼
                                          Step 10 (full regression run)
                                                │
                                                ▼
                                          Step 11 (parity ledger)
                                                │
                                                ▼
                                          Step 12 (finalize)
```

Steps 2/3, 4, 5, 6 are independent of each other and can be executed in any order
(or in parallel) after Step 1. Steps 7, 8, 9 can also be executed in parallel — they
test different files.

---

## Acceptance Criteria → Steps

| AC | Covered by |
|---|---|
| `chronicle_entry_created` emitted from NarrativeLedger when entry written | Steps 2, 3 |
| `world_emergence_event` emitted from EventExtractor per WorldEvent in world_events_add | Step 5 |
| `narrative_milestone` emitted for war, boss spawn, sovereignty shift | Step 5 |
| `scenario_objective_completed`, `scenario_stalled` emitted from ScenarioRuntimeService | Step 6 |
| `hero_death_unrecorded` emitted from EventExtractor entity diff | Step 4 |
| `quest_started/completed/failed` confirmed working (translation layer, no new emission) | Step 7, N-12..N-14 |
| NarrativeLedger `event_recorder` wiring is optional (None-safe) | Steps 2, 3; TC-D17 |
| No import of `src/simulation_quality/` from any narrative phase | Step 7, N-15..N-18 |
| NARRATIVE pillar shows non-zero events in calibration run | Step 10 regression suite |

---

## Decisions Summary — scope-out rationale

| Scoped-out item | Reason | Evidence |
|---|---|---|
| `scenario_objective_progressed` | `ObjectiveEvaluator` returns binary state only (`RUNNING/MET/FAILED`); no partial progress field in schema | investigation.md §ScenarioRuntimeService; test_plan S-05 |
| `hero_death_unrecorded` suppression when chronicle present | No tick-level "chronicled this tick" signal in StateUpdate; orchestrator writes chronicle at episode boundary, not per tick | investigation.md R3; Decision D4 |
| New `WorldEventCategory.WORLD_EMERGENCE_THRESHOLD` | All WorldEvents in world_events_add are by definition world emergence events; threshold is satisfied by presence in the list | investigation.md §WorldEmergencePhase; Decision D1 |
| `WorldEmergencePhase.execute()` changes | @staticmethod; emission goes through EventExtractor reading world_events_add (established pattern) | investigation.md §WorldEmergenceResult; Decision D1 |
| `LifecycleSystem.resolve_lifecycle()` changes | hero_death_unrecorded detection via EventExtractor state diff; LifecycleSystem is stateless | investigation.md §LifecycleSystem; Decision D4 |
| `narrative_milestone` "first X" state in emitter | EventExtractor is stateless per-call; dedup delegated to NarrativeScorer (established pattern) | investigation.md Q2 option (d); Decision D2 |

---

## Unresolved Questions

### UQ-1: boss_spawned vs boss_killed for narrative_milestone

Test plan N-05 expects `payload["milestone"] == "first_boss_kill"`. EventExtractor detects
boss spawn via `entities_add` (new entity with boss kind). No boss-death detection currently
exists in EventExtractor. **Decision made (D2): use `"first_boss_spawned"`.** The test
must be updated to expect `"first_boss_spawned"`. If the NarrativeScorer expects
`"first_boss_kill"` in the milestone payload, the scorer's weight table should be updated
at the same time. **Action at implementation: check `src/simulation_quality/scorers/narrative.py`
for the exact milestone key it scores against, and align the emission payload key to match.**

### UQ-2: EventRecorder import path

Investigation references `EventRecorder` but does not specify its module path. At Step 2
and Step 6 implementation time, run:
```bash
grep -rn "class EventRecorder" src/observability/
```
Use the actual module path. If no `EventRecorder` class exists (events may be recorded
differently), check the `src/observability/` directory for a recorder/collector interface
and adapt accordingly.

### UQ-3: CampaignOrchestrator existing event_recorder field

Step 3 assumes `getattr(self, "_event_recorder", None)` will find an injected recorder.
If the orchestrator has no such field, the `_emit_chronicle_events()` helper will be a
no-op in production until the orchestrator is wired (which may be outside this ticket's
scope if it's a Kernel-level concern). **Action at implementation: check orchestrator
`__init__` signature and wire accordingly if absent.**
