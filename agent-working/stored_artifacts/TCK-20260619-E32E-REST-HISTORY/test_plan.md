---
status: active
ticket_id: TCK-20260619-E32E-REST-HISTORY
artifact_type: test_plan
date: 2026-06-21
---

# Test Plan — TCK-20260619-E32E-REST-HISTORY

## Test File

`tests/api/test_campaign_history_api.py`

## Test Command

```bash
pytest tests/api/test_campaign_history_api.py -x -v
```

## Test Cases

### TC-1: test_campaign_history_endpoint_returns_narrative_ledger (AC-required)
**Flow:** Register a campaign with 3 NarrativeLedgerEntry records. Call
`get_campaign_history(campaign_id=...)`. Assert:
- response.campaign_id matches
- response.entry_count == 3
- response.entries is a list of 3 dicts with expected keys (episode, tick,
  event_type, subject_id, payload, significance)
- No raw domain model fields leak through (entries are dicts, not dataclass objects)

### TC-2: test_campaign_history_404_unknown_campaign
**Flow:** Call `get_campaign_history(campaign_id="nonexistent")`.
Assert: HTTPException with status_code=404.

### TC-3: test_campaign_history_filter_by_event_type
**Flow:** Register a campaign with 2 `entity_death` entries and 1
`quest_completed` entry. Call with `event_type="entity_death"`.
Assert: entry_count == 2, all entries have event_type == "entity_death".

### TC-4: test_campaign_history_filter_by_min_significance
**Flow:** Register a campaign with entries at significance 0.4, 0.5, 0.9.
Call with `min_significance=0.5`. Assert: entry_count == 2 (0.5 and 0.9).

### TC-5: test_campaign_history_filter_by_episode
**Flow:** Register a campaign with entries from episode 0 and episode 1.
Call with `episode=1`. Assert: only entries with episode==1 returned.

### TC-6: test_campaign_history_empty_ledger
**Flow:** Register a campaign with no entries. Call without filters.
Assert: entry_count == 0, entries == [].

### TC-7: test_campaign_history_combined_filters
**Flow:** Register a campaign with multiple entries spanning types, significance
levels, and episodes. Call with all three filters combined. Assert correct
subset returned.

## Coverage Requirements

- Normal flow (TC-1): covered
- Edge cases (TC-6 empty, TC-7 combined): covered
- Failure modes (TC-2 404): covered
- Regression-prone: presenter isolation (no raw domain models), filter logic
- Architecture test: verify entries are shaped dicts, not NarrativeLedgerEntry objects
