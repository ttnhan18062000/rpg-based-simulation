---
ticket_id: TCK-20260619-E53Db-SIEGE-BETRAYAL-LEDGER
phase: test_plan
date: 2026-06-22
---

# Test Plan — TCK-20260619-E53Db-SIEGE-BETRAYAL-LEDGER

## Scope

Tests for:
1. `SIEGE_BEGINS` WorldEvent constant exists in `WorldEventCategory`
2. `BETRAYAL` WorldEvent constant exists in `WorldEventCategory`
3. `MilitaryConflictPhase.execute()` emits `SIEGE_BEGINS` on first siege tick
4. `events_from_transitions()` emits `BETRAYAL` on ALLIED→HOSTILE transition
5. `CampaignOrchestrator._extract_narrative_entries()` converts both to `NarrativeLedgerEntry`
6. `NarrativeLedger.query()` can filter by `"siege_begins"` and `"betrayal"`
7. Regression: existing test suites pass without modification

---

## New Test Files

### File: `tests/unit/faction/test_siege_ledger.py`

```
TC-SL-1  SIEGE_BEGINS constant is in WorldEventCategory
TC-SL-2  MilitaryConflictPhase emits SIEGE_BEGINS on first siege tick (reg.siege_state is None)
TC-SL-3  MilitaryConflictPhase does NOT emit SIEGE_BEGINS on continuation tick (reg.siege_state already set)
TC-SL-4  SIEGE_BEGINS WorldEvent has subject = region_id, tick = state.tick
TC-SL-5  SIEGE_BEGINS flows through _extract_narrative_entries() to NarrativeLedgerEntry
TC-SL-6  NarrativeLedgerEntry for siege_begins has event_type="siege_begins", significance=0.80
TC-SL-7  NarrativeLedgerEntry.subject_id == region_id (not a faction ID)
TC-SL-8  entry_id format: "{episode}:{tick}:siege_begins:{region_id}"
TC-SL-9  NarrativeLedger.query(event_type="siege_begins") returns the siege entry
```

### File: `tests/unit/faction/test_betrayal_ledger.py`

```
TC-BL-1  BETRAYAL constant is in WorldEventCategory
TC-BL-2  events_from_transitions() emits BETRAYAL when ALLIED→HOSTILE detected in transition_updates
TC-BL-3  events_from_transitions() does NOT emit BETRAYAL when TENSE→HOSTILE (prior rel is TENSE, not ALLIED)
TC-BL-4  events_from_transitions() deduplicates BETRAYAL: exactly one event per faction pair
TC-BL-5  BETRAYAL WorldEvent has subject = sorted alphabetically "betrayer:betrayed"
TC-BL-6  BETRAYAL flows through _extract_narrative_entries() to NarrativeLedgerEntry
TC-BL-7  NarrativeLedgerEntry for betrayal has event_type="betrayal", significance=0.85
TC-BL-8  entry_id format: "{episode}:{tick}:betrayal:{betrayer}:{betrayed}" (sorted)
TC-BL-9  NarrativeLedger.query(event_type="betrayal") returns the betrayal entry
TC-BL-10 Betrayal when prior relation is not ALLIED → no BETRAYAL WorldEvent emitted
```

---

## Regression Test Cases (existing files)

### tests/unit/campaigns/test_narrative_ledger.py

Run all 15 existing tests unchanged. Key regressions to watch:

- `TC-D13` (skips unsupported categories): Adding `SIEGE_BEGINS`/`BETRAYAL` to `_SIGNIFICANCE_MAP`
  means they are now supported — this test must still pass because the events it feeds
  (`REGION_ENTERED`, `RESOURCE_HARVESTED`, `NEAR_DEATH`) remain unsupported.
- `TC-D12` (maps WorldEvent correctly): Not affected — tests `ENTITY_DEATH` and `QUEST_COMPLETED`.
- `TC-D14` (advance_state populates ledger): Not affected — tests three existing event types.

