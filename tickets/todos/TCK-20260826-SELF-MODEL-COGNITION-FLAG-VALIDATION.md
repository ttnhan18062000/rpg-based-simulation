---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION
phase: open
date: 2026-08-26
tags: [feature-flags]
---

# TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION

## Title
Produce real validation evidence for `ENABLE_SELF_MODEL_COGNITION` before deciding its default

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Named follow-up from `TCK-20260824-ROLLOUT-FLAG-DECISIONS`: `ENABLE_SELF_MODEL_COGNITION` was kept
`OFF` by default -- real call site (`src/cognition/self_model_phase.py`), 10 test files, but no
corpus profile turns it on and no SHADOW-validation history exists. The now-removed, dead
`RolloutProfileManager` had listed this flag as CLASS_A/B/C default-enabled, but that matrix was
never wired to anything real -- not usable as evidence. This ticket's job is to produce real
evidence.

## Scope
- Run a real corpus-profile trial with the flag `ON`, at minimum against `urban_political.yaml`
  (already noted in `tests/integration/test_world_profile_feature_flag_guardrail.py`'s
  `known_exceptions` as a world where self-model content is seeded but the flag has never shipped
  ON, cited to `INFRA-259`/`INFRA-260` -- read that citation and the guardrail test's own
  documented exception before starting).
- Confirm the untested `ENABLE_SELF_MODEL_COGNITION` + `ENABLE_ADVENTURE_ROUTING` combination
  (flagged as an open question in `TCK-20260824-ROLLOUT-FLAG-DECISIONS`) is either safe or
  documented as unsafe.
- Produce a real keep/flip recommendation with evidence.

## Out of Scope
- Actually flipping the flag's default.
- Resolving `urban_political`'s own `INFRA-259`/`INFRA-260` exception unless this ticket's own
  trial directly requires it.

## Acceptance Criteria
- [ ] A real corpus-profile ON trial is run and documented
- [ ] The `ENABLE_SELF_MODEL_COGNITION` + `ENABLE_ADVENTURE_ROUTING` combination question is
      resolved, not left open again
- [ ] A keep/flip recommendation with evidence is produced

## Related Tickets
- TCK-20260824-ROLLOUT-FLAG-DECISIONS (source of this deferral)

## Related Docs
- docs/guidelines/intentional_divergences.md (DEV-002, DEV-003)
- docs/parity_ledger/infrastructure.yaml (INFRA-259, INFRA-260)

## Related Stored Artifacts
- staging_artifacts/TCK-20260824-ROLLOUT-FLAG-DECISIONS/investigation.md

## Related Code Areas
- src/cognition/self_model_phase.py
- src/domains/optimization/feature_flags.py
- tests/integration/test_world_profile_feature_flag_guardrail.py

## Assumptions / Open Questions
- Whether `urban_political`'s existing seeded-but-unflagged self-model content is itself evidence
  worth investigating first (why was content seeded without ever flipping the flag) -- not decided
  here.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
