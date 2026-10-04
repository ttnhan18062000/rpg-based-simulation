---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-M5-RERUN-AND-M6-CHARTER
phase: done
date: 2026-10-04
tags: [planning, live-map, documentation]
---

# TCK-20261004-VISUAL-ASSETS-M5-RERUN-AND-M6-CHARTER

## Title
Rerun and re-record `AM-M5` for the terrain role, draft the `AM6-W01` pilot charter, and date the M6/M7 plan status

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`AM-M6` starts only after M5 `PASS` and a signed charter plus a new authorization. Child 5 (close-out) of
`TCK-20261004-EPIC-VISUAL-ASSET-PILOT-READINESS`.

## Scope
- Rerun every M5 check (tests, local capture per approved client, gc dry run, rollback drill) on one commit and rewrite
  `docs/assets/surface_rehearsal_result.md` as a new dated result (keep the 2026-10-03 result as history): each `AM5-W*`
  and `AM-C05`/`C06`/`C07`/`C09` gets `PASS`/`FAIL`/`BLOCKED`/`INCONCLUSIVE` with evidence. Never a pass by default; a gap
  that remains stays named.
- Draft `docs/assets/pilot_charter_am6.md` (`AM6-W01`): role and key, release and manifest hashes, clients (from ticket
  3), environment, exposure, duration, owners (activation, rollback, recall), predeclared stop thresholds, forbidden
  scope, and the `AM6-W02`..`W09` evidence list. Every field that needs a human is marked `TO BE SIGNED BY OWNER`;
  the agent fills only facts. Status `DRAFT — not an authorization`.
- Dated status notes (2026-10-xx) in `06_bounded_activation_pilot_plan.md` (prerequisites met / not met, charter draft
  link) and `07_incremental_migration_plan.md` (still dormant: needs M6 `PASS` and a disposition), and in the package `README.md`.
- Epic close-out.

## Planner rulings 2026-10-04
1. The charter's top list names M2 and M4 as "no PASS record exists", and M1 with its open items as the runtime README lists them (AM1-W03, W04, W06-W11, W13; W01 is decided by D8, W08 by D9). Nothing is claimed beyond the records.
2. Classifications accepted: W05 `INCONCLUSIVE` (the hover text is the real Live Map's non-hue route and this harness does not render it; no assistive technology run). `AM5-W09` and `AM-C09` are `INCONCLUSIVE`, not `PASS`, and plan 05 is not edited: "satisfied by construction for the store (gc never deletes tracked state, so previous-release artifacts are protected; tested by the retained-release guard + mutant). Supported-client roots are a deployment fact under Profile A, not modelled. Gate wording unchanged. Reclassify to PASS only if the owner explicitly accepts the narrowed definition (to be asked at charter signing)." That acceptance is one more `TO BE SIGNED BY OWNER` line in the charter. Overall M5 `INCONCLUSIVE`.
3. Commit everything else first, run every check on that clean HEAD, name the hash in the record; the record and the epic close-out are the last commit.
4. Charter: human fields `TO BE SIGNED BY OWNER`, no proposed numbers; the AM6-W02..W09 list marked exists / harness-drill-only / absent; top line "DRAFT — not an authorization; AM-M6 NO-GO until signed and separately authorized". M7 note: still dormant, needs M6 `PASS` and a recorded disposition.

## Out of Scope
- Signing the charter, authorizing or executing `AM-M6`, any deployment, any `AM-M7` planning beyond the dated note.

## Acceptance Criteria
- [x] New M5 result record with a classification and evidence per deliverable and gate, on a named commit.
- [x] Charter draft exists, marked `DRAFT`, with every human field marked and no field invented.
- [x] M6, M7 and README status notes dated and consistent with the result record.
- [x] `make knowledge-index-update` run.

## Related Tickets
- All children of TCK-20261004-EPIC-VISUAL-ASSET-PILOT-READINESS

## Related Docs
- docs/assets/surface_rehearsal_result.md
- docs/plans/visual-asset-management-runtime-integration/05_surface_compatibility_rehearsal_plan.md, 06_bounded_activation_pilot_plan.md, 07_incremental_migration_plan.md, README.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261003-VISUAL-ASSETS-SURFACE-REHEARSAL/

## Related Code Areas
- None new; reruns frontend/src/visualAssets/ and visual_assets/ checks.

## Assumptions / Open Questions
- If M5 is still not `PASS`, the charter draft is still written, with the blocking gates listed at its top.

## Implementation Notes
Rerun commit: `401921bdd165722712a63a2dc5be3204ca2d73e4` (clean before and after). Result: overall M5 `INCONCLUSIVE`; `PASS`: W01-W04, W06-W08; `INCONCLUSIVE`: W05, W09, C05, C06, C07, C09. Unmet prerequisites: no M2 or M4 `PASS` record, M1 open items. Plan 05 was deliberately not edited (planner ruling): the narrowed `gc` definition does not amend the gate. Charter: `docs/assets/pilot_charter_am6.md` (DRAFT, not an authorization).

## Test Summary
On the clean rerun commit: `pytest tests/visual_assets tests/docs tests/architecture tests/static` 1457 passed, 2 skipped, 1 xfailed; frontend `vitest run` 117 passed; scoped eslint and tsc clean; build ok; store `audit` chain ok and `verify` store ok; pilot capture 16 passed on Chromium 148 and Chrome 151 at DPR 1 and 2; old rehearsal capture 8 passed.

## Files Changed
- docs/assets/surface_rehearsal_result.md (rewritten, 2026-10-03 text kept as history), docs/assets/pilot_charter_am6.md (new)
- docs/plans/visual-asset-management-runtime-integration/{06_bounded_activation_pilot_plan,07_incremental_migration_plan,README}.md (dated notes)

## Completion Summary
M5 was rerun for the terrain role and honestly stays `INCONCLUSIVE`; the charter draft lists every unmet prerequisite at its top and marks every human field for the owner. `AM-M6` stays `NO-GO`; nothing was authorized, signed or deployed.
