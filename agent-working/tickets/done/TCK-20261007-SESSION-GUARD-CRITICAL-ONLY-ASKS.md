---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261007-SESSION-GUARD-CRITICAL-ONLY-ASKS
phase: done
date: 2026-10-07
tags: [ai, process-improvement]
---

# TCK-20261007-SESSION-GUARD-CRITICAL-ONLY-ASKS

## Title
The session-roles guard asks the owner only about critical actions

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
Owner decision, 2026-10-07 (chosen in the agent-working-planner session: "Drop all but critical"; the current rule is too strict). The guard now asks only for merge, push to the default branch, remote-branch deletion, worktree or data deletion and workflow runs. The owner confirmed the policy and the literal `registries/session_authority.yaml` diff in the implementer session.

## Scope
- `tools/sessions/guard.py`: `_ALWAYS_ASK` = merge, push_default_branch, delete_remote_branch; no ask for governing_file_edit or authority_file_edit; no ask for a commit on the default branch; an unknown branch asks only for an implicit push; an unresolved role asks only when a critical action is present; an uncertain classification asks only when the action set has push, merge or delete_remote_branch, or the raw text names a critical operation (`critical_text`).
- `registries/session_authority.yaml`: `governing_file_edit` removed from every `needs_user` list; header comment says governing files are protected only by review and PR merge.
- Role cards regenerated; the 400-token cap holds.
- Tests updated to the new policy, with new cases.

## Out of Scope
- The quoted-text false positive in `classify.py` (separate ticket; it still matters for correct DENY classification).
- `.claude/settings.json` permission rules.
- Role DENYs (a planner or designer still cannot commit, push or open_pr) and the writer-lease deny: unchanged.

## Acceptance Criteria
- [x] An Edit of CLAUDE.md, `git commit` on main and an uncertain commit are allowed
- [x] An uncertain push, `git push origin main` and `gh pr merge` ask
- [x] A planner commit is still denied
- [x] `bash -c "git push origin main"` and `eval "gh pr merge 1"` ask; `bash -c "git commit -m x"` and `bash -c "pytest"` are allowed
- [x] `pytest tests/tools -k "session or guard or classify"` green (763 passed)

## Related Tickets
- TCK-20261007-LAUNCHER-RELAUNCH-FIXES
- TCK-20261007-SESSION-GUARD-QUOTED-TEXT-FALSE-POSITIVE (next, not filed yet)

## Related Docs
- `docs/guidelines/session_roles/`; `docs/guides/agent_session_reset_boundaries.md`

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
- `tools/sessions/guard.py`, `registries/session_authority.yaml`, `.claude/agents/session-*.md`, `tests/tools/test_session_guard.py`, `tests/tools/test_session_boundary.py`

## Assumptions / Open Questions
- Open (owner): governing files are now protected only by review and PR merge; a session can edit CLAUDE.md, `.claude/settings.json` and `session_authority.yaml` without a prompt.
- A plain `git push origin x` from an unresolved role (a plain `claude` session) is now allowed; only push to the default branch, merge and deletes ask.

## Implementation Notes
- Deliberate residual fail-closed (planner, 2026-10-07): an UNCERTAIN command (shell indirection, unparseable text) still asks when its raw text matches `\bpush\b`, `\bpr\s+merge\b`, `--delete`, `-X\s*DELETE|--method\s+DELETE`, `\bworktree\s+remove\b`, or `\bmerge\b` with `gh` in the same command, even when no action could be parsed. It does not ask on commit or governing-file names. `git worktree remove` is not classified as authority-class today, so that pattern only matters inside an already-uncertain command.
- `decide()` gained an optional `command` argument; `_guard` passes the Bash command text.

## Test Summary
`pytest tests/tools -k "session or guard or classify"`: 763 passed, 1 skipped. Updated the guard, boundary and end-to-end tests to the new policy; added critical-only, residual fail-closed and `critical_text` pattern tests.

## Files Changed
`tools/sessions/guard.py`, `registries/session_authority.yaml`, `.claude/agents/session-*.md` (12 cards), `tests/tools/test_session_guard.py`, `tests/tools/test_session_boundary.py`, this ticket.

## Completion Summary
The guard asks only about merge, push to the default branch, remote-branch deletion, worktree or data deletion and workflow runs, plus uncertain commands whose text names one of them. Push and PR stay with the owner's branch rule.
