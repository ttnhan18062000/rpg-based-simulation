---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260805-SIMQ-CROSS-PILLAR-CORRELATION-INVESTIGATION
artifact_type: plan
tags: [simulation-quality, calibration]
---

# plan.md — TCK-20260805-SIMQ-CROSS-PILLAR-CORRELATION-INVESTIGATION

## Ordered Steps

1. **Analyze all 76 real calibration reports** for cross-pillar tick-window overlap in negative
   `worst_events` — no files changed, analysis only.
2. **Verify any apparent signal by tracing the actual events** rather than trusting the raw
   correlation number — found the one apparent 81% signal (PROGRESSION↔SOCIAL) is a methodological
   artifact (a fixed-tick constant colliding with a near-continuous event stream), not a real
   compound-failure signature.
3. **Document the conclusion** in `docs/simulation_quality/extension_points.md`'s axis 11.
   - Files: `docs/simulation_quality/extension_points.md`.
4. **Fill this ticket's Completion Summary.**

## Scope Guards

- Do NOT implement any correlation-detection mechanism — investigation-only, confirmed nothing
  real to detect in the current corpus.
- Do NOT touch the Scenario Registry's existing SQ-03 hand-written rule.

## Dependency Map

Step 2 depends on step 1's raw numbers. Step 3 depends on step 2's verified conclusion.

## Acceptance Criteria Map

- AC1 (concrete corpus-wide finding, named pairs, tick-range evidence) → investigation.md's table
  and event-tracing.
- AC2 (extension_points.md axis 11 updated with the finding) → Step 3.
- AC3 (design sketch if a follow-up is justified) → N/A — no follow-up justified by this finding.

No unresolved questions requiring human review.
