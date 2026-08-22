---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260822-GUARD-SCAN-INDEX-RETROFIT
phase: open
date: 2026-08-22
tags: [faction, grand-strategy, performance]
---

# TCK-20260822-GUARD-SCAN-INDEX-RETROFIT

## Title
Retrofit GUARD-entity index into MilitaryConflictPhase's per-war-pair region scan (corrected target)

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Preserves the original intent that E53 shipped without a TerritorialObserver-style seam and needs an index retrofit for faction/region-scoped GUARD-entity queries running an O(N) scan per governance tick. Corrected by investigation: the concern's own title/description misattributed the target to FactionDecisionPhase / src/domains/faction/, which was confirmed to have zero entity/GUARD/border scanning. The real O(N) GUARD-entity scan is MilitaryConflictPhase._find_guard_entities_in_region (src/engine/military_conflict.py, lines 121-137), called once per WAR pair per tick for one already-selected contested_region_id -- not per-faction-per-border as originally framed. This ticket retrofits the corrected, actual call site.

## Scope
- Replace MilitaryConflictPhase._find_guard_entities_in_region(state, region_id)'s full O(N) entity scan with a lookup against the semantic entity index's (TCK-20260822-SEMANTIC-ENTITY-INDEX) role+region dimensions.
- Add net-new test coverage (currently zero) for the >=3-GUARD reinforcement branch (+0.02 service_availability / -0.02 siege_progress) and the squad-commitment branch (GroupRecord capped at 5, FACTION_SQUAD role) before/alongside the retrofit, since neither is exercised by any existing test.
- Correct docs/parity_ledger/faction.yaml FAC-008's v2_evidence/test_path to cite a test that actually covers these branches -- the existing citation (test_siege_model.py) does not.

## Out of Scope
- src/domains/faction/diplomatic_state_machine.py -- investigation found its territorial check is O(faction-pairs), not an O(N) entity scan, and it is not a retrofit target despite being named in the original proposal.
- src/engine/faction_decision.py -- confirmed to have zero entity/GUARD/border scanning (only 3 tension/territory/military-strength rules); not part of this retrofit.
- Any per-faction-per-border query pattern -- the real call site is scoped per-WAR-pair to one already-selected contested_region_id, not the broader per-faction-per-border shape the original concern assumed.

## Acceptance Criteria
- [ ] Index-backed replacement for _find_guard_entities_in_region(state, region_id) returns an identical sorted List[int] of GUARD-role entity IDs to the current full-scan implementation, verified by a new test populating mixed GUARD/non-GUARD entities across regions.
- [ ] New test asserts the reinforcement branch fires +0.02/-0.02 deltas when >=3 GUARD entities are present in the contested region.
- [ ] New test asserts squad commitment produces a GroupRecord capped at 5 when >5 GUARD entities are present.
- [ ] FAC-008's v2_evidence/test_path in docs/parity_ledger/faction.yaml is updated to cite the new/corrected test coverage.

## Related Tickets
- TCK-20260619-E53Cb-SIEGE-MODEL
- TCK-20260619-E53Ca-CONFLICT-PHASE
- TCK-20260619-E53Ab-DECISION-PHASE
- TCK-20260619-E53-FACTION-DIPLOMACY
- TCK-20260702-PLANS-IDEA-REFRESH
- TCK-20260822-SEMANTIC-ENTITY-INDEX

## Related Docs
- docs/parity_ledger/faction.yaml
- docs/engine/performance_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/military_conflict.py
- src/engine/faction_decision.py
- src/domains/faction/diplomatic_state_machine.py
- tests/unit/domains/faction/test_military_conflict_phase.py
- tests/unit/domains/faction/test_siege_model.py
- tests/integration/scenarios/test_faction_campaign.py
- tests/unit/domains/faction/test_faction_decision_phase.py

## Assumptions / Open Questions
- Depends on TCK-20260822-SEMANTIC-ENTITY-INDEX's index existing (or a scoped equivalent) before/alongside this retrofit.
- The corrected target (military_conflict.py) diverges from the original idea doc's wording (which named src/domains/faction/) -- flagged explicitly so future readers aren't confused by the mismatch.
- `layer: engine` chosen over a faction-specific layer since none is registered in registries/layer_registry.jsonl and the actual retrofit target (src/engine/military_conflict.py) is an engine-phase file; `faction` remains a registered tag instead.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
