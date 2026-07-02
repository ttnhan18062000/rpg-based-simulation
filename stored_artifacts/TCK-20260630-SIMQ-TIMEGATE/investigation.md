# Investigation — TCK-20260630-SIMQ-TIMEGATE

## Time-Gate Rules Per Pillar (from config/simulation_quality/detection_params.yaml)

| Key | Tick Value | Pillar | Scorer File | Rule Summary |
|-----|-----------|--------|-------------|--------------|
| `zero_harvest_after_tick` | 100 | ECONOMY | economy.py | Fires on `resource_harvested` when tick > 100 and no `harvest_active` in window |
| `zero_crafting_after_tick` | 200 | ECONOMY | economy.py | Fires on `item_crafted` when tick > 200 and no `crafting_active` in window |
| `zero_trade_after_tick` | 300 | ECONOMY | economy.py | Fires on `trade_executed`/`shop_transaction` when tick > 300 and no `trade_active` in window |
| `zero_quests_after_tick` | 200 | NARRATIVE | narrative.py | Fires on `quest_started` when tick > 200 and no `quest_active` in window |
| `zero_chronicle_after_tick` | 300 | NARRATIVE | narrative.py | Fires on `chronicle_entry_created` when tick > 300 and no `narrative_event` in window |
| `progression_frozen_by_tick` | 200 | PROGRESSION | progression.py | Fires on `level_up` when tick > 200 and `level_milestone == 0` in window (tag: `all_level_1`) |
| `xp_plateau_by_tick` | 50 | PROGRESSION | progression.py | Fires on `progression_plateau_detected` (type=`xp_rate_zero`) when tick > 50 (tag: `xp_plateau`) |
| `stasis_gate_ticks` | 5 | AGENCY | agency.py | `defer_idle` count > 5 adds `stasis_N` tag + per-tick penalty; population stasis fires when tick > 5 AND no `action_taken` |

### Additional non-tick-gated penalties that fired via event payload:
- `progression_frozen` (weight: -10.0): fires on `progression_plateau_detected` with `type=xp_freeze` — no tick check in scorer, detection is engine-side
- `all_level_1` (weight: -30.0): fires via the `progression_frozen_by_tick` gate above
- `population_stasis` (weight: -25.0): fires on first `defer_with_reason` where tick > stasis_gate AND action_taken==0

## Current Test Coverage Assessment

### ECONOMY (economy.py / test_economy_scorer.py)
- `test_zero_harvest_fires_after_gate` ✓ — tests tick > 100 fires zero_harvest tag
- `test_zero_harvest_not_before_gate` ✓ — tests tick=5 does NOT fire zero_harvest tag
- `test_zero_crafting_fires_after_gate` ✓ — tests tick > 200
- `test_zero_trade_fires_after_gate` ✓ — tests tick > 300
- Missing: "not before" tests for crafting and trade gates
- Missing: "fires once" tests for harvest/crafting/trade gates

### PROGRESSION (progression.py / test_progression_scorer.py)
- `test_all_level_1_fires_after_gate` ✓ — tests tick > progression_frozen_by_tick (200)
- `test_xp_rate_zero_after_gate` ✓ — tests tick > xp_plateau_by_tick (50)
- `test_xp_freeze` ✓ — tests payload type=xp_freeze triggers progression_frozen
- Missing: "not before" test for all_level_1 gate
- Missing: "fires once" test for all_level_1

### NARRATIVE (narrative.py / test_narrative_scorer.py)
- `test_zero_quest_starts_after_gate` ✓ — tests tick > 200
- `test_zero_quest_dormant_fires_once` ✓ — fires once
- `test_narrative_silent_after_gate` ✓ — tests tick > 300
- `test_narrative_silent_fires_once` ✓ — fires once
- Missing: "not before" tests for both gates

### AGENCY (agency.py / test_agency_scorer.py)
- `test_stasis_fires_after_gate` ✓ — stasis_N accumulates with extra ticks
- `test_stasis_no_fire_before_gate` ✓ — stasis_N absent before gate
- `test_population_stasis_fires_when_no_actions` ✓
- `test_population_stasis_fires_only_once` ✓

## Test Gap

The ticket acceptance criterion requires `pytest tests/simulation_quality/ -k timegate` to pass.
None of the existing tests are in a file named `test_timegate_penalties.py` or have functions
named with `timegate` in their ID. The gap is a **dedicated consolidated test file** that:
1. Is named `test_timegate_penalties.py` (so `-k timegate` finds all tests in it via path match)
2. Adds "not before" coverage for gates that currently lack it (crafting, trade, narrative)
3. Adds "fires once" coverage for economy gates

## Calibration Data — Existing vs Needed

| World | Seed | Current | Needed |
|-------|------|---------|--------|
| sandbox_world | 42 | 200t | **1000t** |
| dungeon_crawl | 42 | 200t | **1000t** |
| simq_routing_test | 42 | 500t | 500t — ALREADY EXISTS, skip |

## Summary

- All scorer time-gate logic is correctly implemented and partially tested in existing scorer unit tests
- The primary gap is the consolidated `test_timegate_penalties.py` file for `-k timegate` discovery
- 1000-tick calibrations needed for sandbox_world and dungeon_crawl to verify economy grade degrades (zero_harvest fires at tick 100, ECONOMY grade ≤ C by tick 300)
