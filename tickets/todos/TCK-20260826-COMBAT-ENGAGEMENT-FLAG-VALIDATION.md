---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION
phase: open
date: 2026-08-26
tags: [feature-flags]
---

# TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION

## Title
Produce real validation evidence for `ENABLE_COMBAT_ENGAGEMENT` before deciding its default

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Named follow-up from `TCK-20260824-ROLLOUT-FLAG-DECISIONS`: `ENABLE_COMBAT_ENGAGEMENT` was kept
`OFF` by default because it has a real fix history (`TCK-20260809-COMBAT-ENGAGEMENT-FLAG-
SUPPRESSES-PUSH-SHAPER-EVENTS`, a genuine bug found and fixed via one-off live corpus A/B testing)
but no standing production validation -- no SimQ corpus profile turns it on today. This ticket's
job is to produce that evidence (a real corpus-profile trial, or documented reasons it should stay
deferred), not to flip the flag itself.

## Scope
- Run `src/domains/combat_engagement/phase.py`'s real behavior against at least one SimQ corpus
  world with the flag explicitly `ON`, comparing against the same world with it `OFF`.
- Confirm the `TCK-20260809-...` fix (the `u.merge(...)` pattern in `src/engine/pipeline.py`) still
  holds under this trial -- combat push-shaper events must not be suppressed.
- Produce a real keep/flip recommendation with evidence, mirroring
  `TCK-20260824-ROLLOUT-FLAG-DECISIONS`'s own decision-artifact format.

## Out of Scope
- Actually flipping the flag's default -- that's this ticket's own eventual recommendation feeding
  back into a decision, not something to do unilaterally here.
- Any new gameplay content for the combat-engagement system itself.

## Acceptance Criteria
- [ ] A real corpus-profile ON/OFF comparison is run and documented
- [ ] A keep/flip recommendation with evidence is produced
- [ ] If flip is recommended, a concrete next-step ticket is named (not flipped here)

## Related Tickets
- TCK-20260824-ROLLOUT-FLAG-DECISIONS (source of this deferral)
- TCK-20260809-COMBAT-ENGAGEMENT-FLAG-SUPPRESSES-PUSH-SHAPER-EVENTS (the real fix this validation
  must confirm still holds)

## Related Docs
- docs/guidelines/intentional_divergences.md (DEV-002, DEV-003)

## Related Stored Artifacts
- staging_artifacts/TCK-20260824-ROLLOUT-FLAG-DECISIONS/investigation.md (the evidence gathered so
  far)

## Related Code Areas
- src/domains/combat_engagement/phase.py
- src/engine/pipeline.py
- src/domains/optimization/feature_flags.py

## Assumptions / Open Questions
- Which corpus world(s) are the right trial subject -- not decided here.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
