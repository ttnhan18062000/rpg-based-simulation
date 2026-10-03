---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260817-DOC-CONCURRENCY-LIMIT-RATIONALE
phase: done
date: 2026-08-17
tags: [documentation, engine]
---

# TCK-20260817-DOC-CONCURRENCY-LIMIT-RATIONALE

## Title
Document why GovernorPolicy.from_mode()'s concurrency_limit decreases as RuntimeMode escalates

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
GovernorPolicy.from_mode() sets concurrency_limit to 1.0/1.0/0.5/0.25 across NORMAL/CONSTRAINED/DEGRADED/SURVIVAL — not self-evidently correct, since naively more pressure should mean more workers to clear backlog. The real reasoning (LOD/cadence/phase budgets already shrink the batch by the time concurrency throttles, so fewer workers on a smaller batch reduces contention) isn't written down anywhere. The author wants this recorded next to GovernorPolicy.from_mode() or in governance_logic.md.

## Scope
- Add a docstring/comment adjacent to GovernorPolicy.from_mode() in src/engine/policy.py (lines 58-148, values set at 70, 91, 112, 133) explaining that LOD/cadence/phase-budget shedding already shrinks the batch by the time concurrency throttles, so fewer workers reduces contention rather than adding scheduling noise
- Add an explicit subsection with the same rationale to docs/engine/governance_logic.md §3 Degradation Laws (or docs/engine/contracts/bounded_concurrency_contract.md §5, whichever is deemed canonical), cross-referenced from the other
- No production behavior change — concurrency_limit values (1.0/1.0/0.5/0.25) remain unchanged

## Out of Scope
- Adding the rationale to docs/engine/contracts/resource_governor_contract.md — it explicitly disclaims worker-pool/concurrency scaling as a Non-Goal, would self-contradict
- Any change to tests/unit/kernel/test_worker_adaptation.py assertions (peak_workers values) — doc-only fix

## Acceptance Criteria
- [x] A docstring/comment adjacent to GovernorPolicy.from_mode() in src/engine/policy.py explains why concurrency_limit decreases, referencing the LOD/cadence/phase-budget shedding rationale
- [x] governance_logic.md (or bounded_concurrency_contract.md, whichever is canonical) gets an explicit subsection on this rationale, cross-referenced from the other if split
- [x] No production behavior change: concurrency_limit values (1.0/1.0/0.5/0.25) remain unchanged; tests/unit/kernel/test_worker_adaptation.py continues to pass unmodified
- [x] Rationale discoverable both inline (grep/read landing on from_mode()) and via docs/REGISTRY.yaml-indexed doc

## Related Tickets
- TCK-20260817-KERNEL-CONCURRENCY-DESIGN-EPIC
- TCK-20260419-MB-TASK4-ADAPTIVE-POOL
- TCK-20260420-CPU-GOV
- TCK-20260419-MD-TASK1-FREEZE-CONCURRENCY-CONTRACT

## Related Docs
- docs/engine/governance_logic.md
- docs/engine/contracts/resource_governor_contract.md
- docs/engine/contracts/bounded_concurrency_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/policy.py
- src/core/governance.py
- src/engine/worker_manager.py
- docs/engine/governance_logic.md
- docs/engine/contracts/resource_governor_contract.md
- docs/engine/contracts/bounded_concurrency_contract.md
- tests/unit/kernel/test_worker_adaptation.py

## Assumptions / Open Questions
- Two plausible doc locations named (inline docstring vs governance_logic.md) — doing both per the acceptance criteria, rather than picking one and leaving a gap
- Pure doc/comment change with no behavior delta, but a diff-only review is warranted to ensure concurrency_limit values aren't silently altered while adding the comment

## Implementation Notes
Verified the ticket's premise against real code before writing anything:

- **Values confirmed**: `GovernorPolicy.from_mode()` in `src/engine/policy.py` sets
  `concurrency_limit` to `1.0` (NORMAL, line 70), `1.0` (CONSTRAINED, line 91), `0.5` (DEGRADED,
  line 112), `0.25` (SURVIVAL, line 133) — exactly as the ticket claimed.
