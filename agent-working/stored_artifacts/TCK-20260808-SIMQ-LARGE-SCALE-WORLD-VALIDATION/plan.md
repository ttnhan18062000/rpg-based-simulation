---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260808-SIMQ-LARGE-SCALE-WORLD-VALIDATION
artifact_type: plan
tags: [simulation-quality, world, corpus, calibration]
---

# Plan — TCK-20260808-SIMQ-LARGE-SCALE-WORLD-VALIDATION

## Steps (already executed during Investigate — this ticket's own scale-discovery work required
## real tool execution to produce evidence, per its own Investigate scope item 3)

1. Hand-composed a 12-module `WorldCompositionSpec` (`data/content/world_compositions/generated/simq_scale_stress_seed42.yaml`),
   avoiding the 2 real collisions found.
2. Resolved + compiled via the real `world resolve`/`world compile` CLI — 68 entities confirmed.
3. Added `faction_tension_overrides` for 6 factions after the first calibration run showed 8/10
   pillars at zero signal.
4. `config/simulation_quality/profiles/simq_scale_stress_seed42.yaml` — no flags enabled,
   documented as a deliberate skip (no authored INFORMATION content).
5. Real 200t calibration, committed to `grade_anchors.json` as a new entry, added to
   `FAST_ANCHOR_KEYS`.
6. `corpus_registry.yaml` regenerated (picks up the new run_key automatically via ticket 1's own
   generator); `corpus_tier_taxonomy.md` updated with the new world's own row and full disposition.
7. `docs/simulation_quality/current_state.md`: findings summary.

## Acceptance-criteria map

| AC | Disposition |
|---|---|
| investigation.md confirms authoring-tooling gap + concrete target scale | Done — 500-1000 confirmed NOT achievable; 68 is the real, measured ceiling via working tooling |
| ≥1 new world authored at 500+ entities, real content | NOT met at the 500+ number — disclosed honestly; 68 entities with real (not placeholder) faction content is what was achievable |
| Full 10-pillar calibration run committed to grade_anchors.json | Done |
| corpus_tier_taxonomy.md updated | Done |
| Findings documented: pillar behavior, F6/throttle correlation, ceiling implications | Done — see investigation.md |
| Scoped pytest passes | Test phase |
