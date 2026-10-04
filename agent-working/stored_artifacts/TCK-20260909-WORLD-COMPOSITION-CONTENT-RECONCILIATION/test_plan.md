---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION
artifact_type: test_plan
tags: [architecture, content]
---

# Test Plan — TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION

Level and marker vocabulary: `docs/testing/test_taxonomy.md` §10.

## Regression Surface

### Unit

| file | why it is in the surface |
|---|---|
`tests/unit/worldassembly/test_assembly.py` | `:1058`, `:1079` load `data/content/world_compositions/frontier_living_world.yaml` with `assert comp_path.is_file()`. Both break on deletion. Also the `test_path` for `INFRA-256`/`INFRA-257`. |
`tests/unit/content/test_content_paths.py` | `:12` pins `config.world_compositions_dir == "data/content/world_compositions"` literally; `:169` reuses the basename in an exclusion guard. Any `ContentPathConfig` change lands here first. |
`tests/unit/content/test_content_usage_matrix.py` | mention-level only (`:87`, `:97`, `:397`, structural-folder name set), but `src/content/matrix.py:550-551` is in the change surface, so it must keep passing. |
`tests/unit/worldgeneration/test_composition_generator.py` | Gap 1's guard. `:183-199` asserts `output_path.name == "generated_frontier_3_42.yaml"` **and** `"generated" in str(output_path)`. Already `tmp_path`+`monkeypatch`-isolated. `test_path` for `SUBSTRATE-NEW-010`. |
`tests/unit/worldgeneration/test_seed_params.py` | `:94-95` consumes `gen.generate()`'s returned path. `test_path` for `SUBSTRATE-NEW-011`. |
`tests/unit/worldbuilding/` (14 files) | `WorldRepository`/`WorldCompiler` surface — `repository.py` and the `resolved/` redirect are read (not changed) by this ticket, but `SUB-390`, `FAC-012`, `INFRA-256/257` all name files here. |
`tests/unit/rendering/test_variants.py` | `INFRA-373` pins `TVD(sandbox_world, dungeon_crawl) == 0.23161981243456373` at seed 42. **Only at risk if the `dungeon_crawl` question (investigation Risks #1) is settled by editing `data/worlds/dungeon_crawl/world.yaml`.** |
`tests/unit/domains/campaigns/test_campaign_orchestrator.py` | `src/domains/campaigns/orchestrator.py:173-200` loses its `compositions_dir` override (and gains a fixed ticket citation at `:186`). |
`tests/tools/test_content_inventory.py` | `:46`/`:48` glob the directory. **Will pass vacuously after deletion** (both sides become 0) — treat a green result here as uninformative, not as evidence. |

### Integration

| file | why |
|---|---|
`tests/integration/worldassembly/test_real_content_world_compositions.py` | the core of the change: 7 hard-coded catalog loads, 7 repointed sites, 6 synthetic tests that must be left untouched, and the `danger_scale == 2` assertion at `:452`. |
`tests/integration/worldassembly/test_e2e_smoke.py` | `:56`/`:76` loader helpers, used by 4 tests. Not covered by the rule owner's repoint ruling (investigation Risks #5) — needs an explicit decision before it can be made to pass. |
`tests/integration/scenarios/test_scenario_catalog_matrix.py` | module-scoped `resolver` fixture at `:49` constructs `ScenarioSetupResolver(catalog, module_repo)` with **no** `compositions_dir`, so it rides the default. All 8 matrix scenarios use `frontier_living_world` (×7) or `frontier_extended` (×1). |
`tests/integration/scenarios/test_scenario_setup_resolver.py` | same unoverridden fixture at `:37`; `_frontier_scenario()` defaults to `frontier_living_world` + `hero_guild_perspective`. |
`tests/integration/scenarios/test_content_foundation.py` | mention-level (reads the `world_composition` *field* on scenario YAMLs, never the directory) — in the surface because the scenario→composition id mapping must still resolve. |
`tests/integration/content/test_expansion_gate.py` | Gate 08 (`:181-196`) globs the directory; Gate 11 (`:248`) does `sorted(glob("*.yaml"))[0]` and raises **`IndexError`** on an empty dir. |
`tests/integration/content/test_swamp_border_pack.py` | `:93` asserts each `manifest.sample_compositions` id exists at `data/content/world_compositions/<cid>.yaml`. |
`tests/integration/campaigns/` (11 files) | the only real production consumer of `ScenarioSetupResolver`/`CatalogScenarioStateBuilder`. |

### Arena-combat

None. No arena or combat-resolution test reads a world composition path; the change surface is
world definition/assembly only. Stated explicitly rather than omitted.

---

## New Tests Required

### AC-1 / AC-2 — one authoritative source, every caller on the unified layout

- **`test_scenario_setup_resolver_default_compositions_dir_is_data_worlds`** — unit,
  `tests/unit/scenarios/test_resolver_defaults.py` (new file; no `tests/unit/scenarios/` resolver
  test exists today). Asserts `ScenarioSetupResolver._DEFAULT_COMPOSITIONS_DIR ==
  Path("data/worlds")` and that a resolver built with no `compositions_dir` resolves
  `frontier_living_world` to `data/worlds/frontier_living_world/world.yaml`.
- **`test_campaign_orchestrator_uses_resolver_default_not_an_override`** — unit, append to
  `tests/unit/domains/campaigns/test_campaign_orchestrator.py`. Proves the revert at
  `src/domains/campaigns/orchestrator.py:173-200` happened and was not replaced by a second
  hard-coded path.
- **`test_catalog_world_compositions_directory_is_absent`** — architecture guard,
  `tests/architecture/test_world_definition_single_source.py` (new). Asserts
  `not Path("data/content/world_compositions").exists()`.

### AC-6 / AC-10 — the one-`world_id`-one-definition check

- **`test_world_id_resolves_to_exactly_one_definition`** — architecture guard, same new file
  `tests/architecture/test_world_definition_single_source.py`. Scans the repo for any
  `schema_version: worldcomposition.v1` YAML outside `data/worlds/<id>/world.yaml` and fails naming
  each offender. **This is the node id AC-10 records as `SUB-394`'s `test_path`.** It must be
  written so that it fails on today's tree (8 of 9 pairs diverge today;
  `simq_scale_stress_seed42` is byte-identical and would pass a module-set-only check, so the guard
  must key on *existence of a second definition*, not on difference — otherwise it proves nothing
  for that pair).
