# Implementation Sequence — visual-asset-terrain-set-review

`TCK-20261005-EPIC-VISUAL-ASSET-TERRAIN-SET-REVIEW` is the epic-tier parent and is not implemented directly.

All children are built by `asset-implementer` on branch `visual-asset-terrain-set-review` (fresh off origin/main), one
commit per ticket, each reviewed by `asset-planner`. Touches `visual_assets/`, `tests/visual_assets/`, `frontend/`,
`docs/` and `agent-working/` only; no `src/`. One PR for the batch, opened only when the planner says it is ready and the
user authorizes the push; merging needs the user's `--admin`.

## Order

1. `TCK-20261005-VISUAL-ASSETS-SET-COLOUR-VISION-RULE` (P2, standard): set check + rule + whole-map scene criteria,
   user-approved and committed **before any terrain-v1 file changes**; baseline measured.
2. `TCK-20261005-VISUAL-ASSETS-TERRAIN-V1-COLOUR-VISION-REDRAW` (P2, standard): redraw the failing drafts, re-measure.
3. **Owner gate, no ticket:** the user reviews `terrain-v1` on the preview page (`frontend/rehearsal-draft.html`) and
   runs `adopt-set` themselves. The implementer hands them the exact command (absolute venv interpreter path) and waits.
   If the user does not adopt, the batch stops here: child 4 stays open and the PR carries children 1-2 only, by the
   user's choice.
4. `TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN` (P2, standard; moved here from todos/ root, re-scoped): M5 rerun on the
   adopted set, record, refresh handoff snapshots, close the batch.

Strictly sequential.

## Decisions

- User, 2026-10-05 (blocking questions): next batch is the M5 rerun; fix the set first, then rerun. Asset pause lifted
  for this batch only.
- Forest's adopted slots are never redrawn; a failing pair with forest is fixed on the other tile.
- The rule's thresholds are the user's (child 1 asks). Gates are never reworded to pass; a result is information.
- Each ticket was written before the previous one was built. Before starting a ticket, re-check it against what
  actually landed; where they disagree, tell the planner instead of guessing.

## Status

Open (2026-10-05).
