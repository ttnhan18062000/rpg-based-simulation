---
ticket_id: TCK-20260619-E53Db-SIEGE-BETRAYAL-LEDGER
phase: investigation
date: 2026-06-22
---

# Investigation — TCK-20260619-E53Db-SIEGE-BETRAYAL-LEDGER

## Summary

Wire `SIEGE_BEGINS` and `BETRAYAL` world events into the `NarrativeLedger` pipeline.
Three implementation sites: (1) `WorldEventCategory` constants, (2) emission sites in
engine code, (3) `_SIGNIFICANCE_MAP` in `CampaignOrchestrator`.

---

## Finding 1: WorldEventCategory — Neither Constant Exists Yet

`src/domains/world_emergence/schema.py` defines `WorldEventCategory` as a `str, Enum`.
Current tail of the enum (lines 38–44):

```
FACTION_WAR_DECLARED     = "FACTION_WAR_DECLARED"    # E53Bd
FACTION_ALLIANCE_FORMED  = "FACTION_ALLIANCE_FORMED"  # E53Bd
FACTION_PEACE_TREATY     = "FACTION_PEACE_TREATY"     # E53Bd
TERRITORY_TRANSFERRED    = "TERRITORY_TRANSFERRED"    # E53Cc
WAR_ENDED_EXHAUSTION     = "WAR_ENDED_EXHAUSTION"     # E53Cd
```

Neither `SIEGE_BEGINS` nor `BETRAYAL` is present. Both must be added as:

```python
SIEGE_BEGINS = "SIEGE_BEGINS"   # E53Db
BETRAYAL     = "BETRAYAL"       # E53Db
```

No name conflict with legacy enums (confirmed by scan). The ticket notes a possible
rename to `FACTION_BETRAYAL` if conflicts arise — none found, so use plain `BETRAYAL`.

---

## Finding 2: SIEGE_BEGINS Emission Site in military_conflict.py

### Current siege initiation block (lines 279–296)

```python
# Siege initiation (first tick with no active siege for this pair)
if reg.siege_state is None:
    wu = wu.merge(WorldUpdate(
        region_id=contested_region_id,
        siege_state_set=SiegeState(
            attacker_faction_id=attacker_id,
            defender_faction_id=defender_id,
            siege_progress=0.0,
            started_tick=state.tick,
        ),
    ))

# Siege degradation: -5% service_availability, +5% siege_progress per tick
wu = wu.merge(WorldUpdate(...))
```

### Where to emit

`SIEGE_BEGINS` must be appended to `world_events` **inside** the `if reg.siege_state is None:` block, immediately after the `wu = wu.merge(...)` that sets `siege_state_set`. The existing list `world_events: List[WorldEvent]` already collects events returned via `StateUpdate(world_events_add=world_events)`.

`WorldEvent` fields in use by existing events (`WAR_ENDED_EXHAUSTION`, `TERRITORY_TRANSFERRED`):
- `category`: `WorldEventCategory` enum value
- `tick`: `state.tick` (int)
- `subject`: faction pair string or transfer string (str, used for ledger `subject_id`)
- `payload`: `Dict[str, float]` — **must be float-valued** (schema constraint)

### subject_id for SIEGE_BEGINS

The ticket scope states `NarrativeLedgerEntry.subject_id = region_id`. This means
`WorldEvent.subject` should be `contested_region_id` (the region string), not a faction
pair. The faction IDs go in `payload` for downstream use.

**Key constraint:** `WorldEvent.payload` is typed `Dict[str, float]`, not `Dict[str, Any]`.
Faction IDs are strings — they cannot go directly into `payload`. Use `subject` to carry
the region_id, and put only float/numeric data in payload (e.g., `{"siege_progress": 0.0}`).
The `attacker_faction_id` and `defender_faction_id` must be extracted from `WorldEvent.subject`
or via a secondary lookup in `_SIGNIFICANCE_MAP` / orchestrator logic, or the payload approach
must be adjusted. See Decision section below.

### Decision: payload carries only floats; faction IDs in subject context

