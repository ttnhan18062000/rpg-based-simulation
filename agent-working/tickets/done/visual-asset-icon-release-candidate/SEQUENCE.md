# Implementation Sequence — visual-asset-icon-release-candidate

One ticket, built by `asset-implementer` on branch `visual-asset-icon-release-candidate` (worktree
`/home/vboxuser/Work/rpg-aseprite-mcp`), reviewed by `asset-planner`. One PR when the planner says ready and the user authorizes.

## Order

1. `TCK-20261009-VISUAL-ASSETS-ICON-RELEASE-CANDIDATE`: bookkeeping drift (first commit), build the 36 adopted icons,
   assemble `pilot/rc-0008` after the user's answer, re-point guards by equality, docs.

## Decisions

- Owner, 2026-10-09: "start order as your recommendation" (planner order A bookkeeping -> B icon release candidate -> C
  fallback glyph). Planner: A is folded into this ticket's first commit (both values legal, cosmetic only); C is dropped
  for now because its only open part is the client-side glyph in the Live Map, which is parked with activation
  (owner, 2026-10-08).

## Status

DONE (2026-10-10): built by `asset-implementer`; commits `f7d3ffb98` (bookkeeping), `03fba7da3` (36 icons built), `e734ca7c9` (rc-0008 + re-anchored guards), `2eb885539` (manifest pins), `d0ef62c74` (docs), `1e916663d` (planner snapshot); the owner answered "Assemble rc-0008"; planner ruling (c) recorded in the ticket.
