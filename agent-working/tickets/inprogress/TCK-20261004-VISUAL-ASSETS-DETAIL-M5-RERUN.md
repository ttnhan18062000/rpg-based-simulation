---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN
phase: open
date: 2026-10-04
tags: [architecture, testing, live-map]
---

# TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN

## Title
Rerun M5 against the adopted terrain-v1 set (whole map, forest variants mixed), record the results, close the batch

## Status
INPROGRESS

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Originally the last child of `TCK-20261004-VISUAL-ASSETS-TERRAIN-DETAIL-VARIANTS` (rerun only the M5 checks the
forest variants affect). DEFERRED by the user on 2026-10-04 until a full draft set is reviewed and adopted with
`adopt-set`, so one review covers a whole map. Moved on 2026-10-05 into `visual-asset-terrain-set-review` as its last
child and re-scoped against the adopted `terrain-v1` set. Starts only after the user has run `adopt-set` (see
`SEQUENCE.md`); re-check this ticket against what landed before starting.

## Scope
Updated 2026-10-06 after the re-check against what landed (asset-planner approved all nine points; the user approved the release by blocking question):
- **Release (the real path):** `rc-0004` already exists (forest only), so the new candidate is **`pilot/rc-0005`**: `build` of the 31 adopted sources (local Aseprite; tracked `generated/` artifacts), `release` with 34 entries on the same
  registry, `export-runtime` into a NEW fixture folder `frontend/src/visualAssets/__fixtures__/terrainset/` with its own "fresh export equals committed" test. **User approved all three steps on 2026-10-06 (blocking question).** Candidate only:
  nothing active or published; rc-0001..rc-0004 and the pilot fixture stay untouched. Consequence, in this ticket: the guards that pin generated artifacts and release candidates (`adopted_facts`, catalog integrity, store/server stdio tests)
  are re-pointed by equality; the commit message names the cause.
- **Pilot fixture left alone:** `pilot_colour_vision.tile_pixels()` takes the first PNG of the pilot export (a known fragility, not fixed here). The pilot forest rule reruns unchanged on the pilot fixture's plain/bush/tree; the rc-0005
  export's forest slots are shown to be byte-identical to the pilot's.
- **Whole-map scene:** new scene module on the runtime View (the predeclared 40 x 24 layout, markers per `AM5-W03-SET`, borders via `borderRender`), a dev-only page and a capture script shaped like the pilot/rehearsal ones and kept out of the
  normal Live Map build the same way; the layout test the criteria doc promises (every one of the 23 codes, a 3 x 3 patch per code, forest has plain, bush and tree). Captures: borders on and off, image and flat canvases, in the `AM5-W07` matrix
  (Playwright Chromium DPR 1 and 2, system Chrome DPR 1 and 2).
- **`W03-SET` review (the user's own judgement, not steered):** all captures are shown first. Then, per criterion C1..C6, one blocking question with the same neutral options in the same order every time (yes for all 23 terrains /
  no for some / unsure for some, free text naming the terrains), no "(Recommended)". The verbatim answers are recorded, then expanded per terrain. `unsure` with no `no` is INCONCLUSIVE; the rule (PASS only if all yes) is unchanged.
- **`W05`:** `AM5-S` on the adopted set (as measured, with its honest meaning: with mean == fill it is "no worse than the flat fills", closest pair-vision 0.857 dE) and the pilot forest rule unchanged; quote forest bush/tree's protan/deutan closeness
  to other tiles (informational). Never reworded.
- **Fallback checks:** each missing forest variant falls back to `plain`; a missing `plain` to the role fallback; each of the 22 terrain keys missing falls back to its flat fill (loop); a missing border mask gives today's hard edge (test and capture).
- **Rollback drill:** previous release = the rc-0004 export (forest only), new = the rc-0005 export; new client + old release (new keys unknown: flat fills, no borders) and old client + new release (extra keys ignored); never a mixed snapshot; record which
  client/release pairs were not run, if any.
- Record in `docs/assets/pilot_terrain_m5_results.md` (new dated section) with the overall verdict line; a note in the charter draft only if a gate's status changes. Gates are never reworded to pass.
- Unaffected checks listed as not rerun, with the reason.
- Close the batch: refresh `docs/assets/session_handoff/` from both asset handover notes (tell asset-planner when reaching this step); tickets to `done/`, the folder moved with `SEQUENCE.md`.

## Out of Scope
- Charter signing, AM-M6 authorization (the user's). Adoption (the user did it before this ticket).
- Redrawing (child 2); changing any rule or criterion.

## Acceptance Criteria
- [ ] `build` + `pilot/rc-0005` + `terrainset` fixture export done with the user's approval (2026-10-06); `verify` clean; the stdio, catalog and fixture guards re-pointed by equality; rc-0001..rc-0004 and the pilot fixture untouched.
- [ ] W03-SET includes C6 (borders, as approved by the user in `TCK-20261006-VISUAL-ASSETS-TERRAIN-BORDER-CONTRACT`) and the scene is judged with borders on.
- [ ] A fallback check (test and capture) shows that a missing border mask gives today's hard edge, never a blank or broken cell.
- [ ] The whole-map scene code lands with a test asserting the layout predeclared in `docs/assets/pilot_terrain_m5_criteria.md` (AM5-W03-SET): every one of the 23 codes present, a 3 x 3 patch per code, forest cells include plain, bush and tree. The W05 result is quoted together with forest bush/tree's protan/deutan closeness to other tiles (informational, not in the verdict).
- [ ] Each affected check rerun on the adopted set and recorded with its result; unaffected checks listed with the reason.
- [ ] User review of the whole-map scene recorded: every capture shown first; per criterion C1..C6 the same neutral options in the same order, verbatim answers plus the per-terrain expansion.
- [ ] Fallback checks per variant, per key (22) and for a missing mask; rollback drill with the client/release pairs run and not run recorded.
- [ ] Overall M5 verdict stated as measured (it may stay INCONCLUSIVE).
- [ ] Handoff snapshots refreshed; batch folder in `done/`.

## Related Tickets
- TCK-20261005-EPIC-VISUAL-ASSET-TERRAIN-SET-REVIEW (epic), TCK-20261005-VISUAL-ASSETS-SET-COLOUR-VISION-RULE,
  TCK-20261005-VISUAL-ASSETS-TERRAIN-V1-COLOUR-VISION-REDRAW, TCK-20261004-VISUAL-ASSETS-TERRAIN-DETAIL-VARIANTS (former
  parent, done), TCK-20261004-VISUAL-ASSETS-M5-RERUN-AND-M6-CHARTER

## Related Docs
- docs/assets/pilot_terrain_m5_criteria.md, docs/assets/pilot_terrain_m5_results.md, docs/assets/pilot_charter_am6.md,
  docs/assets/session_handoff/

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261004-VISUAL-ASSETS-M5-RERUN-AND-M6-CHARTER/

## Related Code Areas
- frontend/src/visualAssets/ (harness only), visual_assets/catalog/ (release, only if the user approves one)

## Assumptions / Open Questions
- Whether a new release is needed (asked of the user if yes).

## Implementation Notes
DEFERRED by the user, 2026-10-04 (blocking question): rerun M5 once a full draft set has been reviewed and adopted
(`adopt-set`), so one review covers a whole map. Moved out of the detail-variants batch.
Re-scoped 2026-10-05 by asset-planner after the user chose "fix the set, then rerun" (blocking question): moved into
`visual-asset-terrain-set-review`, scope widened from forest variants to the adopted whole set.

## Test Summary

## Files Changed

## Completion Summary
