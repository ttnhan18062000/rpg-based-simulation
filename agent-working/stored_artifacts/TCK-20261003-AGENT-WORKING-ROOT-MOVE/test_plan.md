---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261003-AGENT-WORKING-ROOT-MOVE
artifact_type: test_plan
tags: [ai, process-improvement, governance]
---

# Test plan (retroactive)

**Written after the fact**, from the ticket's acceptance criteria. For each criterion: what the check is, the result, and who
established it. "Verified by design session" means checked against git or GitHub after the merge; "implementer-reported" means
reported by the implementer session and not re-run here.

| AC | Check | Result | Source |
|---|---|---|---|
| 1 | No live code names a moved root outside the constants module; guard test fails on a seeded hardcoded path | guard test `tests/tools/test_agent_working_paths_guard.py` added in Stage 1 (name confirmed in the implementer's records and still on main); the ticket records seeded failures | implementer-reported (not re-run by the design session) |
| 2 | No old root at the repo root; all under `agent-working/`; `git log --follow` works | tree root checked: only `agent-working/` of the old names; Stage 2a is 7,640 renames, all R100 | verified by design session; `--follow` not re-run |
| 3 | No frozen file modified | nothing under `agent-working/tickets/done`, `agent-working/stored_artifacts`, `docs/archive` changed after the rename commit | verified by design session |
| 4 | Pre-move path map resolves a sampled old citation from each folder; validators pass with frozen citations | `docs/guides/agent_working_path_map.md` and `resolve_legacy_citation()` exist on main; per-folder sampling not repeated | map and function seen by design session; sampling implementer-reported |
| 5 | Validators pass; registry regenerated; indexes rebuilt; `search_docs` finds moved files | Stage 3 ran them; the implementer's records do not say a registry regeneration was missed or which CI shard failed at `b8ee7db96`; commit `4fd7a07e6` is an auto-regenerate-registry commit in the PR | implementer-reported; the missed-regeneration claim is not confirmed |
| 6 | Hook-recorded event and a closure-tool run land under `agent-working/agent-monitoring/data/YYYY-Www/` | shards for later tickets (`old-root-residue-guard.*`, `implement-ticket-js-use-before-define.*`) exist under that path in merged PRs | verified by design session from the PR file lists |
| 7 | Make targets, CI and documented commands work on a clean clone at the PR head | clean clone at a real path at 9175b8770: scoped suites green except 7 `codebase_health` tests that need `complexipy` (absent locally, identical on the pre-move tree); the "4,328 passed" figure and the "one failing CI shard at b8ee7db96" are not in the implementer's records and are not confirmed | implementer-reported (scoped, not the full suite) |
| 8 | Owner confirmed each governing-file diff | `CLAUDE.md`, `AGENTS.md`, `settings.json`: the PR body and the ticket's sweep table record each as owner-confirmed | implementer-reported; the confirmations happened in the owner's terminal and are not independently checkable |
| 9 | Config sweep closed; a hand-run `implement-ticket` hotfix on a throwaway ticket completes with records in the new location | sweep checklist closed in the ticket. Hand-run done on 2026-10-03 on throwaway `TCK-20261003-PATH-MAP-INDEX-REBUILD-COMMANDS` (merged in #293): Scope, Implement, Document-Update, Test, Parity (skipped, no `src/` change), Verify (done-checker `READY_TO_CLOSE`, 0 of 13 failing) and Finalize all ran. Its records are in the branch-named shards `agent-working/agent-monitoring/data/2026-W40/old-root-residue-guard.{events,runs,working_log}.jsonl` (shards are named by branch, so no shard carries the ticket's name): 10 event rows, 1 run row (`workflow` implement-ticket, `execution_mode` hand, `final_status` DONE, 201 s) and the working_log row, which sits in the pending `working_log.jsonl` shard and not yet in `working_log.csv`. A native `Workflow` run first failed on a use-before-define bug (fixed in #295, merged b3e631324) and is still to do, with the owner's opt-in already given in the implementer's terminal | verified by the implementer from the shards and the merged PR; native run not yet performed |

## Regression-prone paths named for later work

Old-root residue in an existing worktree (covered by `tests/tools/test_no_tracked_old_root_files.py`), a stale monitoring shard
at an old path that holds a row the new one lacks (documented in the path map), the `search_docs` server of a running session
(restart required).
