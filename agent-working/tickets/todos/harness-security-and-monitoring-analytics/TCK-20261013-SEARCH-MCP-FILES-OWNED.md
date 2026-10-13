---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261013-SEARCH-MCP-FILES-OWNED
phase: open
date: 2026-10-13
tags: [ai, governance, mcp]
---

# TCK-20261013-SEARCH-MCP-FILES-OWNED

## Title
agent-working owns the search MCP files and the MCP launch scripts; platform registers its own new paths in its step PRs

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Owner decisions (2026-10-13), first relayed by lead-planner-u24 and then confirmed by the owner in the
agent-working-planner terminal:
1. `tools/search_mcp.py`, `tools/search_server.py`, `tools/search_shared.py` and `tools/start_*_mcp.sh`
   (`start_search_mcp.sh`, `start_headroom_mcp.sh`) belong to agent-working. They have been unowned since #527 and #522.
   `tools/graphify_to_html.py` stays unowned; the owner was not asked to decide it.
2. A later DevOps step that creates a platform path (`infra/**`, `charts/**`, `docs/runbooks/**`, ...) adds only that
   path's glob to `domains.platform.owns` in the same PR that creates it. The owner confirms the literal diff on that
   PR and agent-working-planner reviews by comment. Each path no longer needs its own agent-working ticket.

## Scope
1. `registries/session_roles.yaml` (governing file), `domains.agent-working.owns`, add after `tools/graphify_prune.py`:
   ```diff
          - tools/graphify_prune.py
   +      - tools/search_*.py          # search_mcp, search_server, search_shared (owner 2026-10-13)
   +      - tools/start_*_mcp.sh       # start_search_mcp, start_headroom_mcp
          - tests/tools/**
   ```
   Also change the `platform.owns` comment so it records decision 2: "each DevOps step adds the globs it creates in its
   own PR (owner confirms the diff there)".
2. Regenerate `.claude/agents/` (`tools/sessions/generate_agents.py`). The three agent-working cards gain the two
   globs. If a card goes over the 400-token budget, shorten the card text, for example by folding into the existing
   `tools/{...}` brace group or tightening the domain card in `docs/guidelines/session_roles/domains/agent-working.md`.
   Never raise the budget. If a shortening changes meaning, stop and ask the planner.
3. `docs/guides/cross_session_messages.md` or the session-roles guide: only if it describes who registers new domain
   paths, add one line for decision 2. Otherwise record it only in the manifest comment.
4. Tests in `tests/tools/`: route.py resolves the five files to agent-working, and every card stays within budget.

## Out of Scope
- `tools/graphify_to_html.py` (undecided).
- Any change to the search MCP code itself.

## Acceptance Criteria
- AC1: `validate.py` reports 0 findings. No overlap: lead routes `tools/**` to agent-working-designer, so this is
  consistent with that route.
- AC2: `generate_agents.py --check` is clean, and every card is within 400 tokens.
- AC3: the route tests pass for all five files.
- AC4: the owner confirms the literal `session_roles.yaml` hunk on the batch PR.

## Related Tickets
- TCK-20261013-PLATFORM-DOMAIN-SEATS (#539); TCK-20261012-HOST-PATH-LITERALS-MAKEFILE-AND-MCP-LAUNCHERS (#522);
  #527 (search-mcp-shared-model).

## Related Docs
- docs/guidelines/session_roles/domains/agent-working.md; docs/architecture/devops_plan_amendment_proposal.md (D8 section).

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261013-SEARCH-MCP-FILES-OWNED/ (created at close)

## Related Code Areas
- registries/session_roles.yaml, tools/sessions/{card,generate_agents,route,validate}.py, .claude/agents/**, tests/tools/

## Assumptions / Open Questions
- Depends on #539 being merged (it adds the platform domain whose comment changes here). If #539 is not merged when
  this starts, do Scope 1's agent-working half only and leave the platform comment for after the merge.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
