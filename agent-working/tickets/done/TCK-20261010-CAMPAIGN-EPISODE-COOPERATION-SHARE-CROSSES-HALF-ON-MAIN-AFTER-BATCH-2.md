---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261010-CAMPAIGN-EPISODE-COOPERATION-SHARE-CROSSES-HALF-ON-MAIN-AFTER-BATCH-2
phase: done
date: 2026-10-16
tags: []
---

# TCK-20261010-CAMPAIGN-EPISODE-COOPERATION-SHARE-CROSSES-HALF-ON-MAIN-AFTER-BATCH-2

## Title
The campaign episode's cooperation check moves from a share of all events to the intent behind it: a typed basis for every cooperation event and a bounded volume per alive entity-tick

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
`test_real_campaign_episode_event_mix_is_not_dominated_by_cooperation` (pooled cooperation share < 0.5) was red on rpg-next (0.6985) and carried a known-red entry expiring 2026-10-31. Diagnosis found two causes; rpg-planner ruled option 2: replace the all-events ratio, which breaks when an unrelated event type is added or retired.

## Scope
- The two cooperation checks in tests/integration/campaigns/test_catalog_entity_spawn_wiring.py (typed basis; volume per alive entity-tick) and the instrumentation they need.
- Remove the known-red entry for the old test (it lives in testing's tools/test_architecture/slow_known_reds.yaml).

## Out of Scope
- Any change to the cooperation phase, evaluators or event extraction; the strict-xfail deliberate-attack test.

## Acceptance Criteria
- [x] Both causes recorded: A (plant-eater herd: more risk-driven help needs, share 0.517 -> 0.598), B (the treasury batch retired the per-head TAX gold_sink_fired, 14% of the stream: 0.58 -> 0.70).
- [x] Falsifiable: with every entity spawned on one tile (scratch copy) the volume check fails (0.4513 > 0.30) and the typed-basis check passes; both pass on the tip (0.2107).
- [x] Measured values in the test comment: c35ebf475, the plant-eater commit, the tip.
- [x] The known-red entry removed in the same change.

## Related Tickets
- TCK-20261006-CAMPAIGN-EPISODE-COOPERATION-SHARE-ABOVE-HALF-UNDER-A-PINNED-NORMAL-GOVERNOR (earlier crossing, closed by AGENCY-07)
- TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING (the co-location the test guards)
- TCK-20261009-GENERIC-PLANT-EATER-ARCHETYPES-GRAZE-AND-FLEE-DECISIONS-45-50 (cause A)
- TCK-20261009-FACTION-TREASURY-IS-ONE-TYPED-ACCOUNT-EXCH-02-C (cause B)

## Related Docs
- None.

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261010-CAMPAIGN-EPISODE-COOPERATION-SHARE-CROSSES-HALF-ON-MAIN-AFTER-BATCH-2/ (probes: bisect scripts and the co-location probe)

## Related Code Areas
- tests/integration/campaigns/test_catalog_entity_spawn_wiring.py, tools/test_architecture/slow_known_reds.yaml

## Assumptions / Open Questions
- Cause B was inferred from the commit lists and the event change (not bisected inside the merge).
- Values at c35ebf475 and 8464582f5 are from pre-determinism-fix commits and vary run to run; the tip is deterministic.
- This ticket file was created at close: the known-red entry cited an id that had no file.

## Implementation Notes
Cooperation checks: (a) every cooperation_event matches one decision made with a typed basis (help need, group membership, incoming offer), none "other"; it does not catch co-location (co-located entities still have typed help needs), it guards the structure. (b) cooperation events per alive entity-tick pooled over seeds 42 and 1337 under 0.30 (tip 0.2107, +42% headroom; co-location 0.4513). Basis at the tip: help need 58%, group member 37%, incoming offer 4%.

## Test Summary
tests/integration/campaigns/test_catalog_entity_spawn_wiring.py: 12 passed, 1 strict xfail (unchanged); tests/unit/tools/test_known_reds.py 33 passed. Falsifiability run in a scratch copy (not committed).

## Files Changed
tests/integration/campaigns/test_catalog_entity_spawn_wiring.py, tools/test_architecture/slow_known_reds.yaml (entry removed).

## Completion Summary
The red cooperation-share test is replaced by two checks on cooperation itself; the known-red entry is gone. Both causes of the share crossing 0.5 are recorded. Not pushed.
