---
ticket_id: TCK-20260619-E12A-BALANCE-MEASURE
phase: plan
date: 2026-06-20
---

# Plan: Balance Measurement Pass

## Implementation Steps

1. Write `tools/balance_measure.py`
   - Load urban_political (WorldRepository + WorldCompiler, seed=42)
   - Patch AdventureRouteScorer.score() → count routes_total / routes_with_blockers
   - Patch Economy to count HARVEST_RESOURCE / REQUEST_CRAFT actions
   - Run 1000 ticks; per-100-tick window: gold, quest counts, entity HP, action counts
   - Print JSON report to stdout

2. Run the script and capture output

3. Fill D04_balance_tuning.md blocked sections with measured numbers

4. Document non-hunger urgency range in D04 and in docs/mechanics/04_strategic_cognition.md

## Metric Definitions

- **harvesting_rate**: total HARVEST_RESOURCE actions / entity_count / (ticks / 100)
- **crafting_rate**: total REQUEST_CRAFT actions / entity_count / (ticks / 100)
- **quest_completion_rate**: delta quest_status_counts["COMPLETED"] / entity_count / (ticks / 100)
- **gold_accumulation**: total_gold at tick 1000 / entity_count
- **combat_attrition**: fraction of entities with hp < 50% of max_hp at tick 1000
- **blocker_frequency**: routes_with_blockers / routes_total
- **blocker_string_samples**: up to 10 unique blocker reason strings (proxy for severity)

## Files Changed

- `tools/balance_measure.py` — new measurement script (not production code)
- `docs/audits/D04_balance_tuning.md` — fill blocked sections with measured values
