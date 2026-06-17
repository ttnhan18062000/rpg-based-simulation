---
status: active
layer: architecture
authority: P1
audience: agent
tags: [release-spine, capability-registry, scenario-runtime, read-model, decision-explanation, feature-packs, epic]
---

# Release Spine + Feature Pack Epic Proposal

## Vision

Close the remaining "release-grade backend" gaps identified in `feature_summary.md` / `expected_first_release.md` (Capability Registry, Scenario Runtime Service, Unified Read Model, Decision Explanation API) as Phase 1, since the underlying mechanics they wrap already exist. Then re-scope Phase 2 as either the pluggable Feature Pack architecture (`rpg_feature_direction.md`) or the Narrative/Macro-economy depth layer, decided after Phase 1 lands and the spine's actual shape is known.

## Context: What Already Works (do NOT re-implement)

Verified via `search_docs` + `graphify` against current `main`:

- **Domain Ownership Map** — `docs/simulation/domains/domain_ownership_map.md` (TCK-20260612/13). All 14 `src/domains/` subsystems documented with read/write interaction rules. ✅
- **Worldbuilding/Content pipeline** — full module/composition/procedural-generation epic shipped (PR #16, `world-generation` branch merged). ✅
- **Authoritative mutation boundary** — `ApplyPath.apply_generation` singular mutation point, deep-freeze tripwires (`docs/engine/authoritative_apply_contract.md`). One open checklist item: `RPG-INFRA-095` (unauthorized phase read) in `docs/logic_checklist_exhaustive.md`. ⚠️ partial
- **Behavior Scorecards / Cohort Analysis / Run Comparison** (Phase 26) — implemented (`EntityBehaviorScorecard`, `RunBehaviorScorecard`, `CohortAnalyzer`). ✅
- **Campaign lifecycle** — `CampaignSpec → CampaignRunner → Kernel ticks → CampaignResult` with sub-analysers (`LifeArcClassifier`, behavior comparison) — `docs/simulation/domains/campaigns_contract.md`. ✅ but scenario-level (not campaign-level) objective/win-loss-stall state machine does not exist yet.
- **Strategic reprioritization from narrative events** (trauma, betrayal) and **succession/legacy** (`docs/systems/world_evolution_and_resilience.md` §3.5) — implemented. Partial building block for a future Narrative Consequence Layer, not a full milestone/nemesis engine.
- **Lab/sweep infrastructure** — `ExperimentSpec`, sweep runner, validators (`docs/archive/engine_contracts/sweep_configuration.md`). ✅
- **Content pack format** — versioned manifests, enable/disable, pack validation contract (`WORLD-ASM-011`). ✅ — this is the closest existing precedent for the Phase 2 Feature Pack manifest shape.

## Confirmed Decisions

| Decision | Choice |
|---|---|
| Sequencing | Phase 1 (spine) ships before Phase 2 (feature packs or narrative depth) is scoped in detail — per user direction "mix: spine now, scope B/C next". |
| Phase 2 selection | Deferred. Re-evaluate after Phase 1 based on what the Capability Registry and Scenario Runtime Service actually expose. |
| Scope boundary | Phase 1 wraps/exposes existing mechanics; it should not require new domain logic, only registry/service/API surfaces. |

## Phase 1 — Release Spine

Targets the four items both `feature_summary.md` and `expected_first_release.md` independently rank P0/P1 and that are still genuinely missing:

1. **Capability / Support Registry** — backend-readable registry of features mapped to `OFFICIAL / SUPPORTED / EXPERIMENTAL / DEPRECATED / UNSUPPORTED`. Extends the existing narrow `docs/archive/engine_contracts/unsupported_register.md` pattern into a full matrix tied to docs/tests/source. This becomes the foundation Phase 2's Feature Pack manifest (if chosen) would build on.
2. **Scenario Runtime Service** — objective/win-loss-stall state machine sitting above raw kernel ticks and above `CampaignRunner`, with pause/resume/checkpoint. Turns lab-only sweep execution into a runnable product loop without touching kernel/domain internals.
3. **Unified Read Model Service** — consolidates the currently fragmented cognition/history/live-status APIs behind one presenter layer, per the project's existing rule that APIs must not expose raw domain objects.
4. **Decision Explanation Model** — promotes the existing adventure route trace (already computed, not yet durable/queryable) into a first-class stored/queryable API.

Open items to resolve during Phase 1 scoping (not yet decided):
- Whether `RPG-INFRA-095` (unauthorized phase read) should be folded into this epic or handled as a separate hotfix ticket first.
- Exact persistence/storage shape for Decision Explanation records (new typed durable state vs. derived/replay-computed).

## Phase 2 — Deferred Scope Decision

To be decided after Phase 1 lands. Candidates, not yet scoped:

- **B: Pluggable Feature Packs** (`rpg_feature_direction.md`) — `FeaturePackManifest`, `RuntimeProfile`, `CompatibilityResolver`, `BalanceExperimentSpec`, `WorldScorecard`. Larger architectural bet; benefits from Phase 1's Capability Registry existing first.
- **C: Narrative/RPG depth** — unified Narrative Consequence Layer (milestones, nemesis, regional scars) and macro-economy health checks. Lower architectural risk, more content-shaped; builds on existing reprioritization/succession mechanics.

## Out of Scope (for this epic)

- Any new domain mechanics (combat, economy, cognition rules) — Phase 1 is wrapping, not adding mechanics.
- Frontend/UI work.
- Mid-run feature hot-swapping (explicitly flagged as a determinism risk in `rpg_feature_direction.md` — packs switch between runs only, if/when Phase 2B is chosen).
