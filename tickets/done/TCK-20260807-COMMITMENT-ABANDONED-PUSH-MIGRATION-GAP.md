---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260807-COMMITMENT-ABANDONED-PUSH-MIGRATION-GAP
phase: open
date: 2026-08-07
tags: [observability, engine, simulation-quality]
---

# TCK-20260807-COMMITMENT-ABANDONED-PUSH-MIGRATION-GAP

## Title
`commitment_abandoned` (AGENCY pillar) is still post-tick diffing in `event_extractor.py`,
ungated by any push-shaper flag — never migrated by Phase 1 or Phase 2

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Found during `TCK-20260807-QUEST-EVENT-PUSH-MIGRATION`'s own investigation (a systematic sweep of
every `event_extractor.py` block for push-shaper gating, prompted by the user asking to file
tickets for any other scored event found still diffing-based).

`commitment_abandoned` (`event_extractor.py`, in the same loop as `quest_event` — see
`docs/simulation_quality/event_type_coverage.md` line 104, scored by `AgencyScorer`) is
constructed unconditionally, gated by neither `ENABLE_PUSH_EVENT_SHAPERS` nor
`ENABLE_PUSH_EVENT_SHAPERS_PHASE2` nor the new `ENABLE_PUSH_EVENT_SHAPERS_QUEST`. It is a
generic, project-kind-agnostic behavioral classification (reads `ProjectState.status ==
ProjectStatus.ABANDONED`, applies to ANY project kind — quest, harvesting, guild, etc.), unlike
`quest_event` which is `QuestState`-specific. This is deliberately independent code (see the
comment at `event_extractor.py`'s quest-lifecycle block: "commitment_abandoned... is deliberately
NOT gated the same way"), so it was correctly left untouched by
`TCK-20260807-QUEST-EVENT-PUSH-MIGRATION`'s own narrower scope — but it is a real, separate
migration gap of the same shape.

## Scope
1. **Investigate**: confirm `commitment_abandoned`'s exact construction logic (uses
   `AbandonmentEvaluator.evaluate_abandonment()`, reads `entity.combat.hp`/`max_hp`); confirm the
   safe reconstruction path from `prior_state` + `update` alone (mirroring
   `_current_projects()`'s pattern, or reusing it directly since it already reconstructs the same
   `projects` dict `commitment_abandoned` also needs).
2. **Plan**: design where this shaper logic lives — likely folded into the same `NarrativeShaper`
   or a sibling shaper reusing `QUEST_SHAPER_REGISTRY`'s own flag
   (`ENABLE_PUSH_EVENT_SHAPERS_QUEST`), since it shares the exact same `projects` diffing loop and
   entity-visiting pattern; confirm this doesn't reintroduce a double-fire risk against the
   now-migrated `quest_event` before reusing the same flag/registry (Investigate must confirm,
   not assume, whether sharing is safe here or whether — like Phase 2 needing its own flag apart
   from Phase 1 — `commitment_abandoned` needs its own SHADOW-validation window with a distinct
   flag).
3. **Implement**: shaper logic + flag-gate `event_extractor.py`'s own block (rollback path);
   real-kernel-adjacent verification of no double-fire.