- **`test_no_source_outside_data_worlds_defines_a_known_world_id`** — architecture guard, same
  file. The complement: for every id in `WorldRepository("data/worlds").list_worlds()`, no other
  path in the tree declares that `world_id` with a composition schema.

### AC-9 — the generator does not recreate the directory

- **`test_generator_output_lands_in_the_decided_location`** — unit, extend
  `tests/unit/worldgeneration/test_composition_generator.py`. Must replace, not sit beside,
  `:183-199`'s `"generated" in str(output_path)` assertion if the chosen option drops that path
  segment.
- **`test_generation_run_does_not_create_data_content_world_compositions`** — unit, same file.
  Runs `generate()` under `tmp_path` and asserts `not (tmp_path / "data/content/world_compositions").exists()`.
  This is the one that directly discharges AC-9.

### AC-4 / AC-5 — the repointed named-world tests

- Repoint the 7 sites in `tests/integration/worldassembly/test_real_content_world_compositions.py`
  to `data/worlds/<id>/world.yaml` and update the measured expectations:
  `:52` `6`→`7`, `:112` `6`→`7`, `:374` `len(spec.module_refs) 3`→`4`, `:437` `2`→`4`.
- **`test_real_world_compositions_normalization` must be redesigned, not repointed** — its
  `ref.order == 0` loop (`:54-56`) contradicts the running file's explicit `order: 0..6`, and its
  subject (shorthand-`modules:` conversion) does not exist on the running side. Either rename it to
  a `module_refs`-form normalization test with new assertions, or keep a synthetic shorthand fixture
  and say so in a comment.
- **`:452`'s `danger_scale` assertion is blocked** — see Proof Plan AC5. Do not edit it from `2` to
  `4` as a mechanical repoint.
- **`test_no_test_asserts_danger_scale_equals_two`** — architecture guard, same new architecture
  file. Greps `tests/` for a `danger_scale` `== 2` assertion on `scalable_bandit_camp` and fails if
  one exists anywhere. This is what makes AC-5's "no surviving copy may reappear in another file"
  checkable rather than a promise.

### AC-7 — the measurement-validity assessment

