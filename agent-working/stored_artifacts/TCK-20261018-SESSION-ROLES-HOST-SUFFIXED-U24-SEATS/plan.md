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

1. **u24 rows: confirmed** on #634 (2026-10-19). Physical paths are kept; each `-u24` role gets a distinct logical worktree name (`<twin worktree>-u24`) in `placement` and `worktrees:`. All five are `staffed` (owner decision for `agent-working-planner-u24`, 2026-10-19).
2. **Registry:** add the five `-u24` roles, mirroring their twins (see the ticket Scope §1). Update the plain twins' `card_note` and `seat_status` per the ticket.
3. **Route:** if `route` resolves by domain → first matching seat, make it explicitly prefer a role with no `-u24`/host suffix, or the declared primary. That's the minimal change; no new registry field unless the existing ordering already guarantees it (then add a test only).
4. **Generate** `.claude/agents/session-*-u24.md`.
5. **Docs:** one paragraph in `docs/guidelines/session_roles/` on host-suffixed twins.
6. **Tests** per test_plan.md.
7. **PR note:** the roles diff needs the owner's confirmation at the merge question. List the five relaunch commands with u24's real paths, copied from the ticket's Scope §1, plus the handover rename. State the transit-bundle risk.
8. **After the merge:** comment the relaunch commands on #620 and #634.

## Guards
- No change to any plain role's ownership or write grant.
- The 400-token card budget isn't raised.
- No `max_sessions` or lease semantics change.
