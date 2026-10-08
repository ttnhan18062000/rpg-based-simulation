# Implementation Sequence — visual-asset-icon-set-v2

`TCK-20261007-EPIC-VISUAL-ASSET-ICON-SET-V2` is the epic-tier parent and is not implemented directly.

Built by `asset-implementer` on branch `visual-asset-icon-set-v2` (fresh off origin/main bc4f7553c, worktree
`/home/vboxuser/Work/rpg-aseprite-mcp`), one commit per ticket, each reviewed by `asset-planner`. Touches
`visual_assets/`, `tests/visual_assets/`, `frontend/src/visualAssets/` + `frontend/rehearsal-icons.html` (preview
only), `docs/` and `agent-working/`; never app components, never `src/`. One PR, opened only when the planner says it
is ready and the user authorizes the push; merging needs the user's `--admin`.

## Order

1. `TCK-20261007-VISUAL-ASSETS-ICON-V2-FAMILY-DECISIONS`: item-family mapping, rarity ladder, glyph choices (**user-approved first**).
2. `TCK-20261007-VISUAL-ASSETS-ICON-V2-KEYS-AND-RC`: all v2 keys at once; next release candidate (**user approval**).
3. `TCK-20261007-VISUAL-ASSETS-ICON-V2-SHEET-RULE-GROUPS`: v2 groups + 24x24 I1 threshold (**user's answer, before any art**).
4. `TCK-20261007-VISUAL-ASSETS-ICON-V2-DRAFT-SET`: draw `icons-v2`, preview, rule result, owner commands.
4b. `TCK-20261008-VISUAL-ASSETS-ICON-RECOGNISABILITY-CHECKS` (added 2026-10-08, user's choice "Fix the process now"): construction specs, reference study, blind recognition check, whole-sheet look-alike report.
4c. `TCK-20261008-VISUAL-ASSETS-ICON-V2-RECOGNISABILITY-REDRAW` (added 2026-10-08): run the checks on `icons-v2`, redraw what they flag (the sword included).
5. **Owner gate, no ticket:** the owner reviews and runs `adopt-set` in their own terminal.
6. `TCK-20261007-VISUAL-ASSETS-RECORD-ICON-V2-ADOPTION` (only if adopted): record, guards, snapshots, close.

Strictly sequential.

## Decisions

- User decisions (blocking questions, 2026-10-07, after PR #388 merged): the next icon batch is **draw only, no
wiring**: using adopted art in the live app is gated (AM-M6 is NO-GO until the owner signs its charter, and AM-M6
covers one forest tile only; HUD icons are broad rollout, beyond it). Families: **map locations (5), buildings +
classes (8), rarity badges (3), item families (~8)**.
- Planner: one key registration and one release candidate for the whole batch (rc-0006 lesson).
- Planner: no UI tab, advanced-class, per-item or per-effect icons (brainstorm section 15: an icon must beat text).
- Gates are never reworded to pass. Re-check each ticket against what landed; disagreements go to the planner.

- User, 2026-10-08 (at the owner gate): the weapon sword looks wrong; asked for the root cause. Planner: gates measure
  distinguishability, never recognisability (4 misreads in 36 icons passed every gate). User chose "Fix the process now" (4b, 4c).

## Status

DONE (2026-10-08): all children done and recorded (1-4, 4b and 4c before the owner gate, 5). The owner adopted `icons-v2` themselves (set adoption `sa-c9082d078b954f6b`, 2026-10-08T00:40:15Z, 22 sources); no release candidate covers an icon slot (rc-0007 has 34) and nothing is built or wired. Branch `visual-asset-icon-set-v2` is not pushed; the user decides.
