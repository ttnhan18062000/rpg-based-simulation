---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-M1-CONTRACT-REGISTER
phase: done
date: 2026-10-04
tags: [architecture, documentation]
---

# TCK-20261004-VISUAL-ASSETS-M1-CONTRACT-REGISTER

## Title
`AM-M1` contract register: every `AM1-W01`..`W13` acceptance clause mapped to as-built evidence, with a verdict

## Status
DONE

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
Wrote `docs/assets/m1_contract_register.md`: 68 clause rows over `AM1-W01`..`W13`, a summary table, a follow-ups list (one line per `GAP`) and a "Where docs and code disagree" section. The page was generated from one table in a scratch script so the summary counts cannot drift from the rows (script not committed).
Result: 40 `MET`, 24 `GAP`, 4 `N/A`. `CLOSED`: W01, W04, W09, W12. `PARTIAL`: W02, W03, W05, W07, W08, W10, W13. `OPEN`: W06, W11 (all `GAP`, updated by their own tickets).
Differences from the ticket's assumptions: `W03` has `MET` rows (limits, fallback depth/cycles: depth is fixed and no fallback edges exist) alongside `GAP`; `W07` client range is `N/A` under Profile A, schema and fallback ranges are `MET` (exact-version match both sides), renderer, capability and retirement are `GAP`; `W13` distribution stop, stale/offline/cache and tested rollback are `GAP`. `W10` locks is a `GAP` (no lock; no decision puts concurrent commands out of scope), leases/pins is `N/A` (nothing reads store objects at runtime under Profile A). `W02` derivation owner is a `GAP` the ticket did not predict.
Docs disagree with code in four places (listed in the register, not fixed): `store_contract.md` "Decisions still open", the ADR Status and Consequences, the plan README status lines (M1-STATUS-CLOSEOUT's), and the unsigned charter's `rc-0001`/no-detail facts. One link to the register added to `store_contract.md`.

## Test Summary
Docs-only; no code changed. Evidence check (scratch script): `checked 179 evidence entries`, none unresolved; a negative control with a broken heading and a broken symbol failed as it should (staging `test_plan.md`). `tools/validate_frontmatter.py` clean on the page, ticket and artifacts. `pytest tests/docs tests/static tests/visual_assets/store/unit/test_docs_commands.py` under a 2 GB cap: 129 passed, 2 skipped, 1 xfailed. `make knowledge-index-update` ran.

## Files Changed
- `docs/assets/m1_contract_register.md` (new)
- `docs/assets/store_contract.md` (one link)
- `agent-working/tickets/` (this ticket), `agent-working/stored_artifacts/TCK-20261004-VISUAL-ASSETS-M1-CONTRACT-REGISTER/`, `agent-working/tickets/working_log.csv`, `docs/REGISTRY.yaml`, monitoring shards

## Completion Summary
Done. The register exists with every evidence entry resolving on the branch. Nothing outside `docs/` and `agent-working/` changed. Owner decisions are not written as made; W06 and W11 rows are `GAP` for their tickets to update. Follow-ups are parked in the register with no tickets.
