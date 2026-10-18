---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-BASE-ALERTS-RUNBOOKS-AND-DRILL
artifact_type: plan
tags: [platform, observability]
---

# Plan: TCK-20261018-BASE-ALERTS-RUNBOOKS-AND-DRILL

Written by platform-planner at filing (2026-10-18); the implementer updates it as the work changes.

## Steps
1. Write the three runbooks and the README index (rules' `runbook_url` must match the paths).
2. Ask platform-planner for the stack run (relayed to lead-planner); run it alone, with host headroom checked.
3. Run the drill as scoped; capture timestamps, ntfy messages (topic redacted), alert state history, `docker stats`.
4. Write the drill record; validate frontmatter; `make knowledge-index-update`.

## Scope guards
No committed threshold edits for the drill. No `src/**`, no `tests/**`. Stack down at the end.
