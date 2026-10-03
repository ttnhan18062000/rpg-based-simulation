---
status: active
layer: observability
authority: P1
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260915-EVENT-SEQ-INTEGRITY
phase: open
date: 2026-09-15
tags: [agent-monitoring, data-quality]
---

# Test Plan — TCK-20260915-EVENT-SEQ-INTEGRITY

| AC | Covered by |
|---|---|
| Duplicate `seq` cause identified or not-determinable | investigation.md — 72% directly explained, remainder sampled and traced to the same family of mechanisms, one specific origin left honestly unresolved |
| Gap semantics resolved | investigation.md — two confirmed mechanisms (multi-invocation, documented pause/resume offset); full 46-case trace not completed, disclosed as a scope limit |
| `seq` guarantee documented | `docs/agent-monitoring/schema.md` edit |
| Detector ratchets, no zero assertion | `test_event_seq_integrity_check.py`'s ceiling pins (duplicates 71, gaps 46) |

## Regression coverage

- `tests/tools/test_event_seq_integrity_check.py` (new).
- `make event-seq-integrity-check` confirmed against the real corpus.
