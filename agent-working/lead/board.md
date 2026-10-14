---
status: active
layer: ai
authority: P2
audience: agent
tags: [ai, process-improvement, governance]
---

# Lead board

Cross-domain view kept by `lead-planner`. **Advice only**: the owner sets planner queues, and the lead never
dispatches, reorders a queue or approves anything. Rows are added by the lead. Third status pass: 2026-10-14 at `main` 6adb134ea (second 2026-10-12 at 6ba9083ef, first 2026-10-11 at 9a9058808). Host ubuntu rows (asset, codebase, perf) come from those planners' replies. Since 2026-10-13 the rpg, testing and agent-working seats run on host u24desktop under `lead-planner-u24`; their rows are folded in from its host page (`hosts/u24desktop.md`, first pass carried in PR #537) and from repo/issue state.

| epic or batch | owner role | state | depends-on | blocked-by | lead's recommended next step | owner decision needed (y/n) |
|---|---|---|---|---|---|---|
| perf M2 (11 tickets; T05b #525 done; T08 canonical reruns in progress) | perf-planner | in delivery, 8/11 | #544 for the mixed_200 reruns; #529 merge before the T06 calibrations | #529: testing-planner re-review (#534 reopened); T06: 3 or more measured CI calibrations (1 so far) | merge #544 after its re-sync; T08 PR carries a before/after baseline table; 4 records stay PENDING-NOISY (spread looks intrinsic, not host load); run 2 A/A calibrations only after #529 merges | y: merges; T08 baselines; slowdown option (i) bigger profile, (ii) perf-debt investigation, (iii) both; lead recommends (ii) |
| perf finding: tick cost grew a lot since May (idle_100 about 50 ms vs 1 ms, strategic_100 about 500 ms vs 13 ms; 4 of 13 baseline scenarios run non-NORMAL) | perf-planner with rpg-planner | found 2026-10-13, not scoped | owner's choice of option | owner decision | if (ii): a joint perf and rpg investigation of the top phases (cooperation, advancement); a bigger budget only if the cost proves legitimate | y: pick (i), (ii) or (iii) |
| import-linter flip, python-code-craft-structure | codebase-planner | BLOCKED (soak) | soak ends 2026-10-19T13:40Z; 0 broken and 0 stale contracts on main (met by #546) | #547: rpg answer on 4 kernel lazy imports; testing OK for the phase19 scope split | on 10-19 flip every other contract; the phase19 test and its 4 ignores stay unchanged until rpg answers | y: make Import contracts blocking; required check after main produces the name; push and merge |
| DevOps plan: ADR D1-D10 accepted 10-12; amendment #537 proposed 10-13 (6 steps, platform domain) | lead-planner reviews; platform-planner delivers (seat registered #539, not yet staffed) | proposal under review | #537 revisions; owner decisions 1-3 | lead review asks (budget alarm is not a cap; no kind on the 11 GB host; devops-s1 named as step 1 start); #537 CONFLICTING | lead-planner-u24 revises #537; owner decides; staff platform seats (u24desktop suggested for memory); on acceptance the lead adds the ADR back-link | y: decisions 1-3 and where to staff platform |
| devops-s1 (compose observability profile, publish-images workflow, roles line) | codebase-implementer, moving to platform | PARKED, local 7e604d3fa, not pushed (owner accepted local-only) | #537 acceptance and platform seats | platform seat unstaffed | platform-planner adopts it as step 1; T1 and T2 carry over; T3 is redone as a platform owns line | y: via #537 |
| visual assets: terrain variants (merged #545, rc-0010) then batch A map markers | asset-planner | A filed (local 16fe7012c): child 1 budget and key design in progress | child 3 (entity markers) gated on rpg #523 and #548 | rpg seats on u24desktop | children 1 and 2 now; if child 3 is still gated when child 2's set is adopted, the owner chooses objects-only | y: silhouettes and adopt-set; push and merge |
| rpg: #536 merged (21 tickets); D69 world and places, live map colours (#523), held-gatherer fix | rpg-planner (u24desktop) | in delivery | none | none known | answer #547 (kernel imports), #548 (entity names for asset), #542 (perf --entities after D69); close #511 and #515 when convenient | n |
| testing: #531 grade anchors under audit_mode; #529 re-review | testing-planner (u24desktop) | #531 CONFLICTING, can rebase now that #536 merged | #536 (merged) | none | rebase and re-anchor #531; re-review #529 via #534; answer #547's scope split before 10-19 | y: merges |
| SimQ grade anchors red on main (#390) | testing-planner; rpg-planner (rebaselines) | open; T08's evaluate_simq run saw 130 of 630 pillars REGRESS | #531 | none | #531 re-anchors; #511 closes the duplicate ticket | n |
| agent-working: Epic E (E2, E3, E5, E6); retro overdue (63 runs); W41 close-week (438 shards); 5 idle epics; #517 | agent-working-planner (u24desktop, idle) | seats staffed 10-13, idle | none | none | run the retro and `make agent-monitoring-close-week WEEK=2026-W41`; close or re-sequence the idle epics; pick up E6 | n |
| machine resources, host ubuntu | lead-planner (owner grant 2026-10-13) | managed | none | none | heavy runs one at a time under MemoryMax; quiet windows for timing runs; each session restarts its knowledge-search MCP (`/mcp` reconnect) to use the shared server (about 1.2 GB) | y: `/mcp` reconnect in each session |

## Cleanup done 2026-10-13 (lead, owner grant)

- Removed the merged worktrees and branches `knowledge-lock-transit-test` (#518), `mypy-dev-pin` (#524) and `search-mcp-shared-model` (#527).
- Deleted 28 local and 65 remote branches whose head equals their merged PR head. Names and SHAs are in `~/.claude/cleanup-backup-20261013/` on host ubuntu.
- Docker: removed the old `rpg-search-server` image (2.16 GB), orphan volumes and the build cache. The root disk went from 73 % to 56 %.

## Residue awaiting the owner

**Never push any of these again.**

- Repo root (main checkout, untracked since 10-03): `agent-monitoring/`, `stored_artifacts/` (27 files, 456 KB, old pre-`agent-working/` layout; NOT duplicates of `agent-working/` copies). Archive or keep.
- Remote branches: 43 of merged PRs whose head moved after the merge, and about 65 with no merged PR. Lead lists them on request.
- u24desktop: 4 merged testing worktrees (about 1.6 GB) and the graphify-out snapshot (about 900 MB), per `lead-planner-u24`.
