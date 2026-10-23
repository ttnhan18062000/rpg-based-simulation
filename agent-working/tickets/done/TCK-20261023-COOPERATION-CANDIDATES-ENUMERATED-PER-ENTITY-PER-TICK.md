---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261023-COOPERATION-CANDIDATES-ENUMERATED-PER-ENTITY-PER-TICK
phase: done
date: 2026-10-23
tags: []
---

# TCK-20261023-COOPERATION-CANDIDATES-ENUMERATED-PER-ENTITY-PER-TICK

## Title
Cooperation partner candidates are enumerated per entity per tick (O(n^2)); build the candidate source once per tick (H2)

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
From docs/plans/architecture/faster_feature_testing_draft_tickets.md (H2, PR #719; user-approved hotspot plan #715 6338321859, lead post #593 6338326690). `PartnerCandidateProvider.get_candidates` (`src/domains/cooperation/providers.py:33`) loops over every entity in `state.entities` for each requesting entity (`:43`), calling `are_entities_hostile` per candidate (`:52-53`, also the H1 path). tick_cost_growth.md section 3 H2: 43-61 % of strategic_100, 27 % of mixed_200, 10-27 % of corpus worlds; cooperation is 31 % of frontier_marches early ticks. #394 fixed only the pending-offer lookup in the same phase.

## Scope
1. Build the candidate source once per tick (e.g. a spatial bucket plus the trusted-social set); `get_candidates` reads it.
2. Keep the selection order and the result exactly (the #394 pattern: per-tick index plus a differential test against the old scan).

## Out of Scope
Hostility semantics (H1, Lane B). Changing which partners are chosen.

## Acceptance Criteria
- Identical canonical hashes on the corpus under audit_mode (performance_contract.md 4.1), and `paired.py --neutral` IDENTICAL.
- A differential test: the old scan and the index give the same candidate tuple on fixed states.
- Before/after cooperation phase cost on strategic_100 and one corpus world, same host, same method (perf-planner reviews the measurement).

## Related Tickets
TCK-20261019-RECORD-BASELINE-V1 (v1 recorded 341f700d0; after-v1 work).

## Related Docs
#593 (lead-planner relays); docs/plans/architecture/faster_feature_testing_draft_tickets.md; docs/engine/performance_contract.md.

## Related Stored Artifacts

## Related Code Areas
src/domains/cooperation/providers.py; src/engine/cooperation*

## Assumptions / Open Questions
Coordinate with H1 (hostility per pair, Lane B): both sit on the `are_entities_hostile` path. Paired runs queue behind other heavy host work (one heavy process at a time).

## Implementation Notes
PartnerCandidateIndex (providers.py) built once per tick in CooperationPhase.execute; see the staging investigation for the design and the evidence block.

## Test Summary
tests/unit/domains/cooperation (incl. new test_candidate_index_differential.py) and tests/unit/combat/test_catalog_hostility_sweep.py: 123 passed. Hash x3 worlds equal, paired --neutral IDENTICAL, cooperation phase -64 % (strategic_100) / -85 % (frontier_marches).

## Files Changed
src/domains/cooperation/providers.py, src/domains/cooperation/phase.py, tests/unit/domains/cooperation/test_candidate_index_differential.py, seven planner todo tickets carried.

## Completion Summary
Candidate source indexed once per tick; selection result identical; cooperation phase 3-6x cheaper on the measured scenarios.
