---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING
phase: open
date: 2026-08-28
tags: [social, cognition, progression]
---

# TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING

## Title
Wire ReputationUpdateService to a Real Witnessed-Event Source

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`ReputationUpdateService.process_witnessed_event()` (`src/domains/commitment/reputation.py`) was
split out of `TCK-20260824-WIRE-ORPHANED-MECHANISMS` during that ticket's Investigate phase because,
unlike the other 6 orphaned mechanisms in that ticket's original scope, none of its 3 recognized
`event_kind` strings (`successful_escort`, `betrayal`, `clear_camp`) has any real, already-detected
production event to attach to. Wiring it meaningfully requires new domain logic first, not just a
call-site insertion — a genuinely different shape of work than the parent ticket's remaining 6
mechanisms.

## Scope
- Decide and implement a real detection path for at least one of the 3 recognized `event_kind`
  strings, OR re-scope `ReputationUpdateService.process_witnessed_event()`'s recognized event-kind
  set to match a real, already-detected production event (planning decision, not assumed) — the two
  concrete options surfaced by the parent ticket's investigation are:
  1. Add a new `QuestKind.ESCORT` value and wire `successful_escort` off `QuestResolutionSystem.enforce()`'s
     existing quest-completion detection (`src/engine/quests.py:154-231`, `is_newly_completed`), OR
  2. Activate the currently dead-but-implemented `CooperationLearningService.learn()` betrayal branch
     (`src/domains/cooperation/services.py:329-360`, `out_type == "betrayal"`) by actually calling it
     from `CooperationPhase` (`src/domains/cooperation/phase.py`), then route its output into
     `ReputationUpdateService.process_witnessed_event(profile, "betrayal")`
- Wire the chosen real detection site to call `ReputationUpdateService.process_witnessed_event()`
- Apply the returned `PublicReputationProfile` through `EntityUpdate.cognition_bundle_set`
  (`src/core/updates.py:655`, applied in `src/engine/patches.py:742-743`) — the only existing typed
  authoritative path back into durable `entity.cognition.public_reputation` state, following the
  working precedent at `src/domains/memory/phase.py:51`
- Add or update parity ledger entries for this mechanism (none currently exist for
  `ReputationUpdateService` anywhere in `docs/parity_ledger/`)

## Out of Scope
- Any of the other 6 mechanisms already wired by the parent ticket `TCK-20260824-WIRE-ORPHANED-MECHANISMS`
- `clear_camp` event kind, unless the chosen implementation approach naturally covers it too (no
  existing quest-kind or event constant matches it today — inventing one is a separate decision,
  not required by this ticket's minimum scope)
- `ReputationService` (`src/systems/social_systems/reputation.py`) — a separately orphaned class
  discovered during the parent ticket's investigation, thematically adjacent but not part of this
  ticket's scope; touching it would be scope creep

## Acceptance Criteria
- [ ] A planning decision is made and documented for which real event source
  `ReputationUpdateService.process_witnessed_event()` will attach to (new QuestKind.ESCORT vs.
  activating CooperationLearningService's betrayal branch vs. another evidenced option)
- [ ] `ReputationUpdateService.process_witnessed_event()` is called from that real, production event
  source — not a synthetic/unreachable trigger
- [ ] The returned `PublicReputationProfile` is applied via `EntityUpdate.cognition_bundle_set`
  through the authoritative apply path
- [ ] A parity ledger entry exists for this mechanism with a passing `test_path`
- [ ] Regression tests in `tests/unit/domains/commitment/`,
  `tests/integration/scenarios/test_phase15_commitment_reputation_scenarios.py`, and (if
  QuestKind.ESCORT is added) `tests/unit/engine/test_quests*.py`/quest-kind stability guards all pass

## Related Tickets
- TCK-20260824-WIRE-ORPHANED-MECHANISMS (parent ticket — this was split out of its Investigate phase)
- TCK-20260618-AUDIT-D11-DEAD

## Related Docs
- docs/simulation/domains/commitment_contract.md (already documents the target-state call site in
  language that will become accurate once this ticket lands)

## Related Stored Artifacts
- stored_artifacts/TCK-20260824-WIRE-ORPHANED-MECHANISMS/investigation.md (once migrated from
  staging_artifacts/ — see "5. ReputationUpdateService.process_witnessed_event()" section for the
  full duplicate/reachability evidence this ticket is based on)

## Related Code Areas
- src/domains/commitment/reputation.py
- src/domains/commitment/__init__.py
- src/engine/quests.py
- src/core/models/quests.py
- src/domains/cooperation/services.py
- src/domains/cooperation/phase.py
- src/core/updates.py
- src/engine/patches.py
- src/domains/memory/phase.py
- docs/parity_ledger/social_narrative.yaml

## Assumptions / Open Questions
- Neither of the two candidate real-event-source options (new QuestKind.ESCORT, or activating
  CooperationLearningService's betrayal branch) has been chosen yet — this is the central open
  question this ticket's own Investigate/Plan phases must resolve before implementation, not
  something to assume from this scoping pass.
- If neither candidate proves viable without disproportionate scope growth, re-scoping
  `ReputationUpdateService.process_witnessed_event()`'s recognized `event_kind` literals themselves
  (rather than inventing a new detection mechanism) is an acceptable alternative outcome, but must be
  justified against the Mechanics Bible / existing `docs/simulation/domains/commitment_contract.md`
  target-state language, not done silently.
- `layer: engine` and `tags: [social, cognition, progression]` inherited from the parent ticket's own
  choices (already registry-valid) since this ticket is a direct scope-split of the same investigation.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
