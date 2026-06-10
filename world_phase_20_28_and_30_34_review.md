Static review only. I reviewed the uploaded full `src_export_34.py` and `test_export_34.py`; I did **not** run pytest.

# Overall verdict

| Review target                   |   Score / 10 | Verdict                                                                                                               |
| ------------------------------- | -----------: | --------------------------------------------------------------------------------------------------------------------- |
| Phase 20–28 repair plan         | **8.1 / 10** | Mostly repaired, but still has one important Option A drift and one full-pipeline blocker.                            |
| Phase 29–34 implementation plan | **6.6 / 10** | Good scaffolding exists, but several “happy path” integrations are still xfail or advisory rather than fully passing. |

Main conclusion:

```text
The code is now much stronger structurally.
But the project is still not fully runtime-authoritative because CAT-REL-099 blocks full assembly paths, and some validation gates still depend on YAML STATE comments.
```

---

# Part 1 — Phase 20–28 repair verification

## Phase 20–28 checking table

| Area                                | Expected from repair plan                                                                            | Current implementation                                                                                                                                                                                                                                            | Status          |   Score |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- | ------: |
| Option A: YAML comments human-only  | Engine/validators should not depend on `# STATE:` comments.                                          | Problem: `test_active_data_consumer.py` scans YAML `STATE` markers and enforces per-record consumer paths. That directly contradicts the strict Option A repair direction, even if it is “only test logic.”                                                       | Drift           | **5.5** |
| Runtime content modes               | Must have explicit `CATALOG_STRICT`, `CATALOG_WITH_COMPATIBILITY`, `LEGACY_FALLBACK`, `TEST_MANUAL`. | Implemented. `RuntimeContentMode` has four modes and tests assert `MIGRATION` / `V2` are removed.                                                                                                                                                                 | Good            | **9.0** |
| Adapter heuristic reporting         | Must report heuristic details, not just count.                                                       | Implemented `AdapterHeuristicUsage` with `record_id`, `family`, `adapter`, `heuristic_type`, `reason`, and mode. `AdapterProjectionResult` now stores `heuristic_usages`.                                                                                         | Good            | **8.5** |
| Normalized module boundary          | `resolve_module_contribution()` should consume normalized modules only.                              | Implemented and tested. Raw `WorldModuleSpec` is rejected in tests.                                                                                                                                                                                               | Good            | **8.5** |
| Normalized v2 refs                  | Normalized fields should use explicit `*_refs`.                                                      | Implemented: `biome_refs`, `ecology_refs`, `population_refs`, `relationship_refs`; count maps remain for resources/buildings/services.                                                                                                                            | Good            | **8.5** |
| Real `data/content` module path     | Default executable path should be `data/content/world_modules`.                                      | Stronger now. `WorldModuleRepository()` is used in strict matrix/scenario tests, and previous old path drift is mostly guarded.                                                                                                                                   | Good            | **8.0** |
| Strict matrix / full pipeline proof | Real content should flow through load → normalize → assemble → compile → registry.                   | Partial. Pre-assembly tests pass, but full assembly tests are `xfail` due to CAT-REL-099. This means the full proof is still not clean.                                                                                                                           | Partial/blocker | **5.0** |
| Registry bootstrap modes            | Strict mode should reject hardcoded fallback; legacy mode explicit; manual mode no catalog required. | Implemented via `src/runtime/bootstrap.py`; tests cover strict no-catalog failure, legacy fallback, test manual, and compatibility projection.                                                                                                                    | Good            | **8.5** |
| Hardcoded gameplay guard            | New hardcoded gameplay IDs should require migration-map coverage.                                    | Implemented architecture guard and migration map. Good direction, though baseline allowlist remains a long-term cleanup area.                                                                                                                                     | Good            | **8.0** |
| Reward classification repair        | Combat reward classification should be centralized and traceable.                                    | Improved. `classify_defeated_target()` exists and reward trace tests cover `REWARD_CATEGORY` / `REWARD_SOURCE`. However, the clean relation path is still shallow: hostile creature is inferred from `MONSTER_HORDE`, not full perspective relation projection.   | Partial-good    | **7.2** |
| Content pack manifest               | Content pack schema should enforce consumers and dependencies.                                       | Implemented `ContentPackManifest` and validator; tests cover schema, consumers, unknown fields, immutability, dependency checks.                                                                                                                                  | Good            | **8.0** |

