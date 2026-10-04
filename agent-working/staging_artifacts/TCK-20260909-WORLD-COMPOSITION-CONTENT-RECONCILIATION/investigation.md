---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION
artifact_type: investigation
tags: [architecture, content]
---

# Investigation — TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION

## Context-search provenance (Step 0c)

`mcp__knowledge-search__search_docs` was called first, per CLAUDE.md's hard rule. It returned
`{"error":"index not found","action":"run make knowledge-index"}` — known-unavailable local
worktree state, not a skipped step. `graphify query` failed with `graph file not found:
graphify-out/graph.json` and `graphify-out/` does not exist in this worktree. The sanctioned
fallback was used instead and its results are reflected in **Prior Work**:

```
.venv-knowledge/bin/python3 tools/knowledge_search.py query \
  "world composition content reconciliation data/worlds authoritative" --top-k 6
```

It surfaced `docs/architecture/world_repository_layout.md` §"Proposed Strategy & Layout",
`TCK-20260614-WORLDDAT-COMPOSE`, `TCK-20260614-WORLDGEN-E2E-SMOKE`, `TCK-20260523-WORLD-COMPILER`,
`TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS` and `TCK-20260605-PHASE27-WORLD-MODULE-COMPOSITION`. Only
then were grep and file reads used, to verify specific paths.

Everything below was measured in the working tree at the branch head, not inferred from the
ticket's prose. Where a measurement contradicts the ticket, it is called out.

---

## Current Behavior

### The two definitions and the three artifacts

| layer | path | schema | who reads it |
|---|---|---|---|
| catalog copy | `data/content/world_compositions/<id>.yaml` (+ `generated/`) | `worldcomposition.v1` | `ScenarioSetupResolver` default, tests, `src/content/validator.py` |
| authoritative source | `data/worlds/<id>/world.yaml` | `worldcomposition.v1` | `WorldRepository`, `CampaignOrchestrator` (explicit override) |
| compiled snapshot | `data/worlds/<id>/resolved/world.resolved.yaml` | `worldspec.v1` | **what production actually compiles** |

**`WorldRepository.load_world()` never compiles `world.yaml` for a composition world.**
`src/worldbuilding/repository.py:74-81`: if `"worldcomposition" in raw_dict["schema_version"]`, it
redirects to `yaml_path.parent / "resolved" / "world.resolved.yaml"` and raises
`WorldRepositoryError` if that file is absent. `load_world_with_context()`
(`src/worldbuilding/repository.py:89-147`) does the same and additionally loads
`resolved/compile_context.json`. So the production path has **two** inputs under
`data/worlds/<id>/`, and `world.yaml` is authoritative only transitively — via `resolved/`.
This is the ADR's own §2 "Discovered Artifact Output Separation". Measured: all 9 catalog-paired
worlds have a `resolved/world.resolved.yaml` present, and `data/worlds/dungeon_crawl/resolved/
world.resolved.yaml` contains all four of `ruins_mystery_quest`, `goblin_camp_conflict`,
`old_mine_resource_loop`, `scalable_bandit_camp` — i.e. the snapshot is derived from the 4-module
`world.yaml`, confirming "running == `data/worlds/`".

### Inventory, re-verified

`data/content/world_compositions/` holds exactly 7 top-level + 2 `generated/` files
(`dungeon_crawl`, `frontier_extended`, `frontier_living_world`, `highland_traverse`,
`swamp_border_world`, `urban_political`, `wilderness_survival`, `generated/generated_frontier_3_42`,
`generated/simq_scale_stress_seed42`) — unchanged from the 2026-09-12 inventory.

`data/worlds/` holds **24** world directories; **all 24** `world.yaml` files are
`schema_version: worldcomposition.v1` and **all 24 validate cleanly against
`WorldCompositionSpec`** (measured, zero failures). 24 − 9 = **15 running-only ids**, matching the
ticket's corrected figure. Zero catalog-only ids.

### Superset direction, re-measured independently

Top-level-key direction (catalog → running), per pair:

| pair | catalog form | running form | keys only on the running side |
|---|---|---|---|
| `frontier_living_world` | `modules` (6) | `module_refs` (7) | `module_refs`, `faction_tension_overrides`, `information_source_profiles`, `pending_information_responses` |
| `wilderness_survival` | `module_refs` (4) | `module_refs` (4) | `faction_tension_overrides` |
| `urban_political` | `module_refs` (3) | `module_refs` (4) | `faction_tension_overrides`, `information_source_profiles`, `pending_information_responses`, `pending_self_model_information_events` |
| `dungeon_crawl` | `module_refs` (2) | `module_refs` (4) | `faction_tension_overrides` |
| `swamp_border_world` | `modules` (3) | `module_refs` (4) | `module_refs`, `faction_tension_overrides`, `information_source_profiles`, `pending_information_responses` |
| `frontier_extended` | `modules` (8) | `module_refs` (9) | `module_refs`, `faction_tension_overrides`, `information_source_profiles`, `pending_information_responses` |
| `highland_traverse` | `modules` (4) | `modules` (4) | `faction_tension_overrides`, `information_source_profiles`, `pending_information_responses` |
| `generated_frontier_3_42` | `module_refs` (6) | `module_refs` (6) | `faction_tension_overrides`, `information_source_profiles`, `pending_information_responses` |
| `simq_scale_stress_seed42` | `module_refs` (12) | `module_refs` (12) | none (byte-identical pair) |

**Zero catalog-only keys in any pair.** The ticket's 2026-10-04 re-measurement reproduces. Note
the *form* difference matters for the test repoint (see **Risks**): four pairs flip from the
shorthand `modules:` list on the catalog side to `module_refs:` on the running side.

### The one value conflict, and what it actually is

`dungeon_crawl`'s `scalable_bandit_camp.parameters.danger_scale`: catalog `2`, running `4`. Both
definitions were assembled *and compiled* here:

| definition | modules | regions | entities | quests |
|---|---|---|---|---|
| `data/content/world_compositions/dungeon_crawl.yaml` | 2 | 2 | **12** | 5 |
| `data/worlds/dungeon_crawl/world.yaml` | 4 | 4 | **32** | 9 |

