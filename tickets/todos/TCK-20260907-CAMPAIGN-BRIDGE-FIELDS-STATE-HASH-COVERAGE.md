---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260907-CAMPAIGN-BRIDGE-FIELDS-STATE-HASH-COVERAGE
phase: open
date: 2026-09-07
tags: [determinism, engine, architecture]
---

# TCK-20260907-CAMPAIGN-BRIDGE-FIELDS-STATE-HASH-COVERAGE

## Title
6 CampaignState-bridge fields added by the Dormant Mechanism Closure epic are absent from the canonical determinism state hash

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
An independent review of PR #144 (Dormant Mechanism Closure epic, `rpg-feature-planning` session)
raised a determinism-coverage question about `information_source_profiles`'s new persistence
semantics (`TCK-20260907-INFORMATION-SOURCE-PROFILES-PERSISTENCE-DECISION`), citing a precedent
of a prior real bug class (an unsorted-set serialization bug the reviewer recalled from PR #128 —
not independently re-verified by this ticket, cited as the reviewer's own stated precedent, not a
confirmed fact of this repo's history).

The orchestrating session independently traced `CanonicalStateHasher.to_canonical_data()`
(`src/engine/checkpoint.py`) — the real function behind `final_state_hash`, the deterministic
proof used for replay/certification — and confirmed the underlying concern is real, and broader
than just the one field the reviewer flagged: **none** of the 6 `AuthoritativeState` fields the
Dormant Mechanism Closure epic added participate in the canonical hash at all:
- `region_loyalty_pressure` (`TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE`)
- `region_culture_states`, `entity_legend_facts` (`TCK-20260907-ROUTE-BIAS-SCORING-
  INFRASTRUCTURE`/`TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING`)
- `information_source_profiles` (`TCK-20260907-INFORMATION-SOURCE-PROFILES-PERSISTENCE-DECISION`,
  now persistent rather than Bounded/single-fire)
- `entity_belief_institutions`, `event_fidelity` (`TCK-20260907-CHRONICLE-BELIEF-CONSUMER-WIRING`)

`CanonicalStateHasher.to_canonical_data()` enumerates included fields explicitly (scalars,
entities, regions, places, local_scars, resource_nodes, buildings, corpses, ground_items, chests,
groups, home_storage, camps, global_resources, periodic_due_ticks, work_debt, blocked_tiles,
town_tiles, building_tiles, rng_checkpoint) — none of the 6 fields above are in that list.

## Scope
- Confirm during Investigate whether this is a real determinism gap in practice (i.e., could two
  replay runs diverge in one of these 6 fields' content while producing an identical state hash?)
  or whether downstream mutation (these fields feed into `personality_bias`, which affects
  entity-level decisions that ARE hashed) makes any real divergence still detectable indirectly —
  do not assume either answer, verify with a real test.
- If a real gap exists: add the 6 fields to `CanonicalStateHasher.to_canonical_data()`, following
  the same sorted/deterministic-iteration discipline the existing fields already use (see
  `regions`/`places`/etc.'s own `sorted(...)` calls).
- Confirm no performance regression from the addition — `CanonicalStateHasher.get_hash()` is
  budget-rate-limited (`BudgetedCanonicalHasher`) for a reason; these fields are typically small
  (bounded by entity/region count), but verify against a real large-world calibration run.

## Out of Scope
- Redesigning the state-hash mechanism itself.
- Any other item from the Dormant Mechanism Closure epic's scope.

## Acceptance Criteria
- [ ] A real determination is made (with test evidence) of whether missing these 6 fields is a
      genuine determinism-verification gap or a benign omission, and the reasoning is recorded.
- [ ] If genuine: all 6 fields are added to the canonical hash, with a real test proving two
      differently-seeded-but-otherwise-identical states (differing only in one of these fields)
      now produce different hashes, and identical states still produce identical hashes.

## Related Tickets
- `TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE` (parent epic — source of all 6 fields)
- `TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE`, `TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE`,
  `TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING`, `TCK-20260907-INFORMATION-SOURCE-PROFILES-
  PERSISTENCE-DECISION`, `TCK-20260907-CHRONICLE-BELIEF-CONSUMER-WIRING` (all `tickets/done/` —
  each added one or more of the 6 fields)

## Related Docs
None yet.

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `src/engine/checkpoint.py` (`CanonicalStateHasher.to_canonical_data()`)
- `src/core/state.py` (`AuthoritativeState`)

## Assumptions / Open Questions
- Whether the omission is a real gap or benign (fields' effects are always indirectly captured
  elsewhere in the hash) is not resolved here — genuine investigation work for whoever picks this
  up.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
