---
status: active
layer: testing
authority: P1
audience: developer
---

# Content Migration Test Ownership Map

**Status:** Active  
**Last updated:** 2026-06-09  
**Relates to:** docs/testing/v2_test_taxonomy.md

This document maps every major test suite to the behavior it owns, identifies duplicate
coverage areas, and specifies where new Phase 29–34 tests belong.

---

## Ownership Table

| Suite path | Marker / tier | Owns | Preserves |
|---|---|---|---|
| `tests/unit/content/` | unit | Catalog schema validation, migration_map YAML schema, active-data-consumer gate, content record structure | — |
| `tests/unit/worldassembly/` | unit, worldassembly | WorldModule normalization, provenance, resolver, archetype preservation, compile-context | — |
| `tests/unit/content_semantics/` | unit | Content semantic rules (tag validation, category constraints) | — |
| `tests/unit/runtime/` | unit | Registry bootstrap modes, HardcodedFallbackError, ContentSourceReport | — |
| `tests/unit/scenarios/` | unit | SimulationScenarioDefinition, ScenarioSetupResolver, ModifierApplicator, ScenarioSetupContext | — |
| `tests/unit/core/` | unit | Core dataclasses, registry bootstrapping, mode enum | — |
| `tests/unit/entities/` | unit | Entity lifecycle, identity resolution, role/faction compat | — |
| `tests/integration/content/` | integration, worldassembly | Strict world matrix (cumulative module loading), active-data-consumer (integration) | — |
| `tests/integration/worldassembly/` | integration, worldassembly | Real catalog assembly, real module normalization, world compositions | — |
| `tests/integration/scenarios/` | integration | ScenarioSetupResolver against real catalog, full setup pipeline | — |
| `tests/integration/combat/` | integration | Combat resolution, durability decay, victory outcomes | — |
| `tests/integration/kernel/` | integration | 6-phase deterministic loop, governance, scheduling | — |
| `tests/integration/pipeline/` | integration | Authoritative mutation pipeline (17-phase) | — |
| `tests/architecture/` | (no marker) | Static code structure: import boundaries, hot-path safety, hardcoded-gameplay guard, structural content path guard | — |
| `tests/arena/` | slow | Full simulation runs: startup, quests, tactics, regional control, stop conditions, stress | Must not be removed or weakened |
| `tests/certification/` | slow | Determinism parity, resilience, envelope violations, harness contract, rollout gates | Must not be removed or weakened |
| `tests/integrity/` | (no marker) | Doc guards, logic guards, manifest guards, parity ledger guards | — |
| `tests/docs/` | (no marker) | Contributor guardrails, doc integrity | — |
| `tests/api/` | (no marker) | REST API parity, WS protocol, observability endpoints, behavior query API | — |
| `tests/perf/` | slow | Performance budgets per phase (combat, idle, strategic, etc.), overhead validation | Must not be removed or weakened |
| `tests/static/` | (no marker) | Static code property checks (no direct dirtyset candidate selection) | — |
| `tests/refactor/` | (no marker) | Import compatibility, public facades | — |
| `tests/cli/` | (no marker) | CLI entry points, observability CLI, world CLI | — |
| `tests/engine/` | (no marker) | Hard law monitor, trace gating | — |
| `tests/observability/` | (no marker) | Event timeline, metrics export, websocket stream events | — |

---

## Phase 29–34 New Test Files — Suite Assignments

| New test file (Phase 29–34) | Assigned suite | Reason |
|---|---|---|
| `tests/unit/content/test_migration_map_schema.py` | `tests/unit/content/` | Schema validation for migration_map.yaml |
| `tests/integration/content/test_strict_world_matrix.py` | `tests/integration/content/` | Cumulative module load matrix (worldassembly marker) |
| `tests/integration/content/test_active_data_consumer.py` | `tests/integration/content/` | Consumer gate requires full catalog + reference graph |
| `tests/unit/scenarios/test_scenario_setup_resolver.py` | `tests/unit/scenarios/` | ScenarioSetupResolver unit tests |
| `tests/unit/scenarios/test_modifier_applicator.py` | `tests/unit/scenarios/` | ModifierApplicator + ScenarioSetupContext |
| `tests/unit/runtime/test_registry_bootstrap_modes.py` | `tests/unit/runtime/` | Registry bootstrap mode routing |
| `tests/architecture/test_no_new_hardcoded_gameplay_truth.py` | `tests/architecture/` | Architecture guard: hardcoded gameplay ID detection |

---

## Duplicate Coverage Areas (Known)

| Behavior | Suites that overlap | Resolution |
|---|---|---|
| Basic catalog loads | `tests/unit/content/`, `tests/integration/worldassembly/test_real_content_world_modules.py` | Unit covers schema; integration covers real assembly. Not a problem — different scopes. |
| Basic assembly works | `tests/integration/worldassembly/`, `tests/integration/content/test_strict_world_matrix.py` | Matrix adds cumulative module rows. Do NOT duplicate basic assembly assertions in matrix. See v2_test_taxonomy.md. |
| Registry bootstrapping | `tests/unit/core/` and `tests/unit/runtime/` | `unit/core` covers registry dataclasses; `unit/runtime/bootstrap.py` covers mode routing. Distinct scopes. |
| Enemy definitions | `tests/unit/content/` (migration_map schema) and `tests/architecture/` (hardcoded guard) | Schema validates format; guard validates absence of new unlisted IDs. Complementary. |

---

## Preserved Regression Suites

The following suites must not have tests removed, weakened, or have assertions loosened:

- `tests/arena/` — full simulation regression; any removal requires P0 justification
- `tests/certification/` — determinism and envelope contracts; any change requires parity ledger update
- `tests/perf/` — per-phase budget tests; regression baseline must remain intact

---

## New Suite Creation Rules

Before creating a new test directory:

1. Check this map — the behavior may already have an owner.
2. If adding to an existing suite, verify the marker matches (see `pyproject.toml` markers).
3. If creating a new suite, add it to this doc and to `v2_test_taxonomy.md`.
4. Never add integration-scope tests to `tests/unit/`.
5. Architecture tests must be static (no runtime simulation, no catalog load via network).
