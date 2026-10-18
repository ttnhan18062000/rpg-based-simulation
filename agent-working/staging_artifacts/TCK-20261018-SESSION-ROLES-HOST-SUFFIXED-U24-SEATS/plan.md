---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261018-SESSION-ROLES-HOST-SUFFIXED-U24-SEATS
artifact_type: plan
tags: [ai, process-improvement, governance]
---

# Plan — TCK-20261018-SESSION-ROLES-HOST-SUFFIXED-U24-SEATS

1. **Confirm the u24 rows on #634 first:** worktree paths and staffing. The planner posts the question; implementation waits for the answer or a timeout agreed with lead.
2. **Registry:** add the five `-u24` roles, mirroring their twins (see the ticket Scope §1). Update the plain twins' `card_note` and `seat_status` per the ticket.
3. **Route:** if `route` resolves by domain → first matching seat, make it explicitly prefer a role with no `-u24`/host suffix, or the declared primary. That's the minimal change; no new registry field unless the existing ordering already guarantees it (then add a test only).
4. **Generate** `.claude/agents/session-*-u24.md`.
5. **Docs:** one paragraph in `docs/guidelines/session_roles/` on host-suffixed twins.
6. **Tests** per test_plan.md.
7. **PR note:** the roles diff needs the owner's confirmation in the PR. After the merge, the u24 seats relaunch once with `launch.py <role>-u24 --worktree <existing path>`.

## Guards
- No change to any plain role's ownership or write grant.
- The 400-token card budget isn't raised.
- No `max_sessions` or lease semantics change.
