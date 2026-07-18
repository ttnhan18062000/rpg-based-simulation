---
status: done
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260619-E63-FEATURE-PACKS
phase: done
date: 2026-06-19
tags: [feature-packs, pluggable-architecture, manifest, runtime-profile, decision-gate, epic, phase-6]
---

# TCK-20260619-E63-FEATURE-PACKS

## Title
Epic 6.3 · Pluggable Feature Pack Architecture (Long Horizon — Decision Gate Required)

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
Zero code beyond the vision doc. The adventure-routing and world-emergence domains already use a clean `enum → generator → scorer → mapper → tests` extension pattern — proven twice at small scale. This epic generalizes that pattern into a pluggable manifest system. A decision gate is required before starting: do not implement until ≥3 independent features have been added via the existing extension points.

Score: 8/10 · Effort: XL · Decision gate required

**Note: Phase 6 epics are speculative at planning time. Scope and sequencing must be re-evaluated after Phase 5 is complete.**

## Scope
- **Decision gate:** Do not start until at least 3 independent features have been added via the existing `adventure_routing_contract.md` and `world_emergence_contract.md` extension patterns. The pattern must be proven at small scale before generalization.
- `FeaturePackManifest`: self-describing YAML + code module entry points
- `RuntimeProfile`: selects which packs are active for a given simulation run
- `CompatibilityResolver`: checks pack dependencies, conflict detection, version constraints
- `BalanceExperimentSpec`: declarative balance test harness tied to a feature pack
- Generalize from existing `adventure_routing_contract.md` and `world_emergence_contract.md` patterns

## Out of Scope
- Third-party pack distribution / marketplace
- Pack-level sandboxing / security

## Acceptance Criteria
- A new quest type is added to the engine via a feature pack manifest without modifying any file in `src/engine/` or `src/domains/`
- Decision gate satisfied: ≥3 independent features added via existing extension points before this epic starts

## Related Tickets
- TCK-20260619-E53-FACTION-DIPLOMACY (prerequisite: proves extension pattern at scale before generalization)
- TCK-20260619-E63A-GATE-VERIFY (child — gate verification + registry architecture design)
- TCK-20260619-E63B-MANIFEST-MODEL (child — FeaturePackManifest + RuntimeProfile + CompatibilityResolver)
- TCK-20260619-E63C-REGISTRY-LOADER (child — FeatureRegistry + FeaturePackLoader + demo pack)
- TCK-20260619-E63D-BALANCE-PARITY (child — BalanceExperimentSpec + parity + integration test + docs)

## Related Docs
- `docs/plans/engine_future_epics_roadmap.md` § F
- `docs/plans/long_term_development_roadmap.md` § Epic 6.3
- `docs/simulation/domains/world_emergence_contract.md` (extension pattern source)

## Related Code Areas
- `src/domains/` (adventure_routing, world_emergence — extension pattern templates)

## Assumptions / Open Questions
- Re-evaluate full scope after Phase 5 is complete and decision gate condition is verified

## Implementation Notes
This ticket is a planning placeholder with an explicit decision gate. Scope this epic fresh only after the gate condition is verified.

When implementing: create `docs/architecture/feature_pack_architecture.md` (FeaturePackManifest schema, RuntimeProfile, CompatibilityResolver contract). Update `docs/parity_ledger/infrastructure.yaml` with feature-pack loading entries. Run `make knowledge-index-update` after docs/ changes.

## Test Summary
To be defined when decision gate is satisfied.

## Files Changed
- `src/domains/feature_packs/` (new package — manifest.py, profile.py, registry.py, loader.py, balance_spec.py)
- `content/packs/demo_escort_pack/` (new — manifest.yaml, generator.py, __init__.py)
- `src/scenarios/schema.py` (modified — RuntimeProfile wired into SimulationScenarioDefinition)
- `src/domains/campaigns/state.py` (modified — region_cultures field from E62)
- `docs/architecture/feature_pack_architecture.md` (new)
- `docs/parity_ledger/infrastructure.yaml` (modified — INFRA-PACK-001/002/003)
- `tests/unit/feature_packs/` (new — 30 unit tests)
- `tests/integration/feature_packs/` (new — 3 integration tests)

## Completion Summary
All 4 child tickets DONE (2026-06-23):
- E63A: Gate verified SATISFIED — 7+ extension patterns in E53/E61/E62; architecture doc created.
- E63B: FeaturePackManifest (Pydantic, frozen, YAML round-trip) + RuntimeProfile + CompatibilityResolver (Kahn's BFS); wired into SimulationScenarioDefinition.
- E63C: FeatureRegistry[T] (dict-based, canonical enum + pack entries) + FeaturePackLoader (discovers manifests, filters by profile, imports classes); demo_escort_pack registers ESCORT_DIGNITARY from content/packs/ without touching src/.
- E63D: BalanceExperimentSpec + pure BalanceExperimentRunner (dot-path metric snapshot); integration tests confirm no src/ modifications; docs finalized; knowledge index updated.
45 tests pass across all child tickets.
This epic-scoped ticket closes now that all four child tickets are done.
