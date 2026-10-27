---
status: active
layer: ai
authority: P2
audience: agent
tags: [ai, process-improvement, governance]
---

# Lead board

Cross-domain view kept by `lead-planner`. **Advice only**: the owner sets planner queues, and the lead never
dispatches, reorders a queue or approves anything. Rows are added by the lead. Fourth status pass: 2026-10-27 at `main` 792a6b439 (third 2026-10-14 at 6adb134ea). Host ubuntu rows come from its planners' replies; host u24desktop rows are folded in from `lead-planner-u24`'s live answer of 2026-10-27 and its host page (`hosts/u24desktop.md`, last pass 2026-10-25 at 54b1dcf85, #749). Owner approvals are on #715.

## Since the 2026-10-14 pass

- **Merged 10-26 to 10-27:** #746-#757, #735 (PERF-M2-T06), #760 (five dead systems classes deleted, cited proof moved to the live paths), #761 (u24: W42/W43 close-week and retro), #762 (unknown craft recipe refused instead of raising; history snapshot query keeps one page and drops the nested graph).
- **Owner stop and resume:** the 10-26 stop (#715 6426468523) was lifted for u24 (6437025815) and then for ubuntu (6441204906, 2026-10-27).
- **Perf program:** M0 governance, M1 correctness and M2 contract are done. M3 (phase observability), M4 (baselines and Gate A), M5 (optimizations) and M6 (Gate B) are not started. Target kept: CLASS_A 10k entities under 50 ms (`docs/engine/performance_contract.md` §5.1). Measured hot spots and their owners: `docs/performance/tick_cost_growth.md` (H1 hostility per pair, H2 cooperation candidates).

## Board

| epic or batch | owner role | state | depends-on | blocked-by | lead's recommended next step | owner decision needed (y/n) |
|---|---|---|---|---|---|---|
| perf F1 #758: the proof digest hashes the carried state (flat-sha256-v3) | perf-planner (ubuntu) | DRAFT, CI green at ac66bafd3; the populated-state parity test is folded in (owner option A, #715 6443266094) | PERF-D5 sign-off | owner PERF-D5 | sign PERF-D5, mark ready, rpg and owner approve, merge; no merge while a HUNGER step A PR is open unless rpg is told; after the merge rpg re-records v1 under v3 | y: PERF-D5, merge |
| perf next batch (dependency fingerprint, M6-T05 fold, 10k probe, `_consider` profile, collection growth) | perf-planner (ubuntu) | local on `perf-record-dependency-fingerprint` | F1 merged | F1 | start after F1; each heavy run takes the host slot | y: pushes |
| rpg U3/U4 (semantic foundation, ubuntu lanes) | rpg-planner-ubuntu | planning after #762 | U2 batch 1 (#757, merged) | none | hash-neutral proof per PR; stay out of the u24 lanes' files and `data/worlds` | y: pushes, merges |
| rpg HUNGER step A (u24, `rpg-hunger-retreat-step-a` 85515ca12) | rpg-planner (u24) | the gated paired run STOPPED (frontier_living_world deaths 123 to 146, blacksmith extinct); attribution probe running on the u24 slot | probe verdict | probe | owner STOP decision once the cause is known | y: STOP or re-plan |
| rpg Lane C (u24): H2 cooperation index 8d1a391c2, then Semgrep src findings b2dd46b69, then F3 checkpoint restore d690c808a | rpg-implementer-3 (u24) | ready, each behind main | one PR at a time | owner push go each | push in order; the lead reviews the CORS section of `docs/architecture/http_api_key_authentication.md` when the Semgrep PR opens | y: three pushes |
| rpg F4 salted group id (u24, eac95383b) | rpg-planner (u24) | not ready | probe A0 and `paired --neutral` | u24 slot after step A | queue after the step A probe | n |
| #759 rpg owns `tools/rpg_measure` | agent-working (u24) | re-sync 130144fd8 ready to push | none | owner push go | push, then both reviews re-check (they predate the re-sync), then merge | y: push, merge |
| engine-modes step 1 revision (`architecture-modes-q1-revision` ec666fb50) | architecture-planner-u24 | unpushed, merges cleanly, 9 behind main | none | owner push go | push with a re-merge | y: push |
| testing PRs (#243 fix, then 5b, T1, T2) | testing-implementer (u24) | queued | one at a time | testing-planner not running (branch 29 behind, launch refused as stale) | owner asks testing-implementer for the #243 fix SHA at push time | y: pushes |
| platform: DevOps step 2 epic closed (3 of 4 children, #627 #688); API dashboard and trace proof parked BLOCKED on rpg R3 (#622 OTel) | platform-planner (ubuntu) | close commit 8a2222cc8 local | none | owner push or hold | fold into the next platform batch; R3 has no ticket or date: filing it needs u24 rpg-planner's release and an owner OK (runtime deps) | y: push or hold; R3 timing |
| agent-working (ubuntu): W44 carried rows 6cf11bc2a local | agent-working-planner | idle at a HARD boundary | none | none | fold into the next agent-working PR; u24 owns close-week and retro | n |
| graphify 0.9.70 on u24 | owner | ready | none | none | install in `.venv-knowledge`, `make graphify-shim`, full extract and prune | y: run it |
| machine resources, host ubuntu | lead-planner (owner grant 2026-10-13) | managed | none | none | one heavy run at a time under `systemd-run MemoryMax=3G MemorySwapMax=0`; start at loadavg1 < 1.5 with 3 GB or more available and swap flat; `/data` floor 10 GB (about 11 GB free after the owner deleted the proof cache) | n |

## Residue awaiting the owner

**Never push any of these again.**

- Repo root (main checkout, untracked since 10-03): `agent-monitoring/`, `stored_artifacts/` (old pre-`agent-working/` layout; NOT duplicates of `agent-working/` copies). Archive or keep.
- Host ubuntu: two detached worktrees, `/home/vboxuser/Work/rpg-aseprite-mcp` (1.3 GB) and `/data/vboxuser/Work/rpg-asset-planner` (0.5 GB), merged state unknown; asset-planner confirms before the owner removes them.
- Dependabot #143 (uuid in `website/package-lock.json`): blocked on Docusaurus.