## Phase 20–28 repair verdict

```text
Phase 20–28 repair is mostly successful, but not fully clean.
```

The two remaining issues are important:

1. **Option A drift:** `test_active_data_consumer.py` validates per-record maturity from YAML `STATE` comments. That contradicts the repair decision unless you intentionally reclassify this as a developer-only advisory gate, not implementation validation. 

2. **Full assembly blocker:** strict matrix full-assembly tests are still xfailed because CAT-REL-099 blocks assembly globally. That means the pipeline is not fully proven end-to-end yet. 

Recommended score:

```text
Phase 20–28 repair: 8.1 / 10
```

---

# Part 2 — Phase 29–34 implementation verification

## Phase 29 — EntityState construction bridge

| Requirement                                     | Current implementation                                                                                                                         | Status  | Score |
| ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ------- | ----: |
| `ResolvedEntityRuntimeContract` exists          | Implemented with clean identity, legacy projection, combat values, inventory, traits/themes, profile source IDs.                               | Good    |     9 |
| `EntitySpawnContext` exists                     | Implemented in `archetype_factory.py`.                                                                                                         | Good    |     9 |
| `ArchetypeEntityFactory` builds `EntityState`   | Implemented and tested with human/wolf/goblin cases.                                                                                           | Good    |   8.5 |
| Resolved archetype → contract bridge            | Implemented via `resolved_archetype_to_contract()`, preserving stats, inventory, traits, themes, and profile IDs.                              | Good    |   8.5 |
| Legacy construction still works                 | Integration tests keep `V2EntityBuilder` path working.                                                                                         | Good    |     8 |
| Integrated into default runtime entity creation | Not fully. The archetype-native path exists and is tested, but it is not yet clearly the default runtime construction path for world assembly. | Partial |     6 |

**Phase 29 score: 8.0 / 10**

Good implementation. The only gap is that this is still a bridge path, not yet clearly the default entity creation path everywhere.

---

## Phase 30 — Scenario setup resolver

| Requirement                           | Current implementation                                                                                                                           | Status       | Score |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ------------ | ----: |
| `SimulationScenarioDefinition` schema | Implemented, fail-closed, allowed initial condition categories defined.                                                                          | Good         |   8.5 |
| `ScenarioSetupResolver`               | Implemented. It loads composition, validates perspective, assembles world bundle, builds modifiers.                                              | Partial-good |     7 |
| `ResolvedScenarioSetup`               | Implemented.                                                                                                                                     | Good         |     8 |
| `StateSetupModifier`                  | Implemented.                                                                                                                                     | Good         |     8 |
| Modifier application                  | `ModifierApplicator` exists and maps region pressure, faction activity, scarcity, alertness, intrusion, trade risk, danger override, spawn bias. | Good         |     8 |
| Happy-path integration                | Blocked by xfail due CAT-REL-099. Scenario happy-path tests are xfailed.                                                                         | Blocked      |     4 |

**Phase 30 score: 6.7 / 10**

The schema and modifier layer are good, but the actual full resolver path is not fully proven because the happy path is xfailed.

---

## Phase 31 — End-to-end strict compile matrix

