---
status: historical
layer: simulation
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261015-STANDARD-PAIRED-MEASUREMENT-COMMAND-FOR-BEHAVIOUR-STEPS
date: 2026-10-15
tags: []
---

# Test plan: TCK-20261015-STANDARD-PAIRED-MEASUREMENT-COMMAND-FOR-BEHAVIOUR-STEPS

Unit (no simulation): flee/pursuit entity-ticks and episodes, a dead entity counts nothing, perception only on the sampling cadence with the sample count, steps counted once under the terrain entered, the observer leaves the states untouched, empty counters still write the tally keys; people set = base tick-0 roster on the same ids in both arms (a new-arm keeps_coin change does not grow it), removed entity = dead, added ids listed apart, SE formula, drift needs > 2 SE and > floor, extinction STOP vs base-state vs recovered, self-check names differing pairs, a non-audit run is refused and named, world section and watch row, cache hit and repeat arm.
System: `--neutral` (base 1a19b9b41 vs the counters commit, 3 worlds, seed 42, 1000 ticks: identical); base-vs-base 3 worlds x 5 seeds x 5000 ticks: every cell identical (spread 0).

## Proof Plan

- level: unit plus system (two measured runs)
- proof kind: regression and neutrality
- oracle source: the base arm itself (state hashes), and hand-staged runs for the arithmetic
- expected effect: counters leave every state hash unchanged; two runs of one arm are byte-identical; a pair with a changed arm reports a per-world delta, SE and verdict
- selected commands: `pytest tests/unit/observability tests/unit/tools/test_rpg_measure.py`; `python -m tools.rpg_measure.paired --base <rev> --new <rev> --neutral`; `python -m tools.rpg_measure.paired --base <rev> --new <rev> --self-check full`
