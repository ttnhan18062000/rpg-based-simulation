---
status: active
layer: testing
authority: P1
audience: developer
---

# Content Migration Test Ownership Map

**Status:** Active  
**Last updated:** 2026-06-09  
**Relates to:** docs/testing/test_taxonomy.md

This document maps every major test suite to the behavior it owns, identifies duplicate
coverage areas, and specifies where new content-migration tests belong.

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
| `tests/unit/domains/` | unit | All domain-subpackage suites with test coverage (18 of `src/domains/`'s 19 subpackages): `adventure`, `campaigns`, `chronicle`, `combat_engagement`, `commitment`, `cooperation`, `culture`, `emotion`, `faction`, `feature_packs`, `information`, `memory`, `motivation`, `optimization`, `perception`, `progression`, `time`, `world_emergence` — `demographics` has no test directory (separate, out-of-scope coverage question) | — |
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

## Content-Migration New Test Files — Suite Assignments

| New test file | Assigned suite | Reason |
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
| Basic assembly works | `tests/integration/worldassembly/`, `tests/integration/content/test_strict_world_matrix.py` | Matrix adds cumulative module rows. Do NOT duplicate basic assembly assertions in matrix. See test_taxonomy.md. |
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
3. If creating a new suite, add it to this doc and to `test_taxonomy.md`.
4. Never add integration-scope tests to `tests/unit/`.
5. Architecture tests must be static (no runtime simulation, no catalog load via network).
6. **Domain-subpackage tests always nest under `tests/unit/domains/<name>/` /
   `tests/integration/domains/<name>/`**, never as a flat `tests/unit/<name>/` sibling — "domain
   subpackage" means anything with a same-named counterpart under `src/domains/`. This wasn't a
   stated rule before 2026-08-19, which let 6 subpackages' tests (`campaigns`, `chronicle`,
   `culture`, `faction`, `feature_packs`, `optimization`) drift to flat placement; fixed by
   `TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING`. This project's test tree is organized
   type-first (`tests/<type>/<domain>/`), not domain-first — do not nest by domain at the top
   level (see that ticket's investigation.md for why a domain-first axis was considered and
   rejected for this repo specifically).
7. **New test directories must be added to the correct job's explicit path list in
   `.github/workflows/test.yml`** — this repo's CI has no glob/auto-discovery; an unreferenced
   directory silently never runs (real incident:
   `TCK-20260817-CI-COVERAGE-GAP-16-ORPHANED-TEST-DIRS`, 16 dirs / 439 tests never run in CI until
   a manual audit caught it). `tests/tools/test_ci_workflow_test_coverage.py` (added by
   `TCK-20260819-HOTFIX-CI-TEST-DIR-COVERAGE-CHECK`) catches an omission after the fact, but does
   not choose which job/lane a new directory belongs in — still do this step by hand.