4. Update `docs/parity_ledger/strategic_cognition.yaml` or `social_narrative.yaml` (whichever
   ledger `AgencyScorer`'s own events are tracked under — confirm before Plan, do not assume).

## Out of Scope
- `quest_event` — already migrated (`TCK-20260807-QUEST-EVENT-PUSH-MIGRATION`, DONE).
- `rejection_cascade_tick` — a separate, also-found migration gap, tracked by its own ticket
  (`TCK-20260807-REJECTION-CASCADE-TICK-PUSH-MIGRATION-GAP`).
- Any change to `AbandonmentEvaluator`'s own classification logic.

## Acceptance Criteria
- [x] `investigation.md` confirms the exact reconstruction path and whether sharing
      `ENABLE_PUSH_EVENT_SHAPERS_QUEST`/`QUEST_SHAPER_REGISTRY` is safe or needs its own flag
      (confirmed: needs its own — new `ENABLE_PUSH_EVENT_SHAPERS_AGENCY`)
- [x] Shaper implemented (`AgencyShaper`), `event_extractor.py`'s own block flag-gated as the
      rollback path
- [x] Real-kernel-adjacent verification: no double-fire in either default or explicit-OFF mode
- [x] Relevant parity ledger entry updated (`INFRA-327`)
- [x] Scoped pytest run passes (16/16 new tests; 952/952 full observability suite)

## Related Tickets
- TCK-20260807-QUEST-EVENT-PUSH-MIGRATION (DONE — source of this finding)
- TCK-20260807-REJECTION-CASCADE-TICK-PUSH-MIGRATION-GAP (sibling follow-up, same investigation)

## Related Docs
- `docs/simulation_quality/event_type_coverage.md` (its own "source" column is stale for most
  rows post-Phase-1/2 migration — not authoritative, confirm against live code)

## Related Code Areas
- `src/observability/event_extractor.py` (`commitment_abandoned` block, adjacent to the
  now-migrated `quest_event` block)
- `src/observability/event_shapers.py` (`NarrativeShaper`/`_current_projects()` — likely reuse
  target)
- `src/simulation_quality/scorers/agency.py` (`AgencyScorer`, the consumer)

## Assumptions / Open Questions
- Whether this can safely share `NarrativeShaper`'s registry/flag or needs its own — not assumed,
  Investigate must confirm against the double-fire-risk precedent established by Phase 2's own
  flag-split history.

## Implementation Notes
Implemented together with `TCK-20260807-REJECTION-CASCADE-TICK-PUSH-MIGRATION-GAP` — both are
`AgencyScorer` gaps found in the same sweep, sharing one new `AgencyShaper` class and one new
`ENABLE_PUSH_EVENT_SHAPERS_AGENCY` flag (kept separate from `NarrativeShaper`'s own already-ON
`ENABLE_PUSH_EVENT_SHAPERS_QUEST` flag, despite sharing the `_current_projects()` helper, to avoid
delivering live with zero independent verification window). hp/max_hp are reconstructed from
`prior_ent.combat` + this tick's `CombatUpdate.hp_delta`/`max_hp_delta` (mirrors `CombatShaper`'s
own established prior-plus-delta pattern), since `AbandonmentEvaluator.evaluate_abandonment()`
needs the post-mutation hp/max_hp, which shapers can't read directly from `current_state`.

## Test Summary
New `tests/unit/observability/test_event_shapers_agency.py` (16 tests total, shared with the
sibling ticket): registry wiring, 4-way flag gating, independence from
`ENABLE_PUSH_EVENT_SHAPERS_QUEST`, and this ticket's own direct `AgencyShaper.shape()` tests for
`commitment_abandoned` (emission on non-SURVIVAL abandonment with correct payload, suppression on
SURVIVAL classification, suppression on non-ABANDONED transitions, hp-delta reconstruction
correctness, no-op without a strategic update). Full `tests/unit/observability/` suite: 952/952
pass. `tests/simulation_quality/` (excluding the pre-existing unrelated
`test_grade_regression.py`): all pass.

Real-kernel-adjacent verification: built a real `AuthoritativeState`/`StateUpdate`/
`StrategicUpdate` (via `V2EntityBuilder`) with a project transitioning `ACTIVE`→`ABANDONED` at
hp=80/100; confirmed default mode delivers exactly 1 `commitment_abandoned` from the shaper (0
from the extractor's rollback branch), explicit OFF delivers exactly 1 from the extractor (0 from
the shaper).

## Files Changed
- `src/observability/event_shapers.py` — new `AgencyShaper` class (`commitment_abandoned` half),
  `AGENCY_SHAPER_REGISTRY`, Agency-mode gating block in `run_shadow_shapers()` (shared with the
  sibling ticket's `rejection_cascade_tick` half)
- `src/observability/event_extractor.py` — `_push_shapers_agency_active` flag read;
  `commitment_abandoned` branch gated behind it
- `src/domains/optimization/feature_flags.py` — new `ENABLE_PUSH_EVENT_SHAPERS_AGENCY` flag
- `tests/unit/observability/test_event_shapers_agency.py` — new, 16 tests (shared)
- `tests/unit/config/test_phase10_feature_flags.py` — allowlist updated
- `docs/parity_ledger/infrastructure.yaml` — new `INFRA-327` entry (shared)
- `docs/guides/feature_flags.md` — new flag row; 15→16 flag-count updates throughout

## Completion Summary
Migrated `commitment_abandoned` to the shaper-registry pattern, the second-to-last real
push-migration gap found during `TCK-20260807-QUEST-EVENT-PUSH-MIGRATION`'s own systematic sweep.
Reconstructed the post-mutation hp/max_hp `AbandonmentEvaluator` needs without reading post-apply
`current_state`, mirroring `CombatShaper`'s own established pattern rather than inventing a new
one. Verified no double-fire via real, unmocked state construction. Implemented alongside its
sibling `rejection_cascade_tick` ticket as one shared `AgencyShaper`, avoiding a proliferation of
near-identical single-purpose flags while keeping each event's own verification/rollback
discipline intact.
