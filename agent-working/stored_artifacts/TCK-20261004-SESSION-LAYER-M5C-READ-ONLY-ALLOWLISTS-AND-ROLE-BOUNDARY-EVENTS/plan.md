---
status: historical
layer: ai
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261004-SESSION-LAYER-M5C-READ-ONLY-ALLOWLISTS-AND-ROLE-BOUNDARY-EVENTS
date: 2026-10-05
tags: [ai, process-improvement, governance]
---

# Plan: TCK-20261004-SESSION-LAYER-M5C-READ-ONLY-ALLOWLISTS-AND-ROLE-BOUNDARY-EVENTS

1. `tools/sessions/boundary.py`: pure `check_edit` (route from the caller's domain; narrow `may_write`/`owns` exempt; `**` does not) and `check_message` (work-assigning first line vs receiver `accepts_dispatch_from`), once-per-session state, own `role_boundary.jsonl` via the shared writer, `advise()` that never raises.
2. `guard.py` calls it only for a call that produced no decision; output is `additionalContext`, never a permission decision.
3. `SendMessage` appended to the guard matcher (owner confirmed the literal one-line diff); pin updated.
4. Schema doc section; tests.
Scope guard: no deny/ask on semantic boundaries, no new `agent` vocabulary, no allowlist set on any seat (none qualifies).
