---
status: historical
layer: world
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261005-CONTESTED-ZONE-DEATH-SPLIT-DECIDES-WHETHER-OVERLAP-OR-GEOMETRY-CAUSES-ZERO-TRAUMA
phase: done
date: 2026-10-05
tags: [world]
---

# test_plan — TCK-20261005-CONTESTED-ZONE-DEATH-SPLIT-DECIDES-WHETHER-OVERLAP-OR-GEOMETRY-CAUSES-ZERO-TRAUMA

No behaviour changed, so no new unit tests. Controls: (1) `frontier_living_world` was run twice under `audit_mode` and the two outputs are **byte-identical** (sha256 `8f348686...`), so the figures below are values, not indications; (2) the geometry output reproduces the planner's tile table exactly (`near_forest` owns 200 of 2116, `wolf_den` 525 of 1476); (3) death rows come from the update the kernel is about to commit, so `credited` agrees with the trauma writer's lookup.

## Proof Plan
- level: corpus measurement
- proof kind: per-death classification under a deterministic (audit_mode) run
- oracle source: the deaths themselves; static geometry; faction hazard immunities
- expected effect: a verdict among H1-H4 with counts, and per-pair evidence for the four author calls
- selected commands: see `probes/README.md`
