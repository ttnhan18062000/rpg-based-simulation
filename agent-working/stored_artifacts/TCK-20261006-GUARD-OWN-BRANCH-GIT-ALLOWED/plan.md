---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261006-GUARD-OWN-BRANCH-GIT-ALLOWED
artifact_type: plan
tags: [ai, process-improvement, governance]
---

# plan

Dispatched by agent-working-design 2026-10-06 onto PR #359 (owner: "handoff to implementer to wire this logic to its current PR").

1. `classify.py`: add `push_default_branch`; parse `git push` destinations (explicit refspec, `--all`/`--mirror`, bare/`HEAD` = implicit); `Classification.push_implicit`; `git -C`/`--git-dir` and a same-command `checkout`/`switch` make commit/push uncertain; `default_branches` parameter.
2. `guard.py`: resolve the cwd's branch and the default branches (`main` plus `origin/HEAD`) only when a commit or implicit push is present; `decide(..., on_default)`; no lease is no longer an ask; another role's lease still denies; `push_default_branch` joins `_ALWAYS_ASK`; a commit on the default branch asks; an unknown branch asks.
3. `session_authority.yaml`: owner confirmed the literal diff through AskUserQuestion before it was applied (quoted in the ticket).
4. Cards: measured over budget after the yaml change (rpg-designer 404, agent-working-planner 401). Fix without touching any card text and without raising the budget: the authority line omits `push_default_branch` under "Needs the user" when "Never" already lists `push` (`_IMPLIED_BY`).
5. Docs: plan section 10 table and Implemented paragraph; guard docstring.
