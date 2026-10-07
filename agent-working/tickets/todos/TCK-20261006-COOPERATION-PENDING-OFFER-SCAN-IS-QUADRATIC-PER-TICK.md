---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261006-COOPERATION-PENDING-OFFER-SCAN-IS-QUADRATIC-PER-TICK
phase: open
date: 2026-10-06
tags: [performance, cooperation, regression]
---

# TCK-20261006-COOPERATION-PENDING-OFFER-SCAN-IS-QUADRATIC-PER-TICK

## Title
`find_pending_incoming_offer` scans every entity's contracts for every entity on every tick (O(N² log N)), turning movement[5000] from 0.5 s to 17 s per tick

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Measured by `test-architecture-reviewer` on 2026-10-06 (filed for Lane A by the routing of `rpg-feature-planning`; evidence on PR #381, comment 6018086519). `BenchHarness` with `PERF_2GB_LOCAL`, `build_movement_state(5000)`, 1 warmup tick and 2–3 sample ticks, wall clock. Single runs, so these are values, not distributions:
- `eedf7d5b47304197593365b163d8a21c913f0595` (the last green slow run, 2026-08-26): 0.51 s per tick, p95 132 ms.
- `origin/main` `d135dd6be041b51711411bfb9fad516c58fb2bfc`: 17.2 s per tick, p95 30,049 ms. `resolution_overhead` 14,278 ms, of which `cooperation` is 10,846 ms. The same profile appears with the 08-26 `src/perf/scenarios.py`, so the engine changed and the scenario did not.
- First-parent bisect over 276 commits (threshold 2 s per tick, scenario held at 08-26): the first slow commit is `589c9045294540a7d4c74d57e69b69800b0dcea1` (#172, 2026-09-12, TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION), at 12.3 s per tick with cooperation at 11.2 s. The last fast commit is `2ab7152c7316a5e911957552813d862a53b27ec2`, at 0.77 s.

Cause, read from the code: #172 added `CooperationDecisionService.find_pending_incoming_offer(entity, state)` (`src/domains/cooperation/services.py`), and `CooperationPhase.execute` calls it for **every** entity, including entities with no help need. Each call iterates `sorted(state.entities.keys())` and then every contract of every offerer, so one tick costs O(N² log N): about 25 M offerer visits at 5,000 entities. The CI timeout traceback (run 37403688489, `test_perf_combat[500]`) stops in this function. These are rows 5–8 of `TCK-20261006-SLOW-STEP-6-REDS-UNMASKED-BY-GATE-FIX` (the four perf benches time out at the 600 s large budget).

## Scope
- Make the per-tick pending-offer lookup linear or near-linear. The expected shape is a per-tick index of live OFFERED recruitment contracts keyed by target id, built once per tick. It must preserve the current choice exactly: the first live, unexpired OFFERED RECRUITMENT contract, ordered by offering entity id and then contract id.
- No behaviour change, including the acceptance preconditions (offerer alive and active, target not in a group).

## Out of Scope
- The `combat_engagement` step (`TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP`, Lane B).
- Richer acceptance criteria (deferred per #172).
- Any change to the perf thresholds or budgets.

## Acceptance Criteria
- [ ] Behaviour-neutral: identical canonical state hashes on the corpus worlds before and after, under `audit_mode`. List the worlds, seeds and tick counts.
- [ ] movement[5000]: the `cooperation` phase returns to near its pre-#172 cost (it was absent from the top phases at 2ab7152c7; target ≤ ~100 ms per tick with the method above) and no longer dominates the breakdown, with before and after values recorded. The TOTAL per-tick cost won't reach the 2026-08-26 level (~0.5 s) from this fix alone, because the combat_engagement step (~3.2 s, Lane B's ticket) and the collection growth (~1.4 s) remain. Record the total and state which steps are left.
- [ ] A test pins the ordering contract of the lookup: several offers to one target resolve to the lowest offerer id and then the lowest contract id.
- [ ] Sequenced after the salience fix, per `rpg-feature-planning`.

## Related Tickets
- TCK-20261006-SLOW-STEP-6-REDS-UNMASKED-BY-GATE-FIX (rows 5–8)
- TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION (introduced the scan)
- TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP (sibling step)

## Related Docs
- PR #381 comment 6018086519 (the bisect and the table)

## Related Stored Artifacts
- None yet.

## Related Code Areas
- `src/domains/cooperation/services.py` (`find_pending_incoming_offer`), `src/domains/cooperation/phase.py`

## Assumptions / Open Questions
- Owner: Lane A (`rpg-implementer`), P2, after the salience fix (routing by `rpg-feature-planning`, 2026-10-06).

## Implementation Notes
None yet.

## Test Summary
None yet.

## Files Changed
None yet.

## Completion Summary
None yet.
