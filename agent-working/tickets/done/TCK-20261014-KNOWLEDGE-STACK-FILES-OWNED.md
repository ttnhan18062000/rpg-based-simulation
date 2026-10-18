---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261014-KNOWLEDGE-STACK-FILES-OWNED
phase: done
date: 2026-10-14
tags: [knowledge-store, process-improvement]
---

# TCK-20261014-KNOWLEDGE-STACK-FILES-OWNED

## Title
Register the knowledge-search stack files (`requirements-knowledge.txt`, `tools/knowledge_search.py`, `tools/eval_search.py`) to the agent-working domain

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
`tools/sessions/route.py` reports all three files `unowned`. They are the knowledge-search stack that
TCK-20261014-KNOWLEDGE-STACK-PIN-AND-EMBEDDING-MAJOR edits, and they sit beside `tools/search_*.py`, which
agent-working already owns (TCK-20261013-SEARCH-MCP-FILES-OWNED). lead-planner-u24 proposed registering them in this
batch; the user agreed in agent-working-planner's terminal on 2026-10-14.

## Scope
1. In `registries/session_roles.yaml`, `domains.agent-working.owns`, add:
   - `requirements-knowledge.txt`
   - `tools/*_search.py` (today it matches exactly `tools/knowledge_search.py` and `tools/eval_search.py`; say so in
     a trailing comment, like the `tools/search_*.py` line). Place it next to the other `tools/` file globs so
     `card.py::_fold_same_dir_files` can fold it.
2. Regenerate the role cards (`tools/sessions/generate_agents.py`) and check every composed card is within 400
   tokens. The agent-working cards were at 399 after #550. If the new lines push any card over, shorten card text;
   never raise the budget (owner policy).
3. `python3 -m tools.sessions.validate` reports 0 findings; the roster and card tests in `tests/tools/` pass.

## Out of Scope
- Any change to the three files themselves (that is the pin ticket).
- `pyproject.toml` / `uv.lock` (lead-owned).
- `tools/graphify_to_html.py` (still unowned; separate owner question).

## Acceptance Criteria
- `route.py` reports all three paths owned by agent-working.
- PR body shows the literal `session_roles.yaml` owns diff and the largest composed card's token count (at most 400).
  The owner confirms that diff on the PR before merging.
- `validate.py` clean; card budget test green.

## Related Tickets
- TCK-20261014-KNOWLEDGE-STACK-PIN-AND-EMBEDDING-MAJOR
- TCK-20261013-SEARCH-MCP-FILES-OWNED
- TCK-20261013-PLATFORM-DOMAIN-SEATS (the `glob-matches-nothing` validator rule)

## Related Docs
- docs/guidelines/session_roles/

## Related Stored Artifacts
- none

## Related Code Areas
- registries/session_roles.yaml, tools/sessions/card.py, tools/sessions/generate_agents.py, .claude/agents/session-*.md

## Assumptions / Open Questions
- `tools/*_search.py` will also catch any future `tools/<x>_search.py`. Accepted: that name pattern is the search
  stack's.

## Implementation Notes
- `registries/session_roles.yaml` `domains.agent-working.owns`: added `tools/*_search.py` (exactly knowledge_search.py and
  eval_search.py today) and `requirements-knowledge.txt` after the `tools/start_*_mcp.sh` line; `card.py` folds the first into the
  `tools/{...}` group. Cards regenerated. Three agent-working cards went over 400 (planner 409, designer 402), so card text was
  shortened, budget untouched: the domain overlay lost "; ticket process problems here" (now "process incl. tickets") and the
  planner function text says "commit only on your own leased branch" for "you may commit on your own branch where you hold the
  lease". That edit also regenerates the other planner cards (wording only).

## Test Summary
- `tools.sessions.validate`: 0 findings. Composed card tokens, largest first: codebase-designer 399, agent-working-planner 398,
  agent-working-designer 398, agent-working-implementer 392. `route` reports all three paths owned by agent-working
  (`longest owns glob`). `test_session_cards.py` and the other session tests pass (`test_session_status.py` timed out under
  load once and passes at low load).

## Files Changed
- registries/session_roles.yaml, docs/guidelines/session_roles/domains/agent-working.md, docs/guidelines/session_roles/functions/planner.md,
  .claude/agents/session-*.md (the planner cards and the agent-working cards)

## Completion Summary
The knowledge-stack files `requirements-knowledge.txt`, `tools/knowledge_search.py` and `tools/eval_search.py` are owned by
agent-working; every composed card stays within 400 tokens. The owner confirms the roster diff on the PR.
