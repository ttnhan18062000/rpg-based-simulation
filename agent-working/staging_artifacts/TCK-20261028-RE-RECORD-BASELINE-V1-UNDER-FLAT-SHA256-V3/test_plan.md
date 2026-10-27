---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261028-RE-RECORD-BASELINE-V1-UNDER-FLAT-SHA256-V3
artifact_type: test_plan
tags: [benchmarking]
---

# Test plan

- **AC3 (amended by rpg-planner's ruling):** `compare_arms.py digest` on R against P, 30 keys. Every non-digest field is equal, and `start_hash` and `final_hash` differ.
- **AC4:** the paired self-check full repeat of R gives spread 0.
- **v1 table (report-only):** `compare_arms.py v1` on R against cache_v1 e6a6a3e10, 30 keys.

## Proof Plan
- **Level:** measurement (simulation runs).
- **Proof kind:** field-by-field equality across a scheme-only change, plus a determinism repeat.
- **Oracle source:** the P (v2) arm results and R's repeat arm.
- **Expected effect:** only the digests move.
- **Selected commands:** see plan.md step 3.
