---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261028-RE-RECORD-BASELINE-V1-UNDER-FLAT-SHA256-V3
artifact_type: plan
tags: [benchmarking]
---

# Plan

Ruling: rpg-planner, Option A (2026-10-28), after two findings in the implementer's plan.
- **Finding 1:** e8df8b96d..main holds a measured behaviour change, #753 step B (2.138). So "outcomes equal v1" cannot hold on main.
- **Finding 2:** only the 1b paired results carry a proof digest (`start_hash`, `final_hash`).

1. **R and P.** R = 957caf8f6 (#758, flat-sha256-v3) and P = 04b85fb2e (its parent, v2). The only change between them is F1. R stays fixed whatever merges later, #765 F4 included.
2. **Class the diff.** Every PR in e8df8b96d..957caf8f6 on the measured paths is classed in the ticket. A live, unmeasured change means STOP.
3. **Digest-only proof.** `tools.rpg_measure.paired --base R --new P --report-only --seeds 42..51 --self-check full --jobs 2`, PYTHONHASHSEED=0, on the 3 gate worlds at 5000 ticks. The base repeat shows spread 0 under v3 (AC4). `compare_arms.py digest R P`: every result field is equal except `start_hash` and `final_hash`, and both of those differ. Any other difference means STOP.
4. **1b base arms.** R's cached results under `/mnt/data/scratch-rpg-implementer-2/v3/cache/results/957caf8f6cff-<child>-5000/` are the v3 base for M1 paired runs. A later run reuses them by passing `--cache` with that path. After the compare, they are copied into the shared cache if rpg-planner wants it.
5. **v1 table.** R against the v1 arm (`cache_v1` e6a6a3e10, carried to v1), seeds 42-51, report-only. Fate differences are attributed to step B (2.138) and other measured steps.
6. **Not re-recorded:** the gate JSON and behavioral_5k. They carry no digest, and the harness sources are unchanged since v1. A behaviour rebaseline that absorbs step B is a separate question.
7. **Docs.** Roadmap §12.5, plus the known-entries file if it names the scheme, records R and flat-sha256-v3, with rpg-planner's review. perf receives the step-3 table.
