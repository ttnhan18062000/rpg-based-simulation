---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261008-SESSION-MERGED-WORKTREE-PRUNE
artifact_type: plan
tags: [delivery, workflows]
---


## Design
Extend `tools/sessions/prune_branches.py` with `--worktrees` (a mode, not a new file: it reuses `PrData`, `fetch_prs`, `_git`, backup writer). Dry run by default; `--execute` acts.
- `WorktreeRow(path, branch, sha, removable: bool, reason: str, size_bytes)`; `WorktreeReport`.
- `classify_worktrees(cwd, prs, state_root, procs) -> WorktreeReport`, from `git worktree list --porcelain`. First matching rule gives the reason; removable only when none match:
  1. the main checkout, or a bare/detached/prunable entry: kept ("main checkout" / "detached").
  2. a session seat: the path is the recorded worktree of any role in `session_roles.yaml` (the 8 per-role seats plus the shared ones) or holds a writer lease (`state.read_lease`) or a live instance (`state.liveness`): kept ("seat worktree: <role>").
  3. branch has an open PR: kept.
  4. `gh` unavailable (`prs is None`): kept (nothing provable).
  5. tip not equal to a merged PR head for that branch name (reuses the `sha in prs.merged.get(name)` rule): kept ("unmerged" / "tip moved after the merged PR").
  6. any process with its cwd inside the path (scan `/proc/*/cwd`, injectable `proc_root`): kept ("process <pid> inside").
  7. dirty: `git status --porcelain` non-empty: kept, listing every path. A dirty monitoring shard is named, not filtered ("dirty: agent-working/agent-monitoring/data/2026-W41/x.tools.jsonl").
- `--execute`: for removable rows only, `git worktree remove <path>` (never `--force`); a refusal by git is reported as "left" with git's message and the run continues; prints freed size (sum of sizes of those actually removed). Branches are kept. Writes the same name-to-SHA backup file the branch mode writes (reusing `write_backup`, extended to take worktree rows: `path branch sha`), with restore commands `git worktree add <path> <branch>`.
- Output via a `render_worktrees` mirroring `render`: counts by removable/kept, one line per row with reason and size.
- Owner-run only (action `delete_worktree_or_data`): the session guard already asks for `git worktree remove`; no change to authority files.

## Scope guards
No branch deletion (branch mode stays as is and ignores `--worktrees`), no `data/runs` deletion, no automatic invocation, no `--force` anywhere. `--worktrees` combined with `--remote` is rejected.

## Acceptance map
1. Fixture repo (tmp bare origin plus worktrees) with gh mocked via `PrData`: merged-clean -> removable; merged-dirty -> kept; unmerged; open-PR; seat (via a tmp `state_root` lease and via the roster) each get the expected row and reason.
2. Dry run: `git worktree list` identical before and after. `--execute`: only removable paths gone; assert no `--force` in any recorded git invocation (wrapper around `_git`), and a worktree git itself refuses is "left", not forced.
3. A worktree whose only change is a dirty monitoring shard is kept and the reason contains that shard's path.
4. Scoped: `pytest tests/tools -k prune`.

## Files
Edit: tools/sessions/prune_branches.py, existing prune tests (add a test module `tests/tools/test_prune_worktrees.py`), docs/guides/delivery_process.md (one line under Worktree & Branch Isolation).

## Questions for the planner
1. Seat detection: roster paths plus lease plus live instance as above, or roster only? The plan takes all three (safest: a false keep costs disk, a false remove costs work).
2. Backup file: reuse the branch backup file for both modes (one file per day), or a separate `worktree-backup-<date>.txt`? Plan: separate file, so the existing format and its readers are untouched.

## Planner answers (approved)
Seat detection uses roster paths, writer lease and live instance; separate `worktree-backup-<date>.txt`; when gh is unavailable print one summary line, not a row per worktree.
