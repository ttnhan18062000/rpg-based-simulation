---
status: open
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E32D-NARRATIVE-LEDGER
phase: open
date: 2026-06-20
tags: [campaign-runtime, narrative-ledger, observability, phase-3]
---

# TCK-20260619-E32D-NARRATIVE-LEDGER

## Title
Epic 3.2D · NarrativeLedger

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The most critical E32 deliverable — it gates Epic 4.3 (Social Memory) and 5.1 (Chronicle). `NarrativeLedger` is a queryable structured record of significant campaign events (quest completions, entity deaths, faction shifts, calamities) by tick + episode.

**Requires:** TCK-20260619-E32C-ORCHESTRATOR

## Scope

### `NarrativeLedgerEntry` — add to `src/domains/campaigns/state.py`

```python
@dataclass(frozen=True)
class NarrativeLedgerEntry:
    episode: int
    tick: int
    event_type: str      # "quest_completed" | "entity_death" | "faction_destroyed" | "calamity"
    subject_id: str      # entity/faction/node id
    payload: dict        # event-specific data
    significance: float  # 0.0-1.0 (quest complete=0.7, entity death=0.5, faction shift=0.9)
```

### `NarrativeLedger` service — `src/domains/campaigns/narrative_ledger.py`

```python
class NarrativeLedger:
    def __init__(self, entries: list[NarrativeLedgerEntry] | None = None):
        self._entries = list(entries or [])

    def record(self, entry: NarrativeLedgerEntry) -> None: ...

    def query(
        self,
        event_type: str | None = None,
        min_significance: float = 0.0,
        episode: int | None = None
    ) -> list[NarrativeLedgerEntry]: ...

    def to_jsonl(self, path: str) -> None: ...
```

### Wire recording into `CampaignOrchestrator._advance_state()`

After each episode: scan `simulation_events.jsonl` for significant events → convert to `NarrativeLedgerEntry` → append to `CampaignState.narrative_ledger`.

## Acceptance Criteria
- After 2 episodes: `CampaignState.narrative_ledger` has ≥10 entries spanning both episodes
- `NarrativeLedger.query(event_type="entity_death")` returns only death entries
- `test_narrative_ledger_populated_with_cross_episode_events` passes
- NarrativeLedger serializes to JSONL

## Related Tickets
- TCK-20260619-E32-CAMPAIGN-RUNTIME (parent epic)
- TCK-20260619-E32C-ORCHESTRATOR (required)
- TCK-20260619-E32E-REST-HISTORY (blocked on this)
- TCK-20260619-E43-SOCIAL-MEMORY (unlocked by NarrativeLedger)
- TCK-20260619-E51-CHRONICLE (unlocked by NarrativeLedger)

## Related Code Areas
- `src/domains/campaigns/narrative_ledger.py` (new)
- `src/domains/campaigns/state.py` (NarrativeLedgerEntry type — add)
- `src/domains/campaigns/orchestrator.py` (wire recording in _advance_state)

## Test Summary
```bash
pytest tests/integration/scenarios/test_campaign_runtime.py::test_narrative_ledger_populated_with_cross_episode_events -x -v -m slow
```
## Files Changed
_To be filled on completion._
## Completion Summary
_To be filled on completion._
