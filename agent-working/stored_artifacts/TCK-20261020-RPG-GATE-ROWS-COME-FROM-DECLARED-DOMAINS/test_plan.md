---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261020-RPG-GATE-ROWS-COME-FROM-DECLARED-DOMAINS
phase: done
date: 2026-10-20
tags: []
---

# Test plan: TCK-20261020-RPG-GATE-ROWS-COME-FROM-DECLARED-DOMAINS

## Proof Plan
- level: unit + real kernel + dry chain
- proof kind: row-identity equality across seeds; stray raises; share arithmetic
- oracle source: testing's ruling and the designer's share and at_risk rulings
- expected effect: identical (id, group, key, tick) sets on every seed; candidate step passes
- selected commands: pytest tests/unit/observability/test_rpg_gate_metrics.py tests/integration/observability/test_gate_rows_are_the_same_on_every_seed_through_the_real_kernel.py; rpg_gate_harness -> rpg_gate_report -> rpg_gate_candidate on 3 worlds x 2 seeds x 1500t
