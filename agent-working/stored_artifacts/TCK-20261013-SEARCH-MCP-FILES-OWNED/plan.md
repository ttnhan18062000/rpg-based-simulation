---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261013-SEARCH-MCP-FILES-OWNED
artifact_type: plan
tags: [ai, governance]
---

# plan — TCK-20261013-SEARCH-MCP-FILES-OWNED

1. Add the two globs to `domains.agent-working.owns` and reword the `platform.owns` comment in `registries/session_roles.yaml`.
2. Regenerate the cards. Only `agent-working-planner` went over 400 tokens (407). The planner decided the shortening (2026-10-14): fold same-directory file globs into one brace group in `card.py`; reword the agent-working domain card; drop "child" and "worktree" from two phrases of the planner function card. The budget stays 400; the designer-briefs sentence stays.
3. Tests: the fold, the five routes, every card within budget.
