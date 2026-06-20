---
status: open
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E51B-GROUPER
phase: open
date: 2026-06-20
tags: [chronicle, grouper, event-hierarchy, incident-episode-era, phase-5]
---

# TCK-20260619-E51B-GROUPER

## Title
Epic 5.1B · Event → Incident → Episode → Era Grouper

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Core grouping algorithm that transforms flat `NarrativeLedger` entries into the four-level hierarchy: events → incidents → episodes → eras.

**Requires:** TCK-20260619-E51A-SIGNIFICANCE

## Scope

New file `src/domains/chronicle/grouper.py`:

```python
class ChronicleGrouper:
    INCIDENT_TICK_WINDOW = 50     # events within 50 ticks → same incident
    ERA_EPISODE_MIN = 3           # ≥3 episodes → era boundary

    def group(self, entries: list[NarrativeLedgerEntry]) -> ChronicleHierarchy:
        """Filter → sort → group incidents → group episodes → group eras."""
        worthy = [e for e in entries if EventSignificanceScorer.is_chronicle_worthy(e)]
        worthy.sort(key=lambda e: (e.episode, e.tick))
        incidents = self._group_incidents(worthy)
        episodes = self._group_episodes(worthy, incidents)
        eras = self._group_eras(episodes)
        return ChronicleHierarchy(events=worthy, incidents=incidents, episodes=episodes, eras=eras)

    def _group_incidents(self, entries: list) -> list[Incident]:
        """Entries within INCIDENT_TICK_WINDOW of same-episode neighbour → same incident."""
        ...
```

Also define:
```python
@dataclass(frozen=True)
class Incident:
    id: str
    episode: int
    tick_range: tuple[int, int]
    entries: tuple[NarrativeLedgerEntry, ...]
    significance: float  # max significance of constituent events

@dataclass(frozen=True)
class ChronicleHierarchy:
    events: list[NarrativeLedgerEntry]
    incidents: list[Incident]
    episodes: list[Episode]
    eras: list[Era]
```

## Acceptance Criteria
- `test_event_grouping_produces_incident_clusters` passes (≥2 incidents from 15 events)
- `test_chronicle_hierarchy_contains_all_four_levels` passes

## Related Tickets
- TCK-20260619-E51-CHRONICLE (parent epic)
- TCK-20260619-E51A-SIGNIFICANCE (required)
- TCK-20260619-E51C-NAMING (blocked on this)

## Related Code Areas
- `src/domains/chronicle/grouper.py` (new)

## Test Summary
```bash
pytest tests/unit/chronicle/test_chronicle_compiler.py -x -v
```
## Files Changed
_To be filled on completion._
## Completion Summary
_To be filled on completion._
