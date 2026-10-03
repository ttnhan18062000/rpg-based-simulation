---
status: active
layer: observability
authority: P0
audience: agent
ticket_id: TCK-20260806-PUSH-SHADOW-VALIDATION-PERF-PHASE2
artifact_type: plan
tags: [observability, engine, simulation-quality, performance]
---

# plan.md — TCK-20260806-PUSH-SHADOW-VALIDATION-PERF-PHASE2

## Ordered Steps

1. Confirm children 2-6's `## Status` directly.
   - No file changes.
2. Build a combined event-stream comparison across all Phase 2 domains, run against 6 real
   worlds x 500 ticks.
   - No file changes; produces the evidence for step 3.
3. Investigate the `urban_political` mismatch found in step 2; root-cause via repeated-run
   variance check, cross-reference against `INFRA-273`.
   - No file changes; investigation finding.
4. Extend `tests/perf/test_simq_isolation_overhead.py` with the Phase 2 full-registry
   overhead gate (2 new committed tests, mirroring child 1's pattern).
   - Files: `tests/perf/test_simq_isolation_overhead.py`
5. Update `docs/performance/simq_isolation_overhead.md` and `docs/parity_ledger/
   infrastructure.yaml` (`INFRA-273`, update in place).
   - Files: as listed.

## Files to Change

- `tests/perf/test_simq_isolation_overhead.py`
- `docs/performance/simq_isolation_overhead.md`, `docs/parity_ledger/infrastructure.yaml`

## Scope Guards

- Do NOT touch any Phase 2 shaper class — this ticket validates, doesn't modify.
- Do NOT recalibrate any anchor or touch `grade_anchors.json` — the `urban_political` mismatch is
  explained, not silently masked by adjusting a baseline.
- Do NOT proceed to cutover — that's child 8's job, gated on this ticket's GO verdict.

## Dependency Map

Steps 1-3 sequential (each depends on the previous). Step 4 independent of 1-3 (perf validation).
Step 5 depends on all prior steps' real findings.

## Acceptance Criteria Map

- AC "children 2-6 confirmed DONE" → step 1
- AC "event-stream comparison, ≥6 worlds, 0 unexplained divergences" → steps 2-3
- AC "full-registry perf re-run passes against committed threshold" → step 4
- AC "infrastructure.yaml updated with validation outcome" → step 5
- AC "explicit GO/NO-GO verdict recorded" → investigation.md's own verdict section
