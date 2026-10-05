---
status: historical
layer: ai
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261004-SESSION-LAYER-M5C-READ-ONLY-ALLOWLISTS-AND-ROLE-BOUNDARY-EVENTS
date: 2026-10-05
tags: [ai, process-improvement, governance]
---

# Test Plan: TCK-20261004-SESSION-LAYER-M5C-READ-ONLY-ALLOWLISTS-AND-ROLE-BOUNDARY-EVENTS

Pure checks (inside, outside, unowned, split, may_write nuance, outside worktree); message class mismatch and accepted senders; once per session; event field set and no `agent`; own file so the vocabulary ratchet is untouched; unresolved caller and unrelated tools; write and state failure swallowed; through the guard: additionalContext only, authority decisions unchanged, advisory failure never changes exit; allowlist rendering.

## Proof Plan

- Level: unit with guard.main driven end to end.
- Proof kind: executable tests with positive controls (inside-owns is silent, outside fires).
- Oracle source: ticket acceptance criteria and plan sections 9.0 and 10.
- Expected effect: one advisory warning and one event per path class per session outside the domain, none inside, no permission decision ever.
- Selected commands: `pytest tests/tools/test_session_boundary.py tests/tools/test_session_guard.py tests/tools/test_settings_json_hooks_wiring.py`; `pytest tests/tools -k "session or claim or write_path or monitoring or schema"`.
