---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261004-SESSION-LAYER-M2C-LAUNCHER-RECOVERY-AND-WORKTREE-SELF-HEAL
phase: done
date: 2026-10-04
tags: [ai, process-improvement, governance]
---

# TCK-20261004-SESSION-LAYER-M2C-LAUNCHER-RECOVERY-AND-WORKTREE-SELF-HEAL

## Title
Session-layer M2c: `cc <role>` launcher, orphan recovery flow and worktree self-heal

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Add `tools/sessions/launch.py` and the `cc` alias: resolve role, ensure its worktree, refuse a live instance, run the recovery flow for an orphan, then `exec claude --name <role> --agent session-<role>` with `SESSION_ROLE` set. After this, a session killed mid-batch can be found and resumed or replaced from the role id alone.

Child of `TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION` (milestone M2). Depends on M2a; uses M2b's binding for the started session.

## Scope
- `tools/sessions/launch.py <role> [--resume]`: unknown role lists the roster and exits; `unstaffed` seat is stated; best-effort `max_sessions` check (process table, advisory).
- Worktree self-heal (plan 8): worktree missing or prunable per `git worktree list` -> `git worktree prune`, `git worktree add` from the role's branch (never from scratch), tell the owner. Never touches uncommitted files elsewhere.
- Existing instance (M2a): live -> refuse and say so; released or none -> start fresh; orphaned -> recovery flow, never silent.
- Recovery flow (plan 6.1): print evidence (transcript mtime, worktree and branch, dirty and unpushed state, git operation left in progress, open PR and batch via `gh`, handover age and its "Awaiting", candidate transcripts for the role by scanning `~/.claude/projects/*/*.jsonl` for `customTitle == <role id>`, newest first); offer resume / replace / inspect; default resume if transcript is newer than the handover else replace; the choice is the owner's. Resume always by **session id**, never by name (M0m). Replace keeps the old transcript.
- Handover stub for a new role with the fixed head (Role, Branch/PR, Pending user decisions, Awaiting, Next).
- `cc` shell alias documented in `docs/guides/` (one line; installing it is the owner's step).
- Generated `session-<role>.md` must keep the "launcher-only, never spawn" description (M1c); a test asserts the launcher uses only generated agent names that exist.

## Out of Scope
- SessionStart hook and binding (M2b), the lease model (M2a), `status.py`/`prune_branches.py` (M4), auto-wake, `PreToolUse` guardrails (M5). No `settings.json` change.

## Acceptance Criteria
1. Dry-run mode prints the exact `claude` command without exec; test asserts `--name <role>`, `--agent session-<role>`, `SESSION_ROLE` and `--resume <session-id>` forms.
2. A live fixture instance is refused; a killed one (positive control from M2a) takes the recovery path; a released one starts fresh.
3. Recovery evidence includes a git operation left in progress (fixture: mid-rebase repo) and flags it as a NEVER-boundary state.
4. Worktree self-heal: a removed worktree with its branch intact is recreated from that branch and uncommitted-loss is stated; a missing branch is reported, not invented.
5. Candidate transcripts are found by `customTitle` across project dirs, including one resumed from another cwd; replace never deletes a transcript.
6. Non-interactive mode never silently resumes or replaces: it prints the evidence and exits non-zero asking for an explicit flag.
7. Epic acceptance rehearsal recorded in the ticket: start a role with `cc`, `kill -9` it, rerun `cc` and recover from the role id alone. Scoped tests green; docs and `docs/REGISTRY.yaml` regenerated.

## Related Tickets
- `TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION` (parent), `TCK-20261003-SESSION-LAYER-M0-HARNESS-SPIKE` (done), M1a-d (done, #314 and the M1d PR)
- M2a (dependency), M2b (parallel), M4 (`status.py` reuses the instance state).

## Related Docs
- `docs/plans/agent_infrastructure/session_layer_working_process.md` (binding; sections 5, 6, 6.1, 8, 10, 12.2)
- `agent-working/stored_artifacts/TCK-20261003-SESSION-LAYER-M0-HARNESS-SPIKE/investigation.md` (M0 record; signal precedence table)
- `docs/guides/agent_session_reset_boundaries.md`, `docs/guides/delivery_process.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION/external_reviews/`

## Implementation Notes
`tools/sessions/launch.py`: role/instance resolution, worktree self-heal from the recorded branch, refuse live / fresh on released / recovery on orphan with evidence (transcript age, dirty, unpushed, git operation in progress as a NEVER state, open PR, handover age and Awaiting, candidate transcripts by customTitle), non-interactive exits 3, resume always by session id and by default only the dead holder's own session, handover stub, `--dry-run`. Live rehearsal 2026-10-04 (owner confirmed a live run): real `claude` started through the launcher in a throwaway worktree, SessionStart bound it (pid found by ancestor walk, no CLAUDE_PID needed), a second launch was refused (exit 4), `kill -9` left the socket file and the instance read orphaned with no SessionEnd, the relaunch printed the evidence and exited 3. The rehearsal found a defect: the newest customTitle transcript was the operator's own live session of the same role, so the default would have resumed it; fixed (default = the holder's own transcript only; none -> replace, explicit `--session-id` otherwise) with a regression test. NOT exercised live: `claude --resume <id> --name --agent` together (dry-run only), because the killed session never took a turn and wrote no transcript.

## Test Summary
`tests/tools/test_session_launch.py` (21): command forms incl. --resume <id> and `<role>-N`; every roster role has its generated launcher-only agent file; dry-run never execs; live refused; killed -> recovery; released/none fresh; real mid-rebase flagged NEVER; self-heal (removed, deleted behind git's back, missing branch, no branch, dry-run); transcripts by customTitle across project dirs; replace never deletes; non-interactive never chooses; default-action regression.

## Files Changed
tools/sessions/launch.py; tests/tools/test_session_launch.py; docs/guides/agent_session_reset_boundaries.md

## Completion Summary
Delivered as part of the M2a-c bundle on branch `session-layer-m2-role-state`; scoped tests green; docs and registry regenerated.

## Related Code Areas
- `tools/sessions/launch.py` (new; reuses `roster.py`, `state.py`), `.claude/agents/session-*.md` (read-only), `tests/tools/`.

## Assumptions / Open Questions
- Rehearsal of kill -9 needs a real `claude` process; if the owner prefers no live probe, AC 7 uses a stub process and says so.
- Idle-wake and inbound-control (M0c/l) are out of scope and stay unverified.
