---
status: authoritative
layer: ai
authority: P1
audience: agent
last_verified: 2026-06-13
tags: [domains, architecture, ownership, ai]
---

# Domain Ownership Map

`src/domains/` contains 14 subsystems that implement entity decision-making, cognition, and world-level behaviour. Each domain owns a slice of an entity's subjective state or a simulation-wide analytical capability.

**Existing coverage** — `docs/architecture/cognition_domain_ownership.md` maps the cognition sub-model components (PerceptionModel, TemporalModel, CausalMemory, SpatialMemory, MotivationModel, CommitmentModel, RelationshipModel) to their domain packages. This document extends that map to cover all 14 domains and establishes interaction rules.

For bounded-cognition strategy/decision contracts see `docs/strategy/`.

---

## Authoritative Status

Domains are **decision logic** — they read `AuthoritativeState` and `EntityState` and return typed result records. They do **not** directly mutate durable state. Any state changes they produce must be applied through the authoritative pipeline.

---

## All 14 Domains

Each domain's "stage" below is its own position in the domain decision pipeline (which produces proposed updates) — a separate, smaller sequence from the engine's 17-stage authoritative mutation pipeline (`docs/engine/authoritative_pipeline.md`) that later applies those proposals to `AuthoritativeState`. The two sequences are not the same numbering; do not conflate a domain's stage with an authoritative-pipeline stage of the same number.

| Domain | src/ path | Domain decision-pipeline stage | Key responsibility | Owned state / output | Detailed contract |
|---|---|---|---|---|---|
| **adventure** | `src/domains/adventure/` | Adventure Decision | Route generation, scoring, selection; project mapping | StrategicUpdate (projects, current_project_id, objectives) | [adventure_contract.md](adventure_contract.md) |
| **campaigns** | `src/domains/campaigns/` | Not a live pipeline stage — analysis-only, wraps the Kernel internally for bounded test/regression runs | Multi-tick campaign orchestration, arc analysis, forbidden-behaviour detection | CampaignResult, EntityArcReport, WorldArcReport | [campaigns_contract.md](campaigns_contract.md) |
| **combat_engagement** | `src/domains/combat_engagement/` | Pre-Combat Assessment | Pre-combat subjective assessment: opponent perception, self-estimate, posture selection | CombatEngagementDecisionResult, CombatPosture | [combat_engagement_contract.md](combat_engagement_contract.md) |
| **commitment** | `src/domains/commitment/` | Inline utility — no dedicated stage | Commitment pressure, abandonment classification, reputation route impact | PublicReputationProfile.labels (via ReputationUpdateService) | [commitment_contract.md](commitment_contract.md) |
| **cooperation** | `src/domains/cooperation/` | Cooperation | Help-need detection, partner scoring, posture selection, party cohesion | ContractState, BlockerState, StrategicUpdate | [cooperation_contract.md](cooperation_contract.md) |
| **emotion** | `src/domains/emotion/` | Event-driven — not scheduled per-tick | Emotional state updates, habit bias, recovery window, opportunity cost | EmotionalModel, HabitMemory (immutable replace) | [emotion_contract.md](emotion_contract.md) |
| **information** | `src/domains/information/` | Information / Belief Processing | Belief assimilation, source trust, contradiction detection, knowledge routing | SourceTrustEntry updates, assimilation records | [information_contract.md](information_contract.md) |
| **memory** | `src/domains/memory/` | Memory Update | Causal attribution, spatial memory, temporal urgency recalculation | CausalMemory, SpatialMemory, TemporalModel (immutable replace) | [memory_contract.md](memory_contract.md) |
| **motivation** | `src/domains/motivation/` | Inline utility — no dedicated stage | Drive evaluation, doctrine-based routing bias, role-fit scoring | None — pure scoring utility; no EntityUpdate produced | [motivation_contract.md](motivation_contract.md) |
| **optimization** | `src/domains/optimization/` | Feature Rollout Control | Cross-cutting performance utilities: cache, degradation, feature flags, budget | DegradationLevel, CacheStrategy, FeatureFlagManager | [optimization_contract.md](optimization_contract.md) |
| **perception** | `src/domains/perception/` | Perception Update | Salience filtering, attention focus, signal budget clamping | entity.cognition.subjective.perception (immutable replace) | [perception_contract.md](perception_contract.md) |
| **progression** | `src/domains/progression/` | Progression Conversion | Reward ledger, conversion option generation, AP/equipment decisions | EquipmentUpdate, TaskUpdate, ResourceTransferIntent, IdentityUpdate | [progression_contract.md](progression_contract.md) |
| **time** | `src/domains/time/` | Memory Update (alongside memory) | Temporal pressure service: deadline/cooldown/staleness urgency calculation | Urgency map (read-only derived signal, not persisted) | [time_contract.md](time_contract.md) |
| **world_emergence** | `src/domains/world_emergence/` | World Emergence | Regional pressure modeling, opportunity generation, signal broadcasting | StateUpdate (world opportunities), entity.exposed_world_signals | [world_emergence_contract.md](world_emergence_contract.md) |

---

## Interaction Rules

1. **Domains read state — they do not write it.** All domain services receive `EntityState` and/or `AuthoritativeState` and return typed result records. The authoritative pipeline applies those results.

2. **Domains do not call other domains directly.** Cross-domain concerns are mediated through `src/core/` types (`KnowledgeFact`, `LeadState`, `SourceTrustEntry`, etc.) — not through direct imports between domain packages.

3. **optimization is cross-cutting utility.** Any domain may use `src/domains/optimization/` cache, degradation, or feature-flag services. These utilities do not own simulation state — they are advisory performance helpers.

4. **Cognition sub-model ownership.** For the six cognition-mapped domains (perception, time, memory, motivation, commitment, cooperation), the owning package is canonical per `docs/architecture/cognition_domain_ownership.md`. That document takes precedence for sub-model path mapping.

5. **Feature flags gate domain activation.** `FeatureFlagManager` in `src/domains/optimization/feature_flags.py` controls which domains are active (OFF/SHADOW/ON/STRICT). A domain in OFF mode must not be called on the tick path. See [optimization_contract.md](optimization_contract.md).

---

## Prohibited Patterns

- A domain service **must not** import from another domain package (e.g. `combat_engagement` must not import `information`).
- A domain service **must not** directly mutate `AuthoritativeState` fields.
- A domain service **must not** call `Kernel.tick_once()` — except `campaigns`, which explicitly wraps the kernel for multi-tick analysis (see [campaigns_contract.md](campaigns_contract.md)).
