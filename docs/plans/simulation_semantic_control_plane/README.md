---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, documentation, schema]
---

# Epic — Simulation Semantic Control Plane

**Status, scoped 2026-09-23.** This is the next phase after the World Rule Catalog
(`docs/world_rules/`, frozen 2026-09-22, 172 Rule IDs) and the Mechanism Registry
(`registries/mechanisms.yaml`, 93 mechanisms): connecting the two. Right now they have **zero
cross-references** — confirmed by direct grep, not assumed — no Rule cites a `mechanism_id`, and
no mechanism cites a Rule. This epic is the design and staged rollout for closing that gap without
repeating this repo's own two prior failures at exactly this kind of problem: the five
independently-drifting status artifacts the Mechanism Registry itself replaced
(`docs/plans/mechanism_registry_initiative.md` §1), and the rejected *derived* `system` tier
(`docs/plans/mechanism_tier_model_initiative.md`, root cause: prerequisite and collaboration are
different relations and no traversal over one produces the other).

**Provenance.** Authored from a three-draft external-AI design conversation. The first two drafts
(`tmp/simulation-semantic-control-plane-ext-ai.md`, `tmp/rpg-core-agent-operating-model-ext-ai.md`)
were reviewed against real repo state (`tmp/semantic-control-plane-review.md`) and found to have 8
open items — mainly an unresourced Rule×Mechanism mapping at 172×93 scale with no feasibility
gate, a `FORBIDDEN` modality with zero grounding in the frozen Catalog, and an unaddressed overlap
with `docs/guidelines/intentional_divergences.md`. A third draft resolved all 8; it is preserved,
unedited, at `docs/brainstorm/simulation_semantic_control_plane_external_draft.md`. **This epic is
independently authored from that design** — not a copy — verified against this repo's own actual
data (mechanism/Rule counts, real examples) rather than restated from the draft's own claims.

## Files

| File | Covers |
|---|---|
| [architecture.md](architecture.md) | The five-truth-layer model, the Rule↔Mechanism mapping shape, State Ownership, the Management Plane, and the explicit non-goals that keep this from becoming a sixth drifting artifact. |
| [agent_operating_model.md](agent_operating_model.md) | Task classification, the 9-step troubleshooting ladder, per-scenario agent workflows (wire vs. introduce, debug-execution vs. debug-semantics, tuning vs. wiring-bug), and the completion-output shape. |
| [rollout_plan.md](rollout_plan.md) | The staged rollout (Stage A → F), the first operational slice (Territory/Control), and the specific open decisions this epic resolves outright rather than leaving implicit. |
| [roadmap.md](roadmap.md) | The bounded, milestone-based plan (M0 → M4) for actually building this — schema and validator, the Territory/Control slice, drift detection, ingesting existing review-export findings, and a second slice proving the model generalizes. Stops where `rollout_plan.md`'s perpetual Stage D/E/F begins. **Start here for "what do I actually build first."** |

## Non-negotiable constraints carried forward from both prior arcs

- **No orphan document data** (`docs/plans/mechanism_claims_as_tests_initiative.md` §1) — every
  artifact this epic produces is either consumed by a running check or explicitly marked
  informational-only. A generated file nothing reads is the same failure this repo already paid
  for once.
- **`depends_on` stays narrow** — functional prerequisite only, never execution order, containment,
  or collaboration. This epic's own Rule↔Mechanism mapping is a *separate* relation and must never
  be folded into `depends_on`.
- **Realization classification (`SUPPORTED`/`PARTIAL`/`CONFLICTING`/`MISSING`/`INERT-OFF`/
  `UNKNOWN`) already exists** — it's the vocabulary the World Rule Catalog's own review exports
  already use for "Repository evidence" (e.g. `TERR-01`'s classification of `owner_faction_id`).
  This epic reuses it, not a new one.
- **`UNKNOWN` is a first-class, permanent state**, not a placeholder to eliminate. Both the
  Mechanism Registry (completeness checker scoped to 2 of ~15 source directories,
  `TCK-20260920-MECHANISM-COMPLETENESS-CHECK-SCOPE-GAP`) and this mapping will start, and likely
  stay, majority-`UNKNOWN` for a long time. That is a correct state, not a failure to fix quickly.