- **Shedding rationale confirmed as true, not assumed** by reading the actual shedding code:
  - `PhaseBudgetGovernor.evaluate()` (`src/engine/phase_governor.py:43-150`) shrinks
    `candidate_budget`/`strategic_budget`/`movement_budget` and tightens `scan_policy`
    (FULL → THROTTLED → EXACT_DIRTY) as `RuntimeMode` escalates (e.g. `candidate_budget`:
    1000 → 500 → 200 → 50).
  - `SystemCadence` / `should_run()` (`src/engine/cadence.py:4-54`) widens per-subsystem
    re-evaluation intervals as `RuntimeMode` escalates (e.g. `strategic_intelligence`:
    every 10 ticks in NORMAL vs. every 100 in SURVIVAL, set in `policy.py`'s per-mode blocks).
  - `DeterministicScheduler.select_work()` (`src/engine/scheduler.py:33-90`) filters candidates
    through readiness gating, `LODService.should_execute()` (`src/engine/lod.py:59-71`), and the
    cadence gate above, before any `WorkItem` is handed to the executor.
  - `WorkerManager.execute_batch()` (`src/engine/worker_manager.py:80-116`) is where
    `concurrency_limit` is actually consumed, via `effective_cap = max(1, ceil(max_workers *
    concurrency_limit))` (line 103) — confirming it acts strictly downstream of all the shedding
    above, on whatever batch survives it.
  - This confirms the rationale holds: by the time concurrency is throttled, the batch it applies
    to has already shrunk via phase budgets, cadence, and LOD. A smaller worker pool on an
    already-smaller batch reduces thread/IPC contention rather than adding scheduling noise.
- Also found `docs/plans/kernel_concurrency_design_review_proposal.md` (C6, and its Part 4 table)
  already contains this exact reconstructed rationale in prose, sourced from prior discussion but
  explicitly marked as "not found written down anywhere" authoritative — this ticket is that
  write-down. Cross-checked my writeup against it for consistency; no conflicts found.
- **Doc placement decision**: chose `docs/engine/contracts/bounded_concurrency_contract.md` §5
  "Concurrency Bounds" over `docs/engine/governance_logic.md` §3 "Degradation Laws". Read both
  files in full first: `governance_logic.md` is scoped to the Town Governance authoritative flow
  (`TownResolutionSystem`/`WorldDynamicsSystem` — tax extraction, vault deposits, maintenance),
  a different "governance" concept entirely from the engine's `ResourceGovernor`/`GovernorPolicy`;
  its §3 "Degradation Laws" already describes per-mode taxation/maintenance behavior, not
  concurrency. `bounded_concurrency_contract.md`'s Purpose is literally "the finished law for
  engine concurrency," and its existing §5 already covers Max Workers/Queue Depth/Saturation —
  the same domain `concurrency_limit` operates in. Added new subsection §5.1 there instead of
  splitting content, so no cross-reference was needed in a second doc.
- Verified `docs/engine/contracts/resource_governor_contract.md`'s Non-Goals section (line 42:
  "Concurrency or worker-pool scaling.") is real and accurate — confirmed the Out-of-Scope
  exclusion is correct and left that file untouched.
- Added a docstring block to `GovernorPolicy.from_mode()` (`src/engine/policy.py`, inserted after
  the existing one-line docstring, before the `budgets = PhaseBudgetGovernor.evaluate(...)` line)
  citing the same four modules/functions, plus a pointer to the new doc subsection. Comment-only
  change — no `concurrency_limit=` value in any of the four per-mode blocks was touched
  (confirmed via `git diff src/engine/policy.py`: 16 insertions, 0 deletions).

## Test Summary
Ran `.venv/bin/python3 -m pytest tests/unit/kernel/test_worker_adaptation.py -v`:
`test_worker_concurrency_throttling` and `test_worker_concurrency_rounding` both PASSED,
unmodified, confirming no production behavior change (2 passed in 0.46s).

## Files Changed
- `src/engine/policy.py` — added rationale docstring to `GovernorPolicy.from_mode()` (comment-only, no value changes)
- `docs/engine/contracts/bounded_concurrency_contract.md` — added §5.1 "Why `concurrency_limit` Decreases as `RuntimeMode` Escalates"
- `docs/plans/kernel_concurrency_design_review_proposal.md` — added completion cross-link after C6
- `docs/parity_ledger/infrastructure.yaml` — added new entry `INFRA-365` (P2, verified) since no prior
  entry existed for this behavior; doc/comment-only ticket so a new entry was added rather than
  strengthening an existing one
- `tickets/inprogress/TCK-20260817-DOC-CONCURRENCY-LIMIT-RATIONALE.md` — this ticket, updated with Implementation Notes/Test Summary/Files Changed/Completion Summary and Status/AC updates

## Completion Summary
Confirmed the ticket's premise was accurate (concurrency_limit values 1.0/1.0/0.5/0.25, and the
LOD/cadence/phase-budget shedding rationale both hold up against the real shedding code in
`phase_governor.py`, `cadence.py`, `scheduler.py`, `lod.py`, and `worker_manager.py`). Recorded
the rationale inline as a docstring on `GovernorPolicy.from_mode()` in `src/engine/policy.py`,
and as a new §5.1 subsection in `docs/engine/contracts/bounded_concurrency_contract.md` (chosen
over `governance_logic.md`, which covers an unrelated Town Governance concept). Left
`resource_governor_contract.md` untouched per its correct Non-Goals disclaimer. No production
values changed; `tests/unit/kernel/test_worker_adaptation.py` passes unmodified.
