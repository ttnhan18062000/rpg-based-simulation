---
status: active
layer: combat
authority: P1
audience: agent
artifact_type: plan
ticket_id: TCK-20261007-SPECIES-HOSTILITY-METAMORPHIC-ENGAGEMENT-CHECK-RED-SINCE-6E7EF56EC
phase: open
date: 2026-10-07
tags: [combat, regression]
---

# Plan — TCK-20261007-SPECIES-HOSTILITY-METAMORPHIC-ENGAGEMENT-CHECK-RED-SINCE-6E7EF56EC (testing rescope)

Scope: `tests/integration/lab/test_species_relations_metamorphic_validation.py` only. No src/ or data/ change; the assertion keeps its exact form (pooled high rate >= pooled baseline rate, no tolerance band).

1. Record rpg-planner's ruling (a) and every measurement in the ticket before any test change (commit 1), so the authority precedes the expectation change (Epic C criterion 4).
2. Pin the governor for the lab runs with a test-scoped monkeypatch of `src.engine.governor.ResourceGovernor` (Kernel's lazy default) to a pinned-NORMAL subclass, so the run is deterministic at a SHA.
3. Move only the `wolf_den` region of `unit_faction_tension` next to `hometown` with a test-scoped `WorldRepository.load_world` override (ruling (a): measure on a contact-rich layout of the same world content).
4. Fix the seed list in advance (301-310 x 200t), sized on the pinned contact-layout measurement.
5. Add a non-vacuity guard on the baseline arm (pooled > 0 and >= measured-2 seeds with contact), labelled as such.
6. Two runs at one SHA must give identical per-seed counts. Then remove the species known-reds entry (after the known-reds PR lands), and close.
