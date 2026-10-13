---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261013-HOST-LEAD-PLANNER-U24
artifact_type: investigation
tags: [ai, governance, process-improvement]
---

# investigation — TCK-20261013-HOST-LEAD-PLANNER-U24

- `boundary.check_edit` grants `may_write + owns` and then exempts any path whose routed domain contains the caller's domain. Role-level `owns_not` was parsed but never read by it (only `route.py` reads the domain-level one). So the ticket's "use owns_not or may_write, whichever the boundary code honours" had no answer in the existing code: with both leads in `lead`, the same-domain exemption hid every crossing. Hence the small `_sibling_crossing` rule.
- The check is advisory (`role_boundary` warning once per session); there is no hard block. "May not write" in the tests means the edit is reported as a crossing and names the sibling seat.
- No role overrides `owns` or `owns_not` today, so no other seat's behaviour changes (tested).
- Card sizes: the lead-planner card was 404 tokens with its first note wording; shortened to fit 399 max across all cards (`codebase-designer`).
