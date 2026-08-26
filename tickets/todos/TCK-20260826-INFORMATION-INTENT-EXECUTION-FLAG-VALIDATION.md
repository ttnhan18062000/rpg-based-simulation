---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION
phase: open
date: 2026-08-26
tags: [feature-flags]
---

# TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION

## Title
Produce real validation evidence for `ENABLE_INFORMATION_INTENT_EXECUTION` before deciding its
default

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Named follow-up from `TCK-20260824-ROLLOUT-FLAG-DECISIONS`: `ENABLE_INFORMATION_INTENT_EXECUTION`
was kept `OFF` by default -- real call site
(`src/engine/pipeline_phases/information_intent_execution.py`), 5 test files, but no corpus
profile turns it on and no SHADOW-validation history exists. Note this flag is a distinct system
from `ENABLE_BELIEF_ASSIMILATION` (already flipped ON this same ticket, `DEV-003`) -- both live in
the information/belief domain but gate different phases; do not conflate them when investigating.

## Scope
- Confirm precisely (read, not assume) what `information_intent_execution` actually does
  differently from the now-ON `information_belief`/`ENABLE_BELIEF_ASSIMILATION` phase, since both
  share a domain and the distinction matters for a correct trial design.
- Run a real corpus-profile trial with the flag `ON` against at least one world, now that
  `ENABLE_BELIEF_ASSIMILATION` (a related, same-domain flag) is globally ON -- confirm no
  unexpected interaction between the two.
- Produce a real keep/flip recommendation with evidence.

## Out of Scope
- Actually flipping the flag's default.
- Re-litigating `ENABLE_BELIEF_ASSIMILATION`'s own already-decided ON default.

## Acceptance Criteria
- [ ] The distinction from `ENABLE_BELIEF_ASSIMILATION`/`information_belief` is confirmed and
      documented, not assumed
- [ ] A real corpus-profile ON trial is run and documented, with `ENABLE_BELIEF_ASSIMILATION` left
      at its now-ON default (not artificially turned off for the trial)
- [ ] A keep/flip recommendation with evidence is produced

## Related Tickets
- TCK-20260824-ROLLOUT-FLAG-DECISIONS (source of this deferral; also flipped the related
  `ENABLE_BELIEF_ASSIMILATION` ON)

## Related Docs
- docs/guidelines/intentional_divergences.md (DEV-002, DEV-003)

## Related Stored Artifacts
- staging_artifacts/TCK-20260824-ROLLOUT-FLAG-DECISIONS/investigation.md

## Related Code Areas
- src/engine/pipeline_phases/information_intent_execution.py
- src/domains/optimization/feature_flags.py

## Assumptions / Open Questions
- Whether this flag and `ENABLE_BELIEF_ASSIMILATION` were ever meant to ship together as one
  logical unit, or are genuinely independent -- not resolved here.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
