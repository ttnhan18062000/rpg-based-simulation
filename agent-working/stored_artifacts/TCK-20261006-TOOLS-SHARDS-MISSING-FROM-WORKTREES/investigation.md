# Investigation — TCK-20261006-TOOLS-SHARDS-MISSING-FROM-WORKTREES

## Method
`classify_sessions.py` (this folder; output `sessions.csv`) reads every local Claude transcript modified since 2026-09-28
(`~/.claude/projects/*/*.jsonl`), takes the `cwd` of every assistant `tool_use` record (both spellings of the parent
directory, `/home/u24desktop/Working` and `/mnt/data/Working`, are normalised) and classes it as repo/worktree root, a
subdirectory of the repo, or outside the repo. It then asks whether the session id appears in any `tools.jsonl` row:
the origin/main tree (`git grep`), every local worktree's data folder, and the main checkout's own data folder, tracked
or not. The hook writes `data/<week>/tools.jsonl` (no branch prefix) first, and `<branch>.tools.jsonl` shards are what the
closure measurement counted, so both file shapes are matched.

Limits: only transcripts still on this machine (removed worktrees' transcripts are missing); closures carry no session id,
so the split is by session, not by closure. The 102 shard-less closures of the time-source design cannot be mapped one by one.

## Result (116 sessions with at least one tool call, 21,119 tool calls)
- 81 sessions have rows; **35 have none (3,045 calls, 14.4%)**.
- The 35 split by where they ran:
  - **17 started in `/mnt/data/Working`, not a git repo (1,843 calls, 61% of the lost calls).** No project hooks load there.
  - 5 in the main checkout (309 calls): the stale checkout, where the hook set differs from origin/main (see LIVE-SESSIONS ticket).
  - 5 in older worktrees (692 calls): agent-monitoring-data-quality-fix 09-28, design-review-rpg-suggestion 09-29 and 10-02, m2-idea43-temporal-note 09-30, doc-tag-enforcement 10-05 (1 call).
  - 5 scratch probe sessions (47 calls): expected, they run with hooks disabled.
  - 3 in other projects (github-profile, ssh-engine; 154 calls): not this repo.
- **Cwd-relative hook commands (the leading hypothesis): real but small.** Only 131 calls (0.6%) ran from a repo subdirectory; 36 of them are in sessions with no rows. A throwaway-worktree probe confirmed the mechanism: `python3 tools/agent-monitoring/post_tool_hook.py` from `docs/` finds no script and `|| true` hides it. A first fix (resolve the top level only) was tested and rejected: it ran the hook but wrote `docs/agent-working/` and `docs/.claude/` under the subdirectory, because the hook's own paths are cwd-relative. The applied fix also does `cd "$R"`.
- **Written but unstaged: not a cause.** 7 of 81 sessions with rows have them only locally (6 in the owner's main checkout, 1 in the still-open lane-a worktree): unmerged work, not loss.

## Verdict
Dominant cause: launching outside the repo (and, secondarily, stale checkouts). That is handed to
TCK-20261006-LIVE-SESSIONS-RUN-STALE-OR-NO-PROJECT-HOOKS (freshness check and launcher preflight, done), not duplicated here.
Secondary cause fixed here: the five `tools/agent-monitoring` hook commands now resolve the repo top level and `cd` into it
(owner-confirmed literal diff, 2026-10-06, after a corrected second diff).
