---
status: active
layer: simulation
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261015-STANDARD-PAIRED-MEASUREMENT-COMMAND-FOR-BEHAVIOUR-STEPS
date: 2026-10-15
tags: []
---

# Plan: TCK-20261015-STANDARD-PAIRED-MEASUREMENT-COMMAND-FOR-BEHAVIOUR-STEPS

Approved by rpg-planner (2026-10-15) with three changes folded in: SE from the per-seed (new - base) differences (the base-vs-base spread is only the self-check, must be 0); the extinction check built in; the tool next to the rpg gate-run tool, not in testing's area.

1. Run ledger counters (src/observability/run_ledger.py): flee and pursuit from the typed MovementMode (entity-ticks and episodes), steps by the terrain entered, `perceived_hostiles` sampled every 10 ticks. A non-authoritative observer; keys `measure|kind_group|person`.
2. `tools/rpg_measure/` (new directory: rpg_gate_run.py lives in testing's tools/test_architecture/, so the tool imports its `build_kernel` and does not edit it): `arm_child.py` (one run, typed JSON), `stats.py` (people set, SE, verdict, extinctions, self-check; pure), `paired.py` (arms from `git archive`, cache by commit, refusals, table, watch rows, `--neutral`).
3. Tests: tests/unit/observability/test_run_ledger_behaviour.py, tests/unit/tools/test_rpg_measure.py.
4. Proofs: `--neutral` base 1a19b9b41 vs the counters commit; base-vs-base 3 worlds x 5 seeds x 5000 ticks, spread 0.

The FLOOR is a named placeholder (`stats.DEFAULT_FLOOR`); the designer sets its value.
