---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E51B-GROUPER
artifact_type: investigation
tags: [chronicle, grouper, event-hierarchy]
---

# Investigation — TCK-20260619-E51B-GROUPER

## Key Findings

### Existing Infrastructure
- `NarrativeLedgerEntry` (frozen dataclass) in `src/domains/campaigns/state.py`:
  fields: `episode: int`, `tick: int`, `event_type: str`, `subject_id: str`,
  `payload: dict`, `significance: float`, `entry_id: str`
- `EventSignificanceScorer` (stateless) in `src/domains/chronicle/significance.py`:
  `score()` and `is_chronicle_worthy()` already handle per-entry filtering.
- Test file already exists at `tests/unit/chronicle/test_chronicle_compiler.py` (6 tests passing).

### Grouping Algorithm Design
- **Incident grouping**: within the same episode, events whose ticks are within
  `INCIDENT_TICK_WINDOW=50` of each other are coalesced into one Incident.
  Algorithm: iterate sorted entries; start a new incident when episode changes or
  gap > INCIDENT_TICK_WINDOW.
- **Episode grouping**: one Episode per unique episode index, collecting all incidents
  belonging to it. Significance = max incident significance.
- **Era grouping**: episodes are accumulated into eras; a new era boundary is drawn
  whenever the accumulated episode count reaches `ERA_EPISODE_MIN=3`. Remaining
  episodes form the last (possibly smaller) era.

### Dataclass Constraints
- `frozen=True` on Incident requires `entries` to be a `tuple` (not list).
- `ChronicleHierarchy` stores `events` as list (mutable field — not frozen).
- Episode and Era are new dataclasses needed alongside Incident.

### No New Dependencies
All imports are intra-project. No engine imports needed.
