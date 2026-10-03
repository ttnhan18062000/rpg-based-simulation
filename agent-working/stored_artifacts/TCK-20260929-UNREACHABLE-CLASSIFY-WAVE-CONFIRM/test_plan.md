---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260929-UNREACHABLE-CLASSIFY-WAVE-CONFIRM
artifact_type: test_plan
tags: [investigation, root-cause, corpus, world, simulation-quality]
---

# Test Plan — TCK-20260929-UNREACHABLE-CLASSIFY-WAVE-CONFIRM

No repo test change. Verification: two standalone 3,000-tick kernel runs (flag `ON` / `OFF`) via a scratchpad script (not
committed — a diagnostic, not a regression test), a one-line grep freshness check for `apply_calamity_consequences`, and
constant reads for the horizon arithmetic. A regression pin for the boss chain already exists
(`tests/unit/world/test_boss_gate_reachability.py`).
