---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261013-PLATFORM-DOMAIN-SEATS
artifact_type: investigation
tags: [ai, governance, process-improvement]
---

# investigation — TCK-20261013-PLATFORM-DOMAIN-SEATS

- `tools/sessions/validate.py` rule `glob-matches-nothing` (line ~186) fails any `owns` glob with no file. Only `compose.yaml` and `docker/**` exist, so the nine DevOps D8 paths cannot be registered until their files exist.
- No ownership overlap: compose.yaml and docker/** are removed from lead and added to platform; the lead card source never named them.
- Cards are generated from `docs/guidelines/session_roles/domains/*.md` plus role lines; the budget test is parametrized over every role, so the platform cards are covered.
- The working-process doc does not enumerate domains.
