---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261006-COOPERATION-PENDING-OFFER-SCAN-IS-QUADRATIC-PER-TICK
phase: done
date: 2026-10-06
tags: [performance, cooperation, regression]
---

# TCK-20261006-COOPERATION-PENDING-OFFER-SCAN-IS-QUADRATIC-PER-TICK

## Title
`find_pending_incoming_offer` scans every entity's contracts for every entity on every tick (O(N² log N)), turning movement[5000] from 0.5 s to 17 s per tick

## Status
DONE

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
- [x] Behaviour-neutral: identical canonical state hashes on the corpus worlds before and after, under `audit_mode`. List the worlds, seeds and tick counts.
- [x] movement[5000]: the `cooperation` phase returns to near its pre-#172 cost (it was absent from the top phases at 2ab7152c7; target ≤ ~100 ms per tick with the method above) and no longer dominates the breakdown, with before and after values recorded. The TOTAL per-tick cost won't reach the 2026-08-26 level (~0.5 s) from this fix alone, because the combat_engagement step (~3.2 s, Lane B's ticket) and the collection growth (~1.4 s) remain. Record the total and state which steps are left.
- [x] A test pins the ordering contract of the lookup: several offers to one target resolve to the lowest offerer id and then the lowest contract id.
- [x] Sequenced after the salience fix, per `rpg-feature-planning`.

## Related Tickets
- TCK-20261006-SLOW-STEP-6-REDS-UNMASKED-BY-GATE-FIX (rows 5–8)
- TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION (introduced the scan)
- TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP (sibling step)

## Related Docs
- PR #381 comment 6018086519 (the bisect and the table)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261006-COOPERATION-PENDING-OFFER-SCAN-IS-QUADRATIC-PER-TICK/`

## Related Code Areas
- `src/domains/cooperation/services.py` (`find_pending_incoming_offer`), `src/domains/cooperation/phase.py`

## Assumptions / Open Questions
- Owner: Lane A (`rpg-implementer`), P2, after the salience fix (routing by `rpg-feature-planning`, 2026-10-06).

## Implementation Notes
- `src/domains/cooperation/services.py`: `build_pending_offer_index(state)` maps a target id to the `(offerer_id, contract_id)` the old scan returned for it. Offerers are visited in ascending id order and each offerer's contracts in ascending contract-id order, and the first live offer per target is kept (lowest offerer id, then lowest contract id; offerer active and alive; RECRUITMENT, OFFERED, not expired; an offerer's offer to itself is never indexed). `find_pending_incoming_offer(entity, state, pending_offers=None)` reads the index (built on demand when none is passed, so other callers keep working).
- `src/domains/cooperation/phase.py`: `CooperationPhase.execute` builds the index once per tick. That is valid because nothing in the loop changes a contract or an active/alive flag: every change is deferred into the returned `StateUpdate`, and `ContractService.accept_contract` only returns an update. The index is transient and derived, never stored.
- `select` was split to let the phase reuse the index without a sixth parameter (the code-health ratchet's `PLR0913` and function-length ceilings are blocking): `accept_pending_offer` (step 0), `select_for_own_needs` (steps 1-3, with `_best_partner_report` and `_has_live_recruitment_offer` extracted), and `select`, which keeps its signature and behaviour. The decision-event block moved into `_record_decision_events`. No ceiling or baseline was edited.
- AC 2 as it landed in #391 asks for the `cooperation` phase at about 100 ms per tick or less, with the total recorded and the remaining steps named; 3.8 ms meets it.

## Test Summary
- New `tests/unit/domains/cooperation/test_pending_offer_index.py` (47 tests): the ordering contract (several offers to one target resolve to the lowest offerer id, then the lowest contract id, whatever the insertion order); excluded offers (dead, inactive, expired, accepted, other kind, self-addressed) falling through to the next offerer; a grouped target; a never-expiring offer; a differential against the pre-index scan, kept verbatim as the oracle, over 40 seeded random worlds; a spy that the phase builds the index once per tick. Disabling control: reversing the offerer order fails 20 of them.
- **Hash neutrality** (all seed 42, `audit_mode`, budget off, `LocalSequentialExecutor`, canonical state hash at every 100 ticks and at the end, plus the cooperation decision counts; baseline `f99cb0c6c` run twice, identical): `crowded_frontier` 2000 ticks, `frontier_living_world` 2000, `highland_traverse` 600, `frontier_marches` 600, `hero_guild_routing` 600, `quest_dense_frontier` 600. Identical on all six. Positive control: 72 to 348 pending offers were accepted in five worlds (338, 348, 150, 278, 72); `quest_dense_frontier` has none, so it shows no behaviour change only.
- **movement[5000]** (`PERF_2GB_LOCAL`, `build_movement_state(5000)`, 1 warmup and 3 sample ticks, two runs each, this box): base `f99cb0c6c` 33.1 and 32.2 s per tick, cooperation 11,464 and 10,483 ms; fix 22.4 and 22.2 s per tick, cooperation 3.8 ms (not in the top 8 in the second run). `combat_engagement` is 15,994 and 15,673 ms before and 16,073 and 15,526 ms after (not moved). On `d135dd6be` this box gives 34.0 s, cooperation 10,246 ms, `combat_engagement` 15,823 ms.
- **Steps left**: the total stays far above the 2026-08-26 level because `combat_engagement` (about 16 s here, Lane B's `TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP`) and `collection` (about 2.7 s) remain. Their values here are about 5x and 2x those measured on test-architecture-reviewer's box on identical code; unexplained, handed to the Lane B ticket.
- CI directory lists, run locally with `-m "not slow and not extra_slow"` on the branch merged with `b43e8f70e`: unit-core 1821 passed, 1 skipped; unit-domain 1451 passed, 1 skipped; unit-infra 2426 passed, 1 skipped; integration plus `tests/integrity` plus `tests/architecture` 1225 passed, 7 skipped, 1 xfailed (the known strict deliberate-attack xfail). Not run locally: the full Tools job and the slow suites. Code-health ratchet 0 new, 0 worse; mypy shows nothing in `cooperation`; CI is the first real run of the scratch-venv gates.

## Files Changed
`src/domains/cooperation/services.py`, `src/domains/cooperation/phase.py`, `tests/unit/domains/cooperation/test_pending_offer_index.py` (new); this ticket and its stored artifacts.

## Completion Summary
The pending-offer lookup is a per-tick index built once, with the original choice preserved exactly (canonical hashes identical on six worlds, a differential test against the old scan). On `movement[5000]` the `cooperation` phase falls from about 11 s to about 4 ms per tick and no longer appears among the top phases. The total per-tick cost stays high because `combat_engagement` and `collection` remain (Lane B).