Not a test. A written section in the ticket's Completion Summary. The tractable mechanical aid is a
one-off grep of `agent-working/stored_artifacts/` for `world_compositions` and
`WorldAssemblyResolver`; only hits get re-checked, and survivals are recorded as survivals.

### AC-8 — docs agreement

- **`test_authoritative_world_location_stated_once`** — architecture guard, same new file. Asserts
  the normative "sole authoritative definition" sentence appears in
  `docs/architecture/world_repository_layout.md` and that neither
  `docs/mechanics/06_worldbuilding_foundation.md` nor `docs/guides/content_authoring.md` restates
  the path without citing the ADR, and that no doc under `docs/guides/` still presents
  `data/content/world_compositions/<world_id>.yaml` as an authoring target.

---

## Proof Plan

### AC1 — every composition has exactly one authoritative source; the catalog directory is gone
- **level**: architecture guard
- **proof kind**: invariant
- **oracle source**: `docs/architecture/world_repository_layout.md` §1 (as amended by AC-8) +
  parity `docs/parity_ledger/substrate.yaml::SUB-394` (new)
- **expected effect**: no `worldcomposition.v1` YAML exists outside `data/worlds/<id>/world.yaml`;
  `data/content/world_compositions/` does not exist
- **selected commands**: `pytest tests/architecture/test_world_definition_single_source.py -q`
- **negative cases**: a planted second definition under `data/content/` fails the guard; a planted
  `data/worlds/x/world.yaml` with a duplicate `world_id` of another directory fails it
- **fixtures**: none — the guard reads the real tree, which is the point

### AC2 — every `ScenarioSetupResolver` caller uses the unified layout
- **level**: unit + integration
- **proof kind**: regression
- **oracle source**: ADR §1 + `docs/parity_ledger/substrate.yaml::SUBSTRATE-NEW-004` (perspective
  resolution through the composition, unaffected — measured identical `default_perspectives` on
  both sides for all 9 pairs)
- **expected effect**: the unoverridden default resolves `frontier_living_world` from
  `data/worlds/`; `CampaignOrchestrator` passes no `compositions_dir`; all 8 matrix scenarios still
  resolve and still produce setup modifiers
- **selected commands**: `pytest tests/integration/scenarios/ tests/unit/scenarios/ tests/unit/domains/campaigns/test_campaign_orchestrator.py -q`
- **fixtures**: reuse the existing module-scoped `catalog`/`module_repo` fixtures in
  `test_scenario_catalog_matrix.py:38-47` — do not add new repository fixtures

### AC3 — one recorded, evidenced authoritative-source decision
- **level**: none (documentation)
- **proof kind**: not testable
- **oracle source**: n/a — this AC is satisfied by prose in the ticket, grounded in the
  investigation's three independent measurements (24/24 `data/worlds` specs valid; 15 running-only
  vs 0 catalog-only ids; zero catalog-only keys in all 9 pairs)
- **expected effect**: the ticket records one decision plus the explicit `danger_scale` call-out
- **selected commands**: none

### AC4 — the full test surface is resolved, with the repoint decision recorded
- **level**: integration
- **proof kind**: regression
- **oracle source**: ADR §1 + §3 (backwards compatibility: tests loading
  `data/worlds/<id>/world.yaml` must remain supported)
- **expected effect**: the 7 named-world sites load from `data/worlds/`; the 6 synthetic tests
  (`:171`, `:188`, `:205`, `:224`, `:265`, `:300`) are byte-unchanged; the whole file passes
- **selected commands**: `pytest tests/integration/worldassembly/ tests/unit/worldassembly/ -q`
- **negative cases**: `git diff` on the six out-of-reach sites must be empty — a scope guard, not an
  assertion
- **non-functional risk**: `test_real_world_compositions_normalization` cannot be repointed
  mechanically (see New Tests Required); a green run achieved by weakening its assertions would be
  a false pass

### AC5 — the `dungeon_crawl` `danger_scale` resolution
- **level**: integration
- **proof kind**: differential
- **oracle source**: **`oracle: unresolved`** — see investigation Risks #1 and #2. The ADR governs
  *location*, not content; the rule owner declined to add a catalog Rule; the only document stating
  an intended value is `agent-working/tickets/done/TCK-20260627-P1I-WORLD-BALANCE-FIX.md`, which
  states `2` with measured evidence (D08: 94-97% attrition; fix target ≤12 entities). Measured
  here: catalog = 12 entities / 2 regions / 5 quests, running = 32 entities / 4 regions / 9 quests.
  **Do not write this test until the decision in Risks #1 is made.**
