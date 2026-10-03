---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260930-MECHANISM-ABSENCE-VERDICTS-NEED-RUNTIME-EVIDENCE
artifact_type: test_plan
tags: [data-quality, process-improvement]
---

# Test Plan — TCK-20260930-MECHANISM-ABSENCE-VERDICTS-NEED-RUNTIME-EVIDENCE

- `tests/unit/tools/test_mechanism_registry.py`: validator rejects `contradicted`+`code_trace`
  (planted fixture, names the mechanism and both values); accepts `contradicted` with each of
  census/scenario/corpus_run; still accepts `code_trace` with observed/inconclusive; the real
  registry has zero `contradicted`+`code_trace` entries; existing all-three-verdicts test updated
  to use a runtime instrument for `contradicted`.
- `tests/tools/test_ticket_scoper_relevance_check.py`: the premise rule appears exactly once in
  `ticket-scoper.md` (names instrument and date) and not in `create-tickets.js`.
- Regression sweep: the nine mechanism-registry unit-test files plus the scoper test.
- Checks: `make mechanism-registry-validate`, `mechanism-registry-html-check`,
  `mechanism-atlas-check`, `mechanism-capabilities-check`, `mechanism-wiring-map-classdef-check`.
- Evidence reproducibility: `runtime_probe.py <world> 300` per corpus world; output committed.
