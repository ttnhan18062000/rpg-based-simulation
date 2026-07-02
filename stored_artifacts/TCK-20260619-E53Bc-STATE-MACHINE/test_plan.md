---
ticket_id: TCK-20260619-E53Bc-STATE-MACHINE
phase: test_plan
date: 2026-06-22
---

# Test Plan — TCK-20260619-E53Bc-STATE-MACHINE

## Tests (appended to test_diplomacy.py)

1. `test_diplomatic_state_transitions_valid` — covers NEUTRAL→TENSE, TENSE→HOSTILE, HOSTILE→WAR, WAR→NEUTRAL, single-step
2. `test_alliance_reduces_shared_territory_threat` — ALLIED suppresses TENSE→HOSTILE on shared territory
3. `test_no_transitions_when_below_thresholds` — no updates when all conditions false
4. `test_tense_to_hostile_from_shared_territory` — shared territory fires at low tension
5. `test_war_to_neutral_exhaustion` — WAR+both_low_ms → NEUTRAL

## Run
```bash
pytest tests/unit/faction/test_diplomacy.py -x -v
```
