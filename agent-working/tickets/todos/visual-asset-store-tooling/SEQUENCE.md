# Implementation Sequence — visual-asset-store-tooling

`TCK-20261010-EPIC-VISUAL-ASSET-STORE-TOOLING` is the epic-tier parent. Built by `asset-implementer` on branch
`visual-asset-store-tooling` (off origin/main 312fbd78c, worktree `/home/vboxuser/Work/rpg-aseprite-mcp`), one commit per
ticket, each reviewed by `asset-planner`. No `src/`, no `.github/`. One PR when the planner says ready and the user
authorizes; merge needs the user's `--admin`.

## Order

1. `TCK-20261010-VISUAL-ASSETS-STORE-LOCK-AND-DELETION-LOG`: store lock + deletion log + kill-mid-publish tests;
   **planner approves the design, owner approves the ADR D24 text, before code**; security review. FIRST (touches every
   writing command; later children build on the lock).
2. `TCK-20261010-VISUAL-ASSETS-PNG-DECODER-SPEEDUP`: pure-Python decoder speedup, bounds unchanged; security review.
3. `TCK-20261010-VISUAL-ASSETS-RELEASE-BYTE-REPRODUCIBILITY`: rc rebuild byte check (local) + export-twice/chunk test (CI).
4. `TCK-20261010-VISUAL-ASSETS-ASEPRITE-LOCAL-PROOF-RECORD`: committed local proof record + CI staleness test;
   **planner approves guarded paths + record shape, owner approves the D10 addendum text**. Needs 3.
5. `TCK-20261010-VISUAL-ASSETS-RUNTIME-ATLAS-EXPORT`: opt-in atlases, not wired. After 3.
6. `TCK-20261010-VISUAL-ASSETS-PALETTE-AS-DATA`: terrain palette, GPL exports, advisory membership lint.
7. `TCK-20261010-VISUAL-ASSETS-ANIMATION-METADATA-FIELDS`: **planner approves field placement first**; registry
   budget review (owner approves any new bound) only if a per-key field is needed.
8. `TCK-20261010-VISUAL-ASSETS-EVIDENCE-CAPTURE-REAL-BUNDLE`: **planner clears any file outside asset-owned frontend
   paths with `rpg-planner` before code** (may move earlier once cleared).
9. `TCK-20261010-VISUAL-ASSETS-STORE-TOOLING-DOCS-AND-CLOSE`: docs drift, hardening research moved to stored_artifacts,
   snapshots, close.

## Decisions

- Owner, 2026-10-10 (blocking questions): next batch = store tooling only, all four groups (release safety, evidence
  capture, palette as data, the parked no-consumer items). Then: reverse D18 -> new D24 (store-wide lock that refuses a
  second writer, append-only deletion log, kill tests); keep D10 with a committed local proof record + CI staleness check
  (no self-hosted runner); decoder speedup in pure Python only, no new dependency, bounds unchanged.
- Planner: the lock refuses instead of waiting (agents must not hang); atlases and animation metadata do not change the
  runtime manifest or reach the client; animation fields default to per-artifact, not per-key, so the registry budget
  (90% used) is not touched unless the design proves it must be.
- Still parked: Git LFS, slices/9-slice/pivots, client use of atlases/animation, raising bounds, self-hosted runner.

## Status

OPEN (2026-10-10): filed by the planner; not started.
