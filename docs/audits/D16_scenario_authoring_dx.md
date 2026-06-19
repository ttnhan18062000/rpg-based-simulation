---
status: active
layer: guidelines
authority: P1
audience: agent
tags: [audit, dx, scenario-authoring, content-authoring, developer-experience, world-modules]
---

# D16 — Scenario & Content Authoring DX

## Dimension Profile

| Axis | Value |
|---|---|
| **Group** | C — Developer Tooling |
| **State** | `done` |
| **Impact** | 3 / 5 |
| **Interest** | 4 / 5 |
| **Priority** | 7 |
| **Method** | review |
| **Audit date** | 2026-06-18 |

**What this dimension answers:** How many files must change to add a new module or content
type, and how quickly does the authoring loop give feedback?

**Related dimensions:** D10 (Test Coverage) — content registry drift (D10 F6) is the
highest-friction authoring trap found here; D17 (Documentation Currency) — the only
content-authoring doc (`modules_contract.md`) is a technical contract, not a guide.

---

## Review Method

Four authoring tasks are assessed. Each is scored on three dimensions to produce a DX Gap
score. Higher score = worse experience = higher priority to improve.

### DX Gap Scoring

3 dimensions, each 1–5. Maximum: 15.

| Dimension | 1 | 3 | 5 |
|---|---|---|---|
| **Discovery Friction** | Everything discoverable from a README or make help | Key rules only in contract docs | Requirements only found by reading source code or failing CI |
| **Path Length** | 1 file, copy-paste from existing example | 2–3 files, all schema documented | 4+ files, or requires updating registries/indexes |
| **Error Feedback Latency** | Immediate error on `make validate` with clear message | Error on test run (minutes) | Error only in CI; no helpful authoring-time message |

---

## Authoring Surface

### Three content types and their home directories

| Content Type | Directory | Schema | File count |
|---|---|---|---|
| World module | `data/content/world_modules/` | `WorldModuleSpec` (Pydantic) | 14 modules |
| World composition | `data/content/world_compositions/` | `WorldCompositionSpec` (Pydantic) | 5 compositions |
| Simulation scenario | `data/content/simulation_scenarios/` | `SimulationScenarioDefinition` (Pydantic) | 8 scenarios (1 file) |

### Available tooling (`make` targets)

| Target | What it does |
|---|---|
| `make world-validate WORLD=<id>` | Validate a world spec against compile constraints |
| `make world-template` | Generate a scaffold world module YAML |
| `make world-list` | List all loaded world modules |
| `make world-compile` | Compile world to AuthoritativeState |
| `make world-inspect` | Inspect assembled world structure |
| `make sim-sweep CONFIG=<path>` | Run a scenario sweep matrix |

---

## Task Assessments

### Task 1 — Add a new world module — DX Gap: 7 / 15

| Dimension | Score | Reason |
|---|---|---|
| Discovery Friction | 3 | `docs/world/modules_contract.md` covers the schema in detail — but it's a technical contract, not an author guide. Sharp edges (`observability_tags` not `tags`; no `provided_features`) require reading the contract carefully |
| Path Length | 2 | Minimum: 1 file (`data/content/world_modules/<new>.yaml`). Optionally add to a composition. Simple. |
| Error Feedback Latency | 2 | `make world-validate` catches schema errors immediately. Catalog ID errors (invalid biome/ecology refs) surface only at assembly — not at YAML parse time. |
| **Total** | **7** | |

**Minimum files to touch:** 1 (the module YAML itself).

**What must be correct in the YAML:**
- `module_id` — unique, not duplicated
- `module_type` — must be one of 7 registered types (`terrain`, `settlement`, `ecology`, `economy`, `conflict`, `population`, `danger_zone`)
- `display_name` — required, min_length=1
- `observability_tags` — correct field name; `tags` is rejected by `extra="forbid"`
- No `provided_features` field — belongs to `WorldCompositionSpec` only
- Catalog refs (`biomes`, `ecologies`, `populations`, `relationships`, `factions`) — must match registered catalog IDs; no pre-flight check exists

**Key sharp edge:** Pydantic's `extra="forbid"` produces helpful errors for unknown keys
but doesn't tell you what valid catalog IDs are. If a biome ID is wrong, the error surfaces
only when the assembly pipeline runs `CatalogRepository.resolve()`.

---

### Task 2 — Add a new simulation scenario — DX Gap: 6 / 15

| Dimension | Score | Reason |
|---|---|---|
| Discovery Friction | 3 | Scenario schema is small (6 fields). The 8 allowed `initial_condition` categories are documented only in `src/scenarios/schema.py:ALLOWED_INITIAL_CONDITION_CATEGORIES` — not in any guide. |
| Path Length | 1 | Add one entry to an existing scenarios YAML file. |
| Error Feedback Latency | 2 | Pydantic validates `initial_conditions` keys at load time with a clear error listing allowed categories. Template validation (`template_id`) also fires at load. |
| **Total** | **6** | |

**Minimum files to touch:** 1 (append entry to `data/content/simulation_scenarios/<file>.yaml`).

**Schema fields:**
```yaml
id: "my_scenario"
world_composition: "frontier_living_world"   # must match an existing composition ID
perspective: "hero_guild_perspective"         # string — no catalog validation
focus_modules: ["goblin_camp_conflict"]       # must match loaded module IDs
initial_conditions:                           # keys must be in allowed set
  region_pressure: "medium"
template_id: "raider_conflict"               # optional — triggers template validation
```

