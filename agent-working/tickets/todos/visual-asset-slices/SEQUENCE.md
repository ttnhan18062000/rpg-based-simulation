# Implementation Sequence — visual-asset-slices

`TCK-20261010-EPIC-VISUAL-ASSET-SLICES` is the epic-tier parent. Built by `asset-implementer` on branch `visual-asset-slices` (off origin/main
cbfe372b0; worktree `/home/vboxuser/Work/rpg-aseprite-mcp`), one commit per ticket, each reviewed by `asset-planner`.
No `src/`, no `.github/`. One PR when the planner says ready and the user authorizes; merge needs the user's `--admin`.

## Order

1. `TCK-20261010-VISUAL-ASSETS-SLICE-SOURCE-FIELDS`: parser + contract + per-source storage + bounds + real-Aseprite parity test; **owner approves the ADR D25
   text before the commit is approved**; security review (hostile binary input). FIRST.
2. `TCK-20261010-VISUAL-ASSETS-SLICE-RUNTIME-EXPORT`: `export-runtime --slices` in artifact pixels. Needs 1.
3. `TCK-20261010-VISUAL-ASSETS-SLICE-DRAWING-TOOL`: drawing-tool slice op + handoff `slice_count`; **planner approves the op shape before code**. Needs 1; may run
   after or alongside 2.
4. `TCK-20261010-VISUAL-ASSETS-SLICES-DOCS-AND-CLOSE`: docs, parked lists, both session_handoff snapshots, ONE proof-record re-run after the last store/drawing
   edit, closure (`batch_hand_close`).

## Decisions

- Owner, 2026-10-10 (blocking questions): slices batch covers the store AND the drawing tool; bounds 16 slices per source,
  16 keys per slice; names 1..32 chars like animation tags.
- Planner: slices live per source revision (`SourceRecord.slices`, absent -> byte-identical), not in the registry,
  `ArtifactRecord` or runtime manifest (registry budget 90% used); geometry stored in source pixels, exported in artifact
  pixels (times the build scale), relative to the image, never an atlas; pivot inside the slice rect (edges inclusive);
  the drawing tool makes single-key slices only; slice user data ignored.
- Still parked: activation (incl. client use of slices/atlases/animation) until the RPG core lands, Git LFS, raising
  bounds, self-hosted runner, other asset kinds.

## Status

OPEN (2026-10-10): filed by the planner; not started.
