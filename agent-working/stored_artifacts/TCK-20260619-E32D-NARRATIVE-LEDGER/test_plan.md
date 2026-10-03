---
status: active
ticket_id: TCK-20260619-E32D-NARRATIVE-LEDGER
artifact_type: test_plan
date: 2026-06-21
---

# Test Plan — TCK-20260619-E32D-NARRATIVE-LEDGER

## Scope

Unit tests in `tests/unit/campaigns/test_narrative_ledger.py` (new).
Integration test in `tests/integration/scenarios/test_campaign_runtime.py` (extend).
Update `tests/unit/campaigns/test_campaign_state.py` for NarrativeLedgerEntry field changes.

## Test Cases — Unit

### TC-D1: NarrativeLedger.record() appends entry
Construct `NarrativeLedger()`, call `.record(entry)`, assert `len` == 1.

### TC-D2: NarrativeLedger.query(event_type=...) filters by event_type
Add entries of mixed event_type. Query for "entity_death" → only death entries returned.

### TC-D3: NarrativeLedger.query(episode=...) filters by episode
Add entries from episode 0 and episode 1. Query episode=1 → only ep1 entries.

### TC-D4: NarrativeLedger.query(min_significance=...) filters by significance
Add entries with significance 0.3, 0.5, 0.9. Query min_significance=0.6 → only 0.9 entry.

### TC-D5: NarrativeLedger.query() with no filters returns all entries
Add 5 entries. Query with no filters → all 5 returned.

### TC-D6: NarrativeLedger.query() combined filters (event_type + episode)
Add mixed entries. Query event_type="quest_completed" AND episode=0 → correct subset.

### TC-D7: NarrativeLedger.to_jsonl() writes valid JSONL
Create ledger with 3 entries. Call to_jsonl(tmp_path). Read lines; assert each is valid JSON
with required fields (episode, tick, event_type, subject_id, payload, significance).

### TC-D8: NarrativeLedger.to_jsonl() round-trip entries parseable
Verify each JSONL line deserializes to a dict matching entry.to_dict().

### TC-D9: NarrativeLedgerEntry is frozen (immutable)
Attempt to mutate a field; assert FrozenInstanceError.

### TC-D10: NarrativeLedgerEntry.to_dict() / from_dict() round-trip
Full field round-trip: episode, tick, event_type, subject_id, payload, significance,
entry_id.

### TC-D11: NarrativeLedger constructed with initial entries
`NarrativeLedger(entries=[e1, e2])` — query returns both.

### TC-D12: _extract_narrative_entries() maps WorldEvent correctly
Unit test the extraction helper: mock final_state.recent_world_events with
ENTITY_DEATH and QUEST_COMPLETED events. Assert resulting NarrativeLedgerEntry
fields (event_type, significance, subject_id, episode).

### TC-D13: _extract_narrative_entries() skips unsupported event categories
Add a WorldEvent with category=REGION_ENTERED (below significance threshold /
not mapped). Assert it is not in the result.

### TC-D14: CampaignState.narrative_ledger populated after _advance_state()
Mock _advance_state call chain. Verify narrative_ledger grows after each episode.

### TC-D15: NarrativeLedger.query() returns empty list when no matches
Query on empty ledger; assert [].

## Test Cases — Integration

### TC-D16: test_narrative_ledger_populated_with_cross_episode_events (AC test)
Tag: `@pytest.mark.slow`
Run 2 episodes (tick_limit=15 each). After both:
- `len(orch.state.narrative_ledger) >= 2` (at least one event per episode)
- Query event_type="entity_death" returns only death entries
- NarrativeLedger wrapping the ledger list can serialize to_jsonl() without error
The ≥10 AC is best-effort; verified via unit test with mocked events.

## Test Cases — State update

### TC-D17: NarrativeLedgerEntry round-trip with full 6-field schema
Update `test_narrative_ledger_entry_round_trip` in `test_campaign_state.py`
to use `episode` (not `episode_index`) and all 6 fields.

## Command

```bash
pytest tests/unit/campaigns/test_narrative_ledger.py tests/unit/campaigns/test_campaign_state.py -x -v
pytest tests/integration/scenarios/test_campaign_runtime.py::test_narrative_ledger_populated_with_cross_episode_events -x -v -m slow
```
