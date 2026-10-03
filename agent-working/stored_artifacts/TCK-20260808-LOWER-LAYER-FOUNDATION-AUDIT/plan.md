---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260808-LOWER-LAYER-FOUNDATION-AUDIT
artifact_type: plan
tags: [simulation-quality, documentation]
---

# Plan — TCK-20260808-LOWER-LAYER-FOUNDATION-AUDIT

## Doc structure
`docs/audits/D21_entity_lifecycle_foundation_layers.md`, matching the existing `D0N_*.md` audit
convention (frontmatter, Summary table, per-topic sections, Related Docs):

1. **Why lower-first** — the user's own stated design priority, framed as the doc's own rationale
2. **Per-bucket table**: VITALS / GROWTH_PROGRESSION / EXPLORATION / COMBAT / STRATEGY_COGNITION
   (baseline) / CONCLUSION_DEMOGRAPHIC — real trigger events, real SimQ scorer + key weights, real
   observed reachability, status (solid / real gap, open / real gap, fixed)
3. **The central distinction**: "wired to a scorer" (event_type_coverage.md's own question,
   answered: excellent) vs. "fires at real, meaningful volume in actual gameplay" (this session's
   own kernel-level question, answered: mostly yes, with GROWTH_PROGRESSION as the one real
   exception)
4. **Known foundation-layer data-integrity risk**: monster role mistagging (disclosed, not fixed)
5. **Recommendation**: hold ECONOMY/SOCIAL/NARRATIVE_QUEST expansion until
   `TCK-20260808-GROWTH-PACING-STALL-DETECTOR-IMBALANCE` lands, since those higher layers'
   entities are the same entities whose lower-layer growth is currently stalled — building
   richer higher-layer content on top of a stalled growth loop would compound rather than
   diagnose the real issue.

## Acceptance-criteria map
All 4 ACs map directly to sections 2-3 of the doc (real events/scorers/gaps documented) and the
doc's own registry inclusion (automatic via `make docs-registry` at Finalize).

## Unresolved Questions
None — grounded entirely in already-verified real data.
