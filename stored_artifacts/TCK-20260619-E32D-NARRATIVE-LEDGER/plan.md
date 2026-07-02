---
status: active
ticket_id: TCK-20260619-E32D-NARRATIVE-LEDGER
artifact_type: plan
date: 2026-06-21
---

# Implementation Plan — TCK-20260619-E32D-NARRATIVE-LEDGER

## Overview

E32D introduces `NarrativeLedger`, the structured cross-episode event record.
The implementation has 4 steps:

1. Expand `NarrativeLedgerEntry` in `state.py` (full 6-field schema)
2. Create `NarrativeLedger` service in `narrative_ledger.py` (query + to_jsonl)
3. Wire extraction into `CampaignOrchestrator._advance_state()` using `recent_world_events`
4. Tests: update state tests + new unit tests + integration test

## Dependency Map

```
Step 1 (NarrativeLedgerEntry expansion)
    └─► Step 2 (NarrativeLedger — imports NarrativeLedgerEntry)
    └─► Step 3 (orchestrator extraction — creates NarrativeLedgerEntry objects)
    └─► Step 4a (update test_campaign_state.py)

Step 2 (NarrativeLedger service)
    └─► Step 4b (new unit tests for NarrativeLedger)

Step 3 (orchestrator wiring)
    └─► Step 4c (integration test — real kernel events)
```

## Step 1 — Expand NarrativeLedgerEntry in state.py

**File:** `src/domains/campaigns/state.py`

Replace stub:
```python
@dataclass(frozen=True)
class NarrativeLedgerEntry:
    entry_id: str
    tick: int
    episode_index: int
```

With full schema (field name `episode` per ticket scope, not `episode_index`):
```python
@dataclass(frozen=True)
class NarrativeLedgerEntry:
    episode: int          # episode in which this event occurred
    tick: int             # simulation tick at which this event was recorded
    event_type: str       # "quest_completed"|"entity_death"|"faction_shift"|"calamity"
    subject_id: str       # entity/faction/node id
    payload: dict         # event-specific data (may be empty)
    significance: float   # 0.0-1.0 relevance weight
    entry_id: str = ""    # deterministic dedup key (optional, defaults to "")
```

Update `to_dict()` and `from_dict()` to serialize/deserialize all 7 fields.

**Scope guards:**
- Do NOT add `episode_index` — the field is renamed `episode`.
- Do NOT break `CampaignState.from_dict()` — it reads from `narrative_ledger` list.
- The `entry_id` default `""` allows from_dict to handle legacy stub records.

## Step 2 — Create NarrativeLedger service

**File:** `src/domains/campaigns/narrative_ledger.py` (new)

```python
class NarrativeLedger:
    def __init__(self, entries: list[NarrativeLedgerEntry] | None = None):
        self._entries = list(entries or [])

    def record(self, entry: NarrativeLedgerEntry) -> None:
        self._entries.append(entry)

    def query(
        self,
        event_type: str | None = None,
        min_significance: float = 0.0,
        episode: int | None = None,
    ) -> list[NarrativeLedgerEntry]:
        result = self._entries
        if event_type is not None:
            result = [e for e in result if e.event_type == event_type]
        if min_significance > 0.0:
            result = [e for e in result if e.significance >= min_significance]
        if episode is not None:
            result = [e for e in result if e.episode == episode]
        return list(result)

    def to_jsonl(self, path: str) -> None:
        import json
        with open(path, "a", encoding="utf-8") as f:
            for entry in self._entries:
                f.write(json.dumps(entry.to_dict()) + "\n")
```

**Import:** only `from src.domains.campaigns.state import NarrativeLedgerEntry`.
No engine imports. No circular imports.

## Step 3 — Wire extraction into CampaignOrchestrator._advance_state()

**File:** `src/domains/campaigns/orchestrator.py`

Add import at top:
```python
from src.domains.campaigns.state import (
    CampaignState, EntityCarryForward, EpisodeSummary,
    FactionCarryForward, NarrativeLedgerEntry,
)
```

