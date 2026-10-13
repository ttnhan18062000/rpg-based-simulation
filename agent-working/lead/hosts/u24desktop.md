---
status: active
layer: ai
authority: P2
audience: agent
tags: [ai, process-improvement, governance]
---

# Host page: u24desktop

Written only by `lead-planner-u24`, the lead seat on host `u24desktop` (`u24desktop-Virtual-Machine`).
`lead-planner` (host ubuntu) reads it and folds it into `board.md`; it never edits this page, and this seat never edits
`board.md`. **Advice only**: neither lead dispatches, reorders a queue or approves anything. Status requests go only to
sessions on this host (`docs/guides/cross_session_messages.md`).

Last status pass: 2026-10-13 (rpg, testing and agent-working planners reported).

## Sessions on u24desktop

| role | branch or ticket | state | blocker | next step | last status time |
|---|---|---|---|---|---|
| rpg-planner | PR #536 `rpg-single-pr` (21 tickets) | CI green (24/24, head 075c9404b), mergeable; lead reviewed the compose redis pin (no blockers) | user merge in GitHub UI (branch policy) | after merge: testing #531 rebases and re-anchors | 2026-10-13 |
| rpg-implementer | #536 CI fixes | working | none | then held-gatherer fix (2.120) | 2026-10-13 (via rpg-planner) |
| rpg-implementer-2 | #536 CI fixes | working | none | then RunLedger metric module | 2026-10-13 (via rpg-planner) |
| rpg-implementer-3 | live map | working (colours done) | none | D69 authored world and places | 2026-10-13 (via rpg-planner) |
| testing-planner | PR #531 `testing-anchors-audit` | reviewed, staged; DO NOT MERGE before #536 | #536 merge (user); user OK pending to delete 4 merged testing worktrees (~1.6 GB) | after #536: dispatch testing-implementer to rebase #531, rerun stage 2, re-anchor, slow-regression | 2026-10-13 |
| agent-working-planner | none (branch `agent-working-planner-idle` @ c35ebf475) | idle; batch 3 #522 merged | user: stale handover note (edit denied); user: graphify-out snapshot cleanup (~900 MB, commands given) | wait for user/designer work; delete remote branch `session-layer-followups-batch-3` (user ask) | 2026-10-13 |
| agent-working-implementer | none | idle | none | sync off batch-3 branch | 2026-10-13 (via agent-working-planner) |
| testing-implementer | PR #531 | idle | waits on #536 merge | re-anchor when dispatched | 2026-10-13 (via testing-planner) |

## Overlap and conflicts

Work that duplicates or blocks another session, on either host. One line each: what, which sessions, since when, what would
resolve it (a recommendation to the owner, not an instruction).

- #531 depends on #536 (testing-planner, rpg-planner), since 2026-10-13: merge #536 first, then #531 rebases and re-anchors.
- #529 (perf): testing-planner review lists 3 blocking items (base arm `ModuleNotFoundError: src`, no measured pair) although CI is green; next move is perf's. Since 2026-10-13.
- DevOps plan amendment proposed (`docs/architecture/devops_plan_amendment_proposal.md`, lead-planner-u24, owner-requested): awaits lead-planner review and owner decisions. Since 2026-10-13.
- #536 adds `grass_cover`, `raw_meat` to the catalog and changes two sample-map evidence PNGs (rpg-planner); how cover draws is asset-planner's call, and asset-planner is not live on this host. Since 2026-10-13.
