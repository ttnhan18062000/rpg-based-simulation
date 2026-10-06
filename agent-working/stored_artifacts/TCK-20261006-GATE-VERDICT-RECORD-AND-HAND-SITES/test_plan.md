---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261006-GATE-VERDICT-RECORD-AND-HAND-SITES
artifact_type: test_plan
tags: [ai, agent-monitoring]
---

# Test plan
Per CLI site: one passing and one failing case, each asserting exactly one valid row. Writer: opt-out flag, env guard, unwritable root (one stderr warning, no raise), invalid row refused. Validator: bad row rejected, valid accepted. Guard: tests never write into the real data root (conftest env var).

## Proof Plan
- level: unit
- proof kind: pytest
- oracle source: the rows' own fields and the CLIs' unchanged stdout and exit code
- expected effect: 25 tests pass, no shard in the real data root
- selected commands: `pytest tests/tools/test_gate_verdicts.py`
