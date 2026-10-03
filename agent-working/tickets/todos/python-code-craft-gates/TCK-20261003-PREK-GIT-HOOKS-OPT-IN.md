---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261003-PREK-GIT-HOOKS-OPT-IN
phase: open
date: 2026-10-03
tags: [delivery]
---

# TCK-20261003-PREK-GIT-HOOKS-OPT-IN

## Title
M4d: prek git hooks with an opt-in install that keeps the post-commit reindex hook

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Roadmap 6.2 picks prek as the git hook runner. `.git/hooks` is shared by every worktree on this machine, so owner decision 2026-10-03: install is opt-in only. `make install-hooks` today copies tools/hooks/post-commit-reindex.sh into .git/hooks/post-commit; prek must not overwrite it.

## Scope
- `.pre-commit-config.yaml` run by prek (pinned): ruff check on staged `.py` files filtered through the ratchet so only new violations block the commit; `uv lock --check` when pyproject.toml or uv.lock is staged
- An opt-in Makefile target that installs prek's pre-commit hook and the existing post-commit reindex hook together; neither overwrites the other; idempotent
- Document install, bypass (`--no-verify`) policy and uninstall in docs/guidelines/agent_working_environment.md
- Tests: the target's recipe and the config's hook list (static), and the ratchet filter on a staged-file list

## Out of Scope
- Any file under src/ (roadmap decision 8.7): no autofix, no reformat, no `# noqa` / `# type: ignore`
- CLAUDE.md, .claude/settings.json, Claude Code hooks, .claude/agents/, .claude/workflows/, .claude/skills/
- Making any check required or blocking (that is TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING, after the soak)
- Installing hooks automatically from any make target, script, CI step or session hook
- Formatting hooks (decision 8.3)

## Acceptance Criteria
- [ ] Opt-in target installs both hooks; running it twice is a no-op; existing post-commit behaviour unchanged (demonstrated in a scratch clone, not the shared .git)
- [ ] A commit adding a new ruff violation in a staged file is rejected with the ratchet's message; a commit touching only grandfathered code passes
- [ ] Hook run time on a typical one-file commit recorded and under 5 s
- [ ] No target, script or CI step installs hooks implicitly (static test)
- [ ] `git diff --stat <base>...HEAD` lists no path under src/, none under .claude/, and not CLAUDE.md

## Related Tickets
- TCK-20261003-PYTHON-CODE-CRAFT-GATES-EPIC
- TCK-20261003-CODE-HEALTH-RESEED-AND-ADVISORY-CI-JOB (depends on: reseeded registry)

## Related Docs
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/plans/codebase_health/python_code_craft_m4_gates_ticket_brief.md
- docs/guidelines/agent_working_environment.md

## Related Stored Artifacts
None.

## Related Code Areas
- .pre-commit-config.yaml (new)
- Makefile (install-hooks)
- tools/hooks/
- tools/code_health/

## Assumptions / Open Questions
- Verification must use a scratch clone: installing into this machine's shared .git/hooks affects every session
- prek version and whether it is a Python dependency (lock group) or a standalone binary is for Investigate

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
