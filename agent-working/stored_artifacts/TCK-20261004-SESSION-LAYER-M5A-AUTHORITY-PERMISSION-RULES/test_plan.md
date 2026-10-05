---
status: historical
layer: ai
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261004-SESSION-LAYER-M5A-AUTHORITY-PERMISSION-RULES
date: 2026-10-05
tags: [ai, process-improvement, governance]
---

# Test Plan: TCK-20261004-SESSION-LAYER-M5A-AUTHORITY-PERMISSION-RULES

Static harness plus the pinned-shape suites; live fresh-session probes for what the static harness cannot see.

## Proof Plan

- Level: unit plus live fresh-session probe.
- Proof kind: executable tests and observed harness refusals with a positive control.
- Oracle source: the ticket's acceptance criteria and the harness's own startup warnings.
- Expected effect: each authority-class command is refused or asked by the rules alone in a fresh session, an unlisted command runs, and the harness prints no warning about the rules.
- Selected commands: `pytest tests/tools/test_settings_permission_rules.py tests/tools/test_settings_json_hooks_wiring.py`; `claude -p` probes listed in the ticket.