The existing `TERRITORY_TRANSFERRED` event uses `subject=f"{attacker}:{defender}:{region}"`.
For `SIEGE_BEGINS`, use `subject=contested_region_id` (matches ticket spec for
`NarrativeLedgerEntry.subject_id = region_id`) and `payload={"siege_progress": 0.0}`.
The orchestrator harvests only `world_event.subject` and `world_event.payload` — the
faction IDs in the payload are specified in the ticket but cannot be `float`. This is a
**payload type mismatch**: the ticket shows string faction IDs in payload, but
`WorldEvent.payload: Dict[str, float]`. Resolution: omit faction IDs from payload, or
store numeric proxies. The `NarrativeLedgerEntry.payload` (in `state.py`) is `dict` (no
type restriction), so the orchestrator can add faction IDs there from separate lookups, or
the implementation must accept that faction IDs are not carried in `WorldEvent.payload`.

**Recommended implementation**: emit `WorldEvent(category=SIEGE_BEGINS, tick=state.tick,
subject=contested_region_id, payload={"siege_progress": 0.0})`. The orchestrator
`_SIGNIFICANCE_MAP` handler reads `world_event.subject` as `region_id` and constructs the
`NarrativeLedgerEntry` with `subject_id=world_event.subject`. Faction IDs are not in the
WorldEvent payload (payload type limitation), so the orchestrator entry's `payload` will be
`{"siege_progress": 0.0}` rather than the ticket's proposed `{"attacker": ..., "defender": ...}`.
If faction IDs in ledger payload are required, this warrants a schema extension or a string
value in payload (would require relaxing `Dict[str, float]` to `Dict[str, Any]`).

---

## Finding 3: BETRAYAL Emission Site — Pipeline Gap

### DiplomaticActionHandler: pure function returning FactionUpdate, no WorldEvent

`src/domains/faction/diplomatic_actions.py` contains the module-level `handle()` function
(not a class — the ticket calls it `DiplomaticActionHandler` but it is a bare module function).

`_handle_betrayal()` (lines 136–156) returns two `FactionUpdate` records when the current
relation is `ALLIED`. It does **not** currently emit any `WorldEvent`. It is a pure function
with no side effects.

### How pipeline wires diplomatic actions

Looking at `src/engine/pipeline.py` Phase 8d (lines 185–213):

```python
_diplo_transition_updates = compute_transitions(state.factions)
_diplo_alliance_updates: list = []
# Only AllianceProposal directives are dispatched through diplomatic_actions.handle
for _fa_id, _fb_id, _ps in compute_common_enemy_pairs(state.factions):
    _diplo_alliance_updates.extend(_diplo_handle(AllianceProposal(...), state.factions))

_diplo_world_events = events_from_transitions(
    _diplo_transition_updates, _diplo_alliance_updates, state.factions, state.tick,
)
update = run_phase("diplomatic_transitions", update,
    lambda u: _SU_dt(faction_updates=_diplo_updates, world_events_add=_diplo_world_events))
```

**Critical gap**: `faction_directives` (produced by `FactionDecisionPhase.execute()` at
line 171) are passed to `AdventureDecisionPhase` but **never dispatched through
`diplomatic_actions.handle()`** for `Betrayal` directives. The pipeline only calls
`_diplo_handle()` for `AllianceProposal` via `compute_common_enemy_pairs`. `Betrayal`
directives are generated by `FactionDecisionPhase` but their `FactionUpdate` effects are
never applied — and therefore no `BETRAYAL` WorldEvent is currently possible.

### Two options for BETRAYAL WorldEvent emission

**Option A (recommended): Add Betrayal dispatch in Phase 8d**
In `pipeline.py` Phase 8d, after the alliance generation loop, add a loop that iterates
`faction_directives`, calls `_diplo_handle(d, state.factions)` for each `Betrayal`
instance, collects the resulting `FactionUpdate` records into `_diplo_alliance_updates`,
and passes them to `events_from_transitions()` (which must be extended to detect
`HOSTILE` transitions from previously-ALLIED pairs as BETRAYAL events rather than generic
hostility events). The `events_from_transitions` function in `diplomatic_state_machine.py`
already deduplicates by pair — it just needs a BETRAYAL category branch.

**Option B: Emit WorldEvent inside `_handle_betrayal()`**
Change `diplomatic_actions.py`'s `_handle_betrayal()` to return a
`(List[FactionUpdate], List[WorldEvent])` tuple and update all callers. This breaks the
current pure-function return contract (List[FactionUpdate] only).

