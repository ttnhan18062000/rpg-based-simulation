---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-RETENTION-AND-ROLLBACK
phase: done
date: 2026-10-04
tags: [mcp, testing, architecture]
---

# TCK-20261004-VISUAL-ASSETS-RETENTION-AND-ROLLBACK

## Title
Retention numbers, `gc` with rollback and client roots, and an old-client / new-release rollback drill

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`AM5-W09` and `AM-C09` are `BLOCKED` (no rollback roots, no client roots, retention unset) and `AM-C06` is `BLOCKED`
(no retained previous release, no rollback authority, no old client). The retention row is the last unset U-05 row.
Child 4 of `TCK-20261004-EPIC-VISUAL-ASSET-PILOT-READINESS`.

## Scope
(Rewritten after the planner decision below; the original wording promised root kinds that do not exist.)
- Retention: measure what exists (store size with the real key and fixtures; growth per adopt/release) and propose a value for the unset row in
  `docs/assets/budgets.md` (age-based clean-up of the LOCAL quarantine and review dirs), with the same rule set (R0-R4). If the measured growth is too small to
  justify a number, propose one with rule R0 and a stated reason. **Ask the user to approve** (blocking question) or keep the row `UNSET`; flip it to `APPROVED <date>` only after.
- `gc` (local-only): dry run stays the default, `--delete` stays opt-in. A PASSED, un-adopted, unrevoked intake older than the approved N days (counted from the
  intake's own timestamp) becomes listable together with its review export; younger ones are protected, and so is anything an adoption or review record references.
  A dry-run-only report line names tracked artifacts that no committed release candidate references, saying "kept: tracked history, never deleted". `gc` still never deletes a tracked
  object or record. Document in `docs/assets/store_contract.md`: if `gc` ever gains a deletion kind for tracked objects, a typed roots record becomes required first, in its own ticket.
  Retained releases are derived (every committed candidate under `manifests/candidates`), not declared.
- Rollback under Profile A (D8): rollback is redeploying the previous whole frontend build. In the harness, "previous release" = the previous frontend build's runtime fixture
  set (the synthetic rehearsal export, a different catalog_id) and "new" = `pilot/rc-0001`. Drill: new client + old release, old client + new release, release with the key removed
  (recall). Each must render the role or its fallback, never a mixed snapshot. The old-client + new-release case is defence in depth against a mis-deploy, not a normal path.
- Ask the user for the rollback/recall owner; record the answer verbatim or leave it explicitly unnamed.
- `AM-C09` is judged as "`gc` removes no protected object", protected = all tracked state + young PASSED intakes + referenced review evidence.

## Planner decision 2026-10-04
1. "Local-only. gc never deletes tracked artifacts or records [...] Retention = age-based clean-up of the LOCAL quarantine/review dirs only (dry run by default, `--delete` opt-in, as gc does today). Add a dry-run-only report line naming tracked artifacts that no committed release candidate references, saying 'kept: tracked history, never deleted'."
2. "No new roots record now. [...] Retained releases = every committed release candidate under manifests/candidates, derived, not declared. 'Evidence pins' = a PASSED intake that is un-adopted and younger than N days, or one referenced by an adoption/review record. Write in store_contract.md: if gc ever gains a deletion kind for tracked objects, a typed roots record becomes required first, and it needs its own ticket."
3. "Under Profile A, 'what a client may still hold' is a deployment fact (which frontend builds are live), not a store fact [...] Don't model it in the store. Record it as a deployment-level item that the M6 charter (ticket 5) declares: 'builds that may still be in use, default only the current one'."

## Out of Scope
- A real deployment or any CI/CD change; the normal Live Map; `src/`.
- Signing (D9 stands).

## Acceptance Criteria
- [x] Retention row approved by the user, or kept `UNSET` with a new stated reason the user accepted.
- [x] `gc` tests: a young PASSED intake and anything an adoption/review record references are protected, an old one and its review export are listed, tracked state is never listed or removed (mutants: drop the age guard, drop the reference guard; each fails a test); dry run is the default; the dry-run report names unreferenced tracked artifacts and deletes nothing.
- [x] Rollback drill tests for the three combinations pass in the harness; mutant "accept a mixed snapshot" fails.
- [x] The rollback/recall owner is recorded as the user's answer, or left explicitly unnamed.
- [x] `store_contract.md` states the rule for future tracked-object deletion; `AM-C09` is recorded as judged in the planner's terms.
- [x] `tests/visual_assets/` (scoped, 2 GB cap) and frontend tests pass; scoped eslint clean; boundary/isolation tests green.

## Related Tickets
- TCK-20261003-VISUAL-ASSETS-BUDGETS (done), TCK-20261004-VISUAL-ASSETS-PILOT-TERRAIN-TILE

## Related Docs
- docs/assets/budgets.md, docs/assets/store_contract.md (gc), docs/assets/surface_rehearsal_result.md (W09, C06, C09)
- docs/architecture/visual_asset_foundation_adr.md (D8, D9)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261003-VISUAL-ASSETS-BUDGETS/

## Related Code Areas
- visual_assets/store/ (gc, release), tests/visual_assets/, frontend/src/visualAssets/

## Assumptions / Open Questions
- Which frontend builds may still be in use is a deployment fact for the M6 charter (ticket 5), not modelled here.

## Implementation Notes
Retention approved by the owner: `MAX_UNADOPTED_INTAKE_AGE_DAYS = 30` (rule R0), rollback/recall owner named "nhan (owner)", both by blocking question, 2026-10-04. `gc` stays local-only per the planner decision; `tracked_unreferenced()` is report-only.
The test that pinned the retention row to UNSET was updated to the new truth (this ticket's purpose). Existing `gc` tests pin `now` to 2026-01-02 because `make_intake` stamps intakes 2026-01-01. Details and numbers: `docs/assets/retention_and_rollback.md`.

## Test Summary
gc tests 17 passed; four gc mutants and the mixed-snapshot mutant each fail a named test; frontend `src/visualAssets` 86 passed; scoped eslint and tsc clean; `pytest tests/visual_assets tests/docs tests/architecture tests/static` 1448 passed, 2 skipped, 1 xfailed (2 GB cap). A first run failed `test_library_code_never_reads_the_clock` (library `gc` imported `datetime`); fixed by passing a cutoff timestamp from the CLI, not by touching the test.

## Files Changed
- visual_assets/store/{gc,config,cli}.py; tests/visual_assets/store/unit/test_gc.py, tests/visual_assets/test_budgets_parity.py
- docs/assets/{budgets,store_contract}.md, docs/assets/retention_and_rollback.md (new)
- frontend/src/visualAssets/__tests__/{rollbackDrill.test.ts,pilotHelpers.ts,pilotScene.test.ts}

## Completion Summary
The last unset U-05 row is approved; `gc` has an age rule and a tracked-history report and still never deletes a tracked object; the rollback drill covers new/old client and release combinations, a recall and a mid-load switch. Nothing is deployed.
