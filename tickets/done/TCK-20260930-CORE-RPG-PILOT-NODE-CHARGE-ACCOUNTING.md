---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260930-CORE-RPG-PILOT-NODE-CHARGE-ACCOUNTING
phase: done
date: 2026-09-30
tags: [testing]
---

# TCK-20260930-CORE-RPG-PILOT-NODE-CHARGE-ACCOUNTING

## Title
Core-RPG test pilot D1 (real surface): node-charge accounting tests for parity TOWN-122, run through the whole test workflow

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Child of `TCK-20260929-EPIC-CORE-RPG-TEST-PILOT`. One small, tests-only change on resource conservation (Mechanics Bible ch03 §3 Node Charges and §1 Atomic Conservation, parity `TOWN-122`, P0, previously `test_path: null`), used to demonstrate capabilities 1–6 of the test workflow with evidence. It is a workflow demonstration, not a feature proof portfolio.

Surface confirmation: `rpg-feature-planning` (2026-09-30, via `world-rule-catalog-design`) says the `pressure-propagation-economy` epic does not plan to change conservation, harvesting or trade behaviour per its declared scope, and has no schedule. That is a scope-level read, not a line-by-line audit. `origin/new_feature_planning` is the only remote branch with a diff on `src/core/conservation.py`; it is not live (last commit 2026-07-02, PR #19 merged 2026-07-02, diff is the branch lagging `main`).

## Scope
- `tests/unit/resource/test_node_charge_accounting.py` (4 unit tests) and `tests/integration/kernel/test_node_charge_cross_actor.py` (1 kernel-integration test).
- `docs/parity_ledger/town_resource.yaml`: `TOWN-122` gains a `test_path` (evidence link; status unchanged).
- Pilot evidence under `stored_artifacts/<ticket>/pilot/` and the pilot report.

## Out of Scope
- Any `src/` change. Any behaviour change.
- The rejection-path assertion gap (`TCK-20260930-CONSERVATION-REJECTION-PATH-ASSERTION-GAP`, owned by `rpg-feature-planning`). D1 targets baseline mutants at `src/core/conservation.py` lines 82-91 only; kills there belong to this pilot, not to that ticket.
- Approved-oracle review (capability 2b, HOLD D-M2): not exercised, not claimed.
- Changing the CI scenario-lane rule (HOLD D-R2).
- Re-running or editing the committed mutation baseline.

## Acceptance Criteria
1. The new tests pass and assert outcomes (deltas, acceptance, yield count), not mutated source text.
2. `TOWN-122` has a passing `test_path`; its status is unchanged; the same-tick corpse-loot sibling (`TOWN-123`) is stated as not covered.
3. Capabilities 1, 2, 3, 4, 5, 6 each have an artifact in the pilot evidence; 2b is recorded as not exercised.
4. The injected failure is a drill: classified with the `regression_policy.md` §13.1 record and routing stated; no ticket or defect report is filed; the scratch worktree is removed.
5. The report before/after invalidation uses copies of the inputs; no tracked baseline is edited.

## Related Tickets
- `TCK-20260929-EPIC-CORE-RPG-TEST-PILOT` (parent)
- `TCK-20260930-TEST-PLAN-PROOF-FIELDS-AND-TRIAGE-PROCEDURE` (workflow inputs)

## Related Docs
- `docs/mechanics/03_economic_laws.md` §1, §3
- `docs/parity_ledger/town_resource.yaml` (`TOWN-122`)
- `docs/testing/regression_policy.md` §13
- `docs/testing/test_taxonomy.md` §10

## Related Stored Artifacts
None.

## Related Code Areas
`src/core/conservation.py` (read only), `tests/unit/resource/`, `tests/integration/kernel/`.

## Assumptions / Open Questions
- Stability is confirmed at scope level only; see Request Summary.
- The mutation baseline `tests/mutation/baselines/src_core_conservation.json` (recorded 2026-09-29, `stale_after` 30 days) has 117 survivors of 177, including the `accepted=False` to `True` family. That is an assertion gap in existing tests, not a live product bug.

## Implementation Notes
- Real surface (resource conservation, ch03 §3/§1, `TOWN-122`); stability confirmed at scope level only (see the pilot report caveats).
- Reviewer-directed changes: kernel-level cross-actor test added so `TOWN-122` is proven end to end (not resolver-only); the injected fault is a drill (nothing filed); report invalidation used copies (tracked baseline untouched); PR CI is the fast-lane evidence.
- `marker_check` flagged a level-placement mismatch on the first draft; the kernel test moved to `tests/integration/kernel/`.
- `TOWN-123` (corpse loot) is not covered; stated in the ledger `support_boundary`.

Scoped: 54 passed (5 new). Manual scenario lane: 53 passed. Parity and ledger readers: `tests/tools/test_parity_index_baseline.py`, `tests/integration/content/test_resource_region_coverage_corpus.py`, `tests/tools/test_done_checker_static.py` pass. Drill: 2 of 5 new tests fail on the injected fault, as expected.

## Files Changed
- `tests/unit/resource/test_node_charge_accounting.py`, `tests/integration/kernel/test_node_charge_cross_actor.py`
- `docs/parity_ledger/town_resource.yaml` (`TOWN-122` test_path)
- `docs/testing/core_rpg_test_pilot_2026-09-30.md`
- pilot evidence under `stored_artifacts/<ticket>/pilot/`

One tests-only exercise on a real conservation surface; capabilities 1 (partly), 2, 3, 4, 5, 6 demonstrated with artifacts, 2b not demonstrated. Result `established` with scope-level stability caveat.