**Allowed `initial_conditions` keys** (documented only in schema.py):
`region_pressure`, `faction_activity`, `resource_scarcity`, `population_alertness`,
`territorial_intrusion`, `trade_route_risk`, `danger_level_override`, `spawn_bias`

**Best-in-class DX task** — small schema, immediate validation, copy-paste friendly.

---

### Task 3 — Add a new content pack (new directory/family) — DX Gap: 12 / 15

| Dimension | Score | Reason |
|---|---|---|
| Discovery Friction | 5 | `ContentUsageMatrix` update requirement is documented nowhere for authors — discovered only when `test_matrix_covers_all_content_files` fails in CI |
| Path Length | 3 | Pack YAML + register in `ContentUsageMatrix` + optionally update composition |
| Error Feedback Latency | 4 | No authoring-time error; silent during `make world-validate`; only surfaces in CI test run as `ValueError: Ignored active YAML files found in repository` |
| **Total** | **12** | |

**What happened in practice (D10 F6):** Three new YAML files were added to `data/content/`
without registering them in `ContentUsageMatrix`:
- `packs/swamp_border_pack.yaml`
- `packs/frontier_extended_pack.yaml`
- `compatibility/migration_map.yaml`

`src/content/repository.py:353` raises `ValueError` on strict load.
`test_matrix_covers_all_content_files` fails. But `make world-validate` does not mention this.
An author who runs only the world validator will believe their content is valid.

**Root cause:** `ContentUsageMatrix` is a manual registry — authors must know to update it,
but nothing at authoring time prompts them to do so.

**Fix options:**
- Auto-generate `ContentUsageMatrix` from directory scan (preferred)
- Add a `make content-check` target that runs the matrix test
- Add a warning to `make world-validate` output when unregistered families are detected

---

### Task 4 — Scaffold a new world module from template — DX Gap: 4 / 15

| Dimension | Score | Reason |
|---|---|---|
| Discovery Friction | 2 | `make world-template` exists; not mentioned in any docs but visible in `make help` output |
| Path Length | 1 | Runs a CLI that generates a valid scaffold YAML |
| Error Feedback Latency | 1 | Scaffold output is valid by construction |
| **Total** | **4** | |

`make world-template` is the best authoring entry point — it produces a structurally valid
YAML scaffold. The main gap is discoverability: no authoring guide points to it.

---

### DX Gap Summary

| Task | Description | DX Gap Score |
|---|---|---|
| Task 3 | Add new content pack / family | **12 / 15** |
| Task 1 | Add new world module | **7 / 15** |
| Task 2 | Add new simulation scenario | **6 / 15** |
| Task 4 | Scaffold from template (make world-template) | **4 / 15** |

---

## Structural Gaps

| Gap | Description |
|---|---|
| No content author guide | No single-page "how to add a module/scenario" document exists. `modules_contract.md` is a technical contract, not a walkthrough. |
| No catalog ID browser | No way to list valid biome/ecology/population/faction IDs without running assembly code. |
| ContentUsageMatrix is manual | New content families must be manually registered; no validation at authoring time. |
| Allowed initial_conditions undocumented | The 8 allowed keys are only in `src/scenarios/schema.py`. |
| Scenario templates undiscovered | 10 scenario templates exist in `src/scenarios/templates.py` with useful structural constraints; no docs link to them. |

---

## Positive Findings

| Area | Assessment |
|---|---|
| `make world-validate` | Immediate schema + Pydantic validation with clear error messages |
| `make world-template` | Scaffold generator produces valid YAML by construction |
| Pydantic `extra="forbid"` | Unknown fields produce clear, actionable errors |
| Scenario schema | Small (6 fields), `initial_conditions` validation fires at load time |
| 10 scenario templates | Rich structural constraints for common simulation setups |
| Module type validation | 7 registered types; adding a new type requires one `register_module_type()` call |

---

## Recommended Follow-Up Tickets

| Priority | Action |
|---|---|
| **P1** | Auto-detect unregistered content families in `make world-validate` output (or auto-update `ContentUsageMatrix`) |
| **P1** | Write a content author guide (`docs/content/authoring_guide.md`): steps to add a module, composition, scenario; list of allowed module types, initial_condition categories, and make targets |
| P2 | Add `make catalog-list` or `make content-browse` to list available catalog IDs by type (biomes, ecologies, populations, factions) |
| P2 | Add `make scenario-new ID=<id> TEMPLATE=<template_id>` scaffold command for simulation scenarios |
| P2 | Document the 10 scenario templates in the authoring guide with example YAMLs |

---

## Related Dimensions

- **D10 (Test Coverage)** — Task 3 DX gap (ContentUsageMatrix drift, 12/15) manifested as D10 F6: 3 new pack files caused 3 test failures and a `ValueError` on strict load.
- **D17 (Documentation Currency)** — `modules_contract.md` is current and accurate as a technical reference, but is not structured for content authors. No new authoring guide is needed in D17's scope — it is a D16 gap.
- **D07 (Content Depth)** — the scenario and world module count established here (14 modules, 5 compositions, 8 scenarios) feeds into D07's content depth assessment.
