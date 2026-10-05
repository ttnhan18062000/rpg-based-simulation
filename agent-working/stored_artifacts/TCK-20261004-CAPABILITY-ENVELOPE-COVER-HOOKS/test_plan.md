---
status: historical
layer: ai
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261004-CAPABILITY-ENVELOPE-COVER-HOOKS
date: 2026-10-05
tags: [ai, process-improvement, governance]
---

# Test Plan: TCK-20261004-CAPABILITY-ENVELOPE-COVER-HOOKS

Existing `tests/tools/test_capability_envelope_baseline.py` stays green (the four-field schema test now excludes `hooks`). New tests cover one row per hook, malformed input degrading, idempotent seed, and added/edited/removed hook reporting.

## Proof Plan

- Level: unit.
- Proof kind: executable tests plus a real-repo `diff`.
- Oracle source: the ticket's acceptance criteria and `docs/ai/capability_envelope_baseline.md`.
- Expected effect: `pytest tests/tools/test_capability_envelope_baseline.py` passes; `diff` against the real `.claude/settings.json` reports no out-of-envelope hook after `seed`.
- Selected commands: `pytest tests/tools/test_capability_envelope_baseline.py`; `python3 tools/capability_envelope_baseline.py diff --settings-path /nonexistent`.
