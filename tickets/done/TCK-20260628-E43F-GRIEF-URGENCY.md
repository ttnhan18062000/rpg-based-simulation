---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260628-E43F-GRIEF-URGENCY
phase: done
date: 2026-06-28
tags: [narrative, consequence, grief, urgency, campaign, motivation, p3]
---

# TCK-20260628-E43F-GRIEF-URGENCY

## Title
Grief/rage urgency modifier from ally deaths (E43F)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Chronicle events (ally deaths) are not fed back into entity motivation at runtime.
E43F wires the first feedback path: when an entity's ally dies in episode N and the
surviving entity had a positive social memory toward the victim (trust ≥ 0.30), inject
a timed grief urgency modifier. The modifier manifests as a SOCIAL_THREAT concern in
entity.strategic.concerns, making it inspectable in the decision trace. Urgency decays
0.25 per episode.

## Scope
1. `src/domains/campaigns/state.py` — `GriefUrgencyModifier` frozen dataclass;
   `CampaignState.grief_urgencies: Dict[int, GriefUrgencyModifier]` field with
   `to_dict()`/`from_dict()` round-trip.
2. `src/domains/campaigns/grief_urgency.py` — `GriefUrgencyImporter.apply(entity, modifier)`
   injects `ConcernState(kind=SOCIAL_THREAT)` into entity.strategic.concerns.
3. `src/domains/campaigns/orchestrator.py` — `_advance_grief_urgencies()` method:
   detects entity_death entries + ally trust check → create modifier; decays existing
   modifiers each episode. Episode-start loop applies GriefUrgencyImporter.
4. `docs/parity_ledger/social_narrative.yaml` — SOC-231 added.
5. Tests: 13 new E43F tests in `tests/unit/campaigns/test_grief_urgency.py`.

## Out of Scope
- NemesisRelation formation from repeated antagonist appearances (E43G).
- Decision-trace observability surface (E43H).
- Route scoring adjustment based on grief urgency (follow-on work).
- Faction-level narrative consequences.

## Acceptance Criteria
- [x] GriefUrgencyModifier is a frozen dataclass with entity_id, dead_ally_id, episode,
      urgency, decay_per_episode (default 0.25)
- [x] Modifier created when trust_score ≥ ALLY_TRUST_THRESHOLD (0.30) in social memory
- [x] urgency = min(1.0, trust_score × 0.8)
- [x] Urgency decays 0.25 per episode; removed when ≤ 0
- [x] GriefUrgencyImporter injects SOCIAL_THREAT ConcernState with deterministic id
      "grief_ally_{dead_ally_id}" into entity.strategic.concerns
- [x] CampaignState.to_dict()/from_dict() round-trips with grief_urgencies
- [x] SOC-231 added to parity ledger
- [x] All 109 campaign unit+integration tests pass

## Related Tickets
- Parent: TCK-20260628-E-NARRATIVE-CONSEQUENCE
- Next: TCK-20260628-E43G-NEMESIS-RELATION

## Related Docs
- `docs/parity_ledger/social_narrative.yaml` (SOC-231 added)
- `docs/mechanics/04_strategic_cognition.md` (motivation urgency model)

## Related Code Areas
- `src/domains/campaigns/state.py` (GriefUrgencyModifier, CampaignState.grief_urgencies)
- `src/domains/campaigns/grief_urgency.py` (GriefUrgencyImporter)
- `src/domains/campaigns/orchestrator.py` (_advance_grief_urgencies, import loop)
- `src/core/strategic.py` (ConcernState, ConcernKind.SOCIAL_THREAT)
- `tests/unit/campaigns/test_grief_urgency.py`

## Implementation Notes
- `MotivationState` does not exist as a class — injection hook found in
  `entity.strategic.concerns: Dict[str, ConcernState]` (ConcernState has `urgency: float`).
- `ConcernKind.SOCIAL_THREAT` is the closest semantic match for grief-driven urgency.
- Non-death entries (quest_completed, faction_shift) produce no grief modifiers.
- Injection follows same SocialMemoryImporter.apply() pattern — new entity returned
  via dc_replace(), original not mutated.
- `_advance_grief_urgencies()` accesses via `object.__new__(CampaignOrchestrator)` in
  tests to avoid full orchestrator initialization.

## Test Summary
- 2 serialisation tests (GriefUrgencyModifier round-trip, CampaignState round-trip)
- 4 importer tests (concern injected, no mutation, overwrite, source naming)
- 7 detection/decay tests (grief created above threshold, not below threshold,
  decay reduces urgency, decay removes at zero, non-death entries ignored,
  CampaignState from_dict missing field → empty dict)
- All 109 campaign unit+integration tests pass (0 regressions)

## Files Changed
- `src/domains/campaigns/state.py` (GriefUrgencyModifier added, CampaignState field +
  to_dict/from_dict)
- `src/domains/campaigns/grief_urgency.py` (new file — GriefUrgencyImporter)
- `src/domains/campaigns/orchestrator.py` (imports, _advance_grief_urgencies, import loop)
- `docs/parity_ledger/social_narrative.yaml` (SOC-231)
- `tests/unit/campaigns/test_grief_urgency.py` (13 tests)

## Completion Summary
Grief/rage urgency modifier fully implemented. Ally deaths at episode N produce a
SOCIAL_THREAT concern in the grieving entity's strategic.concerns in episode N+1,
with urgency proportional to trust (max 0.8) decaying 0.25/episode. 13 tests pass;
SOC-231 added; 0 regressions across 109 campaign tests.
