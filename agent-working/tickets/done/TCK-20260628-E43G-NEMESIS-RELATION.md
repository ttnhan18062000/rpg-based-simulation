---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260628-E43G-NEMESIS-RELATION
phase: done
date: 2026-06-28
tags: [narrative, consequence, nemesis, social, campaigns, p3]
---

# TCK-20260628-E43G-NEMESIS-RELATION

## Title
NemesisRelation — detection from interaction history, importer, and FORM_PARTY route block

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Create a `NemesisRelation` typed record, detect nemesis relationships from
`SocialMemoryRecord.interaction_history` across 2+ distinct negative-interaction episodes,
carry the record forward in `CampaignState.nemesis_relations`, inject a SOCIAL BlockerState
at episode start, and block FORM_PARTY route generation when a nemesis is among candidates.

## Scope
- `NemesisRelation` frozen dataclass in `src/domains/campaigns/state.py`
- `CampaignState.nemesis_relations: Dict[str, NemesisRelation]` with to_dict/from_dict
- `NemesisRelationImporter.apply()` in `src/domains/campaigns/grief_urgency.py`
- `CampaignOrchestrator._advance_nemesis_relations()` in orchestrator.py
- Episode-start nemesis import loop in orchestrator.py
- FORM_PARTY route nemesis check in `src/domains/adventure/generator.py`
- 9 E43G tests in `tests/unit/campaigns/test_grief_urgency.py`
- SOC-232 parity ledger entry in `docs/parity_ledger/social_narrative.yaml`

## Out of Scope
- Observability surface (E43H)
- Revenge-flavored route motivation bonus (deferred)
- Faction-level nemesis tracking

## Acceptance Criteria
- [x] `NemesisRelation` frozen dataclass with protagonist_id, antagonist_id, formation_episode, antagonism_count, strength; to_dict/from_dict round-trip
- [x] `CampaignState.nemesis_relations` field with serialisation support
- [x] `NemesisRelationImporter.apply()` injects BlockerState(kind=SOCIAL, subject=str(antagonist_id))
- [x] `_advance_nemesis_relations()` detects from SocialMemoryRecord.interaction_history (kinds: "betrayed", "conflict") across 2+ distinct episodes
- [x] Strength = min(1.0, count × 0.4)
- [x] FORM_PARTY route blocked (blockers=("nemesis_block",)) when nemesis in candidates
- [x] 9 tests all pass; 174 campaign+adventure tests pass
- [x] SOC-232 parity ledger entry added

## Related Tickets
- Parent epic: TCK-20260628-E-NARRATIVE-CONSEQUENCE
- Predecessor: TCK-20260628-E43F-GRIEF-URGENCY
- Successor: TCK-20260628-E43H-NARRATIVE-OBS

## Related Docs
- `docs/parity_ledger/social_narrative.yaml` — SOC-232

## Related Stored Artifacts
- N/A

## Related Code Areas
- `src/domains/campaigns/state.py`
- `src/domains/campaigns/grief_urgency.py`
- `src/domains/campaigns/orchestrator.py`
- `src/domains/adventure/generator.py`
- `tests/unit/campaigns/test_grief_urgency.py`

## Assumptions / Open Questions
- Detection uses SocialMemoryRecord.interaction_history (not NarrativeLedgerEntry directly) because entity_death entries don't carry antagonist info.
- Key format "{protagonist_id}:{antagonist_id}" is stable string for dict lookups.

## Implementation Notes
- `NEMESIS_EPISODE_COUNT = 2`, `NEMESIS_INTERACTION_KINDS = frozenset({"betrayed", "conflict"})`
- Detection groups interaction_history by other_entity_id, counts distinct episodes per negative kind
- Existing nemesis relations are overwritten (strength/count updated) if count increases
- SOCIAL blocker subject is str(antagonist_id); `.isdigit()` check in generator.py ensures only numeric subjects are treated as nemesis ids
- Tests use `object.__new__(CampaignOrchestrator)` + `orch._state = state` to bypass full init

## Test Summary
9 tests in `tests/unit/campaigns/test_grief_urgency.py` (E43G group):
- NemesisRelation round-trip serialisation
- NemesisRelationImporter injects SOCIAL blocker; does not mutate original
- Detection creates relation at 2 episodes; not at 1; not for positive interactions
- Strength scales with count (3 episodes → 1.2 → clamped 1.0)
- CampaignState round-trip with nemesis_relations; from_dict missing field defaults to {}

174 campaign + adventure tests pass.

## Files Changed
- `src/domains/campaigns/state.py` — NemesisRelation dataclass; CampaignState.nemesis_relations
- `src/domains/campaigns/grief_urgency.py` — NemesisRelationImporter; NEMESIS_* constants
- `src/domains/campaigns/orchestrator.py` — _advance_nemesis_relations(); episode-start import loop
- `src/domains/adventure/generator.py` — FORM_PARTY nemesis check
- `tests/unit/campaigns/test_grief_urgency.py` — 9 E43G tests added
- `docs/parity_ledger/social_narrative.yaml` — SOC-232 added

## Completion Summary
NemesisRelation typed record implemented and wired end-to-end: detection from interaction history → CampaignState persistence → episode-start blocker injection → FORM_PARTY route scoring penalty. All 9 E43G tests pass; 174 total campaign+adventure tests pass.
