# Implementation Sequence — visual-asset-terrain-set-review

`TCK-20261005-EPIC-VISUAL-ASSET-TERRAIN-SET-REVIEW` is the epic-tier parent and is not implemented directly.

All children are built by `asset-implementer` on branch `visual-asset-terrain-set-review` (fresh off origin/main), one
commit per ticket, each reviewed by `asset-planner`. Touches `visual_assets/`, `tests/visual_assets/`, `frontend/`,
`docs/` and `agent-working/` only; no `src/`. One PR for the batch, opened only when the planner says it is ready and the
user authorizes the push; merging needs the user's `--admin`.

## Order

1. `TCK-20261005-VISUAL-ASSETS-SET-COLOUR-VISION-RULE` (P2, standard): DONE. Set check + rule + whole-map scene criteria,
   user-approved and committed before any terrain-v1 file changed; baseline FAIL (30 pair-visions).
2. `TCK-20261005-VISUAL-ASSETS-TERRAIN-V1-COLOUR-VISION-REDRAW` (P2, standard): DONE. All 22 drafts re-tinted onto their
   fills (planner decision A, 2026-10-05); set check PASS (0/1012), nothing adopted.
3. `TCK-20261006-VISUAL-ASSETS-TERRAIN-BORDER-CONTRACT` (standard): terrain priority order, `crisp` set and C6 (borders)
   added to W03-SET, user-approved before any art; pure compositor `borderOverlays`; `border.*` mask key family with
   ADR row and store_contract; decorative fallback; 4 px cap.
4. `TCK-20261006-VISUAL-ASSETS-TERRAIN-BORDER-MASKS` (standard): draw the masks, keep them in `terrain-v1` (one
   `adopt-set` covers tiles and masks), borders on/off toggle on the preview page, evidence sheets.
5. **Owner gate, no ticket (done 2026-10-05T18:17:03Z: the user adopted `terrain-v1`, set adoption `sa-f4c541f25f112221`):** the user reviews the whole map WITH borders on the preview page once, then runs
   `adopt-set` themselves (it covers tiles and masks). The implementer hands them the exact command (absolute venv
   interpreter path) and waits. If the user does not adopt, the batch stops here: child 6 stays open and the PR carries
   children 1-4 only, by the user's choice.
6. `TCK-20261006-VISUAL-ASSETS-RECORD-TERRAIN-SET-ADOPTION` (standard, repair; added 2026-10-06 after the user adopted): commit the user's adoption files byte for byte and re-point the seven guards that described
   the pre-adoption catalog, pinned to exact facts, never loosened; docs state that no release candidate covers the 31 new slots.
7. `TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN` (P2, standard; moved here from todos/ root, re-scoped): M5 rerun on the
   adopted set (W03-SET includes C6 and a missing-mask fallback check), record, refresh handoff snapshots, close the batch.

Strictly sequential.

## Decisions

- User, 2026-10-05 (blocking questions): next batch is the M5 rerun; fix the set first, then rerun. Asset pause lifted
  for this batch only.
- User, 2026-10-06 (blocking question, after reviewing the preview page): terrain borders look wrong (textures stop abruptly along
  square, stair-stepped cell edges). Chosen: (a) Wesnoth-style layered fringes, a priority per terrain, the higher terrain drawing a
  ragged fringe of its own texture onto the lower, one shared mask set for every terrain, no per-pair art; (b) hold `adopt-set`
  until borders exist; the user reviews the whole map with borders once, then adopts.
- Forest's adopted slots are never redrawn; a failing pair with forest is fixed on the other tile.
- The rule's thresholds are the user's (child 1 asks). Gates are never reworded to pass; a result is information.
- Each ticket was written before the previous one was built. Before starting a ticket, re-check it against what
  actually landed; where they disagree, tell the planner instead of guessing.

## Status

DONE (2026-10-06): all children done and recorded; the user adopted `terrain-v1` (tiles and masks) on 2026-10-05T18:17:03Z; the M5 rerun ran on `pilot/rc-0005` (W03-SET PASS, W07 PASS, W05 gate and overall M5 INCONCLUSIVE, unchanged). Branch `visual-asset-terrain-set-review` is not pushed; the user decides.
