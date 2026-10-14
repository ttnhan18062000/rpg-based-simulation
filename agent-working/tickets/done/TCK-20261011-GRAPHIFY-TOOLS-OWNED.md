---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261011-GRAPHIFY-TOOLS-OWNED
phase: done
date: 2026-10-11
tags: [ai, governance]
---

# TCK-20261011-GRAPHIFY-TOOLS-OWNED

## Title
`tools/graphify_link.py` and `tools/graphify_prune.py` route to no domain after #506

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
#506 (TCK-20261011-GRAPHIFY-SHARED-GRAPH-FROM-WORKTREES) added two tools at the root of `tools/`. `route.py`
reports both `unowned`, although agent-working wrote them and owns `.graphifyignore`. Found in the planner's
review of #506.

## Scope
Add the two files to the agent-working domain's `owns` in `registries/session_roles.yaml` (one compact glob,
for example `tools/graphify_*.py`, if it matches exactly these two). Regenerate the role cards.

## Out of Scope
Any change to the tools themselves. Ownership of other unowned root files.

## Acceptance Criteria
1. `route.py tools/graphify_link.py` and `route.py tools/graphify_prune.py` name agent-working.
2. `python3 -m tools.sessions.validate` reports 0 findings; every card stays within the 400-token budget,
   which is not raised. If the budget cannot be met, stop and report it instead of trimming card meaning.
3. The owner confirms the literal `registries/session_roles.yaml` diff (governing file).

## Related Tickets
- TCK-20261011-GRAPHIFY-SHARED-GRAPH-FROM-WORKTREES (#506)
- TCK-20261010-PR-BODY-LINT-WORKFLOW-UNOWNED (same shape)

## Related Docs
- docs/guidelines/session_roles/

## Related Stored Artifacts
None.

## Related Code Areas
- registries/session_roles.yaml, .claude/agents/session-agent-working-*.md

## Assumptions / Open Questions
None.

## Implementation Notes
The ticket suggested `tools/graphify_*.py`, but that glob also matches `tools/graphify_to_html.py` (from #449), which this ticket does not cover. Two explicit entries instead (`tools/graphify_link.py`, `tools/graphify_prune.py`) in the agent-working domain's `owns`; the card compresses them with no token cost beyond the budget check. `graphify_to_html.py` stays unowned (reported in the PR body).

## Test Summary
`route.py` names agent-working for both tools; `tools.sessions.validate` 0 findings (17 roles); `generate_agents --check` 0 drift. Card budget unchanged at 400.

## Files Changed
`registries/session_roles.yaml`, `.claude/agents/session-agent-working-*.md`.

## Completion Summary
Both graphify tools now route to agent-working. Owner confirms the literal `session_roles.yaml` diff in the PR body.
