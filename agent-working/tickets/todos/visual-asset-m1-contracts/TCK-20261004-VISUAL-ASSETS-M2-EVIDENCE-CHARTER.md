---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-M2-EVIDENCE-CHARTER
phase: open
date: 2026-10-04
tags: [architecture, documentation, testing]
---

# TCK-20261004-VISUAL-ASSETS-M2-EVIDENCE-CHARTER

## Title
`AM1-W11` M2 evidence charter (draft): what synthetic evidence M2 needs, and which existing `REHEARSAL_ONLY` evidence could count

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
Child 3 of `TCK-20261004-EPIC-VISUAL-ASSET-M1-CONTRACTS`. `AM1-W11` asks for an M2 charter that predeclares the
synthetic fixtures, supported conditions, exact gate setup, retained evidence and allowed conclusions. Much of M2's
harness (`AM2-W01`..`W10`) was in effect built by the foundation and hardening batches on synthetic fixtures, marked
`REHEARSAL_ONLY`, without a charter declared first. There is no M2 `PASS` record, which is one reason `AM-M6` is `NO-GO`.

## Scope
- New `docs/assets/m2_evidence_charter.md`, status `DRAFT` (owner approval by blocking question at review).
- Section per `AM2-W01`..`W10` (`02_synthetic_contract_harness_plan.md`): the fixtures and tests that exist today
  (paths), the conditions they cover, what is missing, and a declared **allowed conclusion** if M2 were run now.
- **Gate setup**: `AM-C02` in full; the contributing checks toward `AM-C05`, `C06`, `C07`, `C09`, stated so they cannot
  be read as full gate passes (plan lines 48-49).
- **Prior-evidence rule**: the charter decides, and says why, whether evidence produced before the charter existed may
  count. Planner's proposal: it may count only if rerun unchanged on a named commit after the charter is approved (a
  charter predeclares; it cannot be fitted to results already seen). The owner decides.
- **Evidence bundle** (`AM2-W09`): what a run must retain (revisions, environment, raw results, coverage gaps) and
  where; reuse the existing results-doc shape (`surface_rehearsal_result.md`).
- Update the register's `W11` rows to point at this doc.

## Out of Scope
- Running M2 or any test for record; adding fixtures or tests; any code change.
- Authorizing M2: the charter is a draft input to a later, separate owner decision.

## Acceptance Criteria
- [ ] All ten `AM2-W` items covered with existing paths (that resolve) and named gaps.
- [ ] Allowed conclusions declared per item and for M2 as a whole, using the plan's `PASS`/`FAIL`/`BLOCKED`/`INCONCLUSIVE`.
- [ ] The prior-evidence rule is stated as `PROPOSED` (or owner-approved with date and words).
- [ ] Register `W11` rows updated; no file outside `docs/` and `agent-working/` changes.

## Related Tickets
- Parent: TCK-20261004-EPIC-VISUAL-ASSET-M1-CONTRACTS; after TCK-20261004-VISUAL-ASSETS-FALLBACK-SAFETY-FRAMEWORK
  (`AM2-W04` fixtures follow the W06 classes)

## Related Docs
- docs/plans/visual-asset-management-runtime-integration/02_synthetic_contract_harness_plan.md
- docs/assets/surface_rehearsal_result.md, store_contract.md ("What is built now", "Known gaps")

## Related Stored Artifacts
- None.

## Related Code Areas
- Read only: tests/visual_assets/, frontend/src/visualAssets/__tests__/, visual_assets/catalog/ (synthetic fixtures)

## Assumptions / Open Questions
- None beyond the prior-evidence rule, which is the owner's.

## Implementation Notes
(implementer)

## Test Summary
(implementer)

## Files Changed
(implementer)

## Completion Summary
(open)
