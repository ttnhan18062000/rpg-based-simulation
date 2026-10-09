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

OPEN (2026-10-09): filed by the planner; not started.
