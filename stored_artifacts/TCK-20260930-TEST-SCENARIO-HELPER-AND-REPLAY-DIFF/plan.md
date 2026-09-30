---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260930-TEST-SCENARIO-HELPER-AND-REPLAY-DIFF
artifact_type: plan
tags: [testing]
---

# Plan

Scope and approach: see the ticket's Scope and Implementation Notes.

Envelope bounds now live as module constants in `test_determinism_suite.py` (`REPRODUCIBILITY_SEED/TICKS/PROFILE`, values unchanged) and `replay_diff` imports them. The examples are synthetic, sit under `tests/mechanic_scenarios/synthetic_examples/`, declare lane `perf-cert-arena`, and a test checks that lane's CI step lists `tests/mechanic_scenarios`.
