---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING
phase: done
date: 2026-08-28
tags: [social, cognition, progression]
---

# TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING

## Title
Wire ReputationUpdateService to a Real Witnessed-Event Source

## Status
DONE

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
- [x] A planning decision is made and documented for which real event source
  `ReputationUpdateService.process_witnessed_event()` will attach to (new QuestKind.ESCORT vs.
  activating CooperationLearningService's betrayal branch vs. another evidenced option)
- [x] `ReputationUpdateService.process_witnessed_event()` is called from that real, production event
  source — not a synthetic/unreachable trigger
- [x] The returned `PublicReputationProfile` is applied via `EntityUpdate.cognition_bundle_set`
  through the authoritative apply path
- [x] A parity ledger entry exists for this mechanism with a passing `test_path`
- [x] Regression tests in `tests/unit/domains/commitment/`,
  `tests/integration/scenarios/test_phase15_commitment_reputation_scenarios.py`, and (if
  QuestKind.ESCORT is added) `tests/unit/engine/test_quests*.py`/quest-kind stability guards all pass
  (real path: `tests/unit/quest/test_quest_system.py` — no `tests/unit/engine/test_quests*.py` file
  exists, per plan.md's Anti-Drift Notes)

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

Implemented per `staging_artifacts/TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING/plan.md` Option 1
(`QuestKind.ESCORT`), Steps 1-6:

1. Added `QuestKind.ESCORT = auto()` as the 6th member of `QuestKind`
   (`src/core/models/quests.py`), appended after `BOUNTY`. Non-breaking: serialization is by
   `.name` only (confirmed `src/api/presenters/state_presenter.py:90`).
2. Fixed `get_quest_kind()` (`src/worldbuilding/compiler.py`) to map `"escort"` (case-insensitive
   substring) to `QuestKind.ESCORT` instead of silently falling through to `QuestKind.EXPLORE`.
   Left the pre-existing `"fetch"`/`"defend"`/`"investigate"` mismapping untouched (explicit scope
   guard).
3. Wired the reputation side-effect into `QuestResolutionSystem.enforce()`
   (`src/engine/quests.py`): on `is_newly_completed and project.quest_kind == QuestKind.ESCORT`,
   calls `ReputationUpdateService.process_witnessed_event(base_cognition.relationships.public_reputation,
   "successful_escort")` and stages the result via a new local `reputation_cognition_update`
   accumulator, following `NearDeathHardeningPhase.apply()`'s merge-safe base-cognition-read
   pattern (read `ent_upd.cognition_bundle_set` first if already set by an earlier same-tick phase
   such as `MemoryUpdatePhase`, else fall back to `entity.cognition`) so `MemoryUpdatePhase`'s
   same-tick cognition writes are never clobbered. `cognition_bundle_set` is only added to the
   final `replace(ent_upd, ...)` kwargs when the accumulator is non-`None`, preserving
   `ent_upd`'s pre-existing value via `dataclasses.replace`'s default-preserve behavior otherwise.
4. Added parity ledger entry `SOC-252` to `docs/parity_ledger/social_narrative.yaml` (verified,
   P1), citing the `enforce()` call site and `ReputationUpdateService.process_witnessed_event()` as
   the mechanism, with `test_path` pointing at the two new integration tests (both passing).
5. Corrected the two stale "Engine event handlers" call-site descriptions in
   `docs/simulation/domains/commitment_contract.md` (inline-utility bullet list and Domain
   Interactions table) to name the real call site (`QuestResolutionSystem.enforce()`,
   `src/engine/quests.py`) and the real, single wired event kind (`successful_escort` only —
   `betrayal`/`clear_camp` explicitly documented as still unwired).
6. Added 5 tests: `test_successful_escort_completion_updates_reputation` and
   `test_quest_reward_phase_preserves_memory_update_cognition_writes` (both in
   `tests/integration/scenarios/test_phase15_commitment_reputation_scenarios.py`);
   `test_quest_completion_non_escort_kind_does_not_touch_reputation` (in
   `tests/unit/quest/test_quest_rewards.py`); `get_quest_kind("escort")` assertion added to
   `test_helper_enum_mappers` (`tests/unit/worldbuilding/test_world_compiler.py`);
   `test_quest_kind_escort_enum_value_is_new_member_only` (`tests/unit/quest/test_quest_system.py`).

Systemic, pre-existing, out-of-scope gap (unchanged by this ticket, per plan.md's Anti-Drift
Notes): the world-content compiler never populates `target_*` progress-driving metadata for any
`QuestKind`, so a compiled ESCORT quest cannot yet progress to completion purely from static
content in a live simulation run. The wiring itself is real, correct, and directly testable via
manually-constructed `QuestState`/`StateUpdate` objects (all 5 new tests do this), matching the
`BuildingSabotageSystem` "wired but not yet end-to-end reachable" precedent accepted by the parent
investigation.

Deviation from plan.md's exact prose (recorded in plan.md's own Deviations section): Step 3 uses a
single `reputation_cognition_update: Optional[CognitionModel]` local (None-ness doubling as the
"touched" flag) instead of the plan's separate `cognition_touched: bool` + `base_cognition`
accumulator pair — functionally identical, no behavior difference.

## Test Summary

Ran (via `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest`, since this
worktree has no local `.venv`):

- `tests/unit/domains/commitment/ tests/integration/scenarios/test_phase15_commitment_reputation_scenarios.py tests/unit/quest/ tests/unit/worldbuilding/test_world_compiler.py tests/arena/test_arena_quests.py tests/unit/systems/test_quest_activation_pathway.py` → **147 passed**
- `tests/unit/worldbuilding/ tests/unit/engine/ -m "not slow"` → **317 passed, 1 skipped, 3 deselected** (broader regression sweep on the two directly-touched source areas)

All pre-existing tests continued to pass unmodified in behavior; the only pre-existing file with a
new assertion added (not rewritten) is `test_helper_enum_mappers`.

## Files Changed

- `src/core/models/quests.py` — added `QuestKind.ESCORT`
- `src/worldbuilding/compiler.py` — added `"ESCORT"` branch to `get_quest_kind()`
- `src/engine/quests.py` — wired `ReputationUpdateService.process_witnessed_event()` into
  `QuestResolutionSystem.enforce()`
- `docs/parity_ledger/social_narrative.yaml` — added `SOC-252`
- `docs/parity_ledger/world_dynamics.yaml` — added `WORLD-116` (QuestKind.ESCORT enum member +
  `get_quest_kind()` compiler-mapping fix parity entry; resolves the parity cross-reference gate's
  file→shard expectation for `src/core/models/quests.py` and `src/worldbuilding/compiler.py`)
- `docs/simulation/domains/commitment_contract.md` — corrected two stale call-site descriptions
- `docs/simulation/quest_contract.md` — added `ESCORT` to the QuestKind table; extended the
  GATHER/BOUNTY/LIBERATE uncompletable-kinds note to cover ESCORT's distinct (reactive, not
  self-detecting) wiring