| Requirement                                     | Current implementation                                                                                                | Status       | Score |
| ----------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- | ------------ | ----: |
| Matrix of cumulative world modules              | Implemented with frontier, wolf den, goblin camp, old mine, bandit road, undead, moon cult, orc clan, forest warden.  | Good         |     8 |
| Pre-assembly checks                             | Module load, normalize, fingerprint checks exist and pass by design.                                                  | Good         |     8 |
| Runtime registry seeding                        | Covered in strict matrix via `seed_phase1_content`.                                                                   | Good         |   7.5 |
| Full WorldSpec + CompileContext proof           | Full assembly tests are xfailed due CAT-REL-099.                                                                      | Not complete |     3 |
| Deterministic assembly fingerprint              | Test exists but xfailed due same issue.                                                                               | Blocked      |     3 |
| No hidden legacy fallback in archetype entities | Test exists but xfailed due same issue.                                                                               | Blocked      |     3 |

**Phase 31 score: 5.2 / 10**

This phase is structurally present but not complete. The xfail is honest, but it means the phase objective is not achieved yet.

---

## Phase 32 — Legacy hardcoded truth deprecation

| Requirement                  | Current implementation                                                                                                                 | Status  | Score |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ------- | ----: |
| Runtime source modes         | Implemented four explicit modes.                                                                                                       | Good    |     9 |
| Bootstrap report             | `ContentSourceReport` exists with catalog/compat/fallback counts and fallback flag.                                                    | Good    |     8 |
| Migration map                | Implemented at `data/content/compatibility/migration_map.yaml`, with resources, recipes, regions, enemies, roles, factions, services.  | Good    |     8 |
| Hardcoded gameplay guard     | Implemented architecture guard.                                                                                                        | Good    |     8 |
| Fallback isolation           | `CATALOG_STRICT` and compatibility mode disallow missing-catalog hardcoded fallback; `LEGACY_FALLBACK` explicitly allows it.           | Good    |   8.5 |
| Full fallback shrink/removal | Not expected yet; baseline allowlist still exists.                                                                                     | Partial |     6 |

**Phase 32 score: 8.0 / 10**

This is one of the stronger phases.

---

## Phase 33 — Regression alignment with current tests

| Requirement                   | Current implementation                                                                            | Status  | Score |
| ----------------------------- | ------------------------------------------------------------------------------------------------- | ------- | ----: |
| Preserve old tests            | Many legacy/arena/API tests remain untouched.                                                     | Good    |     8 |
| New test ownership tags       | Tests have markers like `scenario_setup`, `strict_matrix`, `content_pack`, `registry_projection`. | Good    |   7.5 |
| Avoid duplicate broad tests   | Mostly respected; strict matrix states it avoids duplicating basic assembler tests.               | Good    |   7.5 |
| Explicit test ownership map   | I do not see a formal test ownership map document/table.                                          | Missing |     4 |
| No-duplication policy encoded | Partially encoded in docstrings, not strongly enforced.                                           | Partial |     5 |

**Phase 33 score: 6.5 / 10**

The spirit is there, but the formal ownership map / no-duplication policy is still weak.

---

## Phase 34 — Horizontal content expansion gate

| Requirement                          | Current implementation                                                     | Status  | Score |
| ------------------------------------ | -------------------------------------------------------------------------- | ------- | ----: |
| Expansion readiness gate             | Implemented `test_expansion_gate.py` with 12 gate items.                   | Good    |   7.5 |
| Content pack manifest                | Implemented schema + tests.                                                | Good    |     8 |
| First pack: `frontier_extended_pack` | Present in `data/content/packs/frontier_extended_pack.yaml`.               | Good    |     7 |
| Active data consumer gate            | Exists, but uses comment `STATE` scanning, which conflicts with Option A.  | Risky   |     4 |
| Full expansion gate passes           | Some items are xfailed due CAT-REL-099.                                    | Partial |     5 |
| Pack can be enabled/disabled         | Manifest has `enabled`; tests validate disabled is valid.                  | Good    |     7 |

**Phase 34 score: 6.2 / 10**

The gate exists, but it depends on comment-state scanning and has known xfails. That makes it more of a readiness dashboard than a completed expansion gate.

