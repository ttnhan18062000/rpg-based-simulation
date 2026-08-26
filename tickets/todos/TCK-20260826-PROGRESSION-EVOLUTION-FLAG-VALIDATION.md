---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION
phase: open
date: 2026-08-26
tags: [feature-flags]
---

# TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION

## Title
Produce real validation evidence for `ENABLE_PROGRESSION_EVOLUTION` before deciding its default

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Named follow-up from `TCK-20260824-ROLLOUT-FLAG-DECISIONS`: `ENABLE_PROGRESSION_EVOLUTION` was
kept `OFF` by default -- real call site (`ProgressionConversionPhase.execute`, gated by the
`progression_conversion` phase name at `src/engine/pipeline.py:322`), 2 test files, but no corpus
profile turns it on and no SHADOW-validation history exists. This confirms
`TCK-20260824-ROLLOUT-FLAG-DECISIONS`'s own open Assumption: the M1 epic plan's "Progression
Conversion" prose naming maps to this exact flag. This ticket's job is to produce real evidence.

## Scope
- Run a real corpus-profile trial with the flag `ON` against at least one world.
- Given only 2 test files reference this flag (the thinnest coverage of the 5 deferred flags),
  confirm real test depth before trusting a trial's result -- a false-clean pass from shallow
  coverage would be worse than an honest "not enough coverage to trust a trial yet" finding.
- Produce a real keep/flip recommendation with evidence.

## Out of Scope
- Actually flipping the flag's default.
- Writing new test coverage beyond what's needed to trust the trial itself (a full coverage
  build-out, if warranted, is its own separate scope decision).

## Acceptance Criteria
- [ ] Test coverage depth is assessed honestly before the trial, not assumed adequate
- [ ] A real corpus-profile ON trial is run and documented
- [ ] A keep/flip recommendation with evidence is produced

## Related Tickets
- TCK-20260824-ROLLOUT-FLAG-DECISIONS (source of this deferral; also resolved the
  Progression-Conversion-naming-maps-to-this-flag assumption)

## Related Docs
- docs/guidelines/intentional_divergences.md (DEV-002, DEV-003)

## Related Stored Artifacts
- staging_artifacts/TCK-20260824-ROLLOUT-FLAG-DECISIONS/investigation.md

## Related Code Areas
- src/engine/pipeline.py (progression_conversion phase)
- src/domains/optimization/feature_flags.py

## Assumptions / Open Questions
None yet -- to be surfaced during this ticket's own investigation.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