### tests/unit/campaigns/test_campaign_orchestrator.py

Run all 15 existing tests unchanged. No changes to orchestrator logic other than `_SIGNIFICANCE_MAP`
dict entries. Architecture guard `TC-14` (no engine imports in state.py) is not affected.

### tests/unit/faction/test_diplomacy.py

Run all existing tests unchanged. Specific regression risks:

- `test_diplomatic_action_betrayal_valid`: tests `_handle_betrayal()` returns `FactionUpdate` list.
  Not affected — `_handle_betrayal()` return type doesn't change.
- `test_events_from_transitions_war_declared` and `test_events_from_transitions_peace_treaty`:
  Must still pass — existing WAR and PEACE branches in `events_from_transitions()` are unchanged.
- New BETRAYAL branch in `events_from_transitions()` must not fire for TENSE→HOSTILE transitions
  (where prior_rel == TENSE, not ALLIED). This must be covered by `TC-BL-3`.

### tests/unit/faction/test_military_conflict_phase.py

Run all 5 existing tests unchanged. All existing tests use `_make_state({})` with no regions,
so no siege initiation code paths are reached. New SIEGE_BEGINS emission inside
`if reg.siege_state is None:` block won't affect noop or war-pair-detection tests.

### tests/unit/faction/test_siege_model.py and test_territory_transfer.py

Run at implementation time. **Check whether these tests set up regions with `siege_state=None`
and WAR factions** — if yes, they will now produce SIEGE_BEGINS WorldEvent in the returned
StateUpdate's `world_events_add`. Verify that existing assertions do not count `world_events_add`
elements. If they do, update expected count (not a behaviour regression — just a count assertion
that needs updating).

---

## Test Patterns

### Pattern: Testing SIEGE_BEGINS emission in MilitaryConflictPhase

```python
def _make_state_with_war_and_no_siege(tick=1):
    """Minimal state: two WAR factions, one contested region with no active siege."""
    from src.core.state import FactionState, RegionState, AuthoritativeState
    from src.core.enums import DiplomaticState
    fa = FactionState(faction_id="fa", diplomatic_relations={"fb": DiplomaticState.WAR},
                      military_strength=1.0, territory=["region_01"])
    fb = FactionState(faction_id="fb", diplomatic_relations={"fa": DiplomaticState.WAR},
                      military_strength=1.0, territory=[])

    class FakeState:
        factions = {"fa": fa, "fb": fb}
        regions = {"region_01": RegionState(region_id="region_01", bounds=(0,0,10,10))}
        entities = {}
        tick = tick

    return FakeState()

def test_siege_begins_emitted_on_first_tick():
    from src.engine.military_conflict import MilitaryConflictPhase
    from src.domains.world_emergence.schema import WorldEventCategory
    state = _make_state_with_war_and_no_siege(tick=3)
    result = MilitaryConflictPhase.execute(state)
    siege_events = [e for e in result.world_events_add
                    if e.category == WorldEventCategory.SIEGE_BEGINS]
    assert len(siege_events) == 1
    assert siege_events[0].subject == "region_01"
    assert siege_events[0].tick == 3
```

### Pattern: Testing SIEGE_BEGINS not emitted on continuation tick

```python
def test_siege_begins_not_emitted_on_continuation_tick():
    from src.core.state import SiegeState
    # Set up region with existing siege_state (continuation tick)
    # ... region_01 has siege_state = SiegeState(attacker_faction_id="fa", ...)
    result = MilitaryConflictPhase.execute(state)
    siege_events = [e for e in result.world_events_add
                    if e.category == WorldEventCategory.SIEGE_BEGINS]
    assert len(siege_events) == 0
```

### Pattern: Testing BETRAYAL in events_from_transitions

