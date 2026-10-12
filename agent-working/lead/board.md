---
status: active
layer: ai
authority: P2
audience: agent
tags: [ai, process-improvement, governance]
---

# Lead board

Cross-domain view kept by `lead-planner`. **Advice only**: the owner sets planner queues, and the lead never
dispatches, reorders a queue or approves anything. Rows are added by the lead. Second status pass: 2026-10-12 at `main` 6ba9083ef (first pass 2026-10-11 at 9a9058808), from the replies of the live planners on this host (asset, codebase, perf) and from repo/issue state for the seats that were not live (rpg, testing, agent-working).

| epic or batch | owner role | state | depends-on | blocked-by | lead's recommended next step | owner decision needed (y/n) |
|---|---|---|---|---|---|---|
| perf M2 (11 tickets; T02b, T07, X1, T05, T04, T03, PERFBUDGET-RETIRE #512 done; T05b in PR #525) | perf-planner | in delivery, 7/11 (8 when #525 lands) | rpg hunting batch (T08 reruns); testing `baseline_change_policy.md` (not blocking T05b) | T08: rpg hunting batch + perf spawn-collision fix; T06 runs last | implementer, one PR each from fresh main: T05b (cherry-picks fc028db8a), T03b, spawn-collision; PR numbers go to the lead for review and merge; testing-planner also reviews T03b | y: merges; possibly a new §5 threshold from T03b; T06 carries a P1 contract edit |
| import-linter flip, python-code-craft-structure | codebase-planner | BLOCKED (soak) | soak ends 2026-10-19T13:40Z; rpg's answer on condition 3 (phase19) | time only | at 10-19T13:40Z check rpg condition 3, then dispatch; watch `test.yml` on ubuntu-26.04 to 11-19. mypy pin already landed separately (#524) | y: make Import contracts blocking; probe PR with an injected break; push/PR/merge |
| shared knowledge-search server (#520, TCK-20261012-SEARCH-MCP-SHARED-MODEL) | codebase-planner (cross-domain; agent-working seat unstaffed) | implemented, fixes in progress | none | none | fix the reload race (one reference swap) and the `--db` key check, then PR to the lead. Measured: 9 sessions 1.22 GB vs ~5.7 GB, 5/5 identical results | y: push, merge |
| visual assets: B real-art proof (merged #521) → D sample Live Map (merged #526) → terrain variants (G4, ~14 tiles + registry budget review; owner pick 10-12) → A entity markers | asset-planner | D merged (#526); terrain variants next | owner decided 10-12: V2 names canonical (#523) | none | asset files terrain variants: registry budget review → V2-name aliases → ~14 variant tiles; then A with V2 kind names | y: merges |
| Live Map terrain colours (#523) | rpg-planner (other host) | owner decided the shape 10-12; not yet scoped | none | rpg seat not live on this host | rpg: one deduplicated V2 terrain vocabulary in the manifest; the client colours by name; regression test with two worlds of different terrain sets | n (decided) |
| rpg queue: #511 (SIMQ anchors close/rescope), #515 (redis pin), #519 (asset data, read-only) | rpg-planner (other host) | filed, unanswered | none | rpg seat not live on this host | answer when rpg is live; none gates delivery here | n |
| SimQ grade anchors red on main (#390) | testing-planner; rpg-planner (rebaselines) | open, tracked | per-anchor rebaseline tickets | none known | #511 closes the duplicate ticket | n |
| Epic E session layer: E2 `fleet.py`, E3 heartbeat, E5 measurement, E6 stack registry/drift check | agent-working-planner (unstaffed) | waiting for a planner | none | unstaffed seat | staff the seat; E6 seed review is done (`stack_seed_review.md`) | y: staff the seat |
| agent-working backlog: retro overdue (57 runs vs 5); W41 close-week (438 shards); 5 idle epics; #517 host literals; u24desktop transit bundle | agent-working-planner / -implementer | open | none | unstaffed seat; the bundle needs that host's implementer | staff the seat, then: retro, `make agent-monitoring-close-week WEEK=2026-W41`, close or re-sequence the idle epics | y: staff the seat |
| residue cleanup | owner | pending | none | owner action | see below | y |

## Residue awaiting the owner

Squash-merged leftovers on this host. **Never push any of these again.** Each owning planner confirmed its own items (2026-10-11/12).

- codebase: worktrees `rpg-knowledge-lock-transit-test` (#518), `rpg-mypy-dev-pin` (#524) with their branches, local + remote; worktree `rpg-codebase-implementer` (no commits of its own; its 2 W41 shard lines were carried into #524).
- perf: the implementer's merged branches `perf-m2-{batch-1-record-and-variants, x1-vacuous-gate, t03-tripwire-paired, t04-capacity-run, t05-baseline-lifecycle, perfbudget-retire}`, local + remote.
- asset: branches `visual-asset-slices` (#499) and `visual-asset-real-art-proof` (#521).
- repo root (main checkout, untracked since 10-03): `agent-monitoring/`, `stored_artifacts/` (27 files, old pre-`agent-working/` layout).
