---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261023-CHECKPOINT-RESTORE-DRAWS-STATELESS-RANDOMS-FROM-SEED-ZERO
phase: open
date: 2026-10-23
tags: []
---

# TCK-20261023-CHECKPOINT-RESTORE-DRAWS-STATELESS-RANDOMS-FROM-SEED-ZERO

## Title
A restored checkpoint rebuilds DeterministicRNG with base_seed=0, so stateless draws after a restore differ from the unbroken run (#593 F3)

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
#593 F3 (comments 6345868460, 6345945757, 6346376586; verified on main by rpg-planner 2026-10-22). `src/engine/scenario_checkpoint.py:83-85` builds `DeterministicRNG(base_seed=0)` on restore with the comment "base_seed is irrelevant post-restore", but `set_state` restores only the per-domain streams, and the stateless `get_int`/`get_float` seed from `_composite_seed(self._base_seed, ...)` (`src/platform/rng.py:85-102`). `scenario_runtime.py:420` builds with `base_seed=initial_state.seed` (`:423` consistent per ubuntu's correction). A restored seeded episode therefore diverges from the unbroken run.

## Scope
1. Restore with the episode's real base seed (from the checkpoint header or state), not 0; fix the stale comment at :83-84.
2. Sizing/regression test: restore at tick N, run K ticks, compare final hash and stateless draws with an unbroken run of N+K.

## Out of Scope
Other checkpoint fields (F1, perf's scheme bump).

## Acceptance Criteria
- A restore-at-N + K run equals the unbroken N+K run (state hash and a sample of stateless draws) on at least one seeded world.
- The comment at scenario_checkpoint.py:83-84 states the actual rule.

## Related Tickets
TCK-20261019-RECORD-BASELINE-V1 (v1 recorded 341f700d0; after-v1 work).

## Related Docs
#593 (lead-planner relays); docs/plans/architecture/faster_feature_testing_draft_tickets.md; docs/engine/performance_contract.md.

## Related Stored Artifacts

## Related Code Areas
src/engine/scenario_checkpoint.py; src/platform/rng.py; src/engine/scenario_runtime.py

## Assumptions / Open Questions
Determinism finding; paired/gate runs never restore, so v1 is unaffected.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
