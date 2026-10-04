---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-EPIC-VISUAL-ASSET-M1-CONTRACTS
phase: done
date: 2026-10-04
tags: [architecture, documentation, planning]
---

# TCK-20261004-EPIC-VISUAL-ASSET-M1-CONTRACTS

## Title
Close the `AM-M1` paperwork for visual assets: write up the contracts as built, draft the two missing charters, and classify M1

## Status
DONE

## Tier
epic

## Type
chore

## Priority
P3

## Request Summary
The user asked on 2026-10-04 whether any foundation work was left. The foundation epic (children 1-6, PRs #286/#299) is
done, but the plan package `docs/plans/visual-asset-management-runtime-integration/` still lists `AM1-W01`, `W03`,
`W04`, `W06`-`W11`, `W13` as open. Most of them are built or decided (Profile A, no signing, the build, retention and
`gc`, the runtime manifest) but were never written up against their `AM-M1` acceptance clauses. `W06` (fallback-safety
framework) and `W11` (M2 evidence charter) have no document at all. The user chose the planner's recommendation on
2026-10-04 ("yes, go with your recommendation"): one **docs-only** batch.

Asset work stays paused (user, 2026-10-04): this batch changes no code, art, release or runtime behaviour, and it
authorizes nothing (`AM-M6` stays `NO-GO`, `AM-M7` dormant).

## Scope
- A clause-by-clause register for every `AM1-W01`..`W13` item: evidence (doc section, code symbol, test) and a
  per-clause verdict `MET` / `GAP` / `N/A` with a reason. Gaps are recorded, not fixed.
- `AM1-W06` fallback-safety framework, written from the built behaviour, `PROPOSED` until the owner approves it.
- `AM1-W11` M2 evidence charter, `DRAFT` until the owner approves it; states whether the existing `REHEARSAL_ONLY`
  evidence can count and what M2 would still have to run.
- Status updates in the plan package, and an `AM-M1` result classification computed from the register (never reworded
  to pass).

## Out of Scope
- Any change under `visual_assets/`, `frontend/`, `src/`, `tests/`, CI or config. A gap that needs code becomes a
  parked follow-up line in the register, not a ticket in this batch.
- Running M2, M5 or anything that needs Aseprite; adopting `terrain-v1`; the charter for `AM-M6`; icons or other kinds.
- New decisions the owner has not made. Where the owner must decide, the doc says `PROPOSED`/`DRAFT` and the planner
  asks a blocking question at review.

## Acceptance Criteria
- [x] `docs/assets/m1_contract_register.md` covers all 13 `AM1-W` items, every acceptance clause of each, with evidence
  that resolves to a real path/symbol on the branch (M1-CONTRACT-REGISTER).
- [x] `docs/assets/fallback_safety.md` exists, `PROPOSED` or owner-approved, and the register's `W06` row points at it
  (FALLBACK-SAFETY-FRAMEWORK).
- [x] `docs/assets/m2_evidence_charter.md` exists, `DRAFT` or owner-approved, and the register's `W11` row points at it
  (M2-EVIDENCE-CHARTER).
- [x] Plan package status, `01_...` plan and `store_contract.md` "Decisions still open" agree with the register; an
  `AM-M1` result (`PASS` / `INCONCLUSIVE` / `BLOCKED`) is recorded with its reasons (M1-STATUS-CLOSEOUT).
- [x] `git diff origin/main --stat` for the batch touches only `docs/` and `agent-working/` (plus regenerated
  `docs/REGISTRY.yaml` and monitoring shards).

## Related Tickets
- TCK-20261002-EPIC-VISUAL-ASSET-FOUNDATION, TCK-20261003-EPIC-VISUAL-ASSET-HARDENING-AND-REHEARSAL,
  TCK-20261004-EPIC-VISUAL-ASSET-PILOT-READINESS, TCK-20261004-VISUAL-ASSETS-TERRAIN-DETAIL-VARIANTS
- Parked, not in this batch: TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN

## Related Docs
- docs/plans/visual-asset-management-runtime-integration/01_architecture_decisions_and_contracts_plan.md (the clauses)
- docs/plans/visual-asset-management-runtime-integration/02_synthetic_contract_harness_plan.md (M2, for W11)
- docs/plans/visual-asset-foundation/README.md, docs/architecture/visual_asset_foundation_adr.md
- docs/assets/store_contract.md, budgets.md, retention_and_rollback.md, aseprite_licence_review.md,
  surface_rehearsal_result.md, pilot_charter_am6.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261004-VISUAL-ASSETS-TERRAIN-DRAFT-SET/cvd_pairs.txt (colour-vision finding, for W06)

## Related Code Areas
- Read only: visual_assets/store/, visual_assets/catalog/, frontend/src/visualAssets/

## Assumptions / Open Questions
- `AM-M1` cannot `PASS` while `W03`, `W07` or `W13` keep a `GAP` on a material clause; the expected result is
  `INCONCLUSIVE` with a short list of what would close it. That is an honest outcome, not a failure of the batch.

## Implementation Notes
Scoped as an epic on 2026-10-04 (asset-planner). Not implemented directly. Children, in order, in `SEQUENCE.md`.
One branch `visual-asset-m1-contracts`, one commit per child, one PR for the batch (push and merge only on the user's
own answer to a blocking question).

## Test Summary
Docs only: frontmatter and docs static tests, `make docs-registry` clean, no code path changed.

## Files Changed
See the children.

## Completion Summary
All four children are done on branch `visual-asset-m1-contracts`: the register (68 clauses, 47 `MET`, 17 `GAP`, 4 `N/A`), the fallback-safety framework (approved 2026-10-04, "Approve as written (Recommended)"), the `AM-M2` evidence charter (approved 2026-10-04, "Approve, with the rerun rule (Recommended)"; the old-results alternative declined), and the status close-out. The `AM-M1` result is `BLOCKED` (not the expected `INCONCLUSIVE`; reasoning in the register): no `AM-M0` result record exists and owner decisions are absent. Nothing outside `docs/` and `agent-working/` changed (plus the regenerated `docs/REGISTRY.yaml` and monitoring shards). Nothing was pushed; push, PR and merge wait for the user's own answer.
