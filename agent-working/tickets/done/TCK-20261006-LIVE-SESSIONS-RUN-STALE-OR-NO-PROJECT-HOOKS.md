---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261006-LIVE-SESSIONS-RUN-STALE-OR-NO-PROJECT-HOOKS
phase: done
date: 2026-10-06
tags: [ai, hooks, agent-monitoring, process-improvement]
---

# TCK-20261006-LIVE-SESSIONS-RUN-STALE-OR-NO-PROJECT-HOOKS

## Title
Live role sessions run with stale or no project hooks, so the session guard, manual-action sampler and session_role stamping never fire

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
The deep retro RETRO-2026-W41 (2026-10-06, owner-requested) found the session-layer instruments dark in every live
session:
- zero `manual_actions*.jsonl` and zero `role_boundary*.jsonl` files exist in any week folder or any worktree (the
  files are not gitignored);
- `session_role` is `unresolved` on 59/59 W41 runs and missing on all 1321 W41 tool rows;
- this session's first owner prompt was a role reminder ("continue as agent-working-design") and nothing recorded
  it.

Live sessions start from one of two places:
1. `/mnt/data/Working`, which is not a git repo. The repo's `.claude/settings.json`, `.claude/agents/` and
   workflows are not loaded. Agent types are missing ("agent type 'ticket-scoper' not found", W41 probe run;
   create-tickets run `wf_4a572e02-40e`). The implementer puts the cost at about 240k tokens.
2. The main checkout, which is 57 commits behind origin/main and carries the owner's uncommitted changes. Its
   `.claude/settings.json` lacks 46 lines of hooks that are on main: the session-roles guard
   (`tools/sessions/guard.py`), the `manual_actions.py hook` UserPromptSubmit sampler and
   `session_start_hook.py`.

So the own-branch guard shipped in PR #359 (TCK-20261006-GUARD-OWN-BRANCH-GIT-ALLOWED) is not active anywhere. Its
AC7 live probe was never possible. The session-layer epic D clock ("M7: four weeks after M6a data begins") has not
started, because no M6a data exists.

The role launcher (`tools/sessions/launch.py`, M2c) already starts a role in its own worktree. It is not used day
to day: the `cc` alias install is an open owner step.

## Scope
1. **Freshness check.** Add a read-only check, `tools/sessions/settings_freshness.py` (name is the implementer's
   call), that reports for a given directory:
   - whether it is inside the repo;
   - whether its `.claude/settings.json` and `.claude/agents/` match origin/main (content diff, not commit
     distance);
   - which origin/main hook commands are missing.
   Exit non-zero on a mismatch.
