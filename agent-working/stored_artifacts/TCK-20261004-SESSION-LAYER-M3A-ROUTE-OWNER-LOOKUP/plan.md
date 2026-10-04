---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261004-SESSION-LAYER-M3A-ROUTE-OWNER-LOOKUP
phase: open
date: 2026-10-05
tags: [ai]
---

# plan — TCK-20261004-SESSION-LAYER-M3A-ROUTE-OWNER-LOOKUP

One module plus tests, no schema change beyond the confirmed owns line.

`tools/sessions/route.py`: `route(path, roster, from_domain)` plus CLI (`<path> [--from <domain>]`). Splits first (both domains + reason), else the longest `owns` glob across domains (a domain whose `owns_not` matches is excluded), else `unowned`. `--from` applies the asking domain's `routes` to a path it does not own. Seat = the owning domain's planner. Output states liveness is not computed. Globs: `**` crosses directories, `*` stays in one segment.
