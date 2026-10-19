---
status: active
layer: ai
authority: P2
audience: agent
tags: [ai, process-improvement, governance]
---

# Host-suffixed twins

Not injected into any card. Read when a role must run on a second host.

When the same role would run on two hosts, add a `-u24`-style twin instead of a second session of the plain role: leases, handover and runtime state are per host, so neither host sees the other's holder and `max_sessions: 1` cannot protect it. The first case is `lead-planner-u24` (TCK-20261013-HOST-LEAD-PLANNER-U24); the five platform and agent-working twins followed in TCK-20261018-SESSION-ROLES-HOST-SUFFIXED-U24-SEATS (#620, owner 2026-10-18). Host ubuntu keeps the plain names.

- **Entry:** copy the plain twin's identity, function, `may_write` and handover rule; `session_name` is the role id and `legacy_session_name` is null. Put the twin after the plain role in `registries/session_roles.yaml`: `route` names the domain's first planner, so the plain seat stays the owner.
- **Worktree:** a worktree name hosts exactly one writer role, so the twin gets its own logical name (`<twin worktree>-u24`) in `placement` and `worktrees:`. The physical path is unchanged: the twin's seat launches with `launch.py <role>-u24 --worktree <existing path>`, which records the binding.
- **Handover:** `.claude/handover/<role>-u24.md`. The file is gitignored and per host, so the host renames its own note before the first relaunch.
- **Dispatch:** `accepts_dispatch_from` names only `user` and same-host roles; the plain roles' lists are unchanged.
- **Card:** a `card_note` on the twin and its plain role names the host. Cards stay within the 400-token budget, so keep the note to a few words.
- **Shards and transit:** monitoring shards are keyed by role name, so the twins write apart. Handover-transit bundles are keyed by role too, so bundles sent under the plain name before the relaunch are not meant for the twin.
