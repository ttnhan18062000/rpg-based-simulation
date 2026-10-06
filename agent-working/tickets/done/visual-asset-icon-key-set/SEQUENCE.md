# Implementation Sequence — visual-asset-icon-key-set

`TCK-20261006-EPIC-VISUAL-ASSET-ICON-KEY-SET` is the epic-tier parent and is not implemented directly.

All children are built by `asset-implementer` on branch `visual-asset-icon-key-set` (fresh off origin/main, worktree
`/home/vboxuser/Work/rpg-aseprite-mcp`), one commit per ticket, each reviewed by `asset-planner`. Touches
`visual_assets/`, `tests/visual_assets/`, `frontend/`, `docs/` and `agent-working/` only; no `src/`. One PR for the
batch, opened only when the planner says it is ready and the user authorizes the push; merging needs the user's `--admin`.

## Order

1. `TCK-20261006-VISUAL-ASSETS-ICON-STYLE-DECISION` (P2, standard): research into `docs/assets/icon_research/`, ADR D20, `docs/assets/icon_style_guide.md`.
2. `TCK-20261006-VISUAL-ASSETS-ICON-KEY-FAMILIES` (P2, standard): the key set's `icon.*` keys with fallbacks (no variant axes, D17).
3. `TCK-20261006-VISUAL-ASSETS-ICON-PALETTE-AND-SHEET-RULE` (P2, standard): palette + sheet rule I1-I3, **user-approved and committed before any icon art**.
4. `TCK-20261006-LIVE-MAP-INTEGER-ZOOM-AND-PIXEL-ICON` (P2, standard): whole-number map zoom, `PixelIcon`. Independent; any slot before 5.
5. `TCK-20261006-VISUAL-ASSETS-ICON-KEY-DRAFT-SET` (P2, standard): draw `icons-key-v1`, preview page, rule result, hand the user the commands.
6. **Owner gate, no ticket:** the user reviews the preview page and runs `adopt-set` themselves. If not adopted, the
   batch stops here and the PR carries children 1-5 by the user's choice.
7. `TCK-20261006-VISUAL-ASSETS-RECORD-ICON-KEY-SET-ADOPTION` (P2, standard, repair; only if adopted): record the adoption, re-point guards, refresh snapshots, close.

Sequential except child 4.

## Decisions

- User, 2026-10-06 (blocking question): asset pause lifted **for icons only**; deep research first.
- User decisions (blocking questions, 2026-10-06, after the research): style **B + tier badges** (16x16 map glyph
  on a shared per-category plate, 24x24 panel icons, an 8x8 tier badge whose shape escalates, status frames that differ
  in shape with up/down chevrons); palette **terrain-v1 base + 3-4 step ramps + a small accent set**, checked sheet-wide;
  outside art **reference only** (recorded as title/author/source/licence), **no AI generators**; map zoom **snaps to
  whole-number scales**.
- Planner: a key set first (style lock), the rest of the icons and panel wiring in the next batch.
- Planner: tier and marker state are separate keys, not variant axes (D17 stands).
- The rule's thresholds are the user's (child 3 asks). Gates are never reworded to pass; a result is information.
- Before starting a ticket, re-check it against what actually landed; where they disagree, tell the planner instead of guessing.

## Status

DONE (2026-10-06): all children done and recorded. The user adopted `icons-key-v1` (set adoption `sa-b4bb738d6b5526f0`, 2026-10-06T15:21:47Z, 14 sources) after reviewing the preview page; no release candidate covers the 14 icon slots (rc-0006 has 34). Panel wiring and a candidate are the next batch. Branch `visual-asset-icon-key-set` is not pushed; the user decides.
