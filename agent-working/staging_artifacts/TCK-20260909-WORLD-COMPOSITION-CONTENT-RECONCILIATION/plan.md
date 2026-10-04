---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION
artifact_type: plan
tags: [architecture, content]
---

# Implementation Plan — TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION

## Summary

`data/worlds/<world_id>/` is authoritative (settled by the rule owner; do not re-open). The content
side of this ticket therefore collapses to **one recorded decision plus one explicit call-out**, and
the real work is: (a) build the structural guard that makes "one `world_id`, one definition" and
"the committed `resolved/` projection equals a fresh resolve" checkable, and observe it **red on
today's tree first**; (b) state the law once, in the ADR, with Bible 06 and `content_authoring.md`
pointing at it; (c) repoint every test and code path that genuinely depends on
`data/content/world_compositions/` at the authoritative layout; (d) only then delete the directory,
after the generator stops writing into it. The `dungeon_crawl` `danger_scale` value is **not this
ticket's content decision** — it belongs to
`TCK-20261004-CLOSED-P1-BALANCE-FIX-WRITTEN-TO-NON-RUNNING-WORLD-DEFINITION`; this ticket's only
obligation there is to leave no test or doc asserting either `2` or `4` as intended design on its own
authority.

Context-search note: `mcp__knowledge-search__search_docs` returns `{"error":"index not found"}` and
`graphify-out/` does not exist in this worktree (recorded in `investigation.md` §"Context-search
provenance"). The sanctioned `tools/knowledge_search.py` fallback was used there; this plan builds on
that investigation plus direct re-verification of every file:line it cites below.

---

## Steps

### Step 1 — Extract one reusable "resolve a composition world" helper

**Files:** `src/worldbuilding/cli.py` (new module-level helper, or a new
`src/worldassembly/resolve_io.py` if the implementer prefers; keep it out of `tests/`).

**Change:** The AC-6 agreement half (Step 2) must compare a committed
`data/worlds/<id>/resolved/world.resolved.yaml` against a **fresh resolve**. Today the only code that
produces that file is inline inside `src/worldbuilding/cli.py::handle_resolve` — verified: it loads
`world.yaml` (`src/worldbuilding/cli.py:140-148`), validates `WorldCompositionSpec`
(`:156-160`), loads `CatalogRepository("data/content")` + `WorldModuleRepository(
ContentPathConfig().world_modules_dir)` (`:162-166`), calls `WorldAssemblyResolver(...).assemble(
composition)` (`:168-170`), then writes with
`yaml.safe_dump(bundle.world_spec.model_dump(exclude_none=True), f, sort_keys=False,
allow_unicode=True)` (`src/worldbuilding/cli.py:177,183-184`).
Extract exactly that sequence into a helper returning the bundle **and** the rendered YAML text, and
have `handle_resolve` call it so the CLI and the guard cannot drift in serialization (a byte
comparison is worthless if the two sides dump differently).

**Other writers to this shared resource** (`data/worlds/<id>/resolved/*`), enumerated — grep over
`src/` and `tools/` for `world.resolved.yaml` returns exactly one writer and five readers:
- **Writer (only):** `src/worldbuilding/cli.py:177-205` (`make world-resolve WORLD=<id>`,
  `Makefile:139-140`). No other `src/` or `tools/` path creates or mutates `resolved/`.
- Readers, unaffected but must keep working: `src/worldbuilding/repository.py:78` (`load_world`),
  `:132` (`load_world_with_context`), `src/lab/orchestrator.py:181-184` (reads only),
  `tools/generate_corpus_registry.py:108,139`, `tools/calibrate_simq.py:150`,
  `tools/perf/profile_sweep.py:73`.
Because there is a single writer, the helper extraction carries no ordering or race risk; the only
interaction to preserve is that `handle_resolve` keeps writing the same five sidecars
(`world.resolved.yaml`, `compile_context.json`, `provenance_manifest.json`, `assembly_report.json`,
`validation_report.json`, `src/worldbuilding/cli.py:176-205`).

**Do NOT touch:** `WorldAssemblyResolver.assemble()` itself; `WorldRepository`'s
composition→`resolved/` redirect (`src/worldbuilding/repository.py:74-81`); the ADR §2 vs.
`world_compile_report.json` naming drift (pre-existing, out of scope).

**Verify:** `pytest tests/unit/worldbuilding/ -q` green (behavior-preserving refactor);
`make world-resolve WORLD=wilderness_survival` still writes all five sidecars.

---

### Step 2 — Add the AC-6 guard and observe it RED before changing any content

**Files:** `tests/architecture/test_world_definition_single_source.py` (new).

**Change:** Two guards, per `test_plan.md` §"AC-6 / AC-10":
1. `test_world_id_resolves_to_exactly_one_definition` — walk the repo for any YAML whose
   `schema_version` contains `worldcomposition` that is **not** at `data/worlds/<id>/world.yaml`, and
   fail naming every offender. Key on **existence of a second definition, not on difference** —
   `simq_scale_stress_seed42` is a byte-identical pair and a difference-based check would pass there
   while the duplicate still exists.
2. `test_no_source_outside_data_worlds_defines_a_known_world_id` — for every id in
   `WorldRepository("data/worlds").list_worlds()` (verified to index only direct children holding a
   `world.yaml`, `src/worldbuilding/repository.py:46-61`), assert no other path declares that
   `world_id` with a composition schema.
3. `test_committed_resolved_projection_equals_a_fresh_resolve` — for every one of the 24
   `data/worlds/<id>/` worlds (measured: all 24 are `worldcomposition.v1`), re-resolve via Step 1's
   helper and compare to the committed `resolved/world.resolved.yaml`. **Equality against a fresh
   resolve, never a field-by-field diff against `world.yaml`** (rule-owner constraint; the projection
   legitimately contains expanded content). Mark it `@pytest.mark.slow` if runtime demands, but do
   not reduce the corpus.

**Record the red run.** Paste the guard's own failure output into the ticket's Implementation Notes:
guard 1/2 must name the 9 catalog duplicates today; guard 3's result is unknown and unmeasured by
Investigate. **If guard 3 fails for any world, or a fresh resolve is not byte-deterministic, file
that as a new finding ticket and leave the guard strict — do not weaken it to a subset and do not
regenerate snapshots to make it green** (see Scope Guards).

**Do NOT touch:** any `data/` content in this step. The guard must be red against the untouched tree
or it proves nothing (AC-6's own wording).

**Verify:** `pytest tests/architecture/test_world_definition_single_source.py -q` **fails**, and the
failure message names the offending ids. This red observation is the deliverable of this step.

---

### Step 3 — Add the two normative sentences to the ADR §1

**Files:** `docs/architecture/world_repository_layout.md`.

**Change:** In §1 "Unified Directory Layout", directly after the existing normative sentence at
`:21` ("The root source file inside a world folder is always `world.yaml`. The schema version within
the YAML determines how the repository indexes it"), add **two** sentences as one rule block (not a
new section):
1. `data/worlds/<world_id>/` is the sole authoritative definition of a `world_id`; no other location
   may define a `world_id`.
2. The rule owner's verbatim clause, quoted exactly from the ticket's BLOCKER section: *"Within that
   directory, `world.yaml` is the authored definition. For a `worldcomposition.v1` world,
   `resolved/world.resolved.yaml` is a generated projection of it: it is never hand-edited, and it
   must equal what the resolver produces from the current `world.yaml` and the current module/catalog
   content. A committed projection that differs from a fresh resolve is a defect. It is not an
   alternative definition."*

Verified: the ADR is 54 lines, `ACCEPTED` (`:10-11`), and does **not** mention
`data/content/world_compositions/` anywhere — so this is an amendment, not a citation. §2 already
draws the source/projection structure at `:40-51`; only the authority and freshness rule is missing.

**Do NOT touch:** ADR §2's `resolved/compile_report.json` line (`:50`) vs. the tree's real
`world_compile_report.json` — pre-existing drift, explicitly out of scope. ADR §3 (`:53-54`)
backwards-compatibility clause stays as-is and constrains later steps to path changes, not loader
changes.

**Verify:** Step 6's docs guard.

---

### Step 4 — Bible 06 states the invariant and cites the ADR

**Files:** `docs/mechanics/06_worldbuilding_foundation.md`.

**Change:** In §7 "Integrity Validation Laws & Severity Gates", add the invariant — *"the world the
engine loads is the one its authored definition resolves to"*, i.e. a `world_id` resolves to exactly
one definition, enforced as a **Level 2 structural ERROR** gate by that chapter's own taxonomy — and
**cite** `docs/architecture/world_repository_layout.md` for the location. Follow the chapter's
existing `WORLD-REACH-001` block formatting as the precedent for naming a rule.

**Do NOT touch:** do not restate the path `data/worlds/<world_id>/` or any freshness mechanics here.
One normative sentence, in the ADR; this chapter points at it. Restating it is how three sources
drift, and Step 6's guard will fail on a restatement. Do not add a catalog Rule under
`docs/world_rules/` — the rule owner explicitly declined (storage/build is below catalog scope; cite
"by analogy to `OWN-01`", never "`OWN-01` governs").

**Verify:** Step 6's docs guard.

---

### Step 5 — Correct `content_authoring.md` at all four sites

**Files:** `docs/guides/content_authoring.md`.

**Change:** Re-verified by grep — the retired path is taught at exactly four places: `:27` (§1 type
table row "World composition | `data/content/world_compositions/`"), `:72` (§2 Step 4 example path
`data/content/world_compositions/frontier_living_world.yaml`), `:167` (§4's location sentence
`data/content/world_compositions/<world_id>.yaml`), `:292` (a YAML comment "# in
`world_compositions/<id>.yaml`"). Change all four to `data/worlds/<world_id>/world.yaml` and link the
ADR from §4 instead of restating the rule.

**Do NOT touch:** §4's `make world-validate` / `make world-compile` workflow block — verified
`Makefile:133-140` already drives `src.worldbuilding.cli` against `data/worlds/`, so the tooling
instructions are already correct. **Only the file-location sentences are wrong.**

**Verify:** Step 6's docs guard; `grep -rn "data/content/world_compositions" docs/guides/` returns
nothing.

---

### Step 6 — Add the docs-agreement guard

**Files:** `tests/architecture/test_world_definition_single_source.py` (extend).

**Change:** `test_authoritative_world_location_stated_once` — asserts (a) the normative
"sole authoritative definition" sentence appears in `docs/architecture/world_repository_layout.md`,
(b) neither `docs/mechanics/06_worldbuilding_foundation.md` nor `docs/guides/content_authoring.md`
restates the authoritative path without citing the ADR, (c) no file under `docs/guides/` presents
`data/content/world_compositions/<world_id>.yaml` as an authoring target.

**Do NOT touch:** `docs/archive/`, `docs/audits/`, `docs/brainstorm/`,
`docs/plans/world_generation_organic_terrain_epic.md` — frozen historical records; the guard must
exclude them, and no step may edit them.

**Verify:** `pytest tests/architecture/test_world_definition_single_source.py -q -k docs`.

---

### Step 7 — Repoint the seven named-world sites in `test_real_content_world_compositions.py`

**Files:** `tests/integration/worldassembly/test_real_content_world_compositions.py`.

**Change:** Swap `Path("data/content/world_compositions/<id>.yaml")` →
`Path("data/worlds/<id>/world.yaml")` at the seven verified path lines `:30`, `:44`, `:62`, `:86`
(`frontier_living_world`), `:345` (`wilderness_survival`), `:385` (`urban_political`), `:436`
(`dungeon_crawl`) — the tests at `:28`, `:42`, `:59`, `:83`, `:333`, `:374`, `:424`. Both sides carry
`schema_version: worldcomposition.v1` and validate against the same `WorldCompositionSpec`, and all
24 `data/worlds/*/world.yaml` were measured to validate and assemble, so the swap is mechanically
safe. Then resolve the measured assertion deltas:
- `:52` `len(normalized.module_refs) == 6` → `7`
- `:112` `len(provenance_manifest.module_fingerprints) == 6` → `7`
- `:374`'s test: `len(spec.module_refs) == 3` → `4`
- `:333`'s test: `len(spec.module_refs) == 4` — unchanged, clean swap
- `test_real_world_compositions_normalization` (`:42-56`) **must be redesigned, not repointed.**
  Verified at `:54-56`: it loops `assert ref.order == 0` and its docstring says "normalizes shorthand
  modules". `data/worlds/frontier_living_world/world.yaml` uses `module_refs` with explicit
  `order: 0..6`, so its subject does not exist on the authoritative side. Either (a) rename it to a
  `module_refs`-form normalization test with assertions that match the authoritative file, or (b)
  keep a **synthetic** shorthand fixture inside the test and say so in a comment. Do not delete the
  shorthand-conversion coverage silently — `WorldCompositionNormalizer` still supports both shapes.
- `test_dungeon_crawl_composition` (`:424`): remove the two content-value assertions
  `len(spec.module_refs) == 2` (`:437`) and
  `bandit_ref.parameters.get("danger_scale") == 2` (`:452`), and rewrite the docstring (which
  currently states "danger_scale=2 (6 bandits)… reduce entity count from 32 to 12
  (TCK-20260627-P1I-WORLD-BALANCE-FIX)"). Replace both with a comment naming
  `TCK-20261004-CLOSED-P1-BALANCE-FIX-WRITTEN-TO-NON-RUNNING-WORLD-DEFINITION` as the owner of the
  module-count and `danger_scale` oracle. **Do not change `2` to `4`** — per the ticket's amended
  AC-5, this ticket must carry neither `2` forward as authoritative nor `4` forward as
  confirmed-correct. Keep the remaining structural assertions (`world_id`, `schema_version`,
  `provided_features`, `default_perspectives`, `bandit_ref` exists, quest count ≥ 2) and keep the
  `scalable_bandit_camp` ref lookup so the other ticket has a seam to assert into.

**Do NOT touch:** the six out-of-reach tests at `:171`, `:188`, `:205`, `:224`, `:265`, `:300`. They
build synthetic specs / synthetic `world_id`s and the ADR says nothing about them; a `git diff` over
those six must be empty.

**Verify:** `pytest tests/integration/worldassembly/test_real_content_world_compositions.py -q`.

---

### Step 8 — Repoint the other genuinely-dependent test files

**Files:** `tests/integration/worldassembly/test_e2e_smoke.py`,
`tests/unit/worldassembly/test_assembly.py`,
`tests/integration/content/test_swamp_border_pack.py`,
`tests/integration/content/test_expansion_gate.py`.

**Change:** All four were re-verified as genuine dependencies (they load or glob the directory and
would break on deletion):
- `test_e2e_smoke.py:54` (`_compile_composition`) and `:74` (`_compile_generated_composition`) →
  `data/worlds/{world_id}/world.yaml`. The two helpers collapse into one: both
  `generated_frontier_3_42` and `simq_scale_stress_seed42` exist as real `data/worlds/<id>/`
  directories (verified by listing — 24 dirs), so the `generated/` special case disappears. Its four
  tests assert only `entity_count > 0`, `quest_count >= 2`, `len(state.resource_nodes) >= 3` — no
  exact counts — so the repoint needs no assertion changes; only the module docstring's prose counts
  at `:17-20` ("dungeon_crawl: 10 ticks, 32 entities") must be corrected or made non-numeric. This
  file was **not** in the rule owner's repoint table, but deletion forces the change and the
  assertions carry no content oracle, so repointing it is a mechanical consequence, not a new
  semantics decision.
- `test_assembly.py:1058` and `:1079` → `data/worlds/frontier_living_world/world.yaml` (both have
  `assert comp_path.is_file()`). Leave `:1185`/`:1190` alone — error-string mentions of the family
  name `'world_compositions'`, not a path.
- `test_swamp_border_pack.py:93` → `data/worlds/{cid}/world.yaml` for each
  `manifest.sample_compositions` (sourced from `data/content/packs/swamp_border_pack.yaml`; the ids
  resolve under `data/worlds/`).
- `test_expansion_gate.py:184` (Gate 08, `compositions_dir.glob("*.yaml")`) and `:248` (Gate 11,
  `sorted(glob("*.yaml"))[0]`) → iterate `Path("data/worlds").glob("*/world.yaml")`. Gate 11 raises
  **`IndexError`**, not an assertion failure, on an empty directory — if the implementer sees an
  `IndexError` here, it is this ticket's step ordering (deletion before this step), not a new bug.

**Do NOT touch:** `tests/unit/content/test_content_usage_matrix.py` (`:87`, `:97`, `:397`) and
`tests/integration/scenarios/test_content_foundation.py` (`:27-61`) — classified as mentions. The
former uses `"world_compositions"` as a structural-folder *name* in a one-directional
`scanned_families - CONTENT_USAGE_MATRIX.keys()` check (verified at `:104-108` and `:411-415`), so
deleting the directory keeps it green; the latter reads the `world_composition` *field* on scenario
YAMLs under `data/content/simulation_scenarios/` and never touches the directory.

**Verify:** `pytest tests/integration/worldassembly/ tests/unit/worldassembly/ tests/integration/content/ -q`.

---

### Step 9 — Flip the resolver default, revert the Campaign override, fix the stale citation

**Files:** `src/scenarios/resolver.py`, `src/domains/campaigns/orchestrator.py`,
`tests/unit/scenarios/test_resolver_defaults.py` (new),
`tests/unit/domains/campaigns/test_campaign_orchestrator.py`,
`tests/integration/scenarios/test_scenario_setup_resolver.py` (only if its error-message assertion
breaks).

**Change:**
1. `src/scenarios/resolver.py:34`: `_DEFAULT_COMPOSITIONS_DIR = Path("data/content/world_compositions")`
   → `Path("data/worlds")`. No loader change is needed: `_load_composition()` (`:58-95`) already tries
   `<dir>/<world_id>/world.yaml` first and falls back to `<dir>/<world_id>.yaml`. **Keep the dual
   layout** (the ticket's open question) — the fallback is three lines, costs nothing, and the flat
   shape still appears in third-party/ad-hoc `compositions_dir` overrides; record that choice in the
   ticket. Update the now-stale explanatory comment at `:59-72` (it describes
   `data/content/world_compositions/` as "this repo's existing default").
2. `src/domains/campaigns/orchestrator.py:199-201`: drop `compositions_dir=Path("data/worlds")` from
   the `CatalogScenarioStateBuilder(...)` construction so Campaign rides the now-unified default, and
   rewrite the comment block at `:172-188` — it both carries the "data/content/world_compositions/ is
   the anomaly" interpretation (`:178`, the real origin of the mis-attribution the ticket corrects)
   and the dead citation `TCK-20260909-WORLD-COMPOSITION-DIRECTORY-CONSOLIDATION` (`:186`, Gap 3).
   Replace the citation with this ticket's ID and point the authority claim at the ADR as amended in
   Step 3.
3. The two default-riding tests: verified neither asserts a module count or any other
   content-sensitive number — `test_scenario_catalog_matrix.py`'s assertions are at `:158-212`
   (ids, perspective, modifier non-emptiness) and its unoverridden fixture is at `:47-49`;
   `test_scenario_setup_resolver.py`'s fixture is at `:37` and its assertions at `:57-101` are
   structural. `default_perspectives` was measured identical on both sides for all 9 pairs, so
   `_validate_perspective()` (`:97-108`) cannot break. The one thing to check by running it:
   `test_invalid_composition_fails_with_scenario_id` (`:114-121`) asserts on the "not found at …"
   message, whose two paths change.
4. New `tests/unit/scenarios/test_resolver_defaults.py`:
   `test_scenario_setup_resolver_default_compositions_dir_is_data_worlds` (asserts the constant and
   that an unoverridden resolver resolves `frontier_living_world` from
   `data/worlds/frontier_living_world/world.yaml`), and append
   `test_campaign_orchestrator_uses_resolver_default_not_an_override` to the campaign orchestrator
   test — proving the revert happened and was not replaced by a second hard-coded path.

**Do NOT touch:** `CatalogScenarioStateBuilder`'s own signature; the legacy
`build_scenario_state()` / `ArenaInjector` / `V2EngineManager` spawn paths (explicitly out of scope);
`WorldRepository`'s production load path.

**Verify:** `pytest tests/integration/scenarios/ tests/unit/scenarios/ tests/unit/domains/campaigns/test_campaign_orchestrator.py tests/integration/campaigns/ -q`.

---

### Step 10 — Resolve the content-layer path registration (investigation Risks #8)

**Files:** `src/content/paths.py`, `src/content/validator.py`, `src/content/repository.py`,
`tests/unit/content/test_content_paths.py`, `tools/generate_content_inventory.py`,
`tests/tools/test_content_inventory.py`.

**Change:** The decision the planner owes here — **repoint the loader, retire the
`data/content/`-relative path field**:
1. `src/content/paths.py:8`: remove `world_compositions_dir: str = "data/content/world_compositions"`
   and add `world_definitions_dir: str = "data/worlds"`. `ContentPathConfig` documents paths under
   `data/content/` (`:6` `content_root`), and the retired path is no longer one of them. Verified the
   field has exactly two production consumers: `src/content/validator.py:38` and `:153`.
2. `src/content/validator.py:38`: `load_all_compositions(worlds_dir=ContentPathConfig().world_definitions_dir)`,
   and `:153` likewise. This is safe without changing the glob: verified at `:43-58` it globs
   `**/*.yaml` and `**/*.yml` but only appends entries whose `schema_version` contains
   `worldcomposition` (`:46`), so the `resolved/world.resolved.yaml` sidecars (tagged
   `worldspec.v1`) are skipped and the nested `<id>/world.yaml` layout is found.
3. `src/content/repository.py:150`: drop `"world_compositions"` from `NON_CATALOG_DIRS`. That
   frozenset names directories **inside `data/content/`** managed by other loaders; after the
   deletion there is no such directory. It must change in lockstep with
   `tests/unit/content/test_content_paths.py:164-174`, which derives the expected set from
   `ContentPathConfig` basenames — leaving either side alone breaks that invariant test.
4. `tests/unit/content/test_content_paths.py:12`: replace the
   `world_compositions_dir == "data/content/world_compositions"` pin with a
   `world_definitions_dir == "data/worlds"` pin **plus** an explicit assertion that
   `ContentPathConfig` no longer exposes `world_compositions_dir`. Update `:169` to drop the member.
   This file is an intentional anti-drift guard — the change is deliberate and recorded here, not a
   literal edited to go green.
5. `tools/generate_content_inventory.py:91-94`: replace the two counters
   `"World compositions"` = `glob("data/content/world_compositions/*.yaml")` and
   `"World compositions (generated)"` = `glob(".../generated/*.yaml")` with a single
   `"World compositions"` = `glob("data/worlds/*/world.yaml")`. Update
   `tests/tools/test_content_inventory.py:46-49` to match **and to assert a non-zero count** — after
   deletion the old equality would have had `0 == 0` on both sides and passed while measuring
   nothing (the silent-degradation case). Note the tool writes
   `config/content_inventory.json` (`:20`, `:100`) via `make content-inventory`; that generated file
   will show the changed key set on its next regeneration — expected, not a defect.

**Deliberate non-changes, recorded so a later reader does not read them as misses:**
`src/content/matrix.py:550-561` (the `world_compositions` `ContentFamilyMatrixEntry`) and `:637-639`
(`_STRUCTURAL_DIRS`), and `src/content/reference_graph.py:42` — these name a content **family**, not
a filesystem location (`repository_index="None"`, and `file_path` is advisory: verified nothing
resolves it to disk for a structural family, `src/content/matrix.py:682-688` only uses it for
auto-discovered entries). The family survives the move. Also note
`docs/mechanics/content_usage_matrix.md` is **generated** by
`tests/unit/content/test_content_usage_matrix.py::test_generate_and_save_report` (verified: it
writes the file at `:111-120`), so it must never be hand-edited — it regenerates unchanged if
`matrix.py` is left alone.

**Verify:** `pytest tests/unit/content/ tests/integration/content/ tests/tools/test_content_inventory.py -q`.

---

### Step 11 — [BLOCKED on Unresolved Question 1] Give the generator a decided output location (Gap 1 / AC-9)

**Files:** `src/worldgeneration/generator.py`, `src/worldbuilding/cli.py`,
`tests/unit/worldgeneration/test_composition_generator.py`, `docs/world/generator_contract.md`.

**Change:** Verified facts: `src/worldgeneration/generator.py:536-538` does
`output_dir = Path("data/content/world_compositions/generated")`, `mkdir(parents=True,
exist_ok=True)`, then writes `{world_id}.yaml`; the docstring at `:383` declares that path as the
output contract; the **only production caller** is
`src/worldbuilding/cli.py:421-422` (`generator.generate(intent, mod_repo)`), everything else is
tests. `docs/world/generator_contract.md:27` and `:305` state the same path and must change in the
same commit.

Because this is a **single writer** to the retired directory, no ordering/race interaction exists —
but **Step 12 cannot run until this step lands**: a single generation run recreates the directory and
silently re-opens the split.

This step is a **placeholder pending Unresolved Question 1** (where generated worlds land). Both
candidate shapes are fully worked out in `investigation.md` §"Measurement 4"; the implementer must
not pick one. Once decided, the step is: parameterize `generate(..., output_dir: Path | None = None)`
(option D) with the decided default, update `cli.py`'s `generate-composition` call site, update the
docstring at `:383` and the two `generator_contract.md` lines, then:
- replace (not sit beside) the `"generated" in str(output_path)` assertion at
  `tests/unit/worldgeneration/test_composition_generator.py:198` if the chosen shape drops that path
  segment — note it survives today only by accident, because the generated id itself begins with
  `generated_`;
- add `test_generation_run_does_not_create_data_content_world_compositions`, which runs `generate()`
  under `tmp_path` (the file already uses `tmp_path` + `monkeypatch` chdir isolation) and asserts
  `not (tmp_path / "data/content/world_compositions").exists()`. Assert the **absence** explicitly —
  asserting only that the new path exists would pass a "wrote to both" implementation.
- if the decision puts output under `data/worlds/<id>/`, two measured consequences must be handled:
  `WorldRepository.load_world()` raises `WorldRepositoryError` for a composition world with no
  `resolved/world.resolved.yaml` (`src/worldbuilding/repository.py:78-81`), and every generated world
  becomes visible to `list_worlds()` (`:46-61`), so Step 2's guard must key on duplicate definitions
  of one id — never on "a generated world exists".

**Do NOT touch:** `WorldRepository`'s indexer. Option B
(`data/worlds/generated/<id>/world.yaml`) was **measured out** — `list_worlds()` only indexes direct
children, so the nested id is invisible; changing the indexer is a different ticket.

**Verify:** `pytest tests/unit/worldgeneration/ -q`.

---

### Step 12 — Delete `data/content/world_compositions/` and add the absence guard

**Files:** `data/content/world_compositions/` (removed: 7 top-level + `generated/` with 2 files —
re-verified by listing), `tests/architecture/test_world_definition_single_source.py` (extend).

**Change:** `git rm -r data/content/world_compositions/`. Add
`test_catalog_world_compositions_directory_is_absent` asserting
`not Path("data/content/world_compositions").exists()`. Also add
`test_no_test_contradicts_the_authoritative_danger_scale`: scan `tests/` for any `danger_scale`
equality literal and fail if one exists whose value differs from
`data/worlds/dungeon_crawl/world.yaml`'s `scalable_bandit_camp.parameters.danger_scale`. Written that
way it discharges AC-5's "no surviving copy of the `== 2` assertion may reappear in another file"
**and** stays correct whichever order this ticket and
`TCK-20261004-CLOSED-P1-BALANCE-FIX-WRITTEN-TO-NON-RUNNING-WORLD-DEFINITION` land in — a hard-coded
"no `== 2` anywhere" guard would become wrong the moment that ticket sets the authoritative value
to `2`.

**Do NOT touch:** anything under `data/worlds/`. In particular do **not** edit
`data/worlds/dungeon_crawl/world.yaml` and do **not** regenerate any `resolved/` snapshot — see
Scope Guards.

**Verify:** `pytest tests/architecture/test_world_definition_single_source.py -q` now **green**
(guards 1 and 2 at minimum; guard 3 green or its failures filed per Step 2). Re-run Steps 7-10's
commands to confirm nothing depended on the deleted files.

---

### Step 13 — Write the AC-7 measurement-validity assessment

**Files:** `agent-working/tickets/inprogress/TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION.md`
(Completion Summary / Implementation Notes).

**Change:** Bound the sweep so the AC can close honestly (the investigation flags the general case as
unbounded): grep `agent-working/stored_artifacts/` for `world_compositions` and for
`WorldAssemblyResolver`, re-check only the hits, and state the method and its bound in the write-up.
Required content: the one confirmed affected artifact
(`agent-working/stored_artifacts/TCK-20260929-UNREACHABLE-CLASSIFY-NEVER-SEEDED/investigation.md`,
which compiled via `data/content/world_compositions/frontier_living_world.yaml`); the five sibling
`UNREACHABLE-CLASSIFY-*` artifacts as the first sweep; and the two conclusions recorded as
**surviving** — the demographic-cohort truncation finding (its decisive probe used
`load_world_with_context` across 21 worlds) and the camp `STALE-PREMISE` closure (both its modules
present in both definitions of `frontier_living_world`). **Survivals are stated as survivals with
what was re-checked** — silence does not satisfy this AC. Do not re-litigate the two surviving
conclusions.

**Do NOT touch:** the stored artifacts themselves — they are historical records; the assessment is
written in this ticket.

**Verify:** no test; the written section exists and names its own sweep bound.

---

### Step 14 — Parity ledger (AC-10) and the two remaining contract docs

**Files:** `docs/parity_ledger/substrate.yaml`, `docs/parity_ledger/infrastructure.yaml`,
`docs/parity_ledger/faction.yaml`, `docs/content/pipeline_contract.md`.

**Change:**
1. Add **`SUB-394`** to `docs/parity_ledger/substrate.yaml` — re-verified the max existing numeric id
   is `SUB-393`; do **not** extend the legacy `SUBSTRATE-NEW-0NN` series. Entry asserts
   one-`world_id`-one-definition; `test_path` = Step 2's
   `tests/architecture/test_world_definition_single_source.py::test_world_id_resolves_to_exactly_one_definition`
   node id; priority P1; `v2_evidence` cites the ADR §1 amendment and the guard.
2. Update `SUBSTRATE-NEW-010` and `SUBSTRATE-NEW-011` `v2_evidence` for the generator's new output
   location (both describe `ProceduralCompositionGenerator`) — follows Step 11's decision.
3. Review and update where wording changed: `FAC-012` (`faction.yaml`, composition-level
   `faction_tension_overrides` — present only on the running side in 8 of 9 pairs, so the
   reconciliation changes which worlds exercise it), `SUB-390` (the "both real compilation paths"
   framing this ticket collapses), `INFRA-256`/`INFRA-257` (`information_source_profiles` /
   `pending_information_responses`, running-side-only; their `test_path`s include the repointed
   `tests/unit/worldassembly/test_assembly.py`).
4. `INFRA-373` pins `TVD(sandbox_world, dungeon_crawl) == 0.23161981243456373` at seed 42. It
   resolves `dungeon_crawl` through `WorldRepository`, and **this ticket edits no `data/worlds/`
   content**, so it should be untouched — run its test once to confirm, and leave the anchor alone.
   If it moves, that is evidence this ticket touched content it must not have.
5. `docs/content/pipeline_contract.md:34` — the `world_compositions_dir` |
   `data/content/world_compositions/` table row must reflect the retirement.

**Do NOT touch:** `SUBSTRATE-NEW-001` and `INFRA-187` — both are P0 with `test_path: None`, a
pre-existing ledger violation reported by the investigation. Filling them is **not** this ticket's
obligation; note them, do not fix them here. Do not hand-edit `docs/mechanics/content_usage_matrix.md`
(generated — see Step 10). Prefer `parity_ledger_writer.py` over a full-file rewrite and check
`git diff --stat` before committing.

**Verify:** `make parity-index-check`; `pytest tests/unit/rendering/test_variants.py -q` (the
`INFRA-373` tripwire).

---

### Step 15 — Full scoped regression

**Files:** none.

**Change:** Run `test_plan.md`'s five scoped commands plus the new guards, all green:
```
pytest tests/integration/worldassembly/ tests/unit/worldassembly/ -q
pytest tests/integration/scenarios/ -q
pytest tests/unit/content/ tests/integration/content/ tests/tools/test_content_inventory.py -q
pytest tests/unit/worldgeneration/ -q
pytest tests/unit/worldbuilding/ tests/integration/campaigns/ tests/unit/domains/campaigns/test_campaign_orchestrator.py -q
pytest tests/architecture/test_world_definition_single_source.py -q
pytest tests/unit/rendering/test_variants.py -q
```
Never `pytest tests/`.

**Do NOT touch:** nothing. If a test fails, fix the cause; do not relax an assertion to go green.

**Verify:** all seven commands green, plus `git diff` empty over the six out-of-reach test sites.

---

## Scope Guards

Named specifically, from the ticket's Out of Scope and the investigation's anti-drift hazards:

1. **`data/worlds/dungeon_crawl/` is not edited by this ticket.** `danger_scale` and the module set
   are owned by `TCK-20261004-CLOSED-P1-BALANCE-FIX-WRITTEN-TO-NON-RUNNING-WORLD-DEFINITION`. Do not
   carry the catalog's `2` forward as authoritative, do not carry `4` forward as confirmed-correct,
   and do not resolve it with a one-line assertion edit from `2` to `4`.
2. **No `resolved/` snapshot is regenerated as a convenience.** Not for all 24 worlds, not for
   `dungeon_crawl`. That rewrites compiled artifacts for 15 worlds this ticket never touches and
   churns determinism fingerprints across unrelated tests. If Step 2's guard 3 finds a stale or
   non-deterministic projection, **file a finding ticket**.
3. **The six out-of-reach tests in `test_real_content_world_compositions.py`** (`:171`, `:188`,
   `:205`, `:224`, `:265`, `:300`) are byte-unchanged. They build synthetic specs / a synthetic
   `world_id` (`"pack_test_world"`) / generated ids, and the ADR does not reach them.
4. **The directory is not deleted before the generator stops writing to it** (Step 11 → Step 12).
5. **`data/worlds/` is not reorganized.** Option B was measured invisible to `list_worlds()`;
   changing the repository indexer is a different ticket.
6. **ADR §2's `resolved/compile_report.json` vs. the tree's `world_compile_report.json`** naming
   drift stays unfixed — real, pre-existing, out of scope.
7. **The authoritative location is stated exactly once**, in the ADR. Bible 06 and
   `content_authoring.md` cite it and must not restate the path or the freshness mechanics. No new
   Rule under `docs/world_rules/`.
8. **No expansion into `build_scenario_state()` / `ArenaInjector` / `V2EngineManager`** spawn paths,
   and no Campaign entity-spawn logic (closed in
   `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING`).
9. **The two P0 ledger entries with `test_path: None`** (`SUBSTRATE-NEW-001`, `INFRA-187`) are
   reported, not fixed.
10. **The generator's output location is not decided implicitly by whoever edits line 536.**
11. **`docs/archive/`, `docs/audits/`, `docs/brainstorm/`,
    `docs/plans/world_generation_organic_terrain_epic.md`** are frozen historical records — not
    edited, and excluded from the docs guard.
12. **`docs/mechanics/content_usage_matrix.md` is generated**, never hand-edited.
13. Two test-architecture questions are **routed out, not answered here**: whether the repointed
    named-world tests now duplicate existing coverage, and whether the directory-shaped authoritative
    layout should change how they load input. Route to `test-architecture-reviewer`; do not merge or
    move tests on this ticket's authority.

## Dependency Map

- **Step 1 → Step 2** (guard 3 needs the extracted helper).
- **Step 2 must precede any `data/` or test change** — it has to be observed red on the untouched
  tree. This is the rule owner's sequencing advice: run the agreement check across every composition
  world before anything is re-applied.
- **Step 3 → Steps 4, 5, 6** (the ADR sentence must exist before the others cite it and before the
  guard checks for it).
- **Steps 7, 8, 9, 10 are independent of one another** and can be done in any order after Step 2.
- **Step 11 blocked on Unresolved Question 1.** Independent of Steps 7-10.
- **Step 12 depends on Steps 7, 8, 9, 10, 11** — every reader and the single writer must be off the
  directory first.
- **Step 13 independent** (documentation; can run any time after Step 2).
- **Step 14 after Steps 11 and 12** (its `v2_evidence` describes the settled end state).
- **Step 15 last.**

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC-1 — one authoritative source per composition; catalog dir empty/removed | 12 (with 7-11 as prerequisites) | `test_world_id_resolves_to_exactly_one_definition`, `test_no_source_outside_data_worlds_defines_a_known_world_id`, `test_catalog_world_compositions_directory_is_absent` |
| AC-2 — every `ScenarioSetupResolver` caller on the unified layout, verified by a real test | 9 | `test_scenario_setup_resolver_default_compositions_dir_is_data_worlds`, `test_campaign_orchestrator_uses_resolver_default_not_an_override`, `tests/integration/scenarios/`, `tests/integration/campaigns/` |
| AC-3 — ONE recorded evidenced authority decision + explicit `danger_scale` call-out | 13 (recorded in the ticket), 3 (the ADR sentence it rests on) | not testable — prose, grounded in the investigation's three measurements (24/24 valid; 15 running-only vs 0 catalog-only; zero catalog-only keys in 9/9) |
| AC-4 — whole test surface resolved; repoint-or-delete decision recorded with reasoning | 7, 8 (+10 for the content-layer tests) | `pytest tests/integration/worldassembly/ tests/unit/worldassembly/ tests/integration/content/ -q`; `git diff` empty on the six out-of-reach sites |
| AC-5 — `danger_scale`: carry neither value forward; no test/doc asserts either as intended design | 7 (de-assert `:437`/`:452` + docstring), 12 (the contradiction guard) | `test_no_test_contradicts_the_authoritative_danger_scale`; oracle stays `unresolved` for this ticket (correct, not a gap) |
| AC-6 — one `world_id` → one module set, **and** committed `resolved/` equals a fresh resolve; must fail on today's content first | 1, 2 | the three guards in `tests/architecture/test_world_definition_single_source.py`; red run recorded in Implementation Notes as the mandatory negative control |
| AC-7 — written measurement-validity assessment, survivals stated as survivals | 13 | not testable — written section with a stated sweep bound |
| AC-8 — ADR (2 sentences) + Bible 06 invariant + `content_authoring.md` 4 sites, all agreeing | 3, 4, 5 | `test_authoritative_world_location_stated_once` |
| AC-9 — nothing writes into the retired directory; a generation run does not recreate it | 11, 12 | `test_generation_run_does_not_create_data_content_world_compositions`, `test_generator_output_lands_in_the_decided_location` |
| AC-10 — parity ledger entry added/updated with AC-6's check as `test_path` | 14 | `make parity-index-check`; `SUB-394` carries the guard node id |
| (ticket's "full scoped regression" bullet) | 15 | the seven scoped commands |

## Unresolved Questions

**UQ-1 — Where do generated compositions land? (Gap 1, `src/worldgeneration/generator.py:383,536`.)**
This is genuinely undecided and it **blocks Step 11, and therefore Step 12 and AC-1/AC-9**. It cannot
be deferred past the deletion: the directory cannot be removed while the only writer still hard-codes
it, and any default chosen inside `generate()` *is* the decision about where generated worlds land.

The two live candidates (option B is measured out; full analysis in `investigation.md`
§"Measurement 4"):
- **A + D (the investigation's recommendation, and this plan's):** parameterize
  `generate(..., output_dir)` and default to `data/worlds/<world_id>/world.yaml`, adding a
  generated-provenance marker **inside the YAML** rather than in the path. ADR-conformant, no second
  root. Costs: every generated run becomes visible to `WorldRepository.list_worlds()`; a `resolved/`
  sibling must be produced or `load_world()` raises; the
  `"generated" in str(output_path)` assertion at `test_composition_generator.py:198` survives only
  because the id keeps its `generated_` prefix.
- **C:** a separate non-authoritative staging root (e.g. `data/generated_worlds/`) with an explicit
  promote step. Preserves provenance and keeps `data/worlds/` hand-authored, but re-creates a second
  location holding `worldcomposition.v1` files — the exact shape being retired — so it needs an added
  ADR clause scoping "authoritative definition" to promoted worlds, **and** Step 2's guard must
  exempt the staging root.

Steps 1-10 and 13 can proceed while this is open. **The implementer must not choose.**

## Anti-Drift Notes

- The known scope-creep direction on this ticket is *"while I'm in this file"*. The six synthetic
  tests in `test_real_content_world_compositions.py` and `data/worlds/dungeon_crawl/world.yaml` are
  the two places that will feel most tempting and are the two most explicitly forbidden.
- `tests/tools/test_content_inventory.py` **degrades silently**: after deletion both sides of its
  equality become `0` and it passes while asserting nothing. Treat a green there as uninformative
  unless Step 10's non-zero assertion landed.
- `tests/integration/content/test_expansion_gate.py:248` raises **`IndexError`**, not an assertion
  failure, on an empty directory. That symptom means step ordering, not a new bug.
- The direction of this ticket's two biggest corrections is **opposite**: the content work shrank
  from 8 decisions to 1, the test work grew ~4.5x. Do not let the "it's just one decision" framing
  shrink the test and docs work.
- `make world-validate` / `make world-compile` already operate on `data/worlds/` via
  `WorldRepository` (`Makefile:133-140`). In `content_authoring.md` §4, only the file-location
  sentence is wrong — do not "fix" the workflow block.
- The "`data/content/world_compositions/` is the anomaly" wording originates at
  `src/domains/campaigns/orchestrator.py:178`, **not** in the ADR. The conclusion holds on three
  independent grounds; only the citation was wrong. Do not reintroduce the mis-attribution when
  rewriting that comment.
- Finalize note (not an implementation step): a duplicate copy of this ticket still exists at
  `agent-working/tickets/todos/TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION.md`; it must be
  removed before the Verify/done-checker gate, per the folder-cleanup rule.
