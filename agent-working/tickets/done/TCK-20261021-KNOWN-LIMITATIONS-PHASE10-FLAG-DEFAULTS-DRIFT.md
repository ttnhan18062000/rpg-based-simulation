---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261021-KNOWN-LIMITATIONS-PHASE10-FLAG-DEFAULTS-DRIFT
phase: done
date: 2026-10-21
tags: []
---

# TCK-20261021-KNOWN-LIMITATIONS-PHASE10-FLAG-DEFAULTS-DRIFT

## Title
known_limitations.md §1.5 says every Phase-10 flag defaults OFF, but feature_flags.py defaults ENABLE_COMBAT_ENGAGEMENT, ENABLE_BELIEF_ASSIMILATION and ENABLE_SOCIAL_COOPERATION to ON

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P3

## Request Summary
Lead-planner-u24 found this on 2026-10-21 by reading the code on origin/main; it was not run. It does not block v1.
- docs/engine/known_limitations.md §1.5 says every Phase-10 flag defaults OFF.
- feature_flags.py defaults ENABLE_COMBAT_ENGAGEMENT, ENABLE_BELIEF_ASSIMILATION and ENABLE_SOCIAL_COOPERATION to ON.

## Scope
- Correct §1.5 to the real defaults (code is truth unless the owner rules otherwise), and check the parity ledger entry.

## Out of Scope
- Anything before v1. The simulation-behaviour freeze holds until the v1 record lands.

## Acceptance Criteria
- The doc matches feature_flags.py.

## Related Tickets
- TCK-20261019-RECORD-BASELINE-V1 (do after it)

## Related Docs
- docs/engine/

## Related Stored Artifacts
- none

## Related Code Areas
- docs/engine/known_limitations.md §1.5, src/core/feature_flags.py

## Assumptions / Open Questions
- This was read from code, not reproduced. Re-verify it before any fix.

## Implementation Notes
Verified against src/domains/optimization/feature_flags.py (the ticket cites src/core/feature_flags.py, which does not exist): ENABLE_COMBAT_ENGAGEMENT, ENABLE_BELIEF_ASSIMILATION, ENABLE_SOCIAL_COOPERATION default ON, the other eight OFF; each flip is deliberate (comment blocks, TCK-20260824-ROLLOUT-FLAG-DECISIONS, TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER) and allowlisted in tests/integration/test_scenario_feature_flag_defaults.py. Code is truth; docs known_limitations.md 1.5 and parity entry INFRA-221 corrected. No code, no runs.

## Test Summary
Docs only. Doc/parity validators and registry check run; no simulation, no pytest.

## Files Changed
docs/engine/known_limitations.md, docs/parity_ledger/infrastructure.yaml (INFRA-221)

## Completion Summary
Docs corrected to match the code; code unchanged. See Implementation Notes.
