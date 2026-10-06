---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261006-GUARD-OWN-BRANCH-GIT-ALLOWED
phase: done
date: 2026-10-06
tags: [ai, process-improvement, governance]
---

# TCK-20261006-GUARD-OWN-BRANCH-GIT-ALLOWED

## Title
Session-roles guard: git actions on a role's own non-default branch are allowed; only landing on the default branch asks

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The owner gets a "Hook PreToolUse:Bash requires confirmation … session-roles guard" prompt for almost every
implementer git action. On 2026-10-06 the owner decided: "only block the merge branch to main, every action on
their own branch is allowed".

Why it asks today (`origin/main`):
- `tools/sessions/guard.py::decide` asks for commit, push and open_pr when the worktree has no writer lease
  (:147-148). The lease is taken only at SessionStart, and only for a role-resolved session started in its
  worktree (`session_start_hook.py:138-143`). Sessions started from `/mnt/data/Working` never get one.
- `registries/session_authority.yaml` lists `push, open_pr` under the implementer's `needs_user`. The
  2026-10-04 grant covers them only "after a complete batch".
- `classify.py` does **not** classify a local `git merge`. Only `gh pr merge` is MERGE (:125-126). It also has no
  notion of which branch a push targets.

## Scope
1. **Branch-aware classification** (`tools/sessions/classify.py`). For `git push`, resolve the destination
   branch: from an explicit refspec (`HEAD:main`, `x:main`, `main`), from `--all`/`--mirror`, or otherwise from the
   current branch of the call's cwd. Add a new action class, working name `push_default_branch`, for a push whose
   destination is the remote's default branch (`main`). Treat "destination cannot be determined" as uncertain.
   Leave `gh pr merge` as MERGE.
2. **Decision** (`tools/sessions/guard.py`). For a role whose function does not forbid the action:
   - commit, push, force-push and open_pr on a non-default branch → **allow**, whether or not a lease exists.
   - **deny** still applies when another live role holds the worktree's writer lease. That branch is not
     "their own".
   - MERGE (`gh pr merge`), `push_default_branch`, and a commit while the current branch is the default branch
     → **ask**, for every role.
   - These are unchanged: `forbidden` (designer and planner never commit, push or open PRs), governing and
     authority file edits (ask), `delete_remote_branch` (ask), and uncertain classification (ask).
3. **Authority registry** (`registries/session_authority.yaml`, a governing file). Remove `push` and `open_pr` from
   `implementer.needs_user`. Add `push_default_branch` to `needs_user` for all three functions, and to the
   always-ask set in `guard.py` (`_ALWAYS_ASK`). Mark the 2026-10-04 grant superseded, or keep it with a
   comment; do not delete its quote. **Show the owner the literal diff of this file and get confirmation
   before applying it.** The owner's decision above sets the policy, not the text.
4. Regenerate the session cards and agents (`generate_agents.py`). The card prints "Needs the user" and
   "Granted". Keep every card within the 400-token budget, using the method of
   `TCK-20261006-SESSION-ROLE-TEMPLATES-OWNERSHIP`: never raise the budget.
5. Update `docs/plans/agent_infrastructure/session_layer_working_process.md` section 10 (the authority table) and
   the guard docstring.

## Out of Scope
- Writer-lease acquisition for sessions launched outside the role launcher. With this ticket, a missing lease no
  longer causes prompts, so this becomes a separate follow-up only if it is still needed.
- Remote-branch deletion and worktree or data deletion. They stay ask; the owner's decision did not cover them.
- Server-side branch protection on GitHub.

## Acceptance Criteria
1. Guard tests (allow): an implementer with no lease, on branch `feature-x`, runs `git commit`, `git push`,
   `git push -u origin feature-x`, `git push --force-with-lease`, `git merge origin/main` and `gh pr create`.
   Every one is allowed.
2. Guard tests (ask): `gh pr merge 1`, `git push origin HEAD:main`, `git push origin main`, a plain `git push`
   while on `main`, and `git commit` while on `main`. Every one asks, for every role, including one with grants.
3. Guard test (deny): a commit or push in a worktree whose live lease belongs to another role is denied.
4. Guard tests (unchanged): designer or planner commit → deny; a `settings.json` edit → ask; `git push --delete`
   → ask; `bash -c "git push"` → ask (uncertain).
5. The `session_authority.yaml` diff matches what the owner confirmed, quoted in Implementation Notes.
6. `tests/tools/test_session_*.py` passes. Every card is ≤ 400 tokens; record the before/after table.
7. A live probe: the owner or implementer, in a real session, confirms one commit and one push to a feature
   branch run with no prompt, and one `gh pr merge --help`-style dry probe classifies as MERGE. Record it, or
   state that it was not done.

