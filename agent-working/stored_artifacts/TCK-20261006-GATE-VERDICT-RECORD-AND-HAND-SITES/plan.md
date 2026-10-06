---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261006-GATE-VERDICT-RECORD-AND-HAND-SITES
artifact_type: plan
tags: [ai, agent-monitoring]
---

# Plan
1. `gate_verdicts.py`: record, validator, never-raising writer, env guards.
2. Emit from the five hand-reachable gate CLIs; `plan_gate_static.py` gets a thin CLI.
3. `validate.py` check, `schema.md` section, conftest env guard.
4. Tests per site, passing and failing.

## Unresolved Questions

None.
