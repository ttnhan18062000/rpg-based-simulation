---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260805-SIMQ-CROSS-PILLAR-CORRELATION-INVESTIGATION
phase: open
date: 2026-08-05
tags: [simulation-quality, calibration]
---

# TCK-20260805-SIMQ-CROSS-PILLAR-CORRELATION-INVESTIGATION

## Title
Investigate whether correlated degradation across pillars actually occurs in the corpus, before building any cross-pillar correlation signal

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
Every SimQ pillar currently scores fully independently — confirmed via direct check (2026-08-05):
the only cross-pillar reasoning anywhere in the system is one hand-written instance in the Scenario
Registry (SQ-03: "WORLD only scored if attrition correlates with spawn config"), not a general
mechanism. This is a real, named gap relative to the "do the scores help troubleshoot" quality
question raised earlier this session (2026-08-03) — if two pillars degrade in the same tick range
today, nothing surfaces that as a compound signal distinct from two coincidental, unrelated grades.

This is filed as an investigation, not a build ticket, because there is currently **zero evidence**
that correlated degradation actually happens often enough in the real corpus to be worth building
detection for. Building a cross-pillar correlation layer before knowing that would be exactly the
kind of premature, unvalidated feature this project's own architecture guidance warns against.

## Scope
- Across the full calibration corpus (fresh `make simq-full-audit-full` run), for every pair of
  pillars, check whether their `worst_events`/degraded tick ranges actually overlap or co-occur
  more often than chance in any real report.
- Produce a concrete finding: either (a) real, non-trivial correlation exists between specific
  pillar pairs (name them, with tick-range evidence), justifying a follow-up build ticket, or (b)
  no meaningful correlation is found in the current corpus, in which case this axis stays
  documented-but-unbuilt until the corpus itself changes.
- If (a): sketch (not implement) what a minimal cross-pillar correlation layer would look like,
  for a future ticket to pick up.

## Out of Scope
- Implementing any actual correlation-detection mechanism — this ticket is investigation-only.
- Changing the Scenario Registry's existing SQ-03 hand-written rule.
- Any change to individual pillar scorers.

## Acceptance Criteria
1. A concrete, corpus-wide finding on whether correlated pillar degradation occurs, with named
   pillar pairs and tick-range evidence if found (not a plausibility argument).
2. `docs/simulation_quality/extension_points.md`'s axis 11 is updated with this ticket's finding
   (either "validated, follow-up ticket X filed" or "investigated, no meaningful correlation found
   in current corpus, revisit if corpus composition changes substantially").
3. If a follow-up build is justified, the design sketch (Scope's last bullet) is concrete enough
   that a future ticket could scope it directly without re-investigating from scratch.

## Related Tickets
None — first ticket on this axis.

## Related Docs
- `docs/simulation_quality/extension_points.md` §11 (Cross-pillar correlation) — the axis this
  investigates.
- `docs/simulation_quality/quality_scoring_contract.md` §6 (Scenario Registry, SQ-03's existing
  hand-written cross-pillar rule — the one precedent to build on/generalize from if warranted).

## Related Stored Artifacts
None yet — standard tier, staging artifacts to be created at Scope.

## Related Code Areas
- `src/simulation_quality/quality_report.py` (`QualityReport`, `worst_events` per pillar)
- `src/simulation_quality/quality_hub.py`

## Assumptions / Open Questions
- What counts as "meaningful" correlation (tick-range overlap threshold, co-occurrence frequency
  across how many reports) is not pre-defined — the investigation phase must propose and justify a
  concrete threshold rather than eyeballing it.

## Implementation Notes
(fill during implementation)

## Test Summary
(fill during implementation)

## Files Changed
(fill during implementation)

## Completion Summary
(fill during implementation)
