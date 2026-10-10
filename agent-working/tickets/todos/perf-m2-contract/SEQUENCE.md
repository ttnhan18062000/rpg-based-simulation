# Implementation Sequence — perf-m2-contract

Tickets must be implemented in this order. `implement-epic` reads this file to override
alphabetical order. Hand-written 2026-10-10 by perf-planner from the merged M2 plan
(`docs/plans/design_enhancement/performance_optimization/performance_m2_performance_contract_epic.md`,
"Delivery plan", #475). Owner decisions OD-1 to OD-8 are recorded there. The `src/` lift is roadmap
RPG-core gate item 8 (six files); every measurement stays provisional, and no check becomes blocking.

## Order

1. TCK-20261010-PERF-M2-T02B-RECORD  (no deps; every later ticket consumes it)
2. TCK-20261010-PERF-M2-T07-CANONICAL-VARIANTS  (same batch as 1; also edits `src/perf/profiles.py`, so it lands after 1 or merged with it)
3. TCK-20261009-PERF-GATE-PASSES-VACUOUSLY-AGAINST-PRE-M1-BASELINE  (plan X1; depends on: 1, for `cost_accounting_version`)  (DONE 2026-10-10)
4. TCK-20261010-PERF-M2-T05-BASELINE-LIFECYCLE  (depends on: 1; and on testing's `baseline_change_policy.md` plus `TCK-20261009-KNOWN-REDS-REGISTRY-SHARED-MODULE`, or their agreed field names if it starts first)
5. TCK-20261010-PERF-M2-T03-TRIPWIRE-PAIRED  (depends on: 1, 2, 4; testing-planner agrees the CI selector change first)
6. TCK-20261010-PERF-M2-T04-CAPACITY-RUN  (depends on: 1, 4; may run in parallel with 5)
7. TCK-20261010-PERF-M2-T08-CANONICAL-RERUNS  (depends on: 2, 3, 4, 5; tactical/combat reruns after RPG's hunting batch lands; `mixed_200_*` after TCK-20261004-PERF-SCENARIO-MIXED-STATE-SPAWN-COLLISION)
8. TCK-20261010-PERF-M2-T06-GATE-CONFORMANCE  (depends on: 4, 5, 6, 7, 9; the P1 contract edit needs the owner)
9. TCK-20261010-PERF-M2-T05B-KNOWN-DEBT-LEDGER  (split from 4 on 2026-10-10; depends on: TCK-20261009-KNOWN-REDS-REGISTRY-SHARED-MODULE; blocks only 8)

## Batches

- Batch 1: 1 + 2
- Batch 2: 3 + 4
- Batch 3: 5 + 6
- Batch 4: 7
- Batch 5: 8
- Batch 2b: 9 runs whenever the shared known-reds module lands, before batch 5
