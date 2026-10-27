---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS
phase: open
date: 2026-10-27
tags: []
---

# rpg-planner rulings for the U3 batch (2026-10-27)

These are rpg-planner (u24)'s rulings, relayed via lead-planner-u24 → lead-planner → rpg-planner-ubuntu
on 2026-10-27. They are NOT owner approvals. They are kept here word for word so they survive a
/clear. Copy each one into the matching ticket's Implementation Notes, with this relay chain.

## Ask A: mechanisms.yaml `world_composition_assembly`
OK. Update ONLY two statements: a duplicate module_id raises before merge, and ASM-COMP-001 iterates
enabled refs only. Change nothing else in that entry.

## TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS (t2)
- DELETE `src/progression/skills.py::SkillScalingService`, with:
  - its test cases (test_progression_v2);
  - its WIDER_PENDING row, under agent-working-planner's 4 conditions;
  - the 3 doc rows, repointed to `src/engine/rpg_depth.py` (attribute_progression_contract.md:341,
    progression_contract.md:27/168/198).
- DELETE `src/core/governance.py::EnvironmentCapture`.
- KEEP both `CapacityService` classes, with an allowlist reason naming the roles: derive
  (cognition_capacity.py) vs enforce (capacity.py).
- KEEP the legacy `src/core/recipes.py::RecipeRegistry`, with an allowlist reason pointing at the
  follow-up TCK-20261027-LEGACY-RECIPE-REGISTRY-AND-BLACKSMITH-ACTION-UNREACHED.
- ObservabilityMode / HardwareClass / ErrorResponse: classify them in the guard's data only, with no
  renames.
- The guard test goes under tests/unit. Record in the ticket that it sits there only because
  testing-planner was not running, so testing-planner may move it to tests/architecture later.
- With SkillScalingService the only twin deleted, WIDER_PENDING loses the :207 row only and the pin
  at test_mechanism_registry_completeness_check.py:329 becomes 1. Send rpg-planner-ubuntu the exact
  diff of that file before the push.

## TCK-20261004-RENDERING-EVIDENCE-PINNED-TO-A-FROZEN-WORLD-SNAPSHOT (t3)
Option (C) is OK: keep the frozen tests, renamed as reference, and add live coverage on
frontier_living_world.
- In the dated comment on each new live pin, name the rebaseline owner: rpg-planner (u24), which
  holds the data/worlds release.
- Drop 0.2867 and record that it was measured as 0.196, with no known origin.
- Send the exact live values and the INFRA-373 diff to rpg-planner-ubuntu (for rpg-planner) BEFORE
  committing them.

## TCK-20261004-MEASUREMENTS-TAKEN-VIA-A-NON-RUNNING-WORLD-DEFINITION (t4)
No objection.
- GOAL-WINNER AC6 reads "retired as evidence (unverifiable: probe gone)".
- ADD the same one dated line to `agent-working/tickets/done/TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE.md`,
  so the two agree.

## New tickets filed by rpg-planner-ubuntu (in todos/, not part of U3)
- TCK-20261027-HUNGER-CAPACITY-DERIVATION-HAS-NO-LIVE-CALLER. Part 1 (measurement only) is dispatched
  separately after U3. Part 2 is blocked.
- TCK-20261027-LEGACY-RECIPE-REGISTRY-AND-BLACKSMITH-ACTION-UNREACHED.
