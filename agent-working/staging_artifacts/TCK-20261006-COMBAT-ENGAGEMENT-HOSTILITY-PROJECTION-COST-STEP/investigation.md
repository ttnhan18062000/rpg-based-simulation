---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP
artifact_type: investigation
tags: [performance, combat]
---

# Investigation

- Cost sits in `is_hostile_compat` / `project_relation` (29 to 62 % of the tick in synthetic profiles, see the ticket's 2026-10-15 evidence). The tables scanned (perspectives, faction relationships, species relations) are fixed after `load_all`, so per-pair scans repeat identical work.
- Only two commits touch `src/domains/combat_engagement` or `src/content_semantics` in `c84352465..132bf09ca`: `1e075b807` (#190) and `6dd2ccd12` (#192); #190 is the probable introducer (to confirm by timing).
- #395 (7aa6f997b, symmetric attack permission) is on main already; check whether it added per-pair cost by timing its parent against it.
- Tests copy a repo's `__dict__` and inject fixtures into the copies, so an index cached on the repo would be shared with a copy; the lookup is kept on the service and validated by table identity and size.
- Open: the `collection` growth (~50 to ~260 ms) is not attributed yet.
