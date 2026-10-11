---
status: active
layer: ai
authority: P2
audience: agent
tags: [ai, process-improvement, governance]
---

# Lead board

Cross-domain view kept by `lead-planner`. **Advice only**: the owner sets planner queues, and the lead never
dispatches, reorders a queue or approves anything. Rows are added by the lead. First status pass: 2026-10-11 at `main` 9a9058808, from the replies of the live planners on this host (asset, codebase, perf) and from repo/issue state for the seats that were not live (rpg, testing, agent-working).

| epic or batch | owner role | state | depends-on | blocked-by | lead's recommended next step | owner decision needed (y/n) |
|---|---|---|---|---|---|---|
| perf M2 (11 tickets; T02b, T07, X1, T05, T04 and T03 done) | perf-planner | in delivery, 6/11 | rpg hunting batch (T08 reruns); testing `baseline_change_policy.md` due 2026-10-13 (not blocking: T05b follows `rpg_gate_baseline_format.md` meanwhile) | T08 only: rpg hunting batch + perf spawn-collision fix; T06 runs last | implementer opens one PR each, in order: PERFBUDGET-RETIRE, T05b (cherry-picks the T03b ticket commit), T03b, spawn-collision; testing-planner reviews T03b by comment | y: merges; confirm the PERFBUDGET-RETIRE `session_roles.yaml` owns-diff; possibly a new §5 threshold if the CI-runner recalibration moves it off 1.40 |
| import-linter flip (+ mypy `==2.1.0` pin), python-code-craft-structure | codebase-planner | BLOCKED (soak) | soak ends 2026-10-19T13:40Z; rpg's answer on condition 3 (phase19) | time only | at 10-19T13:40Z check rpg condition 3, then dispatch the batch; re-check `test.yml` on ubuntu-26.04 from 10-19 to 11-19 | y: make Import contracts blocking in Code health; probe PR with an injected break; push/PR/merge |
| visual assets (last: VISUAL-ASSET-SLICES, merged #499) | asset-planner | idle | rpg core landing (live-app activation of slices/atlases/animation, Live Map glyph) | none | wait for the owner to name the next asset batch (parked: Git LFS, raised limits, self-hosted runner, new asset kinds) | y: name the next batch; confirm `rpg-asset-planner` as asset-planner's worktree (the manifest says main checkout) |
| SimQ grade anchors red on main (#390, slow regression) | testing-planner (#390); rpg-planner (per-anchor rebaselines) | open, tracked | rebaseline tickets per anchor (#390 maps each one) | none known | rpg-planner: close or rescope `SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED` (#511) | n |
| parity-ledger paydown epic + hotfix BASELINE-COMPARISON-FLOW-TEST-WALL-CLOCK-DEPENDENT (from #485) | rpg-planner (other host) | not reported this pass | none known | none known | status-request when rpg is live | n |
| Epic E session layer: E2 `fleet.py`, E3 cross-host heartbeat, E5 measurement, E6 stack registry/ADR/drift check (E1 and E4 done) | agent-working-planner (seat unstaffed) | waiting for a planner | none | unstaffed seat | staff agent-working-planner to scope E2/E3/E5/E6; E6 seed review (stack items) is lead's input | y: staff the seat |
| 5 idle agent-working epics: gate-override-ledger, hand-closure-real-time-and-cost, progression-starvation-chain, python-code-craft-structure*, ticket-path-record | agent-working-planner | stale (>5 days idle) | none | unstaffed seat | close or re-sequence each (*python-code-craft-structure is live through the codebase flip above; idle only in folder mtime) | y |
| agent-working hygiene: retro overdue (48 runs vs 5); `test_handover_transit` isolation + memory split (#513); u24desktop transit bundle unimported | agent-working-planner / agent-working-implementer (u24desktop) | open | none | unstaffed seat; the bundle needs that host's implementer | run `/agent-monitoring-retro`; fix #513 | y: memory-dir merge (#513) |
| residue cleanup | owner | pending | none | owner action | see "Residue awaiting the owner" below | y |

## Residue awaiting the owner

Squash-merged leftovers. **Never push any of these again.** Each one was confirmed by its owning planner on 2026-10-11 (this host only; the other host may differ).

- perf: worktrees `rpg-wt-perf-m2-plan`, `rpg-wt-perf-m2-tickets`; branches `perf-m2-detailed-plan` (#475), `perf-m2-contract-tickets` (in #483), `perf-planner-m2-review` (#486), `perf-planner-m2-followups` (#496).
- asset: local branch `visual-asset-slices` (#499).
- repo root (main checkout, untracked since 10-03): `agent-monitoring/`, `stored_artifacts/` (27 files, old pre-`agent-working/` layout).
