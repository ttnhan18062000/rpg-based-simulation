---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261008-CONTEXT-SEARCH-HOOK-NARROWING
artifact_type: plan
tags: [workflows, agent-monitoring]
---

# Plan

Planner-approved approach (2026-10-08): move the inline hook into `tools/agent-monitoring/context_search_hook.py` (advisory only, exit 0 always), emit the reminder only for an investigation read targeting `src/` or `docs/` when the session has not yet called `search_docs`, measure old vs new firing on the W41 shards first, and do NOT edit `.claude/settings.json` (the owner's file): the replacement entry is recorded in the ticket and the PR body as an owner step.
