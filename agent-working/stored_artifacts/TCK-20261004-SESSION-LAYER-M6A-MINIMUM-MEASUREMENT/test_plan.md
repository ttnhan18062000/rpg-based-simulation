---
status: historical
layer: ai
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261004-SESSION-LAYER-M6A-MINIMUM-MEASUREMENT
date: 2026-10-05
tags: [ai, process-improvement, governance]
---

# Test Plan: TCK-20261004-SESSION-LAYER-M6A-MINIMUM-MEASUREMENT

Session-role resolution (two sessions, unbound, no id, failure, shared sidecar ignored); writers stamp and keep `agent`; tagger fixture with exclusions; hook privacy; tally validation; latency real-batch reproduction and unknown cases; retro section; wired hook fail-open.

## Proof Plan

- Level: unit with in-process writers and subprocess-driven hook runs.
- Proof kind: executable tests with positive controls and one hand-computed real batch.
- Oracle source: ticket acceptance criteria, plan section 11, `gh pr view 346`.
- Expected effect: runs and events carry the right `session_role`; only repeated-instruction prompts are counted; latencies match the hand value or are `unknown`.
- Selected commands: `pytest tests/tools/test_session_layer_measures.py tests/tools/test_settings_json_hooks_wiring.py tests/tools/test_session_guard.py`; `pytest tests/tools tests/docs`.
