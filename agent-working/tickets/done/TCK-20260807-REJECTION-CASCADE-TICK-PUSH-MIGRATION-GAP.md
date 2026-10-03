---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260807-REJECTION-CASCADE-TICK-PUSH-MIGRATION-GAP
phase: done
date: 2026-08-07
tags: [observability, engine, simulation-quality]
---

# TCK-20260807-REJECTION-CASCADE-TICK-PUSH-MIGRATION-GAP

## Title
`rejection_cascade_tick` (AGENCY pillar) is still a post-entity-loop population aggregate in
`event_extractor.py`, ungated by any push-shaper flag — never migrated by Phase 1 or Phase 2

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

`rejection_cascade_tick` (`event_extractor.py`, scored by `AgencyScorer` — see
`docs/simulation_quality/event_type_coverage.md` line 105) is a population-wide aggregate
(iterates every `EntityUpdate.intent_results` across `update.entity_updates`, counts rejected
intents, fires when the total crosses `_MAX_CONSECUTIVE_REJECTIONS`). It is constructed
unconditionally after the main per-entity loop, gated by neither `ENABLE_PUSH_EVENT_SHAPERS` nor
`ENABLE_PUSH_EVENT_SHAPERS_PHASE2` nor the new `ENABLE_PUSH_EVENT_SHAPERS_QUEST`. No shaper in
`event_shapers.py` covers it (confirmed via direct grep — zero references).

Unlike `quest_event`/`commitment_abandoned` (both per-entity, project-keyed), this is
naturally push-ready already: `update.entity_updates` already carries every `intent_results` list
needed, with no dependency on `prior_state` comparison at all (the aggregate is computed purely
from this tick's `update`) — likely the simplest of the three gaps found in this sweep to migrate.

## Scope
1. **Investigate**: confirm the exact aggregate logic (`_total_rejections`/`_reason_counts`
   computed from `update.entity_updates[*].intent_results`, threshold
   `_MAX_CONSECUTIVE_REJECTIONS`); confirm it's genuinely `update`-only (no `prior_state` diffing
   needed), which would make this a StrategyShaper-shaped addition or its own minimal shaper.
2. **Plan**: design shaper placement — likely a natural fit for `StrategyShaper` (AGENCY pillar,
   already covers `route_selected`/`defer_with_reason`/etc. from the same `entity_updates` source)
   under the ALREADY-ON `ENABLE_PUSH_EVENT_SHAPERS_PHASE2` flag, OR its own flag if Investigate
   finds a reason `StrategyShaper`'s own registry isn't the right home — confirm, don't assume.
3. **Implement**: shaper logic + flag-gate `event_extractor.py`'s own block; real-kernel-adjacent
   verification of no double-fire.
4. Update the relevant parity ledger entry for `rejection_cascade_tick`/`AgencyScorer`.

## Out of Scope
- `quest_event` — already migrated (`TCK-20260807-QUEST-EVENT-PUSH-MIGRATION`, DONE).
- `commitment_abandoned` — a separate, also-found migration gap, tracked by its own ticket
  (`TCK-20260807-COMMITMENT-ABANDONED-PUSH-MIGRATION-GAP`).
- Any change to `_MAX_CONSECUTIVE_REJECTIONS`'s threshold value or the rejection-counting logic
  itself.

## Acceptance Criteria
- [x] `investigation.md` confirms the exact aggregate logic and the chosen shaper placement
      (grouped with `commitment_abandoned` into one new `AgencyShaper`, not `StrategyShaper`)
- [x] Shaper implemented, `event_extractor.py`'s own block flag-gated as the rollback path
- [x] Real-kernel-adjacent verification: no double-fire in either default or explicit-OFF mode
- [x] Relevant parity ledger entry updated (`INFRA-327`)
- [x] Scoped pytest run passes (16/16 new tests; 952/952 full observability suite)

## Related Tickets
- TCK-20260807-QUEST-EVENT-PUSH-MIGRATION (DONE — source of this finding)
- TCK-20260807-COMMITMENT-ABANDONED-PUSH-MIGRATION-GAP (sibling follow-up, same investigation)

