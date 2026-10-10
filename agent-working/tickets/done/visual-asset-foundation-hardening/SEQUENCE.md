# Implementation Sequence — visual-asset-foundation-hardening

`TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING` is the epic-tier parent. Built by `asset-implementer` on branch `visual-asset-foundation-hardening` (off
origin/main 48c9785c3, worktree `/home/vboxuser/Work/rpg-aseprite-mcp`), one commit per ticket, each reviewed by
`asset-planner`. No `src/`. One PR when the planner says ready and the user authorizes; merge needs the user's `--admin`.

## Order

1. `TCK-20261008-VISUAL-ASSETS-FIXTURE-GUARD-DECOUPLING`: guard decoupling (design approved by the planner before code). FIRST.
2. `TCK-20261008-VISUAL-ASSETS-MCP-WORKTREE-STORE-ROOT`: worktree-aware drawing server.
3. `TCK-20261008-VISUAL-ASSETS-REGISTRY-SAFETY-AND-LABEL-FIELDS`: safety class + fallback + label fields, verify rules (W02.7, W03.1, W06.3); **owner approves the labels**.
4. `TCK-20261008-VISUAL-ASSETS-SET-REVISIONS-AND-DRAFT-DROP`: set-level revisions + draft drop; **owner approves the design (ADR D22) before code**; security review.
5. `TCK-20261008-VISUAL-ASSETS-REVIEW-TOOLING-IN-STORE-CLI`: review tooling in the store CLI + tile_pixels fix.
6. `TCK-20261008-VISUAL-ASSETS-KEY-USAGE-REPORT`: key-usage report.
7. `TCK-20261008-VISUAL-ASSETS-FOUNDATION-DOCS-DRIFT`: docs drift, snapshots, close.

## Decisions

- Owner, 2026-10-08 (blocking questions): build all seven after the gap research (internal audit + external research in
  the epic's staging folder). Parked: animation/slice fields, visual-evidence capture, PNG decoder, real-Aseprite CI,
  crash tests, atlases, LFS.
- Planner: guard decoupling first, so child 3's registry change needs no new release candidate.

## Status

DONE (2026-10-09): children 1-7 merged as PR #471 (squash `0c3a5654b`, owner `--admin` merge).
