---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260807-QUEST-EVENT-PUSH-MIGRATION
phase: open
date: 2026-08-07
tags: [observability, engine, simulation-quality]
---

# TCK-20260807-QUEST-EVENT-PUSH-MIGRATION

## Title
Migrate `quest_event` (entity-project quest lifecycle) from `event_extractor.py`'s post-tick
diffing to a live, push-based `event_shapers.py` shaper — correcting a stale "already live
elsewhere" claim in the Phase 2 push-migration epic's own closed record

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
User asked, after a status question about the push-based observability migration: "is the
event_extractor all completed, every events now push-based?" Direct code inspection (not the
Phase 2 epic's own record, which turned out to be wrong) found `quest_event`
(`QuestEvent`/`SOC-241`, scored by `NarrativeScorer`) is still constructed unconditionally inside
`event_extractor.py`'s post-tick diffing loop (`event_extractor.py:787-823`), gated by neither
`ENABLE_PUSH_EVENT_SHAPERS` nor `ENABLE_PUSH_EVENT_SHAPERS_PHASE2`.

`TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC`'s own "Out of Scope" section claims
`quest_event` "already come[s] from `quest_system`, a separate live-emission source, not
`event_extractor.py`'s diffing pass," based on a raw-JSONL inspection. This is incorrect — the raw
JSONL almost certainly just showed near-zero `quest_event` hits (because real quest generation
wasn't wired into live gameplay until `TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING`, and `quest_event`
itself had its own type-filter bug until `TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG`, both same
session), not because it comes from elsewhere. The genuinely separate live-emission mechanism the
epic's inspection likely actually saw is `QuestOpportunityRewardSystem`'s `WorldEvent(category=
QUEST_COMPLETED)` (`src/engine/pipeline_phases/quest_opportunity_rewards.py`) — a different
mechanism entirely (world-level `QuestOpportunity` registry rewards, E23C), not the entity-project
`QuestState` lifecycle `quest_event` actually tracks.

This ticket migrates `quest_event` to the shaper-registry pattern, following the Phase 1/Phase 2
precedent exactly, and corrects the epic's own stale record.