**Option A is strongly preferred**: keeps `diplomatic_actions.py` as a pure
FactionUpdate-returning module, adds BETRAYAL detection to `events_from_transitions` where
all diplomatic WorldEvent logic already lives, and wires Betrayal directives through the
same apply-path that all other diplomatic updates use. The ticket's note that "WorldEvent
emission from the faction domain layer must not break the src/engine/ ↔ src/domains/campaigns/
boundary" is satisfied — `events_from_transitions` lives in `src/domains/faction/` and
already handles WorldEvent emission, not `orchestrator.py`.

### events_from_transitions extension for BETRAYAL

Need to detect when a `FactionUpdate` sets a relation to `HOSTILE` and the prior relation
was `ALLIED` (not just `HOSTILE` from TENSE via the state machine). Add a branch in
`events_from_transitions()`:

```python
if new_state == DiplomaticState.HOSTILE:
    prior_fs = prior_factions.get(upd.faction_id)
    if prior_fs is not None:
        prior_rel = prior_fs.diplomatic_relations.get(other_fid, DiplomaticState.NEUTRAL)
        if prior_rel == DiplomaticState.ALLIED:
            events.append(WorldEvent(
                category=WorldEventCategory.BETRAYAL,
                tick=tick,
                subject=":".join(sorted([upd.faction_id, other_fid])),
            ))
```

This correctly identifies ALLIED→HOSTILE transitions (betrayals) vs
TENSE→HOSTILE transitions (normal hostility escalation).

---

## Finding 4: CampaignOrchestrator._advance_state() Structure

`_advance_state()` (orchestrator.py lines 169–185) calls `_extract_narrative_entries()`
as a separate method — it does **not** inline the conversion. This is clean for extension.

`_extract_narrative_entries()` (lines 257–295) iterates `final_state.recent_world_events`,
resolves `world_event.category` to a string key, looks up `_SIGNIFICANCE_MAP`, and
constructs `NarrativeLedgerEntry` with:
- `episode`: episode_index param
- `tick`: `world_event.tick`
- `event_type`: from `_SIGNIFICANCE_MAP[key][0]`
- `subject_id`: `world_event.subject or ""`
- `payload`: `dict(world_event.payload)` if payload else `{}`
- `significance`: from `_SIGNIFICANCE_MAP[key][1]`
- `entry_id`: `f"{episode_index}:{world_event.tick}:{event_type}:{subject_id}"`

**No custom subject_id override logic per category exists** — the orchestrator always uses
`world_event.subject` as `subject_id` verbatim. This means:
- For `SIEGE_BEGINS`: `subject_id` = `world_event.subject` = `region_id` ✓ (matches ticket)
- For `BETRAYAL`: `subject_id` = `world_event.subject` = `"betrayer:betrayed"` (sorted) ✓

The ticket's proposed custom `subject_id=payload["defender_faction_id"]` for SIEGE_BEGINS
is **not needed** — just setting `WorldEvent.subject = region_id` in the emission code
achieves this naturally through the existing orchestrator pipeline.

---

## Finding 5: _SIGNIFICANCE_MAP — Neither Key Exists

`_SIGNIFICANCE_MAP` in `orchestrator.py` (lines 45–60) does not contain `"SIEGE_BEGINS"`
or `"BETRAYAL"`. Both must be added:

```python
# E53Db: Siege and betrayal events
"SIEGE_BEGINS": ("siege_begins", 0.80),
"BETRAYAL":     ("betrayal",     0.85),
```

This is the **only change** needed to `orchestrator.py` (beyond the constant additions to
`schema.py`). No structural change to `_extract_narrative_entries()` is required.

---

## Finding 6: NarrativeLedgerEntry Constructor

Defined in `src/domains/campaigns/state.py` lines 144–166. Frozen dataclass with:

```
episode:      int
tick:         int
event_type:   str
subject_id:   str
payload:      dict
significance: float
entry_id:     str = ""   # optional; empty for legacy records
```

All 6 positional fields are required (entry_id has a default). The constructor matches the
existing pattern in `_extract_narrative_entries()` exactly — no schema change needed.

---

## Finding 7: Existing Test Coverage for Regression Surface