Add `_SIGNIFICANCE_MAP` module-level dict:
```python
_SIGNIFICANCE_MAP: Dict[str, tuple[str, float]] = {
    "ENTITY_DEATH":      ("entity_death",   0.5),
    "QUEST_COMPLETED":   ("quest_completed", 0.7),
    "CAMP_CLEARED":      ("faction_shift",   0.9),
    "CAMP_RAID":         ("faction_shift",   0.6),
    "PARTY_ABANDONED":   ("entity_death",    0.4),
    "QUEST_FAILED":      ("quest_completed", 0.3),
}
```

Add `_extract_narrative_entries()` method:
```python
def _extract_narrative_entries(
    self,
    final_state: "AuthoritativeState",
    episode_index: int,
) -> list[NarrativeLedgerEntry]:
    entries = []
    for world_event in getattr(final_state, "recent_world_events", []):
        key = world_event.category.value if hasattr(world_event.category, "value") else str(world_event.category)
        if key not in _SIGNIFICANCE_MAP:
            continue
        event_type, significance = _SIGNIFICANCE_MAP[key]
        subject_id = world_event.subject or ""
        entry_id = f"{episode_index}:{world_event.tick}:{event_type}:{subject_id}"
        entries.append(NarrativeLedgerEntry(
            episode=episode_index,
            tick=world_event.tick,
            event_type=event_type,
            subject_id=subject_id,
            payload=dict(world_event.payload),
            significance=significance,
            entry_id=entry_id,
        ))
    return entries
```

Update `_advance_state()` to call it and extend `narrative_ledger`:
```python
def _advance_state(self, final_state, summary):
    entity_cfs = self._extract_entity_carry_forwards(final_state)
    faction_cfs = self._extract_faction_carry_forwards(final_state)
    narrative_entries = self._extract_narrative_entries(final_state, summary.episode_index)

    self._state.persistent_entities.update(entity_cfs)
    self._state.persistent_factions.update(faction_cfs)
    self._state.episode_history.append(summary)
    self._state.narrative_ledger.extend(narrative_entries)
    self._state.episode_index += 1
```

**Scope guards:**
- Do NOT import `NarrativeLedger` service in orchestrator — the service wraps
  the list for querying; orchestrator works directly with the list.
- Do NOT add `WorldEventCategory` import — use string `.value` for robustness.
- Do NOT change entity/faction extraction logic.

## Step 4 — Tests

### 4a: Update test_campaign_state.py
- Update `_make_campaign_state()` NarrativeLedgerEntry to use full 6-field schema
- Update `test_narrative_ledger_entry_round_trip()` to test all 7 fields
- Remove reference to `episode_index` field (renamed to `episode`)

### 4b: Create tests/unit/campaigns/test_narrative_ledger.py
- TC-D1 through TC-D15 (see test_plan.md)

### 4c: Extend test_campaign_runtime.py
- Add `test_narrative_ledger_populated_with_cross_episode_events` (TC-D16)

## Files Changed

| Step | File | Change |
|---|---|---|
| 1 | `src/domains/campaigns/state.py` | Expand NarrativeLedgerEntry to 7 fields |
| 2 | `src/domains/campaigns/narrative_ledger.py` | New — NarrativeLedger service |
| 3 | `src/domains/campaigns/orchestrator.py` | Add _extract_narrative_entries + wire _advance_state |
| 4a | `tests/unit/campaigns/test_campaign_state.py` | Update NarrativeLedgerEntry tests |
| 4b | `tests/unit/campaigns/test_narrative_ledger.py` | New — unit tests |
| 4c | `tests/integration/scenarios/test_campaign_runtime.py` | Add E32D integration test |

## Acceptance Criteria Mapping

| AC | Step | Test |
|---|---|---|
| CampaignState.narrative_ledger has ≥10 entries after 2 episodes | 3, 4c | TC-D16 (best-effort with real kernel; guaranteed by TC-D14 unit) |
| query(event_type="entity_death") returns only death entries | 2, 4b | TC-D2 |
| test_narrative_ledger_populated_with_cross_episode_events passes | 3, 4c | TC-D16 |
| NarrativeLedger serializes to JSONL | 2, 4b | TC-D7, TC-D8 |

## Deviations

None yet. Update if implementation diverges.
