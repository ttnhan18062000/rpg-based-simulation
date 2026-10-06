---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261006-GATE-PRECISION-REPORT-AND-RETRO
artifact_type: test_plan
tags: [ai, agent-monitoring]
---

# Test plan
Fixture ledger with 3 gates (6, 2 and 0 adjudicated). Report cells, counts, week filter, CLI, retro dark and zero wording, retro with fixture, Notes preservation without `--force`, fail-soft read.

## Proof Plan
- level: unit
- proof kind: pytest
- oracle source: the fixture ledger's known adjudication counts
- expected effect: 2/6, too few adjudicated, not adjudicated; retro renders each wording
- selected commands: `pytest tests/tools/test_gate_ledger.py tests/tools/test_generate_retro.py`
