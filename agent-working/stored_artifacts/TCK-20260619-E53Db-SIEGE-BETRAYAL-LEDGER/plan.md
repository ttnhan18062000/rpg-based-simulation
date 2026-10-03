# Plan — TCK-20260619-E53Db-SIEGE-BETRAYAL-LEDGER

## Ordered Steps

### 1. `src/domains/world_emergence/schema.py`
Add two members to `WorldEventCategory`:
```python
# E53Db: Siege and betrayal events
SIEGE_BEGINS = "SIEGE_BEGINS"
BETRAYAL = "BETRAYAL"
```

### 2. `src/engine/military_conflict.py`
Inside the `if reg.siege_state is None:` block (line 281), after the `wu.merge(WorldUpdate(..., siege_state_set=SiegeState(...)))`, append a SIEGE_BEGINS WorldEvent:
```python
world_events.append(WorldEvent(
    category=WorldEventCategory.SIEGE_BEGINS,
    tick=state.tick,
    subject=contested_region_id,
))
```
`payload` is empty — attacker/defender faction IDs cannot go in `payload: Dict[str, float]`.
`subject=contested_region_id` is what `_extract_narrative_entries` reads as `subject_id`, enabling `ChronicleNamer.name_milestone("The Siege of {region_name}")`.

### 3. `src/domains/faction/diplomatic_state_machine.py`
Extend `events_from_transitions()` with a new optional parameter:
```python
def events_from_transitions(
    transition_updates: List[FactionUpdate],
    alliance_updates: List[FactionUpdate],
    prior_factions: Dict[str, "FactionState"],
    tick: int,
    betrayal_updates: List["FactionUpdate"] | None = None,
) -> list:
```
At the end, before `return events`, add a loop over `betrayal_updates` detecting ALLIED→HOSTILE:
```python
seen_betrayal_pairs: set = set()
for upd in (betrayal_updates or []):
    for other_fid, new_state in upd.diplomatic_relations_set.items():
        if new_state == DiplomaticState.HOSTILE:
            prior_fs = prior_factions.get(upd.faction_id)
            if prior_fs is not None:
                prior_rel = prior_fs.diplomatic_relations.get(
                    other_fid, DiplomaticState.NEUTRAL
                )
                if prior_rel == DiplomaticState.ALLIED:
                    pair = frozenset([upd.faction_id, other_fid])
                    if pair in seen_betrayal_pairs:
                        continue
                    seen_betrayal_pairs.add(pair)
                    subject = ":".join(sorted([upd.faction_id, other_fid]))
                    events.append(WorldEvent(
                        category=WorldEventCategory.BETRAYAL,
                        tick=tick,
                        subject=subject,
                    ))
```
Existing callers in pipeline.py are unaffected (new param defaults to None).

### 4. `src/domains/campaigns/orchestrator.py`
Add two entries to `_SIGNIFICANCE_MAP`:
```python
"SIEGE_BEGINS":  ("siege_begins",  0.80),
"BETRAYAL":      ("betrayal",      0.85),
```
`_extract_narrative_entries()` already generically reads `world_event.subject` as `subject_id` — no other changes needed.

## Tests

### `tests/unit/faction/test_siege_ledger.py` (new)
- `test_siege_begins_emitted_on_first_siege_tick`: MilitaryConflictPhase emits SIEGE_BEGINS WorldEvent when siege_state is None before execution
- `test_siege_begins_not_emitted_when_siege_already_active`: No SIEGE_BEGINS when siege already in progress
- `test_orchestrator_converts_siege_begins_to_ledger_entry`: `_extract_narrative_entries` converts SIEGE_BEGINS → entry with event_type="siege_begins", significance=0.80, subject_id=region_id
- `test_narrative_ledger_query_siege_begins`: NarrativeLedger.query(event_type="siege_begins") returns correct entry

### `tests/unit/faction/test_betrayal_ledger.py` (new)
- `test_betrayal_emitted_when_allied_faction_transitions_hostile`: events_from_transitions with betrayal_updates containing ALLIED→HOSTILE emits BETRAYAL WorldEvent
- `test_betrayal_not_emitted_when_prior_not_allied`: No BETRAYAL if prior state was not ALLIED
- `test_betrayal_deduped_across_mirror_updates`: Both sides of pair produce only one BETRAYAL event
- `test_orchestrator_converts_betrayal_to_ledger_entry`: `_extract_narrative_entries` converts BETRAYAL → entry with event_type="betrayal", significance=0.85
- `test_narrative_ledger_query_betrayal`: NarrativeLedger.query(event_type="betrayal") returns correct entry

## Constraints
- `DiplomaticState.HOSTILE` must be verified to exist (from E53Bc) — grep before assuming
- `WorldEvent.payload` is `Dict[str, float]` — faction ID strings cannot go in payload
- `betrayal_updates` parameter defaults to `None` for full backward compatibility with existing pipeline.py call
