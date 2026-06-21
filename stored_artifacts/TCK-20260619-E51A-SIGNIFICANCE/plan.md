---
status: active
ticket_id: TCK-20260619-E51A-SIGNIFICANCE
artifact_type: plan
date: 2026-06-21
---

# Plan — TCK-20260619-E51A-SIGNIFICANCE

## Ordered Steps

### Step 1 — Create `src/domains/chronicle/` package
- Create `src/domains/chronicle/__init__.py` (empty, marks package)
- No dependencies on other steps

### Step 2 — Implement `src/domains/chronicle/significance.py`
- Exactly as specified in ticket scope
- `BASE_SIGNIFICANCE` dict with 8 event types
- `CHRONICLE_THRESHOLD = 0.5`
- `EventSignificanceScorer` with two static methods: `score()` and `is_chronicle_worthy()`
- Imports only: `from src.domains.campaigns.state import NarrativeLedgerEntry`
- Depends on: Step 1

### Step 3 — Create `tests/unit/chronicle/` package
- Create `tests/unit/chronicle/__init__.py` (empty)
- No other dependencies

### Step 4 — Implement `tests/unit/chronicle/test_chronicle_compiler.py`
- TC-1: `test_significance_scoring_ranks_death_above_harvesting`
- TC-2: `test_hero_death_scores_higher_than_commoner_death`
- TC-3: `test_is_chronicle_worthy_filters_below_threshold`
- TC-4: `test_known_event_types_score_correctly`
- TC-5: `test_score_capped_at_1_0`
- TC-6: `test_unknown_event_type_scores_default`
- Depends on: Steps 2 and 3

## Files to Change Per Step

| Step | Files |
|------|-------|
| 1 | `src/domains/chronicle/__init__.py` (new) |
| 2 | `src/domains/chronicle/significance.py` (new) |
| 3 | `tests/unit/chronicle/__init__.py` (new) |
| 4 | `tests/unit/chronicle/test_chronicle_compiler.py` (new) |

## Scope Guards (What NOT to Touch)

- `src/domains/campaigns/state.py` — read only; do not modify NarrativeLedgerEntry
- `src/domains/campaigns/narrative_ledger.py` — no changes
- Any existing test files — no modifications
- No changes to docs/ (chronicle_contract.md is an E51D/E51E deliverable, not E51A)

## Dependency Map

Step 1 → Step 2 (package must exist before module)
Step 3 → Step 4 (test package must exist before test file)
Steps 1+3 → Step 4 (both src and test packages needed to run tests)

## Acceptance Criteria Mapped to Steps

| AC | Step |
|----|------|
| `test_significance_scoring_ranks_death_above_harvesting` passes | Step 4 (TC-1) |
| `test_hero_death_scores_higher_than_commoner_death` passes (≥ 0.8) | Step 4 (TC-2) |
| Events with default score < 0.5 filtered by `is_chronicle_worthy` | Step 4 (TC-3) |

## Deviations

_None at time of writing._