**This is not a dead value.** `agent-working/tickets/done/TCK-20260627-P1I-WORLD-BALANCE-FIX.md`
(DONE, P1) exists precisely to produce the `2`: D08 measured `dungeon_crawl` at 94–97% attrition by
tick 100, and that ticket's recorded remedy (`:73-76`, `:93`, `:101-103`) was to remove
`goblin_camp_conflict` and `old_mine_resource_loop` ("both had unmet `requires:
frontier_village_core` dependency in dungeon_crawl") and reduce `danger_scale` 4→2, taking the
entity count from 32 to 12. It edited **only** `data/content/world_compositions/dungeon_crawl.yaml`
(its own Files Changed list, `:59`/`:93`). See **Risks and Open Questions** #1 — this is the one
genuinely blocking item this investigation found.

### `ScenarioSetupResolver`

`src/scenarios/resolver.py:34` — `_DEFAULT_COMPOSITIONS_DIR = Path("data/content/world_compositions")`.
`_load_composition()` (`:58-95`) already tries `<dir>/<world_id>/world.yaml` first, then
`<dir>/<world_id>.yaml`, so pointing the default at `data/worlds` needs no loader change.
`_validate_perspective()` (`:97-108`) checks the scenario perspective against
`composition.default_perspectives` — measured: `default_perspectives` is **identical on both sides
for all 9 pairs**, so the redirect cannot break perspective validation.

Verified: **all 9** `data/worlds/<id>/world.yaml` specs assemble successfully through
`WorldAssemblyResolver.assemble()` (regions 8/4/3/4/5/11/5/6/13). The redirect is mechanically safe;
only asserted *values* shift.

### Callers / writers / other consumers of the retired directory

- `src/domains/campaigns/orchestrator.py:173-200` — the explicit `compositions_dir=Path("data/worlds")`
  override to revert; stale ticket citation at `:186` (`TCK-20260909-WORLD-COMPOSITION-DIRECTORY-CONSOLIDATION`,
  this ticket's pre-retitle name, file no longer exists — Gap 3); the "anomaly" interpretation
  originates at `:178`.
- `src/worldgeneration/generator.py:383` (docstring output contract), `:536-540`
  (`Path("data/content/world_compositions/generated").mkdir(parents=True, exist_ok=True)` then
  writes `{world_id}.yaml`) — the **writer**, Gap 1.
- `src/content/paths.py:8` — `ContentPathConfig.world_compositions_dir`.
- `src/content/validator.py:38` (`load_all_compositions(worlds_dir=ContentPathConfig().world_compositions_dir)`),
  `:153` (its caller).
- `src/content/repository.py:150` — `NON_CATALOG_DIRS` excludes the dir from catalog strict-mode load.
- `src/content/matrix.py:550-551` — a `ContentFamilyMatrixEntry` keyed `world_compositions` with
  `file_path="world_compositions"`; `:638` the structural-dirs set. `src/content/reference_graph.py:42`
  maps `world_compositions` → `composition`.
- `src/worldbuilding/cli.py:160`, `src/worldbuilding/repository.py:265` — error strings only
  (family label `'world_compositions'`), no path dependency.
- `tools/generate_content_inventory.py:91-94` — globs the directory for two inventory counters.

### Measurement 5 — does any frontend/API read model surface it? **No.**

`grep` over `src/api/` and every frontend tree returns exactly one hit:
`src/api/routes/scenarios.py:94`, `world_composition="default"` — a placeholder *field value* on a
synthesized `SimulationScenarioDefinition` in the checkpoint-restore path. No API route, presenter
or schema reads `data/content/world_compositions/`, and no read model exposes the directory or a
composition path. The ticket's unmeasured risk is closed: **zero API/frontend surface**.

### Measurement 1 — the nine test files, classified

Genuine dependency = loads/globs the directory or asserts on its contents (would break or go
vacuous on deletion). Mention = the string appears as a family/structural name or a different
field.

| file | classification | evidence |
|---|---|---|
`tests/integration/worldassembly/test_real_content_world_compositions.py` | **GENUINE — 7 hard-coded loads** | `:30`, `:44`, `:62`, `:86` (`frontier_living_world`), `:345` (`wilderness_survival`), `:385` (`urban_political`), `:436` (`dungeon_crawl`); `:452` asserts `danger_scale == 2` |
`tests/integration/worldassembly/test_e2e_smoke.py` | **GENUINE — 2 loader helpers** | `:56` `_compile_composition`, `:76` `_compile_generated_composition`, both `assert comp_path.is_file()`; used by 4 tests (`wilderness_survival`, `urban_political` ×2, `dungeon_crawl`, `generated_frontier_3_42`) |
`tests/integration/content/test_expansion_gate.py` | **GENUINE — globs the dir** | `:184` Gate 08 iterates `compositions_dir.glob("*.yaml")`; `:248` Gate 11 takes `sorted(...glob("*.yaml"))[0]` and would raise `IndexError` on an empty dir |
`tests/unit/worldassembly/test_assembly.py` | **GENUINE — 2 loads, with `assert comp_path.is_file()`** | `:1058`, `:1079` both load `frontier_living_world.yaml`; `:1185`/`:1190` are error-string mentions only |
`tests/unit/content/test_content_paths.py` | **GENUINE — pins the constant** | `:12` `assert config.world_compositions_dir == "data/content/world_compositions"`; `:169` reuses the basename in an exclusion guard |
`tests/tools/test_content_inventory.py` | **GENUINE but vacuous-on-delete** | `:46`/`:48` assert the tool's counts equal `glob(...)` lengths; after deletion both sides are 0 and it passes while measuring nothing |
`tests/integration/content/test_swamp_border_pack.py` | **GENUINE — existence assertion** | `:93` `assert os.path.exists(f"data/content/world_compositions/{cid}.yaml")` for each `manifest.sample_compositions` |
`tests/unit/content/test_content_usage_matrix.py` | **MENTION** | `:87`, `:97`, `:397` — `"world_compositions"` as a member of a structural-folder *name* set; no path load |
`tests/integration/scenarios/test_content_foundation.py` | **MENTION — different thing entirely** | `:27-61` reads the `world_composition` *field* on scenario YAMLs under `data/content/simulation_scenarios/`; never touches the directory |

**Result: 7 of 9 genuinely depend on it, 2 are mentions.** One of the 7
(`test_content_inventory.py`) degrades silently rather than failing, which is the worst case for
a cleanup ticket. Plus the two default-riding tests the ticket already names
(`test_scenario_catalog_matrix.py` fixture at `:49`, `test_scenario_setup_resolver.py` fixture at
`:37`) which reference no path at all — bringing the real surface to **9 files** by a different
count than the ticket's nine.

### Measurement 2 — does repointing work mechanically? **Yes for the path; no for four assertions.**

The authoritative layout being a directory is **not** an obstacle: `data/worlds/<id>/world.yaml`
carries the same `schema_version: worldcomposition.v1` and validates against the same
`WorldCompositionSpec`, and the named-world tests load by `yaml.safe_load(path)` +
`WorldCompositionSpec.model_validate(raw)` with no repository involved. `Path("data/content/
world_compositions/<id>.yaml")` → `Path("data/worlds/<id>/world.yaml")` is a literal one-line swap
at each of the 7 sites, and all 9 specs were confirmed to assemble.

What does **not** survive the swap (measured deltas the implementer must resolve):

| site | assertion today | after repoint |
|---|---|---|
`:52` | `len(normalized.module_refs) == 6` | 7 |
`:54-56` | `for ref ...: assert ref.order == 0` | **fails** — the running file sets explicit `order: 0..6`. The whole test (`test_real_world_compositions_normalization`) exists to prove *shorthand `modules:` → `module_refs` conversion*, and the running `frontier_living_world` has no shorthand at all. Its premise disappears; it needs a changed premise or a synthetic shorthand fixture, not a path swap. |
`:112` | `len(provenance_manifest.module_fingerprints) == 6` | 7 |
`:437`-`:452` | `len(spec.module_refs) == 2`; `danger_scale == 2`; docstring citing the balance fix | 4; `4`; docstring is now wrong |
`:333` (`wilderness_survival`) | `len(spec.module_refs) == 4` | 4 — unchanged, clean swap |
`:374` (`urban_political`) | `len(spec.module_refs) == 3` | **4** |
`:28`, `:59`, `:83` | `world_id`/`name`/`>0 regions`/`len(default_perspectives) == 3` | all hold |

`test_e2e_smoke.py`'s 4 tests will also see different compiled counts
(`dungeon_crawl` 12→32 entities, 2→4 regions) if they are repointed; the ADR's reach over that
file was **not** ruled on and it is not in the ticket's repoint table — see Anti-Drift Hazards.

### Measurement 4 — Gap 1, the generator's output location

`src/worldgeneration/generator.py:536` hard-codes the directory; `:383` declares it as the
contract. Relevant constraints, measured:

- `WorldRepository._validate_world_id()` (`src/worldbuilding/repository.py:27-29`) enforces
  `^[a-zA-Z0-9_-]+$`, and `list_worlds()` (`:46-61`) only indexes **direct child** directories of
  `worlds_dir` that contain a `world.yaml`.
- `tests/unit/worldgeneration/test_composition_generator.py` already runs the generator under
  `tmp_path` + `monkeypatch` (chdir), so it is isolated from the real tree — but `:183-199`
  (`test_output_path_pattern`) asserts `output_path.name == "generated_frontier_3_42.yaml"` **and**
  `"generated" in str(output_path)`.
- Parity entries `SUBSTRATE-NEW-010` and `SUBSTRATE-NEW-011` describe this generator; their
  `v2_evidence` must follow whichever option is chosen.

| option | shape | cost |
|---|---|---|
| **A** `data/worlds/<world_id>/world.yaml` | generator creates the per-world directory | ADR-conformant and the obvious default. Every generated run now appears in `WorldRepository.list_worlds()`, so any corpus test or tool that enumerates `data/worlds/` sees generated worlds mixed with hand-authored ones; generated output becomes indistinguishable from authored content (no provenance marker); `"generated" in str(output_path)` at `test_composition_generator.py:198` fails unless the id keeps its `generated_` prefix (it does today — `generated_frontier_3_42` — so this assertion survives by accident, which is fragile). Needs `resolved/` to be produced too, or `WorldRepository.load_world()` raises "has not been resolved". |
| **B** `data/worlds/generated/<world_id>/world.yaml` | a grouping level | **Ruled out by measurement.** `list_worlds()` only looks one level down, so `generated/` (no `world.yaml`) is skipped and the nested id is invisible to `WorldRepository`; `_resolve_world_path("generated_frontier_3_42")` would also not find it. Would require changing the repository indexer — out of this ticket's scope. |
| **C** a separate non-authoritative output root (e.g. `data/generated_worlds/`) with an explicit promote step into `data/worlds/` | two-stage | Keeps `data/worlds/` hand-authored and preserves provenance, and is honest that a generated composition is a candidate, not a world definition. But it re-creates a second location that holds `worldcomposition.v1` files — the exact shape of the split being retired — unless the ADR sentence explicitly scopes "authoritative definition" to promoted worlds. Needs an added ADR clause, and AC-6's check must exempt the staging root or it will fire. |
| **D** parameterize `generate(..., output_dir: Path = ...)` | caller decides | Smallest blast radius and makes the hard-coded path a parameter, but a default still has to be chosen, so it defers rather than resolves. Pairs well with A as the default. |

**Recommendation to the planner (a recommendation, not a decision): A + D** — parameterize, default
to `data/worlds/<world_id>/`, and add the generated-provenance marker inside the YAML (not in the
path) so option C's provenance benefit is kept without a second root. The decision is the user's
or the planner's; this investigation does not make it.

---

## Mechanics / Engine Constraints

- **`docs/architecture/world_repository_layout.md` §1 (Status: ACCEPTED)** — "we will maintain the
  existing unified world repository root at `data/worlds/` ... The root source file inside a world
  folder is always `world.yaml`", and `worldcomposition.v1` is one of the two indexed schema
  versions. Verified by full read (54 lines): it **does not mention**
  `data/content/world_compositions/`, confirming the ticket's own attribution correction. It also
  does not currently say *sole* — which is why AC-8 amends rather than cites it.
- **ADR §2** — a `worldcomposition.v1` source is **NEVER** passed directly to `WorldCompiler`;
  resolved artifacts must be written to `data/worlds/<id>/resolved/`. This binds Gap 1's chosen
  location: whatever the generator writes must be a *source*, and a `resolved/` sibling must exist
  before `WorldRepository.load_world()` will serve it.
- **ADR §2 vs. the tree** — the ADR names `resolved/compile_report.json`; the tree has
  `data/worlds/<id>/world_compile_report.json` at the world root. Pre-existing drift, **out of
  scope**, noted so nobody "fixes" it inside this ticket.
- **ADR §3 Backwards Compatibility** — "All existing tools, scripts, and tests that load
  `worldspec.v1` from `data/worlds/<world_id>/world.yaml` must remain fully supported and
  unaltered." Constrains the repoint to additive path changes, not loader changes.
- **`docs/mechanics/06_worldbuilding_foundation.md` §7 "Integrity Validation Laws & Severity
  Gates"** — the gate ladder (Level 1 Pydantic / Level 2 structural / Level 3 runtime-gated
  compiler) and the ERROR/WARNING severity split. AC-6's "one `world_id`, one module set" check is
  a **Level 2 structural** rule at **ERROR** severity by that chapter's own taxonomy, and the
  chapter's `WORLD-REACH-001` block (`:118`) is the formatting precedent for naming a new rule.
- **Bible 06 §9 "Content Catalog Database Structure (`data/content/`)"** — enumerates Layers 1-5
  under `data/content/` and conspicuously does **not** list `world_compositions/` as one of them.
  Useful supporting evidence that the directory was never a catalog layer, and a place a reader
  could expect a sentence.
- **`docs/guides/content_authoring.md`** — teaches the retired path at **three** sites, not one:
  the §1 type table (`:27`), §2 Step 4 (`:72`), and §4's own location sentence (`:164-167`), plus a
  comment at `:292`. Gap 2 is wider than the ticket records.

---

## Docs Requiring Update

- `docs/architecture/world_repository_layout.md`: AC-8 — §1 gains the single normative sentence
  ("`data/worlds/<world_id>/` is the sole authoritative definition of a `world_id`; no other
  location may define a `world_id`"). The rule-layer ruling puts the sentence here and only here.
- `docs/mechanics/06_worldbuilding_foundation.md`: AC-8 — §7 gains the integrity invariant (a
  `world_id` resolves to exactly one definition, enforced as a Level 2 ERROR gate) and **cites**
  the ADR for the location rather than restating it.
- `docs/guides/content_authoring.md`: Gap 2 / AC-8 — correct the authoring path at `:27`, `:72`,
  `:164-167` and `:292` and link the ADR, so the documented process stops re-creating the split.
- `docs/parity_ledger/substrate.yaml`: AC-10 — add the one-`world_id`-one-definition entry
  (`SUB-394`) carrying AC-6's check as `test_path`, and update `SUBSTRATE-NEW-010`/`-011`'s
  `v2_evidence` for the generator's new output location (Gap 1).
- `docs/world/generator_contract.md`: Gap 1 — states the generator's output location; must follow
  whichever option AC-9 chooses, or it contradicts the code.
- `docs/content/pipeline_contract.md`: references `world_compositions` as a pipeline input family;
  must reflect the retirement.
- `docs/mechanics/content_usage_matrix.md`: documents the content families including
  `world_compositions` (mirrors `src/content/matrix.py:550`), which this ticket changes.

Considered and **not** required: `docs/world/compiler_contract.md` and
`docs/world/raid_boss_camp_contract.md` mention `world_compositions` only as the name of a spec
family or in an example id, with no claim about the directory's location, so nothing in them
becomes false. `docs/testing/test_taxonomy.md` and `docs/testing/no_duplication_test_policy.md`
cite `test_real_content_world_compositions.py` by file name, which survives the repoint, so no
edit is needed unless that file is renamed or deleted. Everything under `docs/archive/`,
`docs/audits/`, `docs/brainstorm/` and `docs/plans/world_generation_organic_terrain_epic.md` is a
frozen historical record of a past state and is deliberately left untouched. `docs/REGISTRY.yaml`
is regenerated, never hand-edited.

---

## Parity Ledger Overlap

Worldbuilding integrity lives in **`docs/parity_ledger/substrate.yaml`** (405 entries). There is
**no existing entry asserting "one `world_id`, one definition"** — AC-10 needs a **new** entry.
Next available numeric id: **`SUB-394`** (max is `SUB-393`; the file also carries 12 legacy
`SUBSTRATE-NEW-0NN` ids outside the numeric sequence — do not extend that series).

| id | file | status | priority | relevance |
|---|---|---|---|---|
| `SUB-394` *(to add)* | `substrate.yaml` | — | P1 suggested | AC-10's entry; `test_path` = AC-6's one-`world_id`-one-module-set check |
| `SUBSTRATE-NEW-001` | `substrate.yaml` | verified | **P0** | "Two compilation paths: direct (`WorldSpec`→`AuthoritativeState`) and composition". **`test_path: None` on a P0** — pre-existing violation of the P0-requires-a-passing-`test_path` rule, flagged per instruction. This ticket's AC-6 check is a natural candidate to fill it, but doing so is a judgment call for the planner, not an assumption. |
| `SUBSTRATE-NEW-010` | `substrate.yaml` | verified | P1 | `ProceduralCompositionGenerator` → `WorldCompositionSpec` YAML. `test_path: tests/unit/worldgeneration/test_composition_generator.py` (exists). **Must be updated by Gap 1** — its `v2_evidence` describes the generator whose output path changes. |
| `SUBSTRATE-NEW-011` | `substrate.yaml` | verified | P1 | Generator seed-based parameter sampling; `test_path: tests/unit/worldgeneration/test_seed_params.py` (exists). Same Gap-1 exposure. |
| `SUBSTRATE-NEW-004` | `substrate.yaml` | verified | P1 | `CompileContext.perspectives` from `WorldCompositionSpec.default_perspectives`. Unaffected — `default_perspectives` measured identical on both sides for all 9 pairs. |
| `SUBSTRATE-NEW-006` | `substrate.yaml` | verified | P1 | `WorldCompositionSpec.pack_refs` validated at assembly start; `test_path: tests/unit/worldassembly/test_pack_validation.py`. Touches the `:224` pack test the ticket says to leave alone. |
| `FAC-012` | `faction.yaml` | verified | P1 | faction tension seeded from a composition-level `faction_tension_overrides`. **Directly relevant**: `faction_tension_overrides` is present on the running side of 8 of 9 pairs and absent from the catalog side of all of them, so the reconciliation changes which worlds exercise this entry. Review, likely `v2_evidence` only. |
| `INFRA-187` | `infrastructure.yaml` | verified | **P0** | the WorldAssembly pipeline `WORLD-ASM-001..010`. **`test_path: None` on a P0** — same pre-existing gap, flagged. |
| `INFRA-256`, `INFRA-257` | `infrastructure.yaml` | verified | P1 | `information_source_profiles` / `pending_information_responses` compile-time plumbing — both are keys present **only** on the running side. Their `test_path`s include `tests/unit/worldassembly/test_assembly.py`, one of the 7 genuinely-dependent files. |
| `INFRA-373` | `infrastructure.yaml` | verified | P2 | pins `TVD(sandbox_world, dungeon_crawl) == 0.23161981243456373` at seed 42, `test_path: tests/unit/rendering/test_variants.py::test_total_variation_distance_same_spec_different_seed_is_zero_for_dungeon_crawl`. **Watch this one**: it is a `dungeon_crawl` terrain-histogram anchor. It resolves `dungeon_crawl` through `WorldRepository`, so it should be unaffected — but if the `danger_scale`/module-set question (Risks #1) is settled by editing `data/worlds/dungeon_crawl/world.yaml`, the anchor constant moves and this P2 entry plus its test must be re-anchored. |
| `SUB-390` | `substrate.yaml` | verified | P1 | `PlaceState` construction across "both real compilation paths" — the same two-path framing this ticket collapses. Review for wording. |
| `INFRA-230` | `infrastructure.yaml` | verified | P2 | `RunManifest.world_id`. Mention-level; no change expected. |

All cited `test_path`s above that name a file were checked to exist. The two P0 `test_path: None`
entries (`SUBSTRATE-NEW-001`, `INFRA-187`) are reported as found, not treated as this ticket's
obligation.

---

## Prior Work

- **`agent-working/stored_artifacts/TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING/`** — the
  ticket that found this split and added the nested-first dual-layout fallback at
  `src/scenarios/resolver.py:58-95`. That fallback is why the redirect needs no loader work.
- **`agent-working/tickets/done/TCK-20260627-P1I-WORLD-BALANCE-FIX.md`** — **the most important
  prior work, and neither this ticket nor the folded one cites it.** It is the recorded origin of
  the catalog's `danger_scale: 2` and 2-module `dungeon_crawl`, as a measured fix for 94-97%
  attrition. See Risks #1.
- **`agent-working/stored_artifacts/TCK-20260614-WORLDDAT-COMPOSE/`** — authored
  `wilderness_survival`, `urban_political`, `dungeon_crawl` as catalog compositions and wrote the
  `:333`/`:374`/`:424` tests. Explains why those tests' premise is "the real composition".
- **`agent-working/stored_artifacts/TCK-20260607-STRICT-MODE-PRODUCTION/`** — the
  `NON_CATALOG_DIRS` exclusion at `src/content/repository.py:150`; retiring the directory makes
  that exclusion entry dead code.
- **`agent-working/stored_artifacts/TCK-20260929-UNREACHABLE-CLASSIFY-NEVER-SEEDED/investigation.md`**
  — the one confirmed artifact that measured through the catalog path (AC-7's known-affected case).
  Five sibling `UNREACHABLE-CLASSIFY-*` artifacts exist in `stored_artifacts/` and are the obvious
  first sweep for AC-7's general case.
- `TCK-20260614-WORLDGEN-E2E-SMOKE` — authored `test_e2e_smoke.py`'s two loader helpers.
- `TCK-20260915-WORLDBUILDING-DUPLICATE-REGION-ID-ACROSS-MODULES` — same "one id, two meanings"
  family one scope down; worth reading for how its guard was shaped.

---

## Risks and Open Questions

1. **BLOCKING — the `dungeon_crawl` `danger_scale` "confirm" would silently revert a closed P1
   balance repair.** This is not the authority question (that stays closed: `data/worlds/` is
   authoritative) and not a per-world content decision (those collapsed correctly). It is narrower
   and new: AC-5 instructs recording "catalog value never drove a run; running value (4) kept".
   Measured, the running definition compiles to **32 entities / 4 regions / 9 quests**, which is
   *exactly* the configuration `TCK-20260627-P1I-WORLD-BALANCE-FIX` was filed to eliminate after
   D08 measured 94-97% attrition by tick 100; the catalog's 12-entity version is that ticket's
   delivered remedy. Keeping `4` therefore does not drop a never-executed value — it ratifies a
   known, previously-fixed extinction defect as the authoritative definition, and the fix's own
   stated reason (`goblin_camp_conflict` and `old_mine_resource_loop` "had unmet `requires:
   frontier_village_core` dependency in dungeon_crawl") is still asserted in
   `test_real_content_world_compositions.py:424`'s docstring. The decision needed — **from the user
   or the rule owner, not from the implementer** — is whether reconciliation **re-applies** the
   balance fix into `data/worlds/dungeon_crawl/world.yaml` (2 modules, `danger_scale: 2`), which is
   fully consistent with `data/worlds/` being authoritative, or **abandons** it with a recorded
   rationale. Note the fix's dependency claim is also now questionable: the 4-module running
   definition assembles and compiles cleanly here, so the `requires: frontier_village_core`
   constraint is either a warning or has since changed. Do not let this be resolved by a one-line
   assertion edit from `2` to `4`.
2. **`oracle: unresolved` for the `danger_scale` expectation.** Until #1 is decided there is no
   authoritative oracle for the value: the ADR governs *location*, not *content*; the rule owner
   explicitly declined to add a catalog Rule; and the only document stating an intended value is a
   closed ticket that states `2` with measured evidence. The test plan reflects this.
3. **`test_real_world_compositions_normalization` (`:42-56`) cannot be repointed as-is.** Its
   subject is shorthand-`modules:`→`module_refs` conversion and it asserts `ref.order == 0` for
   every ref; the running `frontier_living_world` uses `module_refs` with explicit `order: 0..6`.
   Repointing it makes it assert something it was not written to assert. It needs either a changed
   premise plus a renamed test, or retention of a synthetic shorthand fixture. The ticket's repoint
   table lists `:42` without noting this.
4. **The third artifact — `resolved/` staleness — is an unguarded divergence axis this ticket does
   not address.** Production compiles `data/worlds/<id>/resolved/world.resolved.yaml`, not
   `world.yaml`. Nothing measured here verifies the snapshot is current with its source. If
   reconciliation edits any `world.yaml`, the matching `resolved/` must be regenerated or the
   "one `world_id`, one definition" guarantee holds at the source layer while production still runs
   the stale snapshot. Whether AC-6's check should also cover source-vs-resolved agreement is an
   open scoping question for the planner.
5. **`test_e2e_smoke.py` was not covered by the rule owner's repoint ruling.** It has the same
   shape as the repointed tests (loads by world name, asserts on real content) but was not in the
   table. Repointing it changes `dungeon_crawl` from 12 to 32 entities, which interacts with #1.
   Leaving it on the catalog path is impossible once the directory is deleted. Needs an explicit
   call.
6. **`tests/tools/test_content_inventory.py` degrades silently.** Both sides of its equality go to
   zero when the directory is removed, so it passes while asserting nothing. If
   `tools/generate_content_inventory.py` keeps reporting "World compositions"/"World compositions
   (generated)" counters at all, they must be repointed; if not, the counters and their test should
   be removed deliberately rather than left green and meaningless.
7. **`test_expansion_gate.py:248` (Gate 11) raises `IndexError`, not an assertion failure,** on an
   empty directory (`sorted(glob("*.yaml"))[0]`). An obscure failure mode if the deletion lands
   before the test update.
8. **`src/content/matrix.py:550-551` + `src/content/reference_graph.py:42` + `src/content/
   paths.py:8` + `src/content/validator.py:38,153` + `src/content/repository.py:150` form a
   content-family registration that outlives the directory.** Removing `world_compositions_dir`
   from `ContentPathConfig` is an API-shaped change with five dependents and a test (`:12`) pinning
   the literal; keeping it pointed at a non-existent directory is a different kind of debt. Not
   pre-judged here; the planner must pick and say which.
9. **`INFRA-373`'s pinned TVD constant for `dungeon_crawl`** moves if #1 is resolved by editing
   `data/worlds/dungeon_crawl/world.yaml`. Re-anchoring a documented float is its own small task.
10. **AC-6's "must fail on today's content before the reconciliation lands"** needs a defined
    corpus to be meaningful. Today it would fire on 8 of 9 pairs (`simq_scale_stress_seed42` is
    byte-identical, so a strict module-set check passes there). After reconciliation it must have
    nothing to find — which means it must also be written so that a *future* generated world
    landing in `data/worlds/` (Gap 1 option A) does not make it fire. Options A and C interact with
    this directly.
11. **AC-7's general case is genuinely unbounded.** `stored_artifacts/` holds hundreds of
    investigations. A tractable definition of "assessed" is needed (e.g. grep `stored_artifacts/`
    for `world_compositions` and for `WorldAssemblyResolver`, and re-check only hits), or this AC
    cannot be closed honestly.

Deliberately **not** reopened, per the ticket and the dispatch brief: which location is
authoritative; whether the 8 pairs need per-world decisions; whether
`test_real_content_world_compositions.py` is repointed or deleted; where the normative sentence
lives.

---

## Anti-Drift Hazards

- **Do not "repoint" by editing the assertion value from `2` to `4` and moving on.** That is the
  exact silent-reconciliation the catalog owner warned against, and Risks #1 shows a measured
  12-vs-32-entity balance consequence behind it.
- **Do not touch the six out-of-reach tests** in `test_real_content_world_compositions.py`
  (`:171`, `:188`, `:205`, `:224`, `:265`, `:300`). They build synthetic specs; the ADR says nothing
  about them and they are the second reason the file survives.
- **Do not delete `data/content/world_compositions/` before `src/worldgeneration/generator.py:536`
  stops writing to it.** A single generation run recreates the directory and silently re-opens the
  split.
- **Do not reorganize `data/worlds/` while here.** Option B (`data/worlds/generated/<id>/`) was
  measured to be invisible to `WorldRepository.list_worlds()`; changing the indexer is a different
  ticket.
- **Do not fix the ADR §2 `resolved/compile_report.json` vs. real
  `world_compile_report.json` naming drift.** Real, pre-existing, out of scope.
- **Do not restate the authoritative location in Bible 06 or `content_authoring.md`.** One
  normative sentence, in the ADR; the others cite it. Restating it is how three sources drift.
- **Do not regenerate `resolved/` snapshots for all 24 worlds as a convenience.** That rewrites
  compiled artifacts for 15 worlds this ticket never touches and would churn determinism
  fingerprints across unrelated tests.
- **Do not expand into the legacy `build_scenario_state()`/`ArenaInjector`/`V2EngineManager` spawn
  paths.** Explicitly out of scope in the ticket.
- **Do not let the generator's output-location decision be made implicitly by whoever edits line
  536.** It is a recorded decision with four measured options.
- **Do not treat `make world-validate`/`world-compile` (Makefile `:133-136`) as catalog-path
  commands.** They already operate on `data/worlds/` via `WorldRepository`, so
  `content_authoring.md` §4's workflow block is already pointing at the right tooling while its
  file-location sentence points at the wrong directory. Only the location sentence is wrong.
