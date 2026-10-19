---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261018-SESSION-ROLES-HOST-SUFFIXED-U24-SEATS
artifact_type: investigation
tags: [ai, process-improvement, governance]
---

# Investigation — TCK-20261018-SESSION-ROLES-HOST-SUFFIXED-U24-SEATS

## Current state (origin/main bd935e81b)
- `registries/session_roles.yaml`:
  - agent-working: designer (staffed), planner (unstaffed, `interim_holder: agent-working-designer`), implementer (staffed). Worktrees: `agent-working-designer`, `agent-working-planner`, `agent-working`.
  - platform: planner (worktree `platform-planner`) and implementer (worktree `platform`).
  - Every one is `max_sessions: 1`.
- Both hosts now run the plain names:
  - platform since #618 (2026-10-16);
  - agent-working since #634 (2026-10-18).
- Runtime state (`.claude/handover/`, leases, bound worktree) is per host and gitignored, so neither host sees the other's holder.
- Precedent: `lead-planner-u24` (TCK-20261013-HOST-LEAD-PLANNER-U24). It's a separate role id plus `card_note`, launched from the main checkout. The generator already supports `card_note` (registries/session_roles.yaml L336).
- The validator has a `duplicate-session-name` check, and the roster comment says a worktree hosts exactly one writer role. So a `-u24` twin can't reuse its twin's worktree name, and needs its own.

## Risks
- Routing: `tools.sessions.route` returns the owning *seat* for a path. With twins in the same domain, the route must stay deterministic (the plain role is the primary). Check how route picks the seat when two roles share a domain+function.
- Messaging: `--name` is now unique per host, which fixes the collision.
- Shards: the monitoring shard name is keyed by branch/batch, and u24 branches will carry the `-u24` role prefix, so the collision risk drops.
- Dispatch: the ubuntu seats are directed by lead-planner under the owner's 2026-10-11 grant, not by the registered dispatchers. That's an open owner question, and the default is no change.
