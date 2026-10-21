---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261021-WORK-ITEM-PRIORITY-LOOKUP-KEY-MISMATCH
phase: done
date: 2026-10-21
tags: []
---

# TCK-20261021-WORK-ITEM-PRIORITY-LOOKUP-KEY-MISMATCH

## Title
The executor looks up local_priority by a packet work_id format that never matches the scheduler's WorkItem work_id, so the priority is always 0. The kernel's sort order also contradicts bounded_concurrency_contract §3.

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Lead-planner-u24 found this on 2026-10-21 by reading the code on origin/main; it was not run. It does not block v1.
- The WorkItem work_id is "{tick}:{kind_lower}:{id}" (scheduler.py:143).
- executor.py:335/340 looks the priority up by the packet work_id "{tick}:{id}:{KIND}" (lines 189/290), so local_priority is always 0.
- It is latent today: priority is never set, and only CRITICAL work is produced.
- kernel.py:606 sorts by -local_priority (higher first), while bounded_concurrency_contract.md §3 says lower is earlier.

## Scope
- Use one work_id builder for both sides, so the keys match.
- The contract or the code decides the sort direction; fix the other and update the parity entry.
- Add a test: a set priority changes the execution order as the contract says.
- Determinism: the final hash must be unchanged on the 3 gate worlds, since priority is 0 today. If it moves, stop and report.

## Out of Scope
- Anything before v1. The simulation-behaviour freeze holds until the v1 record lands.

## Acceptance Criteria
- The keys match.
- The sort order matches the contract, with a test.
- The hash is unchanged.

## Related Tickets
- TCK-20261019-RECORD-BASELINE-V1 (do after it)

## Related Docs
- docs/engine/

## Related Stored Artifacts
- none

## Related Code Areas
- src/engine/scheduler.py:143, src/engine/executor.py:189/290/335/340, src/engine/kernel.py:606, docs/engine/bounded_concurrency_contract.md §3

## Assumptions / Open Questions
- This was read from code, not reproduced. Re-verify it before any fix.

## Implementation Notes
- Verified by reading origin/main (735a1c635): WorkItem.work_id is `{tick}:{kind_lower}:{id}` (scheduler.py), the packet and result work_id is `{tick}:{id}:{KIND}` (executor.py), and `priority_map` was keyed by the first and looked up by the second, so `WorkerResult.local_priority` was always 0 (the packet itself already carried `item.priority`).
- Fix: one builder `src.core.work.packet_work_id(tick, owner_id, work_kind)` used for both packet work_ids and for the `priority_map` key. Both id texts are unchanged (WorkItem.work_id is not touched, packet work_id text is identical), so nothing hashed or validated changes.
- Sort direction: this resolves a doc-against-doc conflict, ruled by rpg-planner (docs/engine owner) on 2026-10-21: the code is right, higher `local_priority` is earlier. Four citations agree with the code: `docs/parity_ledger/infrastructure.yaml` INFRA-420 (verified), `docs/engine/deterministic_execution.md:138`, `docs/engine/contracts/scheduler_contract.md:38` (priority_hint descending), and `kernel.py` `_phase_resolution`. `bounded_concurrency_contract.md` §3 was the lone outlier ("lower is earlier") and only for `local_priority`; its `class_priority` line (lower is earlier) matches the code and stays. §3 is corrected; the sort is now `ConcurrencyLaw.commit_key` (same tuple), used by `Kernel._phase_resolution`, so the order can be tested.
- Nothing sets WorkItem.priority today, so behaviour is unchanged; the determinism check on the 3 gate worlds confirmed it (hashes equal, see Test Summary).

## Test Summary
tests/unit/engine/test_work_item_priority_reaches_the_result.py (5): a set priority reaches the result; unset stays 0; a set priority changes the commit order higher-first; class_priority still ranks before local_priority; the packet work_id text is unchanged and differs from the scheduler id. The two priority tests fail with the old lookup key. With test_tied_worker_result_order and test_protocol_validator_system_results: 35 passed, serial. Final hash on 3 gate worlds, seed 42, 5000 ticks, PYTHONHASHSEED=0, one process at a time (peak RSS 147-201 MB), base 735a1c635 vs 1fbfdaafc: EQUAL on all three: frontier_living_world 96749d4b5b63, urban_political a44bac862465, crowded_frontier e86be67e56ae.

## Files Changed
src/core/work.py, src/core/concurrency_law.py, src/engine/executor.py, src/engine/kernel.py, docs/engine/contracts/bounded_concurrency_contract.md, docs/parity_ledger/infrastructure.yaml (INFRA-420), tests/unit/engine/test_work_item_priority_reaches_the_result.py

## Completion Summary
The executor's priority look-up now uses the packet's own work id, so a WorkItem's priority reaches its result; the commit order is one tested function and the contract's local_priority wording matches the code. Determinism check: final hash equal on the 3 gate worlds.
