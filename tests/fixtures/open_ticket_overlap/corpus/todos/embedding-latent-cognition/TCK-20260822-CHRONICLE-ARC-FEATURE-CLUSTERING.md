---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260822-CHRONICLE-ARC-FEATURE-CLUSTERING
phase: open
date: 2026-08-22
tags: [world, determinism]
---

# TCK-20260822-CHRONICLE-ARC-FEATURE-CLUSTERING

## Title
Numeric feature-vector clustering for Chronicle narrative arcs (offline, non-runtime)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The original proposal asked to embed event sequences to enable narrative arc clustering in Chronicle, framed as text embeddings. Investigation found NarrativeLedgerEntry carries no free-text/description field -- only numeric event-specific payload data -- so a literal text-embedding model has no natural input. This ticket instead builds an offline, hand-built numeric/categorical feature-vector representation (event-type one-hot, tick-delta, subject continuity, payload numerics) clustered with a classical deterministic algorithm to detect narrative arcs, kept fully decoupled from ChronicleCompiler's runtime path and respecting grouper.py's determinism law.

## Scope
- Build an offline numeric-feature-vector representation for NarrativeLedgerEntry sequences (event-type one-hot + tick-delta + subject continuity + payload numerics)
- Apply a classical, deterministically-seeded clustering algorithm over that feature vector to detect narrative "arcs" with a coherence score
- Keep the clustering module fully decoupled from ChronicleCompiler.compile()'s runtime entry point
- Emit arc/coherence output as an offline-only artifact distinct from chronicle.json unless the ticket explicitly extends both chronicle_contract.md and the presenter in the same session

## Out of Scope
- Bravery coefficient calibration (separate ticket)
- Social memory vector field (separate ticket)
- Cross-region culture convergence (separate ticket)
- Personality/life-arc drift mechanism (separate ticket)
- Any literal text-embedding/NLP model (no free-text field exists to embed)
- Wiring arc output into chronicle.json/REST schema unless explicitly extended in this same ticket
- Fixing the pre-existing chronicle_contract.md/significance.py doc drift found independently during investigation (separate concern)

## Acceptance Criteria
- [ ] Explicitly scoped as numeric/categorical feature-vector clustering (event_type one-hot + tick-delta + subject continuity + payload numerics), NOT text embedding -- NarrativeLedgerEntry has no free-text/description field, so no natural text input exists for a literal embedding-model approach
- [ ] New offline clustering module is invocable independently of ChronicleCompiler.compile(); compile() with/without the module present produces byte-identical output, proving zero coupling into the runtime pipeline
- [ ] Running the clustering step twice on the same fixed NarrativeLedgerEntry list produces identical arc-cluster assignments both times, satisfying grouper.py's "deterministic, stateless, no engine imports" design law
- [ ] For an entry sequence forming exactly one rule-based Incident, the clustering step assigns all its events to one arc -- regression guard proving no contradiction with existing tick-window semantics
- [ ] Each detected arc carries a coherence score float in a documented range, serialized in an offline-only output artifact distinct from chronicle.json's schema, unless the ticket explicitly extends both chronicle_contract.md and the presenter in the same session
- [ ] If any clustering algorithm has nondeterministic default behavior (e.g. k-means random init, HDBSCAN), it uses explicit seeding/fixed ordering to satisfy the determinism law

## Related Tickets
- TCK-20260619-E51A-SIGNIFICANCE
- TCK-20260619-E51B-GROUPER
- TCK-20260619-E51C-NAMING
- TCK-20260619-E51D-RENDERER
- TCK-20260619-E53Da-SIGNIFICANCE-NAMING
- TCK-20260619-E53Dc-COMPILER-INTEGRATION
- TCK-20260629-SIMQ-EMIT-NARRATIVE
- TCK-20260628-E-NARRATIVE-CONSEQUENCE

## Related Docs
- docs/simulation/domains/chronicle_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/domains/chronicle/grouper.py
- src/domains/chronicle/significance.py
- src/domains/chronicle/compiler.py
- src/domains/chronicle/renderer.py
- src/domains/campaigns/state.py
- docs/simulation/domains/chronicle_contract.md
- requirements.txt
- requirements-knowledge.txt
- expected: src/domains/chronicle/arc_clustering.py

## Assumptions / Open Questions
- Whether cluster/arc output should ever surface through chronicle.json/REST or remain a standalone offline analysis script is unresolved and should be clarified in the ticket rather than assumed
- Choice of classical clustering algorithm and its determinism-safe configuration (seeding/fixed ordering) is an implementation decision not yet made
- Whether "embedding" in the proposal's original wording can be satisfied by a hand-built feature vector (as recommended) or whether the requester specifically wants a learned embedding model needs confirmation
- `layer: world` was chosen because Chronicle is world/narrative content generation and no more specific "narrative" or "chronicle" layer is registered in `registries/layer_registry.jsonl`; flagged here per the layer-selection guidance rather than force-fit silently

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
