---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261022-RPG-GATE-KNOWN-ENTRY-CAN-NAME-A-WORLD-AND-SEED
artifact_type: test_plan
tags: [testing, regression]
---

# Test plan

`tests/unit/tools/test_known_reds.py`: own exactly the three cases; sharing a match; uncovered (world, seed) unowned; new entity unowned; violations over examples unowned; no `entity_id` unowned; pooled unowned; case without entity owns the (world, seed); unscoped entry after scoped ones; string lookups skip scoped; stale cases; lint (overlap, shadow both ways, malformed/empty cases, drift with cases, slow registry rejects `cases`).
`test_rpg_gate_report.py`: scoped ownership, fourth fail RED, new entity RED, cap RED, pooled unowned plus stale case listed.
`test_rpg_gate_candidate.py`: scoped omit, uncovered seed/entity refuse, pooled refuse, missing required row not owned.

## Proof Plan

- level: unit (tools lane)
- proof kind: behavioural tests on the matcher, the lint, the report and the candidate
- oracle source: the ruling in the ticket's Assumptions (testing-planner, 2026-10-23)
- expected effect: scoped V3 entries own exactly the three v1 cases; every other V3 fail is unowned and RED
- selected commands: `pytest tests/unit/tools -k "known or rpg_gate or slow"`
