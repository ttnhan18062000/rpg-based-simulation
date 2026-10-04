---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-M2-EVIDENCE-CHARTER
phase: done
date: 2026-10-04
tags: [architecture, documentation, testing]
---

# TCK-20261004-VISUAL-ASSETS-M2-EVIDENCE-CHARTER

## Title
`AM1-W11` M2 evidence charter (draft): what synthetic evidence M2 needs, and which existing `REHEARSAL_ONLY` evidence could count

## Status
DONE

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
Wrote `docs/assets/m2_evidence_charter.md`, status `DRAFT` (no owner approval): where `AM-M2` stands (a run today is `BLOCKED`), supported conditions, synthetic fixtures, a per-deliverable table for `AM2-W01`..`W10` (existing paths and test names, missing coverage, allowed conclusion today), gate setup (`AM-C02` in full; `C05`/`C06`/`C07`/`C09` as contributing evidence only), the evidence bundle, allowed conclusions for `AM-M2` as a whole, and the prior-evidence rule as `PROPOSED` (rerun unchanged on a named commit after approval; the owner decides).
Findings worth the planner's eye: nothing resolves `variant_axes`, so variant precedence has no fixture; the client manifest reader has no input byte bound (Python bounds bytes first), so "reject before allocation" is shown for Python only; the store's unknown-key message echoes the caller's key and no test bounds diagnostics; no cache exists (cache keys and disposal untested); no test shows a prior snapshot survives an incompatible manifest; origins, redirects and MIME have no tests under Profile A; no removal-without-residue proof. No item has an allowed conclusion above `INCONCLUSIVE`; `W04` and `W09` are `BLOCKED`. The register's `W11` rows now point at the doc and stay `GAP`; counts unchanged (40/24/4).

## Test Summary
Docs-only; nothing run for record. Every path and named test in the charter resolves, and the register's 190 evidence entries resolve (scratch script). `tools/validate_frontmatter.py` clean; `pytest tests/docs tests/static` under a 2 GB cap: 124 passed, 2 skipped, 1 xfailed; `make knowledge-index-update` ran.

## Files Changed
- `docs/assets/m2_evidence_charter.md` (new, DRAFT)
- `docs/assets/m1_contract_register.md` (W11 rows and follow-ups)
- `agent-working/` ticket, stored artifacts, monitoring shards; `docs/REGISTRY.yaml`

## Completion Summary
Done as DRAFT. Nothing is written as an owner decision; approval of the charter and its prior-evidence rule is the planner's blocking question at review. No code, fixture or test was added and nothing was run.

Update 2026-10-04: the owner approved it in a blocking question, answering "Approve, with the rerun rule (Recommended)" (relayed by asset-planner). `m2_evidence_charter.md` is now `APPROVED 2026-10-04` with the prior-evidence rule approved (the alternative declined); `AM2-W04` moved from `BLOCKED` to `INCONCLUSIVE`; register W11.1 to W11.5 are `MET`; `AM-M2` stays `BLOCKED`. Recorded in the approval commit after review.
