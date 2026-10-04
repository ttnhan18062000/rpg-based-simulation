---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261004-PERF-M1-TIED-WORKER-RESULT-VERIFICATION
date: 2026-10-04
tags: [performance, determinism, testing]
---

# Test plan: TCK-20261004-PERF-M1-TIED-WORKER-RESULT-VERIFICATION

| AC | Test | Proof |
|---|---|---|
| 1 | `test_permuted_arrival_order_leaves_all_five_levels_unchanged` (5 scenarios x 3 routes) | batch, raw update, refined update, state, digest equal under 3 permutations |
| 2 | `test_id_zero_...`, `test_equal_class_and_local_priority_...`, `test_same_entity_tie_...` | tied keys equal, permuted input order differs |
| 3 | outcome recorded in docs and ledger | one of four outcomes with evidence |
| 4 | `git diff --stat` | no gated file |
| 5 | `test_mutation_proof_a_noncommutative_tie_makes_the_comparison_fail` | digest diverges; equal-valued duplicates commute |
