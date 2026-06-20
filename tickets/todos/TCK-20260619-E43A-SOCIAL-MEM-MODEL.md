---
status: open
layer: social
authority: P1
audience: agent
ticket_id: TCK-20260619-E43A-SOCIAL-MEM-MODEL
phase: open
date: 2026-06-20
tags: [social-memory, datamodel, cross-episode, phase-4]
---

# TCK-20260619-E43A-SOCIAL-MEM-MODEL

## Title
Epic 4.3A · SocialMemoryRecord Model

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
No cross-episode social memory model exists. This ticket defines `SocialMemoryRecord` and `InteractionRecord` as the data layer that E43B's exporter/importer will write and read.

**Blocks:** All other E43 child tickets

## Scope

New file `src/domains/campaigns/social_memory.py`:

```python
@dataclass(frozen=True, slots=True)
class InteractionRecord:
    episode: int
    tick: int
    kind: str   # "helped" | "betrayed" | "traded" | "fought_alongside" | "conflict"
    other_entity_id: Optional[int]
    faction_id: Optional[str]
    magnitude: float  # 0.0–1.0

@dataclass(frozen=True, slots=True)
class SocialMemoryRecord:
    entity_id: int
    interaction_history: Tuple[InteractionRecord, ...] = ()
    relationship_scores: Dict[int, float] = field(default_factory=dict)
    faction_reputation: Dict[str, float] = field(default_factory=dict)
    last_betrayal_tick: Optional[int] = None
    last_cooperation_tick: Optional[int] = None
```

Must serialize/deserialize to JSON (for `CampaignState` persistence).

## Acceptance Criteria
- `SocialMemoryRecord` constructs and round-trips through JSON
- `test_social_memory_record_serializes_to_campaign_state` passes

## Related Tickets
- TCK-20260619-E43-SOCIAL-MEMORY (parent epic)
- TCK-20260619-E43B-EXPORT-IMPORT (blocked on this)

## Related Code Areas
- `src/domains/campaigns/social_memory.py` (new)

## Test Summary
```bash
python3 -c "from src.domains.campaigns.social_memory import SocialMemoryRecord; print('OK')"
pytest tests/unit/social/test_social_memory.py::test_social_memory_record_serializes_to_campaign_state -x -v
```
## Files Changed
_To be filled on completion._
## Completion Summary
_To be filled on completion._
