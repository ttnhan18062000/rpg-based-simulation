---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-M1-CONTRACT-REGISTER
phase: open
date: 2026-10-04
tags: [architecture, documentation]
---

# TCK-20261004-VISUAL-ASSETS-M1-CONTRACT-REGISTER

## Title
`AM-M1` contract register: every `AM1-W01`..`W13` acceptance clause mapped to as-built evidence, with a verdict

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
Child 1 of `TCK-20261004-EPIC-VISUAL-ASSET-M1-CONTRACTS`. The `AM-M1` items are mostly built or decided but are
documented across the store contract, the ADR, budgets, retention and the licence review, never against their own
acceptance clauses. Write one register that does that, so a reader can see per clause what is met and what is not.

## Scope
- New `docs/assets/m1_contract_register.md` (frontmatter `layer: architecture`, `authority: P2`).
- One section per item `AM1-W01`..`W13`. For each, split the "Objective acceptance" cell of
  `01_architecture_decisions_and_contracts_plan.md` into its clauses (e.g. `W10`: reachability roots, leases/pins, grace,
  locks, dry run, deletion audit, storage-pressure disposition) and give each clause one row:
  `clause | evidence | verdict | note`.
  - **evidence** = a doc section (`docs/assets/<file>.md#<heading>`), an ADR row (`D1`-`D11`), a code symbol
    (`visual_assets/store/<module>.py::<name>`) or a test path. Every one must exist on the branch.
  - **verdict** = `MET` (built or decided, with evidence), `GAP` (not covered; say what is missing), or `N/A` (say why,
    e.g. "Profile B only" or "single local machine: no leases needed", and cite the decision that makes it so).
  - Built behaviour is described as it is, not as the plan imagined it. Where the code and a doc disagree, the code
    wins and the row says so (and the disagreement goes on the follow-up list, not fixed here).
- `W06` and `W11` rows: `GAP` with "written by FALLBACK-SAFETY-FRAMEWORK / M2-EVIDENCE-CHARTER"; those tickets update
  the rows.
- A closing "Follow-ups (parked, no tickets)" list: one line per `GAP` that would need code or an owner decision.
- A summary table at the top: item, title, MET/GAP/N/A counts, overall `CLOSED` (no `GAP`) / `PARTIAL` / `OPEN`.

## Out of Scope
- Fixing any gap, editing any other doc beyond a link to the register from `store_contract.md`'s pointer list.
- Classifying `AM-M1` as a whole (M1-STATUS-CLOSEOUT does that).

## Acceptance Criteria
- [ ] All 13 items present; every clause of the plan's acceptance cell has exactly one row (the planner checks the
  split against the plan text).
- [ ] Every evidence entry resolves: doc headings exist, symbols exist (`grep -n` on the branch), test paths exist.
  The implementer runs that check and pastes its output into `test_plan.md`'s results.
- [ ] Known facts appear correctly: Profile A (D8), no signing (D9), Aseprite local only + `U-02` closed (D10,
  `aseprite_licence_review.md`), detail axis (D11), retention 30 days and the `gc` protected set, budgets approved.
- [ ] No file outside `docs/` and `agent-working/` changes.

## Related Tickets
- Parent: TCK-20261004-EPIC-VISUAL-ASSET-M1-CONTRACTS

## Related Docs
- See the parent; plus `docs/brainstorm/render-and-art/asset_management_and_runtime_integration_proposal.md` §6-§9.6 for
  what each clause means.

## Related Stored Artifacts
- None.

## Related Code Areas
- Read only: visual_assets/store/ (contracts/, release.py, runtime_export.py, build/, gc.py, revoke.py, audit.py,
  verify.py, config.py), frontend/src/visualAssets/ (manifest parser, resolver, loader)

## Assumptions / Open Questions
- Expected `PARTIAL` items: `W03` (HUD ownership, fallback depth/cycles), `W07` (client/schema/renderer ranges,
  retirement), `W13` (distribution stop, stale/offline cache under Profile A). Confirm from the code; do not assume.

## Implementation Notes
(implementer)

## Test Summary
(implementer)

## Files Changed
(implementer)

## Completion Summary
(open)
