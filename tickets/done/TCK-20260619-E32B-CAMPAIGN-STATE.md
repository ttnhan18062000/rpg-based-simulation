---
status: done
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E32B-CAMPAIGN-STATE
phase: done
date: 2026-06-20
tags: [campaign-runtime, campaign-state, persistent-state, phase-3]
---

# TCK-20260619-E32B-CAMPAIGN-STATE

## Title
Epic 3.2B · CampaignState Data Model

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
No `CampaignState` model exists for multi-episode persistence. This ticket introduces the data model that `CampaignOrchestrator` (E32C) will read/write between episodes.

**Requires:** TCK-20260619-E32A-RENAME-RUNNER

## Scope

New file `src/domains/campaigns/state.py`:

```python
@dataclass
class CampaignState:
    campaign_id: str
    episode_index: int                              # current episode number
    episode_history: list[EpisodeSummary]           # completed episodes
    persistent_entities: dict[int, EntityCarryForward]  # id → carried state
    persistent_factions: dict[str, FactionCarryForward]  # faction_id → carried state
    world_timeline: list[WorldTimelineEntry]        # calamities/shifts by tick+episode
    narrative_ledger: list[NarrativeLedgerEntry]    # significant events (see E32D)

@dataclass(frozen=True)
class EntityCarryForward:
    entity_id: int
    level: int
    xp: int
    equipment: dict          # item_id → item state
    reputation: dict         # faction_id → rep score
    alive: bool              # dead entities carried but marked dead

@dataclass(frozen=True)
class FactionCarryForward:
    faction_id: str
    alive: bool              # destroyed factions not spawned in next episode
    tension: float
```

All dataclasses must serialize/deserialize to JSON (for campaign checkpoint in E32C).

## Acceptance Criteria
- `CampaignState(...)` constructs and serializes to JSON
- `EntityCarryForward` includes all carry-forward fields
- Dead entities (`alive=False`) and destroyed factions (`alive=False`) are representable

## Related Tickets
- TCK-20260619-E32-CAMPAIGN-RUNTIME (parent epic)
- TCK-20260619-E32A-RENAME-RUNNER (required)
- TCK-20260619-E32C-ORCHESTRATOR (blocked on this)

## Related Docs
- `docs/core/state.md` (immutability law — entity state carry-forward must respect it)

## Related Code Areas
- `src/domains/campaigns/state.py` (new)
- `src/domains/campaigns/schema.py:L43` (CampaignEvent — reference for existing field patterns)

## Implementation Notes

Created `src/domains/campaigns/state.py` as a pure data model (no engine imports).
Five frozen sub-record dataclasses: `EntityCarryForward`, `FactionCarryForward`,
`EpisodeSummary`, `WorldTimelineEntry`, `NarrativeLedgerEntry`. One mutable
`CampaignState` container. All types implement `to_dict()` / `from_dict()` with
sorted keys for determinism. Entity keys in `persistent_entities` are stringified
in `to_dict()` and restored with `int()` in `from_dict()` for JSON safety.
OQ-1 resolved: `reputation: float` (maps to `public_reputation`). OQ-2 resolved:
equipment uses full composite form `{"slots": {...}, "durability": {...}}`.
OQ-3 resolved: `faction_id: str` with E32C owning the int->str mapping.
17 unit tests added in `tests/unit/campaigns/test_campaign_state.py`; all pass.
No existing tests broken (40/40 pass in `tests/unit/campaigns/`).

## Test Summary
```bash
python3 -c "from src.domains.campaigns.state import CampaignState; print('OK')"
pytest tests/unit/campaigns/test_campaign_state.py -x -v  # 17 tests, all pass
pytest tests/unit/campaigns/ -x -v  # 40 tests, all pass (regression clean)
```

## Files Changed
- `src/domains/campaigns/state.py` (new)
- `tests/unit/campaigns/test_campaign_state.py` (new)

## Completion Summary
Pure data model for multi-episode campaign persistence introduced. All 6 types
(`CampaignState`, `EntityCarryForward`, `FactionCarryForward`, `EpisodeSummary`,
`WorldTimelineEntry`, `NarrativeLedgerEntry`) implement `to_dict()`/`from_dict()`.
17 unit tests pass; 40 pre-existing campaign tests unbroken. No engine imports.
Ready for E32C (CampaignOrchestrator).