- **expected effect**: whichever value is chosen, exactly one `danger_scale` expectation exists in
  `tests/` and it matches `data/worlds/dungeon_crawl/world.yaml`
- **selected commands**: `pytest tests/integration/worldassembly/test_real_content_world_compositions.py -q -k dungeon_crawl`
  then `pytest tests/architecture/test_world_definition_single_source.py -q -k danger_scale`
- **negative cases**: a `== 2` assertion planted in any other test file must fail the architecture
  guard — this is the explicit "deleting the test must not quietly relocate the wrong expectation"
  protection
- **non-functional risk**: if `4` is kept, `dungeon_crawl` remains a 32-entity world that D08
  measured at 94-97% attrition, which will degrade any later SimQ/rule-map slice that samples it

### AC6 — full scoped regression across every consumer
- **level**: integration
- **proof kind**: regression
- **oracle source**: `docs/parity_ledger/infrastructure.yaml::INFRA-187` (the WorldAssembly
  pipeline, P0 — note its `test_path` is `None` today, a pre-existing gap) +
  `substrate.yaml::SUBSTRATE-NEW-001`
- **expected effect**: no new failures across worldassembly, worldbuilding, scenarios, content,
  campaigns, worldgeneration
- **selected commands**: the five scoped commands below, all five green

### AC7 — the one-`world_id`-one-module-set check fails on today's content
- **level**: architecture guard
- **proof kind**: invariant (with a pre-fix negative control)
- **oracle source**: `docs/mechanics/06_worldbuilding_foundation.md` §7 (Level 2 structural, ERROR
  severity) + `docs/parity_ledger/substrate.yaml::SUB-394` (new)
- **expected effect**: on the pre-reconciliation tree the guard fails and names the offending ids;
  after reconciliation it passes with nothing to find
