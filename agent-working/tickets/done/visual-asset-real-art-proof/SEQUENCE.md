# Implementation Sequence — visual-asset-real-art-proof

`TCK-20261011-EPIC-VISUAL-ASSET-REAL-ART-PROOF` is the epic-tier parent. Built by `asset-implementer` on branch `visual-asset-real-art-proof` (off origin/main 9a9058808; planning commit made in
asset-planner's worktree `/data/vboxuser/Work/rpg-asset-planner`, upstream unset; the implementer checks the branch out in its own worktree), one commit per
ticket (child 2 and 3 may need two), each reviewed by `asset-planner`. No `src/`, no `.github/`, no `frontend/`. One PR when the planner says ready and the user
authorizes; merge needs the user's `--admin`.

## Order

1. `TCK-20261011-VISUAL-ASSETS-REAL-ART-KEYS`: three optional keys + both handoff snapshots. **Planner approves the key text before the commit.** FIRST.
2. `TCK-20261011-VISUAL-ASSETS-REAL-ART-DRAFTS`: draw, hand off, intake PASS, measure. **Owner adopts (blocking question).** Needs 1.
3. `TCK-20261011-VISUAL-ASSETS-REAL-ART-RELEASE-PROOF`: build, rc-0009 = 70 + 3 **on the owner's answer**, `export-runtime --atlas --slices` proof. Needs 2.
4. `TCK-20261011-VISUAL-ASSETS-REAL-ART-BUDGETS-AND-CLOSE`: budgets.md measurements, Git LFS + raise-bounds verdicts, docs, closure (`batch_hand_close`). Needs 1-3.

## Decisions

- lead-planner, owner-authorized, 2026-10-11: candidate B chosen. Conditions: (1) any bound exceeded -> STOP, its own owner question, no bound change in
  this batch; (2) adopt and rc approval stay with the owner and appear as explicit asks in the PR body; (3) measured sizes against every bound in
  budgets.md, fits included, and the closing summary names the Git LFS and raise-bounds questions with a verdict each; (4) the stale session_handoff
  refresh belongs in this PR.
- Planner: keys `ui.panel_frame` (24x24, 1 frame, 9-slice), `fx.selection_ring` (32x32, 8 frames, pivot), `fx.campfire` (64x64, 16 frames, pivot), all
  `optional: true`, `decorative`, `fallback: none`; keys only, no registry schema field. `fx.campfire` is the heaviest realistic case we would draw
  (16 frames = `MAX_ANIMATION_FRAMES`), the measurement the D2 trigger needs. Owner may overrule the families.
- Planner: no store/drawing code change; a pipeline gap = STOP and report. The build exports frame 1 only (`build/exportconfig.py:53`): recorded as a
  fact for activation, not changed.
- Still parked: activation (incl. client use of slices/atlases/animation, Live Map icon glyph) until the RPG core lands, Git LFS, raising bounds,
  self-hosted runner. Next batch (candidate A, entity markers) starts with the `MAX_REGISTRY_BYTES` budget review. Candidate C waits for rpg-planner.

## Status

DONE (2026-10-11): all four children committed and reviewed by asset-planner; closed by hand (`batch_hand_close`). Awaiting the user's push/PR decision.
