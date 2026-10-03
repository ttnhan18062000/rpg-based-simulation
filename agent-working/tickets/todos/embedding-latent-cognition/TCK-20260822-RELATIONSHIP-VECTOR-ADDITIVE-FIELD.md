---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260822-RELATIONSHIP-VECTOR-ADDITIVE-FIELD
phase: open
date: 2026-08-22
tags: [social, cognition, determinism]
---

# TCK-20260822-RELATIONSHIP-VECTOR-ADDITIVE-FIELD

## Title
Additive latent relationship-vector field for multi-party social memory

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The original proposal asked to replace the scalar relationship_scores/trust_history float with a latent vector for richer multi-party social memory. Investigation found relationship_scores/trust_history is read by 20+ scalar call sites across 12 files doing direct float arithmetic and threshold comparisons -- a literal replacement would be a large breaking change. This ticket instead adds a new typed relationship-vector field additively, alongside the unchanged existing float field, following the precedent set by TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY, with any consumer confined to offline use per the idea doc's runtime-determinism constraints.

## Scope
- Add a new typed, frozen-dataclass relationship-vector field alongside the existing relationship_scores/trust_history float dict
- Provide to_dict()/from_dict() JSON round-trip with sorted-key determinism, matching SocialMemoryRecord/InteractionRecord's existing pattern
- Ensure any consumer of the new field runs offline only, per the idea doc's runtime hot-path block
- Preserve docs/simulation/social_systems_contract.md's existing precedence (bond sentiment over trust_history when both exist)

## Out of Scope
- Bravery coefficient calibration (separate ticket)
- Chronicle arc clustering (separate ticket)
- Cross-region culture convergence (separate ticket)
- Personality/life-arc drift mechanism (separate ticket)
- Replacing or removing the existing relationship_scores/trust_history float dict or touching any of its ~20 existing scalar-read call sites
- Any runtime/hot-path scoring use of the new vector field
- Changing bond-sentiment-vs-trust_history precedence rules

## Acceptance Criteria
- [ ] Scoped as an ADDITIVE new relationship-vector field alongside the existing relationship_scores/trust_history float dict -- NOT a replacement, matching the precedent set by TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY; the proposal's literal "replace the float with a vector" framing is explicitly out of scope because it would break 20+ existing scalar-read call sites across 12 files
- [ ] The existing relationship_scores/trust_history type/default/serialized shape is unchanged; all ~20 existing scalar-read call sites remain byte-identical and untouched
- [ ] The new vector field has a typed frozen dataclass model with to_dict()/from_dict() JSON round-trip and sorted-key determinism, matching SocialMemoryRecord/InteractionRecord's existing pattern
- [ ] Any consumer of the new vector field runs offline only, per the idea doc's runtime-hot-path-blocking constraint -- enforced/documented, not just assumed
- [ ] test_replay_determinism.py (or an equivalent new determinism test) passes with the new field populated
- [ ] The new representation respects docs/simulation/social_systems_contract.md's existing precedence rule (bond sentiment over trust_history when both exist) -- does not silently override it

## Related Tickets
- TCK-20260619-E43-SOCIAL-MEMORY
- TCK-20260619-E43A-SOCIAL-MEM-MODEL
- TCK-20260619-E43B-EXPORT-IMPORT
- TCK-20260619-E43C-DECAY
- TCK-20260628-E43G-NEMESIS-RELATION
- TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY

## Related Docs
- docs/plans/idea_embedding_latent_cognition.md
- docs/simulation/social_systems_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/domains/campaigns/social_memory.py
- src/core/models/social.py
- src/systems/social_systems/party_composition.py
- src/systems/social_systems/relationships.py
- src/systems/social_systems/appraisal.py
- src/systems/social_systems/consequence_events.py
- src/systems/social_systems/party.py
- src/domains/cooperation/providers.py
- src/domains/cooperation/services.py
- src/domains/cooperation/evaluators.py
- src/domains/campaigns/plan_revision.py
- src/domains/campaigns/grief_urgency.py
- src/domains/campaigns/orchestrator.py
- src/engine/tactical.py
- src/systems/world_systems/groups.py
- src/ai/goals/social_contract_scorer.py
- src/observability/event_extractor.py
- src/observability/event_shapers.py
- src/api/presenters/state_presenter.py
- src/core/state.py
- src/core/builder.py

## Assumptions / Open Questions
- No embedding model, dimensionality, or determinism-proof mechanism exists yet for the new vector field -- needs a design decision before implementation
- Whether this work is authorized now given the source idea doc's own "Phase 3+, not scheduled" framing should be confirmed, not assumed
- Consumer(s) of the new vector field (which system reads it, and for what purpose) are not yet specified by the proposal and need clarification during planning

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