## Related Docs
- `docs/simulation_quality/event_type_coverage.md` (its own "source" column is stale for most
  rows post-Phase-1/2 migration — not authoritative, confirm against live code)

## Related Code Areas
- `src/observability/event_extractor.py` (`rejection_cascade_tick` block, post-entity-loop)
- `src/observability/event_shapers.py` (`StrategyShaper` — likely placement target, same
  `entity_updates`-only read pattern as its existing AGENCY events)
- `src/simulation_quality/scorers/agency.py` (`AgencyScorer`, the consumer)

## Assumptions / Open Questions
- Whether `StrategyShaper`'s existing `PHASE2_SHAPER_REGISTRY`/`ENABLE_PUSH_EVENT_SHAPERS_PHASE2`
  is the right home (likely, given the shared `entity_updates`-only read pattern) or whether this
  needs its own flag — not assumed, Investigate must confirm.

## Implementation Notes
Implemented together with `TCK-20260807-COMMITMENT-ABANDONED-PUSH-MIGRATION-GAP` — both grouped
into one new `AgencyShaper` class and one new `ENABLE_PUSH_EVENT_SHAPERS_AGENCY` flag rather than
2 separate near-identical single-purpose flags. `rejection_cascade_tick` itself needed no
reconstruction logic at all — confirmed genuinely `update`-only (no `prior_state` dependency),
the simplest possible migration in this file. Caught and corrected an initial verification
mistake during Implement: first attempt used 10 simulated rejections, which is below the real
`_MAX_CONSECUTIVE_REJECTIONS` threshold (confirmed `20`, not assumed) — re-verified with 25 before
trusting the result.

## Test Summary
New `tests/unit/observability/test_event_shapers_agency.py` (16 tests total, shared with the
sibling ticket): this ticket's own direct `AgencyShaper.shape()` tests for
`rejection_cascade_tick` (emission at/above threshold with correct payload, suppression below
threshold, suppression when all accepted, population-aggregate-not-per-entity correctness,
no-prior-state-dependency correctness). Full `tests/unit/observability/` suite: 952/952 pass.
`tests/simulation_quality/` (excluding the pre-existing unrelated `test_grade_regression.py`):
all pass.

Real-kernel-adjacent verification: built a real `EntityUpdate` with 25 rejected `IntentResult`s;
confirmed default mode delivers exactly 1 `rejection_cascade_tick` from the shaper with the
correct payload (0 from the extractor's rollback branch), explicit OFF delivers exactly 1 from
the extractor (0 from the shaper).

## Files Changed
- `src/observability/event_shapers.py` — new `AgencyShaper` class (`rejection_cascade_tick`
  half), `AGENCY_SHAPER_REGISTRY`, Agency-mode gating block in `run_shadow_shapers()` (shared with
  the sibling ticket's `commitment_abandoned` half)
- `src/observability/event_extractor.py` — `rejection_cascade_tick` block gated behind
  `_push_shapers_agency_active`
- `src/domains/optimization/feature_flags.py` — new `ENABLE_PUSH_EVENT_SHAPERS_AGENCY` flag
  (shared)
- `tests/unit/observability/test_event_shapers_agency.py` — new, 16 tests (shared)
- `tests/unit/config/test_phase10_feature_flags.py` — allowlist updated (shared)
- `docs/parity_ledger/infrastructure.yaml` — new `INFRA-327` entry (shared)
- `docs/guides/feature_flags.md` — new flag row; 15→16 flag-count updates throughout (shared)

## Completion Summary
Migrated `rejection_cascade_tick` to the shaper-registry pattern — the last real push-migration
gap found during `TCK-20260807-QUEST-EVENT-PUSH-MIGRATION`'s own systematic sweep. As of this
ticket's own close, every scored event this repo tracks is either push-based or a confirmed,
deliberately-undisturbed new signal (`capability_growth_stalled`/`life_arc_incoherent`) — no real
migration gaps remain. Verified no double-fire via real, unmocked state construction, correcting
an initial under-threshold verification mistake before trusting the result rather than assuming
it was fine.