```python
def test_betrayal_worldevent_emitted_on_allied_to_hostile():
    from src.core.state import FactionState
    from src.core.updates import FactionUpdate
    from src.core.enums import DiplomaticState as DS
    from src.domains.faction.diplomatic_state_machine import events_from_transitions
    from src.domains.world_emergence.schema import WorldEventCategory

    prior_factions = {
        "traitor": FactionState(faction_id="traitor",
                                diplomatic_relations={"victim": DS.ALLIED}),
        "victim":  FactionState(faction_id="victim",
                                diplomatic_relations={"traitor": DS.ALLIED}),
    }
    betrayal_updates = [
        FactionUpdate(faction_id="traitor", diplomatic_relations_set={"victim": DS.HOSTILE}),
        FactionUpdate(faction_id="victim",  diplomatic_relations_set={"traitor": DS.HOSTILE}),
    ]
    events = events_from_transitions([], betrayal_updates, prior_factions, tick=7)

    betrayal_events = [e for e in events if e.category == WorldEventCategory.BETRAYAL]
    assert len(betrayal_events) == 1
    assert betrayal_events[0].subject == "traitor:victim"  # sorted
    assert betrayal_events[0].tick == 7
```

### Pattern: Testing _extract_narrative_entries for new categories

```python
def _make_world_event(category_value, tick, subject):
    """Use MagicMock matching test_narrative_ledger.py convention."""
    from unittest.mock import MagicMock
    cat = MagicMock()
    cat.value = category_value
    ev = MagicMock()
    ev.category = cat
    ev.tick = tick
    ev.subject = subject
    ev.payload = {}
    return ev

def test_siege_begins_flows_through_extract_narrative_entries():
    from src.domains.campaigns.orchestrator import CampaignManifest, CampaignOrchestrator
    manifest = CampaignManifest(id="t", episodes=[], base_seed=0)
    orch = CampaignOrchestrator(manifest)

    class FakeState:
        recent_world_events = [_make_world_event("SIEGE_BEGINS", tick=4, subject="border_region")]
        entities = {}

    entries = orch._extract_narrative_entries(FakeState(), episode_index=0)
    assert len(entries) == 1
    e = entries[0]
    assert e.event_type == "siege_begins"
    assert e.significance == 0.80
    assert e.subject_id == "border_region"
    assert e.tick == 4
    assert e.entry_id == "0:4:siege_begins:border_region"
```

---

## Test Execution Commands

```bash
# New tests
pytest tests/unit/faction/test_siege_ledger.py -x -v
pytest tests/unit/faction/test_betrayal_ledger.py -x -v

# Regression suite (must run clean)
pytest tests/unit/campaigns/test_narrative_ledger.py -x -v
pytest tests/unit/campaigns/test_campaign_orchestrator.py -x -v
pytest tests/unit/faction/test_diplomacy.py -x -v
pytest tests/unit/faction/test_military_conflict_phase.py -x -v
pytest tests/unit/faction/test_siege_model.py -x -v
pytest tests/unit/faction/test_territory_transfer.py -x -v
```

---

## Files to Create / Modify

| File | Action | Why |
|---|---|---|
| `src/domains/world_emergence/schema.py` | ADD `SIEGE_BEGINS`, `BETRAYAL` to `WorldEventCategory` | New event constants |
| `src/engine/military_conflict.py` | ADD `WorldEvent(SIEGE_BEGINS)` inside `if reg.siege_state is None:` block | Emit on onset |
| `src/domains/faction/diplomatic_state_machine.py` | EXTEND `events_from_transitions()` with ALLIED→HOSTILE → BETRAYAL branch | Betrayal detection |
| `src/engine/pipeline.py` | ADD Betrayal directive dispatch loop in Phase 8d | Wire Betrayal directives through `_diplo_handle` so FactionUpdates and BETRAYAL events are produced |
| `src/domains/campaigns/orchestrator.py` | ADD `"SIEGE_BEGINS"` and `"BETRAYAL"` entries to `_SIGNIFICANCE_MAP` | Harvest into NarrativeLedger |
| `tests/unit/faction/test_siege_ledger.py` | CREATE | New coverage |
| `tests/unit/faction/test_betrayal_ledger.py` | CREATE | New coverage |
