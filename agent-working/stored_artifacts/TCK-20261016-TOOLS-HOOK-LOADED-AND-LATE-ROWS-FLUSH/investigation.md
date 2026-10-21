---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261016-TOOLS-HOOK-LOADED-AND-LATE-ROWS-FLUSH
artifact_type: investigation
tags: [agent-monitoring, observability, hooks]
---

# Investigation — TCK-20261016-TOOLS-HOOK-LOADED-AND-LATE-ROWS-FLUSH

Measured on host u24desktop on 2026-10-21 from `agent-working/agent-monitoring/data/2026-W41/{runs,tools}.jsonl` and the session transcripts under `~/.claude/projects/`.

## Reproduced baseline
- 41 distinct sessions closed W41 runs (runs rows with `session_id`). 11 have a tool row on `main`: **27%**. 30 do not.
- 19 of the 30 have a transcript on this host. For those, rows were then searched in every worktree's `*tools.jsonl` shards (all weeks) and in the main checkout.

## Where the 19 went
| class | sessions | evidence |
|---|---|---|
| Rows exist, not on `main` (late/unmerged rows) | **8** | 3815e2c5, 6a6363dd, e4959c75 in `testing` worktree `testing-seat.tools.jsonl` (uncommitted `M`); 51f7360e, 81a7dd61 in `lane-a-tactical-path-batch`; 6b582444, 8655026f, a3ac1bbf in `testing-planner`'s `rpg-seat` shard |
| No hook event at all in the transcript | **6** | 7e0e9157, 987e384b, bee3973d (their worktrees are gone), f5b55df9, fec64c9a, fe5e6fc1 |
| Hook events fired, but no tool row anywhere | **5** | 83885e22, 97318cc4, ebe7c2c8, 219a8468, c64f1f51 (all in the `rpg` worktree) |

The earlier "14 no trace / 5 ran" split counted the text `post_tool_hook` in a transcript. A transcript does not record hook command text; that string only appears when the model mentions it. So that split is not a reliable measure of whether the hook ran. The classes above use what a transcript does record: hook events.

## Causes
1. **Late/unmerged rows are the larger share (8 of 19, 42%), not a quarter.** `pre_push_advisory_hook.check_monitoring_shard_staged` inspects only the *current* ISO week's directory. The `testing` worktree carries uncommitted W41 rows that no push ever flags once the week turns.
2. **Hook not loaded: 6 of 19 had no hook events whatever.** The PostToolUse monitoring command is `test -f "$R/tools/agent-monitoring/post_tool_hook.py" || exit 0`: if the worktree lacks the script, it is silent. The `settings_freshness` launch check compares content to `origin/main` but runs only at launch, and SessionStart said nothing.
3. **5 of 19 had hook events and still no rows.** The same silent `test -f` skip in a stale worktree is the likely cause, but the transcripts cannot prove it. Stated as a gap.

## Decision on late rows (numbers above)
A flush at the next hook call would make a hook run `git add`/`git commit` (a second write path on top of `post_tool_hook.py`'s own append) for rows that were already written. The 8 late-row sessions lost nothing at write time; they lost a commit. A reminder at SessionStart costs one line and no writes, and covers the case the pre-push check misses (older weeks). Chosen: **report-only reminder**, no flush.
