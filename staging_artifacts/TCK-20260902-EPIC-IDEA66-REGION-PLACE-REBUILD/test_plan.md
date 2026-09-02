---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD
artifact_type: test_plan
tags: [content, determinism]
---

# Test Plan — TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD

Scope-only epic — no direct test plan. Each child ticket owns its own test plan. The epic-level
acceptance signal (per the source plan doc) is:

- Stage A (`unit_information_source`) compiles with a byte-identical `state_hash` to its committed
  baseline, or any hash change is explained and accepted before Stage B begins.
- Stage B (`hero_guild_routing`) compiles correctly with all 4 non-uniform region kinds represented as
  the expected `Place.kind` values.
- All 21 worlds pass the `state_hash`-first recalibration procedure with recorded triage notes for any
  world whose hash changes.