- **selected commands**: `pytest tests/architecture/test_world_definition_single_source.py -q`
- **negative cases**: **mandatory positive control** — run the guard on a stashed/`git worktree`
  copy of the pre-change tree and record that it failed, naming the pairs. A guard that was never
  observed red proves nothing (AC-6's own wording).
- **non-functional risk**: must not fire on a future generated world landing in `data/worlds/`
  (Gap 1 option A) — the guard keys on duplicate definitions of one id, not on the existence of
  generated worlds

### AC8 — the measurement-validity assessment (merged AC-7)
- **level**: none (documentation)
- **proof kind**: not testable
- **oracle source**: n/a
- **expected effect**: a written list of re-checked prior conclusions, survivals stated as
  survivals. Known-affected:
  `agent-working/stored_artifacts/TCK-20260929-UNREACHABLE-CLASSIFY-NEVER-SEEDED/investigation.md`.
  Known-surviving (per the ticket, do not re-litigate): the demographic-cohort truncation finding
  and the camp `STALE-PREMISE` closure.
- **selected commands**: none

### AC9 — the three docs agree (merged AC-8)
- **level**: architecture guard
- **proof kind**: architecture guard
- **oracle source**: the rule-layer ruling recorded in the ticket (ADR = the one normative
  sentence; Bible 06 = integrity invariant citing the ADR; `content_authoring.md` = corrected path
  + link)
- **expected effect**: the sentence exists once, in the ADR; the other two cite it; no guide still
  teaches `data/content/world_compositions/<world_id>.yaml`
- **selected commands**: `pytest tests/architecture/test_world_definition_single_source.py -q -k docs`
- **negative cases**: a restatement of the path in Bible 06 fails the guard (enforces "define
  information once")

### AC10 — no code path writes into the retired directory (Gap 1)
- **level**: unit
- **proof kind**: regression
- **oracle source**: ADR §2 (resolved artifacts separated from source) +
  `docs/parity_ledger/substrate.yaml::SUBSTRATE-NEW-010`/`SUBSTRATE-NEW-011` (both must have
  `v2_evidence` updated)
- **expected effect**: a `generate()` call creates no `data/content/world_compositions/` anywhere,
  and its output lands at the decided location
- **selected commands**: `pytest tests/unit/worldgeneration/ -q`
- **negative cases**: assert the absence explicitly under `tmp_path`, not merely that the new path
  exists — "wrote to both" would otherwise pass
- **non-functional risk**: if option A is chosen, a generated world in `data/worlds/` must still
  satisfy `WorldRepository.load_world()`, which raises `WorldRepositoryError` for a composition
  world with no `resolved/world.resolved.yaml`

### AC11 — the parity ledger entry (AC-10 in the ticket)
- **level**: none (ledger)
- **proof kind**: not testable by pytest
- **oracle source**: `docs/parity_ledger/schema.json`
- **expected effect**: `SUB-394` added to `docs/parity_ledger/substrate.yaml` with
  `test_path` = the AC-7 guard node id; `SUBSTRATE-NEW-010`/`-011` `v2_evidence` updated;
  `FAC-012` reviewed (`faction_tension_overrides` is running-side-only in 8 of 9 pairs)
- **selected commands**: `make parity-index-check`

---

## Scoped Pytest Commands

Never `pytest tests/`. Run these five, scoped to the affected domains:

```bash
# 1. the core change — assembly and the repointed named-world tests
pytest tests/integration/worldassembly/ tests/unit/worldassembly/ -q

# 2. the two default-riding tests and the scenario resolution surface
pytest tests/integration/scenarios/ -q -m scenario_setup
pytest tests/integration/scenarios/ -q          # the rest of the directory, unmarked

# 3. content paths, usage matrix, packs, expansion gate, inventory tool
pytest tests/unit/content/ tests/integration/content/ tests/tools/test_content_inventory.py -q

# 4. Gap 1 — the generator's output location
pytest tests/unit/worldgeneration/ -q

# 5. the production load path and the only real consumer
pytest tests/unit/worldbuilding/ tests/integration/campaigns/ \
       tests/unit/domains/campaigns/test_campaign_orchestrator.py -q

# conditional — ONLY if data/worlds/dungeon_crawl/world.yaml is edited (Risks #1/#9)
pytest tests/unit/rendering/test_variants.py -q   # INFRA-373's pinned TVD anchor

# new guards
pytest tests/architecture/test_world_definition_single_source.py -q
```

Parity: `make parity-index-check`.

---

## Anti-Drift Test Guards

- **`test_no_test_asserts_danger_scale_equals_two`** — the AC-5 relocation guard. The single most
  important new guard: it is what prevents the wrong expectation from migrating to a sibling file
  when a test is deleted or rewritten.
- **`test_catalog_world_compositions_directory_is_absent`** + **the generator's
  "does-not-recreate" test** — together they close the regrowth loop. Either alone is insufficient:
  the directory check passes right up until a generation run, and the generator check passes even
  if someone re-adds the directory by hand.
- **Byte-unchanged check on the six out-of-reach tests** (`test_real_content_world_compositions.py`
  `:171`, `:188`, `:205`, `:224`, `:265`, `:300`) — a `git diff` scope guard in the plan, not a
  pytest assertion. The known scope-creep direction on this ticket is "while I'm in this file".
- **`test_authoritative_world_location_stated_once`** — catches the "write the location in three
  docs" drift the rule owner explicitly ruled against.
- **`tests/unit/content/test_content_paths.py:12`** is already an anti-drift guard for
  `ContentPathConfig`. Whatever the planner decides about `world_compositions_dir` (remove it, or
  leave it pointing at nothing — investigation Risks #8), this test must be updated deliberately
  and the choice stated; changing the literal to make it green without stating the choice is the
  failure mode.
- **`tests/unit/rendering/test_variants.py`'s `INFRA-373` anchor** is an unintentional but effective
  tripwire for a silent `dungeon_crawl` content change. Keep it in the conditional command set
  rather than removing it.
- **Treat `tests/tools/test_content_inventory.py` green as uninformative** after the deletion —
  both sides of its equality become 0. If the inventory counters survive, they must be repointed
  and the test must assert a non-zero count; otherwise remove counters and test together.
- **`tests/integration/content/test_expansion_gate.py` Gate 11 (`:248`) raises `IndexError`, not an
  assertion failure,** on an empty directory. If a run reports `IndexError` there, it is this
  ticket's ordering (deletion before test update), not an unrelated bug.
