---
status: historical
layer: ai
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261004-SESSION-LAYER-M5B-ROLE-CONDITIONAL-PRETOOLUSE-HOOK
date: 2026-10-05
tags: [ai, process-improvement, governance]
---

# Test Plan: TCK-20261004-SESSION-LAYER-M5B-ROLE-CONDITIONAL-PRETOOLUSE-HOOK

Classifier table; decision table; two-session resolution; fail-closed (authority exits 2, non-authority exits 0, positive control exit 1); wrapper behaviour with the script absent and present; pinned-shape suites.

## Proof Plan

- Level: unit with subprocess-driven hook runs.
- Proof kind: executable tests with positive controls.
- Oracle source: the ticket's acceptance criteria and plan section 10 (M0n result).
- Expected effect: authority-class calls ask or deny by role, non-authority calls pass, exceptions exit 2 only for authority input, a missing script passes.
- Selected commands: `pytest tests/tools/test_session_classify.py tests/tools/test_session_guard.py`; `pytest tests/tools -k "settings or hook or session or capability or pre_push"`.
