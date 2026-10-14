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

Last status pass: 2026-10-14 morning (rpg, testing and agent-working planners reported).

## Sessions on u24desktop

| role | branch or ticket | state | blocker | next step | last status time |
|---|---|---|---|---|---|
| rpg-planner | next PR `rpg-next` 56cefc2f4 (local, unpushed): #532 docs, ai_worker metrics, INFORMATION fix, gatherer, id fix, D71, D72, livemap/D69 | in delivery | user: #538 merge; user yes before the next PR opens; delete Lane A's finished worktrees | open the PR after D70 and a full local run; triage #547, #548, #542 after D70 | 2026-10-14 |
| rpg-implementer (Lane A) | D70 camps and raids | working (D71 done) | none | D70 measured alone | 2026-10-14 (via rpg-planner) |
| rpg-implementer-2 (Lane B) | D74 diet/species | working | none | 15 paired runs | 2026-10-14 (via rpg-planner) |
| rpg-implementer-3 (Lane C) | arena gold fix, then D75 terrain time | working (D72 done) | none | D75 | 2026-10-14 (via rpg-planner) |
| testing-planner | #531 `testing-anchors-audit` (re-anchor 64f339f98: 81/81 identical, 27 pairs held) | re-reviewing #529 (#534); agreed #547's scope split | #531 CONFLICTING after the latest main merges | user merges #531 once green | 2026-10-14 |
| testing-implementer | #531 | merging main into #531 | none | AC8 and the close after the merge | 2026-10-14 (via testing-planner) |
| agent-working-planner | batch 5 `harness-security-and-monitoring-analytics` | waiting on its implementer | none (later: user manifest diff and merge) | review the batch 5 PR; retro, W41 close-week, idle epics and Epic E stay queued until the user says | 2026-10-14 |
| agent-working-implementer | batch 5 branch `harness-security-monitoring-analytics` | working on tickets 1-3 | none | open the batch 5 PR | 2026-10-14 (via agent-working-planner) |
| platform-planner, platform-implementer | registered in #539 | not launched | user launches them | step 1 from devops-s1 once #537 decision 1 is accepted | 2026-10-14 |

## Overlap and conflicts

Work that duplicates or blocks another session, on either host. One line each: what, which sessions, since when, what would
resolve it (a recommendation to the owner, not an instruction).

- #531 waited on #536, which merged 2026-10-13 (b396080cc). It's now CONFLICTING from later main merges, and testing-implementer is merging main.
- #529 (perf): testing-planner review lists 3 blocking items (base arm `ModuleNotFoundError: src`, no measured pair) although CI is green; next move is perf's. Since 2026-10-13.
- DevOps plan amendment proposed (`docs/architecture/devops_plan_amendment_proposal.md`, lead-planner-u24, owner-requested): awaits lead-planner review and owner decisions. Since 2026-10-13.
- #536 adds `grass_cover`, `raw_meat` to the catalog and changes two sample-map evidence PNGs (rpg-planner); how cover draws is asset-planner's call, and asset-planner is not live on this host. Since 2026-10-13.
- #547 (import-linter flip on 10-19) needs rpg's answer on 4 kernel lazy imports. rpg plans to triage after D70, which could land close to the date; flagged to rpg-planner on 2026-10-14. testing agreed the scope split.