## Scope
1. **Investigate**: confirm `quest_event`'s exact construction logic (done — see investigation.md),
   confirm no shaper already covers it (done), confirm the safe reconstruction path from
   `prior_state` + `update` alone (mirroring `_current_leads()`'s pattern for `StrategicUpdate`).
2. **Plan**: design a new `NarrativeShaper` (named after the scoring pillar, matching
   `FactionShaper`/`StrategyShaper`/`SocialShaper`'s naming convention) and a new, dedicated
   `ENABLE_PUSH_EVENT_SHAPERS_QUEST` flag — NOT reusing `ENABLE_PUSH_EVENT_SHAPERS_PHASE2` (which
   already defaults `ON`; reusing it would deliver live immediately with no shadow-validation
   window, the exact "double-fire risk / no shadow window" mistake `TCK-20260806-PUSH-SHAPER-
   REGISTRY-STRATEGY` already found and fixed once for Phase 2 itself).
3. **Implement**: `NarrativeShaper.shape()` in `event_shapers.py`; register it; gate
   `event_extractor.py`'s existing quest_event block behind `not
   _push_shapers_quest_active` (rollback path, same pattern as every migrated domain);
   real-kernel-verify both SHADOW (constructed, not delivered) and ON (delivered, no double-fire
   against the still-present rollback path) before defaulting the new flag to `ON`.
4. File follow-up tickets for any other scored event found still diffing-based and ungated during
   this investigation (found 2: `commitment_abandoned`, `rejection_cascade_tick`, both
   `AgencyScorer` — see Related Tickets).

## Out of Scope
- `commitment_abandoned`/`rejection_cascade_tick` — found during this ticket's own investigation,
  filed as separate follow-up tickets (not fixed here, to keep this ticket's own blast radius to
  the one event the user asked about).
- `capability_growth_stalled`/`life_arc_incoherent` — also unguarded in `event_extractor.py`, but
  deliberately so per their own code comment: genuinely new signals with no `ProgressionShaper`
  equivalent, added after Phase 2 closed, so no double-fire risk exists. Not a migration gap, not
  filed as a follow-up.
- `QuestOpportunityRewardSystem`'s `QUEST_COMPLETED` `WorldEvent` — a different, already-live
  mechanism, unaffected by this ticket.
- Correcting the Phase 2 epic's closed ticket file itself — historical tickets in `tickets/done/`
  are not edited after close; this ticket's own record (and the doc/parity updates below) serve as
  the correction going forward.

## Acceptance Criteria
- [x] `investigation.md` confirms `quest_event`'s exact construction logic and the corrected
      understanding of where it actually comes from
- [x] `NarrativeShaper` implemented, registered, gated behind a new dedicated flag
- [x] `event_extractor.py`'s existing block gated behind the same flag (rollback path preserved)
- [x] Real-kernel verification: SHADOW mode constructs but does not deliver; ON mode delivers
      correctly with no double-fire
- [x] New flag defaults `ON` after verification (matching Phase 1/Phase 2's own "verify then
      default ON" precedent)
- [x] `docs/parity_ledger/social_narrative.yaml` (`SOC-241`) updated
- [x] Follow-up tickets filed for `commitment_abandoned`/`rejection_cascade_tick`
- [x] Scoped pytest run passes

## Related Tickets
- TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC (DONE — the epic whose own
  "Out of Scope" claim about `quest_event` this ticket corrects)
- TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG (DONE — fixed a real bug in the same diffing code this
  ticket relocates)
- TCK-20260807-COMMITMENT-ABANDONED-PUSH-MIGRATION-GAP (new follow-up filed from this ticket's own
  investigation)
- TCK-20260807-REJECTION-CASCADE-TICK-PUSH-MIGRATION-GAP (new follow-up filed from this ticket's
  own investigation)

## Related Docs
- `docs/parity_ledger/social_narrative.yaml` (`SOC-241`)
- `docs/simulation_quality/event_type_coverage.md` (its "source" column is stale for most rows
  post-Phase-1/2 — flagged, not corrected wholesale here; out of this ticket's own scope)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC/`

## Related Code Areas
- `src/observability/event_shapers.py` (new `NarrativeShaper`)
- `src/observability/event_extractor.py` (quest_event block, gated)
- `src/domains/optimization/feature_flags.py` (new `ENABLE_PUSH_EVENT_SHAPERS_QUEST` flag)
- `src/engine/kernel.py` (`NarrativeShaper.reset_run_state()` wiring, if any per-run state needed)

## Assumptions / Open Questions
None — scope is narrow and fully confirmed via direct code reading before implementation.

## Implementation Notes
Added `NarrativeShaper` to `event_shapers.py`, reading `prior_state`/`update` directly (no
post-apply `current_state` read) via a new `_current_projects()` helper mirroring the already-
proven `_current_leads()` pattern exactly. Gated behind a new, dedicated
`ENABLE_PUSH_EVENT_SHAPERS_QUEST` flag (own `QUEST_SHAPER_REGISTRY`, own gating block inside
`run_shadow_shapers()`) rather than folding into the already-ON `ENABLE_PUSH_EVENT_SHAPERS_PHASE2`
— avoids the exact double-fire/no-shadow-window mistake `TCK-20260806-PUSH-SHAPER-REGISTRY-
STRATEGY` already found and fixed once when Phase 2 needed its own flag apart from Phase 1's.
Gated `event_extractor.py`'s own quest_event construction (only the `QuestState`-specific branch,
NOT the co-located `commitment_abandoned` branch, which is a separate, still-unmigrated signal)
behind the new flag as the rollback path. No `kernel.py` change needed — confirmed
`Kernel._phase_observability()`'s own outer gate already delegates the ON/SHADOW/delivery decision
down into `run_shadow_shapers()`'s own return value, the same mechanism Phase 2's shaper already
relies on; my ticket's own initial "Related Code Areas" note assumed a kernel.py change might be
needed, which turned out unnecessary.

Systematic sweep (per the user's own request) found 2 more real scored events still diffing-based
and ungated (`commitment_abandoned`, `rejection_cascade_tick`, both `AgencyScorer`) — filed as
separate follow-up tickets rather than expanding this ticket's own scope. Also found
`capability_growth_stalled`/`life_arc_incoherent` are deliberately unguarded (a genuinely new
signal added after Phase 2 closed, no shaper equivalent ever existed) — confirmed NOT a gap, not
filed.

## Test Summary
New `tests/unit/observability/test_event_shapers_narrative.py` (13 tests): registry wiring, 4-way
flag gating (default/OFF/SHADOW/ON), independence from `ENABLE_PUSH_EVENT_SHAPERS_PHASE2`, direct
`NarrativeShaper.shape()` behavior including the same non-`QuestState`-project exclusion
`TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG` fixed in `event_extractor.py`'s own version. Updated
`tests/unit/config/test_phase10_feature_flags.py`'s allowlist. Full `tests/unit/observability/`
suite: 936/936 pass (existing `MagicMock`-based extractor tests continue exercising the rollback
path unaffected, same as every prior migrated domain). `tests/simulation_quality/` (excluding
`test_grade_regression.py`, confirmed pre-existing/unrelated via `git stash` A/B — those tests
read static calibration files, not live kernel output): 460/460 pass.

Real-kernel-adjacent verification: built a real `AuthoritativeState`/`StateUpdate`/
`StrategicUpdate` (via `V2EntityBuilder`, not mocks) with a quest transitioning `ACTIVE`→
`COMPLETED`; confirmed default mode delivers exactly 1 `quest_event` from the shaper (0 from the
extractor's rollback branch), explicit OFF delivers exactly 1 from the extractor (0 from the
shaper) — no double-fire in either mode.

## Files Changed
- `src/observability/event_shapers.py` — `_current_projects()` helper, `NarrativeShaper` class,
  `QUEST_SHAPER_REGISTRY`, Quest-mode gating block in `run_shadow_shapers()`
- `src/observability/event_extractor.py` — `_push_shapers_quest_active` flag read; quest_event
  construction gated behind it
- `src/domains/optimization/feature_flags.py` — new `ENABLE_PUSH_EVENT_SHAPERS_QUEST` flag
- `tests/unit/observability/test_event_shapers_narrative.py` — new, 13 tests
- `tests/unit/config/test_phase10_feature_flags.py` — allowlist updated
- `docs/parity_ledger/social_narrative.yaml` — `SOC-241` update note; new `SOC-242` entry
- `docs/guides/feature_flags.md` — new flag row; 14→15 flag-count updates throughout
- `tickets/todos/TCK-20260807-COMMITMENT-ABANDONED-PUSH-MIGRATION-GAP.md` — new follow-up
- `tickets/todos/TCK-20260807-REJECTION-CASCADE-TICK-PUSH-MIGRATION-GAP.md` — new follow-up

## Completion Summary
Migrated `quest_event` to the shaper-registry pattern, correcting a stale claim in the Phase 2
push-migration epic's own closed record (it claimed `quest_event` "already come[s] from
`quest_system`," which direct code reading showed was never true — that mechanism is actually a
different, unrelated system, `QuestOpportunityRewardSystem`'s `QUEST_COMPLETED` `WorldEvent`).
Verified no double-fire in either delivery mode via real, unmocked state construction, not just
unit-level mocks. Per the user's explicit request, swept the rest of `event_extractor.py`
systematically rather than stopping at the one event asked about — found 2 more real gaps
(`commitment_abandoned`, `rejection_cascade_tick`) and filed clearly-scoped follow-up tickets for
both, while correctly identifying and NOT filing a ticket for a third candidate
(`capability_growth_stalled`/`life_arc_incoherent`) that turned out to be a deliberate, already-
disclosed design decision rather than a real migration gap.
