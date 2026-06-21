---
status: active
ticket_id: TCK-20260619-E51A-SIGNIFICANCE
artifact_type: test_plan
date: 2026-06-21
---

# Test Plan — TCK-20260619-E51A-SIGNIFICANCE

## Regression Surface (existing tests that must pass)

- `tests/unit/campaigns/test_narrative_ledger.py` — 35 tests covering NarrativeLedger and NarrativeLedgerEntry. Must remain fully green; this ticket does not touch those files.

## New Tests Required (per AC)

File: `tests/unit/chronicle/test_chronicle_compiler.py`

### TC-1: `test_significance_scoring_ranks_death_above_harvesting`
- Create a `NarrativeLedgerEntry` with `event_type="entity_death"` (no hero payload)
- Create a `NarrativeLedgerEntry` with `event_type="harvesting"` (unknown type → default 0.1)
- Assert `scorer.score(death_entry) > scorer.score(harvest_entry)`
- Assert death score == 0.5, harvest score == 0.1

### TC-2: `test_hero_death_scores_higher_than_commoner_death`
- Create death entry with `payload={"entity_role": "HERO"}`
- Create death entry with `payload={}` (commoner)
- Assert hero_death_score == 0.8 (0.5 + 0.3)
- Assert hero_death_score >= 0.8 (AC requirement)
- Assert hero_death_score > commoner_death_score

### TC-3: `test_is_chronicle_worthy_filters_below_threshold`
- Events at exactly 0.5 (entity_death) → worthy (>= threshold)
- Events below 0.5 (harvesting = 0.1) → not worthy
- Events above 0.5 (quest_completed = 0.7) → worthy

### TC-4: `test_known_event_types_score_correctly`
- Verify each key in BASE_SIGNIFICANCE maps to its defined value
- faction_destroyed → 0.9, quest_completed → 0.7, calamity → 0.85, etc.

### TC-5: `test_score_capped_at_1_0`
- If base + hero_bonus would exceed 1.0 (e.g. faction_destroyed=0.9 + hero=0.3 → 1.2), assert result == 1.0

### TC-6: `test_unknown_event_type_scores_default`
- `event_type="some_unknown_type"` → score == 0.1

## Scoped Pytest Commands

```bash
# Primary: new tests only
pytest tests/unit/chronicle/test_chronicle_compiler.py -x -v

# Regression: narrative ledger must stay green
pytest tests/unit/campaigns/test_narrative_ledger.py -x -v

# Combined scoped run
pytest tests/unit/chronicle/ tests/unit/campaigns/test_narrative_ledger.py -x -v
```

## Anti-Drift Test Guards

- Do not import engine or core modules in test file — only `from src.domains.chronicle.significance import EventSignificanceScorer, CHRONICLE_THRESHOLD, BASE_SIGNIFICANCE` and `from src.domains.campaigns.state import NarrativeLedgerEntry`.
- Tests must be deterministic: no random data, fixed entry values.
- Confirm `NarrativeLedgerEntry` is used correctly: `episode`, `tick`, `event_type`, `subject_id`, `payload`, `significance`, `entry_id` (7 fields).
