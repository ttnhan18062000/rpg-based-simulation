---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E51A-SIGNIFICANCE
phase: done
date: 2026-06-20
tags: [chronicle, significance-scoring, event-filtering, phase-5]
---

# TCK-20260619-E51A-SIGNIFICANCE

## Title
Epic 5.1A · Event Significance Scorer

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The Chronicle Compiler needs a significance scoring model to filter raw events before grouping. Events below threshold are omitted from the chronicle.

**Blocks:** All other E51 child tickets

## Scope

New file `src/domains/chronicle/significance.py`:

```python
BASE_SIGNIFICANCE = {
    "entity_death": 0.5,           # HERO death → 0.8 via hero_bonus
    "faction_destroyed": 0.9,
    "quest_completed": 0.7,
    "calamity": 0.85,
    "LEGENDARY_ARRIVAL": 0.75,
    "KNOWN_TRAITOR_SPOTTED": 0.6,
    "betrayal_desertion": 0.7,
    "INFLATION_SPIRAL": 0.5,
}
CHRONICLE_THRESHOLD = 0.5

class EventSignificanceScorer:
    @staticmethod
    def score(entry: NarrativeLedgerEntry) -> float:
        base = BASE_SIGNIFICANCE.get(entry.event_type, 0.1)
        hero_bonus = 0.3 if entry.payload.get("entity_role") == "HERO" else 0.0
        return min(1.0, base + hero_bonus)

    @staticmethod
    def is_chronicle_worthy(entry: NarrativeLedgerEntry) -> bool:
        return EventSignificanceScorer.score(entry) >= CHRONICLE_THRESHOLD
```

## Acceptance Criteria
- `test_significance_scoring_ranks_death_above_harvesting` passes
- `test_hero_death_scores_higher_than_commoner_death` passes (≥ 0.8)
- Events with default score < 0.5 filtered by `is_chronicle_worthy`

## Related Tickets
- TCK-20260619-E51-CHRONICLE (parent epic)
- TCK-20260619-E51B-GROUPER (blocked on this)

## Related Code Areas
- `src/domains/chronicle/significance.py` (new)
- `src/domains/campaigns/state.py` (NarrativeLedgerEntry — input type)

## Test Summary
```bash
pytest tests/unit/chronicle/test_chronicle_compiler.py::test_significance_scoring_ranks_death_above_harvesting -x -v
pytest tests/unit/chronicle/test_chronicle_compiler.py::test_hero_death_scores_higher_than_commoner_death -x -v
```
## Implementation Notes
Created `src/domains/chronicle/` package with `__init__.py` and `significance.py`. `EventSignificanceScorer` is a stateless classifier with two static methods: `score()` returns a float in [0.0, 1.0] derived from BASE_SIGNIFICANCE dict + 0.3 hero_bonus (capped at 1.0); `is_chronicle_worthy()` returns True when score >= CHRONICLE_THRESHOLD (0.5). Created `tests/unit/chronicle/test_chronicle_compiler.py` with 6 test cases covering all ACs plus edge cases (cap, default, all known types).

## Files Changed
- `src/domains/chronicle/__init__.py` (new)
- `src/domains/chronicle/significance.py` (new)
- `tests/unit/chronicle/__init__.py` (new)
- `tests/unit/chronicle/test_chronicle_compiler.py` (new)

## Completion Summary
Implemented `src/domains/chronicle/significance.py` — new `src/domains/chronicle/` package containing `EventSignificanceScorer` with static `score()` and `is_chronicle_worthy()` methods. `BASE_SIGNIFICANCE` dict maps 8 event types; unknown types default to 0.1. Hero bonus (+0.3) applies when `payload["entity_role"]=="HERO"`, capped at 1.0. `CHRONICLE_THRESHOLD=0.5`. Added 6 unit tests in `tests/unit/chronicle/test_chronicle_compiler.py` covering all ACs plus cap, default, and all-known-types paths. 23/23 tests pass. Parity entry SOC-CHRON-001 added to `docs/parity_ledger/social_narrative.yaml`. Unblocks E51B–E51E.
