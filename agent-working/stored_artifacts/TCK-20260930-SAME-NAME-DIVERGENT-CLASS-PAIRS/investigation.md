---
status: active
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS
artifact_type: investigation
tags: [core, bug]
---

# Investigation

Scan: `same_name_scan.py` over `src/` at origin/main 3b5fab1e9 plus the batch branch; rows in `same_name_scan.jsonl`. Top-level class names defined in more than one module: **23** now (the ticket recorded 24). 4 are mechanism-shaped (suffix list), 19 are not. Importers are matched by `from <module> import ... Name` and `<module>.Name`; a dynamic import would be missed, and the dead-twin claims below were checked by name over `src/`, `tests/` and `tools/`.

## The four mechanism-shaped pairs
| name | keep (live) | twin | twin's readers | state |
|---|---|---|---|---|
| `ItemRegistry` | `src/core/registries.py` (catalog) and `src/core/items.py` (static) | both | both have src and test readers | TCK-20260914 (done) decided, user-approved, to keep both: same data in catalog mode, different failure semantics for unknown ids, now counted and recorded. Needs only an allowlist reason. |
| `RecipeRegistry` | `src/core/registries.py` (25 entries; used by `engine/blacksmith.py`, `engine/intent/action_intent.py`, the providers, `material_predicate.py`) | `src/core/recipes.py` (legacy) | one src reader, `src/town/blacksmith.py::BlacksmithAction`, which nothing in `src/` or `tools/` constructs; its only reader is `tests/unit/world/test_economy_contract.py` | dead chain: legacy registry -> `BlacksmithAction` -> one test file |
| `SkillScalingService` | `src/engine/rpg_depth.py` (`engine/apply.py`, `engine/domain/skill_actions.py`, `domains/campaigns/orchestrator.py`) | `src/progression/skills.py` | no src reader; `tests/unit/progression/test_progression_v2.py` imports it; `tools/mechanism_registry/mechanism_registry_completeness_check.py:207` names it in `WIDER_PENDING` | dead twin |
| `CapacityService` | `src/strategy/capacity.py` (`engine/pipeline_phases/capacity_enforcement.py`) | `src/strategy/cognition_capacity.py` | one src reader: `StrategicIntelligenceSystem.derive_cognition_profile` (`systems/strategic_systems/intelligence.py:1827`), which only `tests/unit/strategic/test_interruption_resistance.py` calls; `tests/unit/strategic/test_cognition_capacity.py` tests the class; `WIDER_PENDING` names it | dead twin |

## The other 19 names (classification, by reading the two definitions)
- Intentional: different shape and layer, same word. `AnalysisContext` (anomaly pipeline vs Phase 8 analyzers), `AnomalyRecord` and `MetricWindowRecord` (domain record vs warehouse row), `BudgetCheckResult`, `ConfidenceLevel` (two enums in two analyzers), `InformationQuery`, `ItemDefinition` (catalog schema vs runtime template), `KnowledgeFact` (persisted self-model fact vs provider DTO), `RuntimeProfile`, `SkillDefinition` (live `core/skills.py` vs genetics), `SocialScorer` (goal scorer vs SimQ pillar), `ValidationIssue`, `ValidationResult`, `BehaviorChangeProofDetector` (campaign vs observability), `QuestTemplate` (three unrelated definitions).
- Same name, different referent that a reader can confuse: `ObservabilityMode` (8 operational modes in `observability/config.py` vs 4 backpressure states NORMAL/PRESSURE/DEGRADED/SURVIVAL in `observability/event_recorder.py`).
- Duplicate with drift risk: `HardwareClass` (`certification/models.py` and `config/profiles.py` define the same three members, each with its own readers); `ErrorResponse` (identical `detail` model copied into three route modules).
- Dead twin: `EnvironmentCapture` in `src/core/governance.py` (no reader in `src/` or `tests/`; the certification harness uses `certification/models.py`).
