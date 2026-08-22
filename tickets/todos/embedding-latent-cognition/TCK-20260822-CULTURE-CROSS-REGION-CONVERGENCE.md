---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260822-CULTURE-CROSS-REGION-CONVERGENCE
phase: open
date: 2026-08-22
tags: [world]
---

# TCK-20260822-CULTURE-CROSS-REGION-CONVERGENCE

## Title
Cross-region cultural convergence mechanism (net-new, does not currently exist)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The original proposal described replacing an existing rule-based cross-region cultural convergence algorithm with a learned latent-space representation, so that regions organically drift toward each other based on shared events. Investigation found this convergence mechanism does not exist anywhere in the shipped E62 Culture Drift system today -- CultureState is derived purely per-region from that region's own local events, with no cross-region similarity or convergence logic at all. This ticket therefore builds cross-region convergence as new functionality (not a refactor), starting from a classical similarity/distance metric between regions' existing 4-axis CultureState vectors, with a genuinely learned/latent representation left as an open design option contingent on preserving a documented decode path back to the 4 named axes.

## Scope
- Design and implement a cross-region cultural convergence mechanism (similarity/distance metric and/or convergence delta) operating on existing per-region CultureState axis vectors
- Respect the episode-boundary derivation lifecycle (CampaignState.region_cultures), not per-tick
- Preserve round-trip to the 4 named CultureState axes for CulturalBiasApplicator, or explicitly re-scope/deprecate the affected parity entries with a recorded divergence
- Keep the cultural overlay transient (per motivation-scoring call), not baked into durable MotivationModel/ValuePreferenceProfile state

## Out of Scope
- Personality/individual entity drift (separate ticket -- different module, different lifecycle, zero shared mechanism)
- Bravery coefficient calibration (separate ticket)
- Chronicle arc clustering (separate ticket)
- Social memory vector field (separate ticket)
- Replacing CultureDeriver's rule table with a trained/learned model as a hard requirement -- only pursued if it still round-trips to the 4 axes, otherwise explicitly flagged as a divergence
- Baking the cultural overlay into durable MotivationModel/ValuePreferenceProfile state

## Acceptance Criteria
- [ ] Ticket explicitly states this is NEW functionality -- cross-region cultural convergence does not exist anywhere in src/domains/culture/ today -- not a refactor of an existing convergence algorithm
- [ ] Given two regions with independently-derived CultureState axis vectors and a defined 'shared event' history between them, a similarity/distance metric between the two regions measurably decreases (or a defined convergence delta applies) after N shared episodes -- testable via a 2-region N-episode acceptance test analogous to test_two_regions_diverge
- [ ] Any replacement of CultureDeriver's rule table with a latent representation must still round-trip to the 4 named axes for CulturalBiasApplicator and parity entries WORLD-CULT-001/002/003, or those entries are explicitly re-scoped/deprecated with a recorded divergence in docs/guidelines/intentional_divergences.md
- [ ] A latent-space representation must have a documented decode/inspection path satisfying the Durable State Rule -- an opaque vector with no interpretable readout is not acceptance-testable
- [ ] Convergence derivation continues to respect the episode-boundary lifecycle (CampaignState.region_cultures), not per-tick, and the cultural overlay remains transient, not baked into durable MotivationModel/ValuePreferenceProfile state

## Related Tickets
- TCK-20260619-E62-CULTURE-DRIFT
- TCK-20260619-E62A-CULTURE-MODEL
- TCK-20260619-E62B-CULTURE-DERIVER
- TCK-20260619-E62C-MOTIVATION-OVERLAY
- TCK-20260619-E62D-PARITY-VERIFY
- TCK-20260619-E63A-GATE-VERIFY

## Related Docs
- docs/world/culture_drift_contract.md
- docs/mechanics/05_world_evolution.md
- docs/parity_ledger/world_dynamics.yaml
- docs/guidelines/intentional_divergences.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/domains/culture/model.py
- src/domains/culture/deriver.py
- src/domains/culture/applicator.py
- src/domains/culture/exporter.py
- src/domains/motivation/service.py
- docs/world/culture_drift_contract.md
- docs/parity_ledger/world_dynamics.yaml
- expected: src/domains/culture/convergence.py

## Assumptions / Open Questions
- Whether 'convergence' should be implemented as a classical similarity/distance metric (recommended, no new dependency) or a genuinely learned/latent representation (larger, ML-dependent change) is an open design decision
- Whether WORLD-CULT-001/002/003 parity entries can remain verified as-is or need re-scoping/deprecation depends on the final representation chosen
- This is a first-of-its-kind mechanism in this codebase (no prior embedding/latent work referenced anywhere in REGISTRY.yaml or working_log.csv) -- raises the bar for architecture review before implementation

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