- `tests/integration/scenarios/test_phase15_commitment_reputation_scenarios.py` — added
  `test_successful_escort_completion_updates_reputation`,
  `test_quest_reward_phase_preserves_memory_update_cognition_writes`
- `tests/unit/quest/test_quest_rewards.py` — added
  `test_quest_completion_non_escort_kind_does_not_touch_reputation`
- `tests/unit/worldbuilding/test_world_compiler.py` — extended `test_helper_enum_mappers` with an
  `"escort"` assertion
- `tests/unit/quest/test_quest_system.py` — added
  `test_quest_kind_escort_enum_value_is_new_member_only`
- `staging_artifacts/TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING/plan.md` — added a Deviations
  section documenting the Step 3 variable-naming difference from plan prose
- `tickets/inprogress/TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING.md` — this file (Implementation
  Notes, Files Changed, Test Summary, Completion Summary, Status, Acceptance Criteria)

## Completion Summary

`ReputationUpdateService.process_witnessed_event()` is now wired to a real, live production event:
`QuestKind.ESCORT` quest completion, detected in `QuestResolutionSystem.enforce()`. A new
`QuestKind.ESCORT` enum member was added, the world-content compiler's `get_quest_kind()` was
fixed to correctly map authored `type: "escort"` quests (6 world-content files were previously
silently miscompiled to `EXPLORE`), and `enforce()` now calls `process_witnessed_event(...,
"successful_escort")` on ACTIVE→COMPLETED transition, applying the result through
`EntityUpdate.cognition_bundle_set` via the merge-safe base-cognition pattern that mirrors
`NearDeathHardeningPhase.apply()` (preventing clobbering of `MemoryUpdatePhase`'s same-tick
writes). Parity ledger entry `SOC-252` and updated `commitment_contract.md` prose document the
real call site; 5 new tests (147 total in the scoped regression suite) verify the wiring, the
compiler fix, the non-ESCORT no-op guard, the merge-safety property, and enum-append stability —
all passing. The separate, pre-existing, systemic gap in which static content never gets quest
progress-driving `target_*` metadata (affecting all `QuestKind` values, not introduced by this
ticket) remains out of scope, consistent with the parent investigation's precedent.
