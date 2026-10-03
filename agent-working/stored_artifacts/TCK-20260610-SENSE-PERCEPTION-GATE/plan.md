---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260610-SENSE-PERCEPTION-GATE
artifact_type: plan
tags: [sense, perception, gate]
---

# Plan — TCK-20260610-SENSE-PERCEPTION-GATE

## Approach

Create `src/world/perception/` package. `PerceptionGate.can_perceive()` maps
7 sense channels to target signal keys, loads profile from CatalogRepository,
computes per-channel score, and returns `PerceptionResult`.

## Key decisions

- Channel mapping table (`_SENSE_TO_SIGNAL`): decouples field names from signal keys
- Score formula: `sense_strength * signal_strength * distance_factor * terrain_mod * alertness_factor`
- Threshold 0.2 for perceived = True
- Fallback `_BASELINE_SENSE` matches normal_humanoid_senses values
- Profile not found → baseline_humanoid (never raises)
