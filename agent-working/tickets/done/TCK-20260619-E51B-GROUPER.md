---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E51B-GROUPER
phase: done
date: 2026-06-20
tags: [chronicle, grouper, event-hierarchy, incident-episode-era, phase-5]
---

# TCK-20260619-E51B-GROUPER

## Title
Epic 5.1B · Event → Incident → Episode → Era Grouper

## Status
DONE

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

## Out of Scope
- Naming/rendering of hierarchy (E51C, E51D)
- REST API exposure (E51E)
- NarrativeLedger changes

## Acceptance Criteria
- `test_event_grouping_produces_incident_clusters` passes (≥2 incidents from 15 events) ✓
- `test_chronicle_hierarchy_contains_all_four_levels` passes ✓

## Related Tickets
- TCK-20260619-E51-CHRONICLE (parent epic)
- TCK-20260619-E51A-SIGNIFICANCE (required)
- TCK-20260619-E51C-NAMING (blocked on this)

## Related Docs
- `docs/parity_ledger/social_narrative.yaml` (SOC-CHRON-002 added)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E51B-GROUPER/`

## Related Code Areas
- `src/domains/chronicle/grouper.py` (new)
- `tests/unit/chronicle/test_chronicle_compiler.py` (extended with TC-7 through TC-12)

## Assumptions / Open Questions
None.

## Implementation Notes
Created `src/domains/chronicle/grouper.py` with four frozen dataclasses (`Incident`,
`Episode`, `Era`, `ChronicleHierarchy`) and `ChronicleGrouper` class.

Incident grouping: iterates sorted (episode, tick) entries; starts a new incident when
the episode changes or the tick gap > `INCIDENT_TICK_WINDOW=50`. `_make_incident()`
builds a frozen `Incident` with `id="ep{ep}:t{start}-{end}"` and `significance=max(scores)`.

Episode grouping: `_group_episodes()` collects incidents by episode index via an ordered
dict; one `Episode` per unique episode index.

Era grouping: `_group_eras()` batches episodes in `ERA_EPISODE_MIN=3` chunks; the final
batch may be smaller.

All fields on `Incident`, `Episode`, `Era`, `ChronicleHierarchy` are `frozen=True`;
`entries`/`incidents`/`episodes` stored as tuples to satisfy hashability constraints.

## Test Summary
12 tests total (6 E51A preserved + 6 new E51B), all passing in 0.06s.

```bash
pytest tests/unit/chronicle/test_chronicle_compiler.py -x -v
# 12 passed in 0.06s
```

New tests:
- TC-7 `test_event_grouping_produces_incident_clusters` (AC-1)
- TC-8 `test_chronicle_hierarchy_contains_all_four_levels` (AC-2)
- TC-9 `test_incident_groups_by_tick_window`
- TC-10 `test_below_threshold_events_excluded`
- TC-11 `test_era_boundary_every_n_episodes`
- TC-12 `test_empty_input_returns_empty_hierarchy`

## Files Changed
- `src/domains/chronicle/grouper.py` (new)
- `tests/unit/chronicle/test_chronicle_compiler.py` (extended — TC-7 through TC-12 added)
- `docs/parity_ledger/social_narrative.yaml` (SOC-CHRON-002 added)

## Completion Summary
Implemented `src/domains/chronicle/grouper.py` — new `ChronicleGrouper` class producing
`ChronicleHierarchy` (events/incidents/episodes/eras) from flat `NarrativeLedgerEntry`
lists. `INCIDENT_TICK_WINDOW=50` controls same-episode tick clustering; `ERA_EPISODE_MIN=3`
controls era batching. All four hierarchy levels are frozen dataclasses. 12/12 tests pass.
Parity entry SOC-CHRON-002 added. Unblocks E51C (ChronicleNamer).
