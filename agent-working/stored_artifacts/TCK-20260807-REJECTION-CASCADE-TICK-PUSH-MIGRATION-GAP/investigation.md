---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260807-REJECTION-CASCADE-TICK-PUSH-MIGRATION-GAP
artifact_type: investigation
tags: [observability, engine, simulation-quality]
---

# Investigation: TCK-20260807-REJECTION-CASCADE-TICK-PUSH-MIGRATION-GAP

Implemented together with the sibling ticket `TCK-20260807-COMMITMENT-ABANDONED-PUSH-MIGRATION-
GAP` — both are the last 2 real push-migration gaps found during
`TCK-20260807-QUEST-EVENT-PUSH-MIGRATION`'s own systematic sweep, both `AgencyScorer`, and share
one implementation (`AgencyShaper`). See that ticket's own `investigation.md` for the shared
`commitment_abandoned` half.

## Exact aggregate logic (confirmed, not assumed)

`event_extractor.py`'s `rejection_cascade_tick` block (post-entity-loop, in
`EventExtractor.extract()`): iterates `update.entity_updates.values()`, for each entity's
`intent_results` counts entries where `not getattr(ir, "accepted", True)`, tallies rejection
reasons into a dict, and when the total crosses `_MAX_CONSECUTIVE_REJECTIONS`
(`src/systems/strategic_systems/intelligence.py:27`, value `20`) emits one event with
`payload={"count": ..., "tick": ..., "dominant_failure_reason": <most common reason>}`.

**Confirmed genuinely `update`-only**: unlike `commitment_abandoned`, this aggregate reads
nothing from `prior_state` at all — every input (`entity_updates[*].intent_results`) is already
present on `update`, this tick's own typed record. This is the simplest possible shape for the
shader architecture; the migration is a near-verbatim relocation, no reconstruction logic needed.
Confirmed via a dedicated test (`test_rejection_cascade_tick_does_not_need_prior_state_entities`)
that the shaper still fires correctly even when `prior_state.entities` is empty.

## Placement: shared `AgencyShaper`, not `StrategyShaper`

Investigated whether `StrategyShaper` (the existing AGENCY/COGNITION/INFORMATION shaper, already
live under `ENABLE_PUSH_EVENT_SHAPERS_PHASE2`) was the right home, since it already reads
`update.entity_updates` for other AGENCY events (`route_selected`, `defer_with_reason`, etc.) via
the exact same source. Decided against it: `StrategyShaper`'s own flag is already `ON`, so adding
new logic there would deliver it live immediately with no independent verification window — the
same reasoning that already justified giving `commitment_abandoned` its own shaper rather than
colocating with `NarrativeShaper`. Grouped both remaining `AgencyScorer` gaps
(`commitment_abandoned` + `rejection_cascade_tick`) into one new `AgencyShaper` class instead,
under one new dedicated flag — avoids proliferating a 5th nearly-identical single-purpose flag for
what is, in total, still just 2 events, while keeping the verification/rollback discipline intact.

## Real-kernel-adjacent verification

Built a real `EntityUpdate` with 25 rejected `IntentResult`s (above the real `20` threshold, not
the smaller placeholder count initially tried and corrected after checking the real constant
value). Confirmed: default mode delivers exactly 1 `rejection_cascade_tick` from the shaper
(`payload={"count": 25, ..., "dominant_failure_reason": "no_capacity"}`, 0 from the extractor's
rollback branch); explicit `ENABLE_PUSH_EVENT_SHAPERS_AGENCY="OFF"` delivers exactly 1 from the
extractor (0 from the shaper). No double-fire in either mode.
