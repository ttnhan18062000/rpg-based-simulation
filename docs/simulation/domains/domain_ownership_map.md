---
status: authoritative
layer: ai
authority: P1
audience: agent
last_verified: 2026-06-12
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

| Domain | src/ path | Phase | Key responsibility | Owned state / output | Detailed contract |
|---|---|---|---|---|---|
| **adventure** | `src/domains/adventure/` | — | Route scoring, mapper, quest resolution for exploration | AdventureResult, route scores | (see files) |
| **campaigns** | `src/domains/campaigns/` | Phase 9 | Multi-tick campaign orchestration, arc analysis, forbidden-behaviour detection | CampaignResult, EntityArcReport, WorldArcReport | [campaigns_contract.md](campaigns_contract.md) |
| **combat_engagement** | `src/domains/combat_engagement/` | Phase 4 | Pre-combat subjective assessment: opponent perception, self-estimate, posture selection | CombatEngagementDecisionResult, CombatPosture | [combat_engagement_contract.md](combat_engagement_contract.md) |
| **commitment** | `src/domains/commitment/` | — | Commitment tracking, abandonment pressure, reputation impact | commitment records | (see cognition_domain_ownership.md) |
| **cooperation** | `src/domains/cooperation/` | — | Group cooperation evaluators, cooperative postures, social events | cooperation evaluations | (see cognition_domain_ownership.md) |
| **emotion** | `src/domains/emotion/` | — | Emotional state, habit formation, opportunity cost, recovery | emotion updates | (see files) |
| **information** | `src/domains/information/` | Phase 5 | Belief assimilation, source trust, contradiction detection, knowledge routing | SourceTrustEntry updates, assimilation records | [information_contract.md](information_contract.md) |
| **memory** | `src/domains/memory/` | — | Spatial memory attribution and updates | spatial memory records | (see cognition_domain_ownership.md) |
| **motivation** | `src/domains/motivation/` | — | Motivation/drive resolution and filtering | motivation evaluations | (see cognition_domain_ownership.md) |
| **optimization** | `src/domains/optimization/` | Phase 10 | Cross-cutting performance utilities: cache, degradation, feature flags, budget | DegradationLevel, CacheStrategy, FeatureFlagManager | [optimization_contract.md](optimization_contract.md) |
| **perception** | `src/domains/perception/` | — | Sensory salience filtering and perception phase | perception records | (see cognition_domain_ownership.md) |
| **progression** | `src/domains/progression/` | — | XP, skill gaps, ledger, progression generation | progression records | (see files) |
| **time** | `src/domains/time/` | — | Temporal tracking service | temporal state | (see cognition_domain_ownership.md) |
| **world_emergence** | `src/domains/world_emergence/` | — | World-level emergence aggregation, ecology events | emergence models | (see files) |

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