---

# Phase 29–34 summary table

| Phase                                      | Score / 10 | Verdict                                                           |
| ------------------------------------------ | ---------: | ----------------------------------------------------------------- |
| Phase 29 — EntityState construction bridge |    **8.0** | Strong bridge implementation; not fully default runtime path yet. |
| Phase 30 — Scenario setup resolver         |    **6.7** | Schema/modifiers are good; full resolver happy path xfailed.      |
| Phase 31 — Strict compile matrix           |    **5.2** | Matrix exists, but full assembly proof is xfailed.                |
| Phase 32 — Legacy fallback deprecation     |    **8.0** | Strong mode/guard/migration-map work.                             |
| Phase 33 — Regression alignment            |    **6.5** | Good markers/docstrings, missing formal ownership map.            |
| Phase 34 — Content expansion gate          |    **6.2** | Gate exists, but comment-state scanning + xfails weaken it.       |

Average:

```text
Phase 29–34 implementation: 6.6 / 10
```

---

# Most important blockers

## 1. CAT-REL-099 blocks too much

This is now the largest blocker. It causes xfails in:

```text
- ScenarioSetupResolver happy path
- strict world matrix full assembly
- expansion readiness world assembly gate
```

The tests honestly mark this, which is good. But as long as this remains unresolved, Phase 30, 31, and 34 cannot be called complete.  

## 2. Comment-state scanning violates Option A

`test_active_data_consumer.py` says it scans YAML `STATE` markers and validates active records based on `EXISTING-LOGIC`, `LEGACY-EXPORT`, and `REDESIGNED-CORE`. 

That contradicts the selected Option A:

```text
YAML comments are human planning notes only.
Do not validate per-record maturity from comments.
```

Fix options:

```text
Option 1: Convert this test into advisory/report-only.
Option 2: Replace it with family-level ContentUsageMatrix validation.
Option 3: Keep it, but explicitly document that this is developer QA lint, not engine/implementation validation.
```

My recommendation: **Option 2** for Phase 20–28 repair compliance.

## 3. Scenario setup is not yet truly executable

`ScenarioSetupResolver` exists, but the real success path is xfailed. Its modifier conversion tests pass, but that only proves partial behavior. 

## 4. Strict matrix is still not a strict matrix

The test name says strict matrix, but full assembly rows are xfailed. This is useful as scaffolding, but not yet a real gate. 

---

# Recommended next repair order

| Priority | Fix                                                             | Reason                                 |
| -------: | --------------------------------------------------------------- | -------------------------------------- |
|        1 | Fix CAT-REL-099                                                 | Unblocks Phase 30, Phase 31, Phase 34. |
|        2 | Replace comment-state active-data gate                          | Restores Option A compliance.          |
|        3 | Turn strict matrix xfails into passing tests                    | Makes Phase 31 real.                   |
|        4 | Turn ScenarioSetupResolver happy path xfails into passing tests | Makes Phase 30 real.                   |
|        5 | Add formal test ownership map                                   | Finishes Phase 33.                     |
|        6 | Upgrade expansion gate from dashboard to hard gate              | Finishes Phase 34.                     |

---

# Final assessment

| Target             | Status                                       |
| ------------------ | -------------------------------------------- |
| Phase 20–28 repair | **Mostly done, but Option A drift remains.** |
| Phase 29           | **Good.**                                    |
| Phase 30           | **Partially blocked.**                       |
| Phase 31           | **Scaffolded, not complete.**                |
| Phase 32           | **Good.**                                    |
| Phase 33           | **Partially done.**                          |
| Phase 34           | **Partially done.**                          |

Final scores:

```text
Phase 20–28 repair: 8.1 / 10
Phase 29–34 implementation: 6.6 / 10
```

The codebase is moving in the right direction. The biggest thing now is not adding more systems; it is fixing the known catalog issue and removing validation dependence on YAML comment states.
