---
status: historical
layer: ai
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261004-SESSION-LAYER-M6A-MINIMUM-MEASUREMENT
date: 2026-10-05
tags: [ai, process-improvement, governance]
---

# Plan: TCK-20261004-SESSION-LAYER-M6A-MINIMUM-MEASUREMENT

1. `session_role.py` (by session id from the binding record) stamped in `record_run.py`, `record_events.py`, the hand-orchestrated closure writer.
2. `manual_actions.py`: conservative tagger, `UserPromptSubmit` hook (category only), owner tally.
3. `batch_latency.py`: triplet from PR data, `unknown` never zero.
4. `session_layer_report.py` plus one gated section in `generate_retro.py`; schema doc.
5. Hook wiring with the owner's literal-diff confirmation.
Scope guard: no `agent` vocabulary change, no `tools` row field, no batch registry, no M6b analytics or roster check.
