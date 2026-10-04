---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-EPIC-VISUAL-ASSET-M1-UNBLOCK
phase: done
date: 2026-10-04
tags: [architecture, documentation, planning]
---

# TCK-20261004-EPIC-VISUAL-ASSET-M1-UNBLOCK

## Title
Unblock `AM-M1` for visual assets: write the missing `AM-M0` result, record the owner's decisions, and reclassify M1

## Status
DONE

## Tier
epic

## Type
chore

## Priority
P3

## Request Summary
PR #330 recorded `AM-M1` as `BLOCKED` (`docs/assets/m1_contract_register.md`, "Result"): no `AM-M0` result record
exists, and owner decisions are absent. On 2026-10-04 the user asked to unblock M1 and answered the planner's
blocking questions (all "(Recommended)" options):

| Item | Owner decision (user, 2026-10-04) |
|---|---|
| `AM-M0` prerequisite | Write an `AM-M0` result record from what exists ("Write an M0 result"). This is the separate authorization the M0 plan asks for, scoped to read-only inspection and docs. |
| `W03.4`, `W05.4`, `W08.5` roles | nhan (owner) holds every role: Live Map owner, HUD owner, approver, audit authority, build, publish, activate. Approver/audit separation is an accepted, stated limit of a one-person project. |
| `W02.2` key derivation | The frontend derives visual keys from read-model fields, next to the registry it ships with (Profile A); owner nhan. The backend API never carries visual keys. The real mapping is built only at `AM-M6`. |
| `W07.7` retirement | Never retire: release candidates stay as tracked history; primitive fallbacks are never retired; an old client path retires only by deploying a newer frontend (Profile A). Revisit when release count matters. |
| `W03.5`, `W07.3` ranges | Not needed under Profile A (same reasoning as `W07.1`); exact `schema_version` / `fallback_contract_version` matching stays. Reopen on Profile B or a second renderer. |
| `W03.1` variant axes | Freeze empty: the detail axis (D11) is the only variant mechanism; `variant_axes` must stay empty; defining a context axis needs its own decision. Enforcing it in `verify` is a later code ticket (parked). |
| `W10.4`, `W10.6`, `W10.7` retention | Single-operator rule: one store command at a time, no lock; `gc --delete` prints what it removed (already built: `visual_assets/store/cli.py`, the `gc` branch) and keeps no record, since it cannot delete tracked state; the owner reviews growth by hand when the tracked catalog passes 50 MB (today about 0.9 MB, `du -sh visual_assets/catalog`). |
| `W13.3`, `W13.4`, `W13.6` | Stay `GAP`, carried to `AM-M6` as its prerequisites; not narrowed to the harness drill. |

Asset work otherwise stays paused (user, 2026-10-04). This batch is **docs only** and authorizes nothing: `AM-M2`
needs `AM-M1` `PASS` plus new authority, `AM-M6` stays `NO-GO`, the charter stays unsigned.

## Scope
- `AM-M0` result record (child 1).
- The decisions above as ADR rows, register rows and the docs they touch (child 2).
- `AM-M1` reclassified from the updated register and the M0 result, status lines aligned, epic close-out (child 3).

## Out of Scope
- Any change under `visual_assets/`, `frontend/`, `src/`, `tests/`, CI or config. Code follow-ups (`W02.7` class
  field, `W06.3` activation check, a `verify` rule rejecting non-empty `variant_axes`, `W07.4` with the first
  capability) stay parked lines in the register, no tickets.
- Signing or filling the human fields of `docs/assets/pilot_charter_am6.md`; any `AM-M2`/`AM-M6` work; adopting
  `terrain-v1`; the M5 rerun; icons or other kinds.
- Any decision beyond the table above. A new question goes to the planner, who asks the user.

## Acceptance Criteria
- [x] An `AM-M0` result record exists with a result from the M0 plan's own table, never reworded to pass (child 1).
- [x] ADR rows and register rows carry each decision above with its date and source; no `GAP` is flipped without
  a decision or evidence (child 2).
- [x] The register's "Result" section is re-derived from the plan's table after children 1 and 2, whatever it comes
  out as (child 3).
- [x] `git diff origin/main --stat` touches only `docs/` and `agent-working/` (plus regenerated `docs/REGISTRY.yaml`
  and monitoring shards).

## Related Tickets
- TCK-20261004-EPIC-VISUAL-ASSET-M1-CONTRACTS (PR #330, the register and the `BLOCKED` result)
- Parked: TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN

## Related Docs
- docs/assets/m1_contract_register.md
- docs/plans/visual-asset-management-runtime-integration/00_repository_grounded_discovery_plan.md (M0)
- docs/plans/visual-asset-management-runtime-integration/01_architecture_decisions_and_contracts_plan.md (M1)
- docs/architecture/visual_asset_foundation_adr.md, docs/assets/retention_and_rollback.md, docs/assets/store_contract.md

## Related Stored Artifacts
- None.

## Related Code Areas
- Read only: visual_assets/store/, visual_assets/catalog/, frontend/

## Assumptions / Open Questions
- The M1 result after this batch is not assumed. Remaining code gaps (`W02.7`, `W06.3`, `W07.4`) and the `AM-M6`
  carries (`W13.3/4/6`) may still keep it short of `PASS`; child 3 says so if they do.
- The M0 record is written after D8 selected Profile A. Whether that affects M0's own "neither profile was selected"
  condition is child 1's call, stated openly.

## Implementation Notes
Scoped 2026-10-04 (asset-planner). Not implemented directly. Children, in order, in `SEQUENCE.md`. Branch
`visual-asset-m1-unblock` (fresh off origin/main f6783200f), one commit per child, one PR for the batch (push and
merge only on the user's own answer to a blocking question; merge needs `--admin`).

## Test Summary
Docs only: frontmatter and docs static tests, `make docs-registry` clean, no code path changed.

## Files Changed
See the children.

## Completion Summary
All three children are done on branch `visual-asset-m1-unblock`. `AM-M0` record: `INCONCLUSIVE` (retrospective; the user kept it, 2026-10-04). Owner decisions: ADR D13-D18, register 55 `MET` / 7 `GAP` / 6 `N/A`. `AM-M1` result: still `BLOCKED`, now because `AM-M0` did not pass, with the remaining `GAP` rows judged one by one. Nothing outside `docs/` and `agent-working/` changed. `AM-M2` stays `BLOCKED`, `AM-M6` `NO-GO`, the charter unsigned.
