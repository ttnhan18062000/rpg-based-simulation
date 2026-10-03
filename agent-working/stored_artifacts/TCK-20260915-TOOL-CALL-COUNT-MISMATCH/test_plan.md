---
status: active
layer: observability
authority: P1
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260915-TOOL-CALL-COUNT-MISMATCH
phase: open
date: 2026-09-15
tags: [agent-monitoring, data-quality]
---

# Test Plan — TCK-20260915-TOOL-CALL-COUNT-MISMATCH

| AC | Covered by |
|---|---|
| Authoritative side documented | `docs/agent-monitoring/schema.md` edit |
| August cluster explained or recorded not-determinable | investigation.md — explained via schema.md's own already-documented pre-2026-08-24 cross-session contamination fix, cross-referenced with a concretely-confirmed shared example |
| Shared-cause hypothesis confirmed or refuted | Confirmed in `TCK-20260915-SIDECAR-ATTRIBUTION-GAP`'s own investigation; cross-referenced, not re-derived |
| Detector ratchets, no zero assertion | `test_tool_call_count_mismatch_check.py`'s ceiling pin |

## Regression coverage

- `tests/tools/test_tool_call_count_mismatch_check.py` (new).
- `make tool-call-count-mismatch-check` confirmed against the real corpus.