2. **Launcher preflight.** `launch.py` runs the check against the role worktree before `exec claude`. On a
   mismatch it prints the diff summary and refuses, unless `--allow-stale`. It never execs from a directory
   outside the repo. Self-heal stays as-is (from the role's own branch, never from scratch); report staleness, do
   not auto-merge.
3. **Guidance.** In `docs/guides/agent_session_reset_boundaries.md` (or the launcher guide, if one exists), state
   that:
   - role sessions start via the launcher from their worktree;
   - a session started from the parent directory or the stale main checkout runs without the project hooks and
     agent types;
   - any `/clear` resume note should include the freshness check.
4. **Re-baseline the M7 clock.** Update `agent-working/tickets/todos/session-layer/` epic D and its INDEX.md:
   the four-week M7 window starts at the first real `manual_actions.jsonl` record, not at the M6a merge. Remove
   the "about 2026-11-02" figure wherever it appears in the session-layer docs.
5. **Live probe (owner-run, recorded here).** In one session started through the launcher from a fresh role
   worktree, confirm three things:
   - (a) a role-reminder prompt writes a `manual_actions.jsonl` row;
   - (b) a run records a resolved `session_role`;
   - (c) the guard's AC7: own-branch commit and push run without prompt, and a `gh pr merge --help`-style probe
     classifies as MERGE.
   This also closes TCK-20261006-GUARD-OWN-BRANCH-GIT-ALLOWED AC7; note it in that ticket's done file.

## Out of Scope
- Changing `.claude/settings.json` content. That is TCK-20261006-SETTINGS-OWN-BRANCH-PERMISSION-PROMPTS, and any
  settings or hook change needs the owner's literal-diff confirmation (session-layer hold rule).
- Updating the main checkout. It holds the owner's uncommitted changes, so syncing it is the owner's call.
- Relative-path hook commands silently no-opping outside the repo root. That is
  TCK-20261006-TOOLS-SHARDS-MISSING-FROM-WORKTREES.

## Acceptance Criteria
1. The freshness check reports a mismatch for the current main checkout and for `/mnt/data/Working`, and a match
   for a fresh `git worktree add --detach origin/main`. Unit tests cover the cases: match, missing hook, outside
   the repo, agents dir differs.
2. `launch.py --dry-run` against a stale role worktree prints the mismatch and does not print an exec line, unless
   `--allow-stale` is passed. Tested.
3. The guide states the launch rule and the failure symptoms, quoting "agent type '…' not found" and
   `session_role: unresolved`.
4. Epic D and session-layer INDEX.md say the M7 clock starts at the first `manual_actions.jsonl` record.
5. The Scope 5 probe is recorded with its date and session id, or marked "owner step, not yet run". In that case
   the ticket may close with AC5 explicitly open, as TCK-20261006-GUARD-OWN-BRANCH-GIT-ALLOWED did.

## Related Tickets
- TCK-20261006-GUARD-OWN-BRANCH-GIT-ALLOWED (AC7)
- TCK-20261004-SESSION-LAYER-M2C (launcher)
- TCK-20261004-SESSION-LAYER-M6A-MINIMUM-MEASUREMENT
- TCK-20261002-EPIC-SESSION-LAYER-MEASUREMENT-AND-REVIEW (epic D, M7)
- TCK-20261006-SETTINGS-OWN-BRANCH-PERMISSION-PROMPTS
- TCK-20261006-RETRO-DARK-INSTRUMENT-SHOWN-AS-ZEROS
- TCK-20261006-TOOLS-SHARDS-MISSING-FROM-WORKTREES
- TCK-20261006-CREATE-TICKETS-FAILED-INVESTIGATIONS-REPORTED-AS-COVERED

## Related Docs
- `agent-working/agent-monitoring/retro/RETRO-2026-W41.md` (Notes)
- `docs/guides/agent_session_reset_boundaries.md`
- `docs/plans/agent_infrastructure/session_layer_working_process.md` (sections 5, 6.1, 8, 11)

## Related Stored Artifacts
- none yet

## Related Code Areas
- `tools/sessions/launch.py`, `tools/sessions/session_start_hook.py`, `tools/sessions/guard.py`
- `tools/agent-monitoring/manual_actions.py`
- `.claude/settings.json` (read only)

## Assumptions / Open Questions
- Assumes Claude Code loads project settings from the launch directory's repo root and not from a later `cd`.
  The W41 evidence (no records at all) is consistent with this; the live probe confirms it.
- Note: the knowledge index was absent when this was drafted (`make knowledge-index` not run in any checkout), so
  the duplicate scan used grep over the todos and the session-layer folder. No overlap was found beyond the items
  linked above.

## Implementation Notes
Verified against origin/main 9299891a9: `launch.py` main() order (ensure_worktree, plan_launch, exec) held; the preflight is inserted after the plan and before the exec line. New: `tools/sessions/settings_freshness.py`, `launch.preflight()`, `--allow-stale`.
Real-directory check (see investigation.md): `/mnt/data/Working` and the main checkout report MISMATCH.
**AC5 is open: the live probe is an owner step, not yet run.** Run it in one session started with `python3 tools/sessions/launch.py <role>` from a fresh role worktree: (a) a role-reminder prompt writes a `manual_actions.jsonl` row; (b) a run records a resolved `session_role`; (c) own-branch commit and push run without prompt and `gh pr merge --help` classifies as MERGE. Record the date and session id here; it also closes AC7 of TCK-20261006-GUARD-OWN-BRANCH-GIT-ALLOWED.

## Test Summary
`tests/tools/test_session_settings_freshness.py` (11 new) and `tests/tools/test_session_launch.py`: 32 passed. Docs and the M7 clock edits verified by grep (no other "about 2026-11-02" in the session-layer docs).

## Files Changed
`tools/sessions/settings_freshness.py` (new), `tools/sessions/launch.py`, `tests/tools/test_session_settings_freshness.py` (new), `docs/guides/agent_session_reset_boundaries.md`, `docs/plans/agent_infrastructure/session_layer_working_process.md`, `agent-working/tickets/todos/session-layer/INDEX.md` and epic D.

## Completion Summary
A read-only freshness check and a launcher preflight now refuse a role session that would run without the project hooks and agent types; the guide states the launch rule and symptoms; the M7 clock starts at the first real `manual_actions.jsonl` record. The live probe (AC5) remains the owner's step.