## Related Tickets
- `TCK-20261004-SESSION-LAYER-M5B-ROLE-CONDITIONAL-PRETOOLUSE-HOOK` (built the guard)
- `TCK-20261006-SESSION-ROLE-TEMPLATES-OWNERSHIP` (card budget method)
- `TCK-20261002-EPIC-SESSION-LAYER-MEASUREMENT-AND-REVIEW` (M7 reviews guard friction; record this change as evidence)

## Related Docs
- `docs/plans/agent_infrastructure/session_layer_working_process.md` section 10
- `docs/guides/cross_session_messages.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261004-SESSION-LAYER-M5B-ROLE-CONDITIONAL-PRETOOLUSE-HOOK/`

## Related Code Areas
`tools/sessions/guard.py` (`decide` :127-160, `_ALWAYS_ASK` :58), `tools/sessions/classify.py`
(`_segment_actions` :110-131), `registries/session_authority.yaml`, `tools/sessions/card.py`,
`tools/sessions/generate_agents.py`, `tests/tools/test_session_*.py`.

## Assumptions / Open Questions
- "Default branch" means `main`. Read it from `origin/HEAD` when available, and fall back to `main`.
- The owner's rule covers force-push to the role's own branch. Note this in the PR so it is a visible choice.
- The guard is a guardrail against mistakes, not a sandbox (plan section 10). A push through indirection that
  hides its target still asks, as uncertain.

## Implementation Notes
Drafted by agent-working-design (interim planner), 2026-10-06, from the owner's decision quoted in Request Summary.

Implementation (agent-working-implementer, 2026-10-06): dispatched onto PR #359. Owner confirmation of the literal
`registries/session_authority.yaml` diff, given through AskUserQuestion as "Apply as shown": `implementer.needs_user`
loses `push` and `open_pr`; `push_default_branch` is added to `needs_user` for designer, planner and implementer; a
comment records the owner's rule; the 2026-10-04 grant is marked SUPERSEDED with its quote kept; one comment line
names `push_default_branch` among the classes that always win over a grant. Plan, investigation and test plan are in
`agent-working/stored_artifacts/TCK-20261006-GUARD-OWN-BRANCH-GIT-ALLOWED/`.

## Test Summary
- `tests/tools/test_session_*.py` and `test_attest_gate.py`: 496 passed (guard, classify and cards extended; the cd follow-up below added 28).
- Cards (estimate_tokens): rpg 398/386/383, agent-working 391/395/396, testing 377/356/352, codebase 377/366/364; all at most 400. The yaml change first put rpg-designer at 404 and agent-working-planner at 401; fixed by eliding the redundant `push_default_branch` from the "Needs the user" list when `push` is "Never" (no card text changed, budget unchanged).
- AC7 (live probe in a real role-resolved session): not done. Update 2026-10-06: the guard was absent from sessions started outside a current worktree (stale or no project hooks) and was never probed in a resolved role session; the probe is now Scope 5 / AC5 of `TCK-20261006-LIVE-SESSIONS-RUN-STALE-OR-NO-PROJECT-HOOKS` and closes this AC when run through the launcher.

Follow-up on PR #359 review (agent-working-design, 2026-10-06): `cd <dir> && git push` was checked against the session's cwd branch. Fixed: a literal `cd`/`pushd` target (chained, relative or absolute, `~`, inside `( ... )`) before the first commit or push is recorded in `Classification.cd_chain`, and the guard resolves the branch and the lease's worktree at the directory the command actually runs in (`effective_cwd`). A target that is a variable, substitution, glob, `cd -` or `~user`, a directory that does not exist, or a `cd` that follows the commit or push in the same call, is uncertain and asks. Tests use two real worktrees (`repo` on main, `wt` on feature-x).

## Files Changed
- `tools/sessions/classify.py`, `tools/sessions/guard.py`, `tools/sessions/card.py`
- `registries/session_authority.yaml` (owner-confirmed diff)
- `.claude/agents/session-*.md` (regenerated)
- `tests/tools/test_session_guard.py`, `test_session_classify.py`, `test_session_cards.py`
- `docs/plans/agent_infrastructure/session_layer_working_process.md`
- `agent-working/stored_artifacts/TCK-20261006-GUARD-OWN-BRANCH-GIT-ALLOWED/`

## Completion Summary
Own-branch git actions are allowed with or without a lease; landing on the default branch (gh pr merge, an explicit or implied push to main, a commit on main) asks for every role; another role's lease still denies. ACs 1-6 met; AC7 not done. Force-push to a role's own branch is allowed, as the owner's rule says.
