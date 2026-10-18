---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261010-CAMPAIGN-EPISODE-COOPERATION-SHARE-CROSSES-HALF-ON-MAIN-AFTER-BATCH-2
date: 2026-10-16
tags: []
---

# Plan: TCK-20261010-CAMPAIGN-EPISODE-COOPERATION-SHARE-CROSSES-HALF-ON-MAIN-AFTER-BATCH-2

rpg-planner's ruling (2026-10-16, option 2): replace the "cooperation_event is under half of ALL events" assertion with two checks on cooperation itself, because a ratio over all events breaks whenever an unrelated event type is added or retired.
(a) every cooperation_event comes from one cooperation decision with a typed basis (help need, group membership, incoming offer), none with another basis;
(b) cooperation events per alive entity-tick, pooled over seeds 42 and 1337, under a ceiling set from the measured tip with headroom. Prove (a)/(b) falsifiable against the original co-location bug in a scratch copy only. Remove the known-red entry in the same change (the entry lives in testing's tools/test_architecture/slow_known_reds.yaml).
Test-only change: tests/integration/campaigns/test_catalog_entity_spawn_wiring.py.