### tests/unit/campaigns/
- `test_campaign_orchestrator.py` — 12 tests, covers `_advance_state`, entity/faction
  carry-forward. No tests for `_SIGNIFICANCE_MAP` entries by name, but TC-D14 checks that
  3 event types populate the ledger. Any `_SIGNIFICANCE_MAP` change that breaks dispatch
  will surface in TC-D12/TC-D13.
- `test_narrative_ledger.py` — 15 tests including TC-D12 (maps WorldEvent→entry) and TC-D13
  (skips unsupported categories). Adding new map entries won't break either.

### tests/unit/faction/
- `test_diplomacy.py` — covers E53Bb `_handle_betrayal()` (tests `test_diplomatic_action_betrayal_valid`,
  `test_diplomatic_action_betrayal_invalid_not_allied`). Also covers `events_from_transitions`
  for WAR/PEACE/ALLIANCE. **Regression risk**: if `events_from_transitions` is extended to
  detect ALLIED→HOSTILE as BETRAYAL, the existing `_diplo_transition_updates` path for
  TENSE→HOSTILE must NOT accidentally emit BETRAYAL (prior_rel would be TENSE, not ALLIED).
- `test_military_conflict_phase.py` — 5 tests covering noop, war pair detection, state
  return type. No tests for siege initiation or WorldEvent emission from siege. New
  `SIEGE_BEGINS` emission will not break existing tests (all existing tests return before
  reaching the siege block, or have no regions set up).
- `test_siege_model.py` and `test_territory_transfer.py` — may contain siege initiation
  coverage; these must be checked at implementation time for any region/siege_state setup
  that would now trigger a `SIEGE_BEGINS` event.

---

## Key Architectural Decisions

### Decision 1: Betrayal WorldEvent emitted in events_from_transitions, not in _handle_betrayal
`diplomatic_actions.handle()` remains a pure `List[FactionUpdate]` return function. BETRAYAL
WorldEvent detection lives in `events_from_transitions` (same as WAR/PEACE/ALLIANCE).
Betrayal directives must be dispatched through `_diplo_handle` in `pipeline.py` Phase 8d.

### Decision 2: SIEGE_BEGINS emission appended to world_events inside the `if reg.siege_state is None:` block
This is the natural first-tick onset gate. `world_events` list is collected and returned
via `StateUpdate(world_events_add=world_events)` — the same path used by WAR_ENDED_EXHAUSTION
and TERRITORY_TRANSFERRED.

### Decision 3: WorldEvent.subject carries the semantically correct subject_id
- `SIEGE_BEGINS`: `subject = contested_region_id` → orchestrator uses as `subject_id = region_id`
- `BETRAYAL`: `subject = ":".join(sorted([betrayer, betrayed]))` → orchestrator uses as `subject_id`

### Decision 4: WorldEvent.payload carries only floats
`WorldEvent.payload: Dict[str, float]`. Faction IDs cannot be in payload. For SIEGE_BEGINS,
payload will be `{"siege_progress": 0.0}`. The `NarrativeLedgerEntry.payload` (unconstrained
`dict`) can hold whatever the orchestrator injects — but since `_extract_narrative_entries`
copies `world_event.payload` directly, faction IDs will not appear in the ledger entry payload.
This is a known limitation vs the ticket spec. Either accept it, or raise a schema extension
ticket to make `WorldEvent.payload: Dict[str, Any]`.

---

## Open Questions

1. **WorldEvent.payload type**: Can it accept `str` values (faction IDs)? If yes, the ticket's
   proposed payload with faction ID strings is achievable without schema change. Needs
   confirmation from `src/core/updates.py` / `apply_plan.py` — is `Dict[str, float]`
   enforced via validation or just a type hint? If a type hint only, `Dict[str, Any]` behavior
   may already work at runtime.

2. **Betrayal directive dispatch gap**: `Betrayal` directives from `FactionDecisionPhase` are
   currently never dispatched through `diplomatic_actions.handle()`. This is a pre-existing
   pipeline gap that this ticket must fix as a prerequisite to BETRAYAL WorldEvent emission.
   Confirm this is in scope (ticket text implies it) and not deferred to another ticket.

3. **test_siege_model.py and test_territory_transfer.py**: Need to check whether existing
   siege tests will newly produce SIEGE_BEGINS events that break assertion counts. These tests
   were not read during investigation — check at implementation start.
