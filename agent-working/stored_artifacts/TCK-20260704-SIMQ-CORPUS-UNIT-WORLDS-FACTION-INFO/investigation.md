---
status: draft
layer: simulation
authority: P1
audience: agent
artifact_type: investigation
tags: [simulation-quality, world, faction, information, corpus, calibration]
---

# Investigation — TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO

PHASE_TS: 2026-07-06T17:47:46Z

## Context search performed (per CLAUDE.md hard rule)

1. `mcp__knowledge-search__search_docs` (query: "unit-tier world authoring FACTION tension
   INFORMATION source profiles world composition wilderness_survival sandbox_world") — surfaced
   `docs/simulation_quality/corpus_tier_taxonomy.md`, `docs/simulation_quality/eval_matrix_results.md`,
   `docs/audits/D08_multi_scenario.md` (world inventory), `TCK-20260630-WORLD-DEPLOY-MODULES`
   (unwired module inventory) as the primary prior-work trail.
2. `graphify query "world composition authoring faction_tension_overrides
   information_source_profiles WorldCompiler resolve compile"` — 2755-node BFS confirmed the
   schema/state backbone (`WorldSpec`, `WorldCompositionSpec`/`NormalizedWorldComposition`,
   `WorldAssemblyResolver`, `FactionState`, `Faction` enum, `InformationProviderState`,
   `WorldRepository`) as the structural surface this ticket touches — matches the doc trail, no
   contradicting edge found.

Both tools confirmed the same picture the ticket body gives; raw grep/Read used only as follow-up,
per the Hard Rules.

## Path correction (ticket cites a stale path)

The ticket's "Related Docs"/"Request Summary" cite
`staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md`. That folder was
renamed to `staging_artifacts/TCK-20260704-SIMQ-CORPUS-TIERS-EPIC/` once the epic ticket ID was
minted (confirmed: the renamed file's own header states this explicitly, and
`EPIC-SCOPE-full-feature-world-coverage` no longer exists under `staging_artifacts/`). All
citations below use the current path.

---

## 1. World-authoring mechanism — composition YAML, not a generator, for these two worlds

There is no "new world" generator/wizard beyond hand-authoring a `world.yaml` **composition**
file (`schema_version: "worldcomposition.v1"`, validated by `WorldCompositionSpec`,
`src/worldassembly/schema.py:21-95`). A separate procedural generator exists
(`src/worldgeneration/generator.py`, driven by `GenerationIntentSpec` + `cli.py generate`,
producing `generated_frontier_3_42`) but it is for procedurally-varied stress-scale worlds, not
minimal hand-authored unit-tier isolation worlds — not the right tool here (confirmed via
`cli.py`'s `handle_generate`, which takes a `GenerationIntentSpec`, not a hand-picked module list).

**Simplest composition shape, confirmed from the two reference worlds:**

- `wilderness_survival/world.yaml` (11 entities, 4 regions) — `module_refs:` (structured form,
  each with `order`), plus `global_parameters.topology_width/height` explicitly set. No
  `entities`/`regions`/`factions` authored directly — everything comes from 4 modules
  (`forest_deep_ecology`, `wolf_den_near_forest`, `undead_battlefield`, `survivor_camp_shelter`).
- `sandbox_world/world.yaml` (18 entities, 3 regions) — even simpler: uses the `modules:`
  **shorthand** (a bare list of module-id strings), no `global_parameters`, no explicit topology.
  `WorldCompositionSpec.normalize_modules_shorthand` (a `model_validator(mode="before")`) rewrites
  `modules: [...]` into `module_refs: [{module_id, enabled: true, order: 0}, ...]` before
  validation — the two are mutually exclusive (specifying both raises `ValueError`) but produce
  an identical result. `sandbox_world` composes exactly two modules:
  `frontier_village_core` + `wolf_den_near_forest`.

**Required minimum fields for a new `worldcomposition.v1` file** (all confirmed via
`WorldCompositionSpec`, `src/worldassembly/schema.py:21-45`): `schema_version` (literal
`"worldcomposition.v1"`), `world_id`, `name`, and either `modules:` (shorthand) or `module_refs:`
(structured). `generation_seed` defaults to `42` if omitted (both example worlds set it
explicitly to avoid collision with other worlds using the same seed value as a *world* id, not a
technical requirement — the seed is per-composition, no dedup enforced). Everything else
(`topology`, `regions`, `factions`, `entities`, quest defs, resource nodes, buildings) is either
auto-computed by `WorldAssemblyResolver.assemble()` from the referenced modules' own region
bounds (topology auto-fits to the union of all region bounds — confirmed:
`sandbox_world/resolved/world.resolved.yaml` topology is `106x100`, `urban_political`'s is
`101x100`, neither was authored in the composition file) or pre-seeded from the full faction
catalog (all 16 factions always populate `state.factions`, confirmed in
`stored_artifacts/TCK-20260702-SIMQ-UPLIFT2-FACTION/plan.md`'s opening correction).

**Conclusion:** the two new unit-tier worlds should use the `modules:` shorthand form (mirrors
`sandbox_world`, the simplest precedent), listing 1-2 already-catalog-registered modules, plus the
Pattern-6 fields (`faction_tension_overrides` for World A; `information_source_profiles` +
`pending_information_responses` for World B) added directly on the composition — exactly as
`urban_political/world.yaml` does today (it also uses zero hand-authored `regions`/`entities`,
only `module_refs` + the four Pattern-6-adjacent composition-level fields).

---

## 2. Faction IDs for World A (FACTION isolation)

**Decision: reuse `sandbox_world`'s exact module pair — `frontier_village_core` +
`wolf_den_near_forest` — and override tension on `town_council` and `merchant_league`.**

Evidence:
- `frontier_village_core.yaml` declares `factions: ["town_council", "merchant_league"]` and
  `populations: ["frontier_village_population"]`. Both `town_council` (`data/content/social/
  factions.yaml:12`) and `merchant_league` (`:54`) are catalog-registered, real faction IDs — not
  invented. `investigation.md` §2 of the epic (via `sandbox_world`'s own populated-faction row)
  independently confirms these two (plus `wild_beast_pack`) are the three factions actually
  assigned to populations when this exact module pair is composed.
- `wolf_den_near_forest.yaml` contributes `wild_beast_pack` (not touched by the override — stays
  at catalog default `0.0`, keeping the isolation clean: only 2 of the 3 populated factions get a
  non-zero override, matching the ticket's ">= 2 non-zero entries" AC without touching every
  faction present).
- This pairing is a **zero-novel-risk reuse**: `sandbox_world` (the exact same module
  composition) is already a committed, anchored regression-tier world with grade history through
  2000 ticks (`sandbox_world_seed42_2000t` in `grade_anchors.json`) — proving this composition is
  population-stable at every tick depth this ticket cares about (200-300t), with zero hazard-kind
  risk (`wolf_den_near_forest`'s two regions already declare `hazard_kind: "NATURAL_TERRAIN"`, and
  `wild_beast_pack` already declares matching `hazard_immunities` — both fixed under
  `TCK-20260701-HAZARD-NATIVE-IMMUNITY`, confirmed present in the live YAML). Reusing it verbatim
  (same modules, new `world_id`, new seed, plus the tension override) inherits that proof instead
  of re-deriving it.
- Values: `town_council: 0.5`, `merchant_league: 0.5` — mirrors `urban_political`'s exact
  `bandit_company: 0.5` / `town_council: 0.5` shape and clears the same `>0.4` NEUTRAL→TENSE
  threshold with margin (per `compute_transitions()`'s `pair_tension = max(fa.tension_level,
  fb.tension_level)` proxy) without crossing `>0.7` TENSE→HOSTILE — same "clean signal, no
  cascade" property `TCK-20260702-SIMQ-UPLIFT2-FACTION`'s plan chose deliberately.

Entity count for this composition (from `sandbox_world/world_compile_report.json`, since it is
byte-for-byte the same module set): **18 entities, 3 regions** — squarely inside the
"11-18 entities" unit-tier scale band the ticket names.

---

## 3. `information_source_profiles` / `pending_information_responses` shape for World B

Read directly from `urban_political/world.yaml` (not the epic investigation's paraphrase):

```yaml
information_source_profiles:
  - source_id: "town_notice_board"
    source_kind: "guide"
    knowledge_scopes: ["regional_danger", "common_resource_sources"]
    accuracy: 0.4
    freshness: 0.6
    bias: 0.1
    cost_gold: 0
    max_answers_per_query: 2
pending_information_responses:
  - target_population_id: "pop_0"
    subject: "bandit_road_danger"
    query_kind: "danger_rating"
    source_id: "town_notice_board"
    answer_kind: "KNOWN_FACT"
    certainty: 0.8
    details:
      danger_level: "elevated"
      region: "bandit_road"
    cost_paid: 0
```

Field-level confirmation against `src/worldbuilding/schema.py`:
- `InformationSourceProfileSpec` (`:57-72`): `source_id` (free string — looked up via
  `state.entities.get(source_id)` for a proximity cost; a non-entity string like
  `"town_notice_board"` is valid and simply yields `dist_cost=0.0`), `source_kind` is a **closed
  Literal** (`"guide"|"guild"|"blacksmith"|"traveler"` — no new kinds allowed),
  `knowledge_scopes` free-form list, `accuracy`/`freshness` in `[0,1]`, `bias` unconstrained,
  `cost_gold >= 0`, `max_answers_per_query >= 1`.
- `PendingInformationResponseSpec` (`:75-96`): `target_population_id` is **not** a raw entity ID —
  it is matched at compile time against each compiled entity's `properties["population_id"]`
  (`src/worldbuilding/compiler.py:317`, `:428-439`). `answer_kind` is a closed Literal
  (`KNOWN_FACT|PARTIAL_LEAD|RUMOR|CONTRADICTION` — `UNKNOWN` deliberately excluded, produces no
  `KnowledgeFact`). `subject`/`query_kind`/`source_id`/`details` are free-form strings/dict, not
  validated against any catalog — synthetic values are fine per the unit-tier philosophy.

**Where does `"pop_0"` come from?** This is the load-bearing discovery of this investigation.
`PopulationSpec.id` is a **required** field (`schema.py:147`) for every named population (e.g.
`frontier_village_population_village_worker`) — so the compiler's fallback
`pop_key = getattr(pop_spec, "id", f"pop_{pop_idx}")` (`compiler.py:286`) never actually triggers
for named populations; `pop_key` is always the real, human-readable id. `"pop_0"`/`"pop_1"`
appear only because **`hero_adventurers.yaml`** (the module urban_political also composes)
authors its populations as inline `population_recipes:` entries with **no `id` field at all**
(3 bare `{role: "hero", count: 1, faction: "hero_guild", spawn_region: "hometown"}` recipes) — a
different, module-level field (`WorldModuleSpec.population_recipes`, distinct from the
named-population `populations: [...]` list `frontier_village_core`/`wolf_den_near_forest` use).
The resolver's merge step for these un-ided recipes
(`src/worldassembly/resolver.py:452-453`: `pop_id = f"{prefix}{getattr(pop, 'id', f'pop_{pop_idx}')}"`)
falls back to positional `pop_0`, `pop_1`, `pop_2` — confirmed by grep: `urban_political/
resolved/world.resolved.yaml` has an `entities:` block with a literal `id: pop_0` (and `pop_1`),
sourced from exactly these 3 hero recipes.

**Consequence for World B's authoring:** to get an addressable `pop_0`-style population without
inventing new catalog content, **compose `hero_adventurers` into World B** (mirrors
`urban_political`'s own mechanism for the identical field, verbatim) — this is the only
already-existing module in the catalog that produces this addressing shape "for free."
`hero_adventurers` is a small module (3 `hero_guild` entities, no regions of its own — spawns into
`hometown`, which must be provided by another module in the same composition, e.g.
`frontier_village_core`).

---

## 4. Exact compile/resolve command sequence

Confirmed against `stored_artifacts/TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS/plan.md` Step 2 and
`src/worldbuilding/cli.py`'s `handle_resolve`/`handle_compile`:

```bash
python3 -m src.worldbuilding.cli resolve <world_id>
python3 -m src.worldbuilding.cli compile <world_id> --seed <seed> --from-resolved
```

`resolve` reads `data/worlds/<world_id>/world.yaml`, runs it through
`WorldAssemblyResolver.assemble()`, and writes the 5 standard sidecar files under
`data/worlds/<world_id>/resolved/`: `world.resolved.yaml`, `compile_context.json`,
`provenance_manifest.json`, `assembly_report.json`, `validation_report.json`. `compile
--from-resolved` then loads `resolved/world.resolved.yaml` + `compile_context.json`, runs
`WorldValidator.validate()` (abort on `ERROR`; abort on `WARNING` too only if `--strict` is also
passed — it is not part of this ticket's command), then `WorldCompiler.compile()`, writing
`data/worlds/<world_id>/world_compile_report.json`.

**"0 warnings" means:** `world_compile_report.json`'s `"warnings"` array (confirmed shape via
`wilderness_survival/world_compile_report.json`: `"warnings": []` today) is empty. `handle_compile`
prints any non-empty warnings to stdout in yellow but does not fail the run unless `--strict` is
passed (only `ERROR`-severity issues from `WorldValidator.validate()` abort the compile
unconditionally). AC-level "0 warnings" is therefore a post-compile inspection of this JSON
array, not a flag — no `--strict` needed for these two worlds' compile step, but the report must
still show `warnings: []` after compiling.

**`world_index.json`:** neither `resolve` nor `compile` touches `data/worlds/world_index.json` —
only `save_world()` (used by `create-template`/`generate`) and `handle_list`'s `rebuild_index()`
update it (`src/worldbuilding/repository.py:88-165, 166+`). `rebuild_index()` scans every
subdirectory under `data/worlds/` for a `world.yaml` and rewrites the index from scratch, so
running `python3 -m src.worldbuilding.cli list` once after authoring both `world.yaml` files
picks them up automatically — this is the one bookkeeping step precedent
(`TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS`'s own test_plan.md Regression Surface) explicitly
calls out ("`world_index.json` — must be updated if new world directories are added").

**Calibration:**
```bash
python3 tools/calibrate_simq.py --ticks 200 --seed 42  --name <world_id>
python3 tools/calibrate_simq.py --ticks 200 --seed 123 --name <world_id>
python3 tools/calibrate_simq.py --ticks 200 --seed 456 --name <world_id>
```
`tools/calibrate_simq.py`'s `_resolve_profile(name)` (`:32-41`) uses a profile file named
`config/simulation_quality/profiles/<name>.yaml` **if it exists**, else `"default"` — matching by
world name automatically, no `--profile` flag needed as long as the profile file's name equals
the `--name` value (confirmed: `dungeon_crawl`'s calibration command in the same plan explicitly
passes `--profile dungeon_crawl` only because the world name and profile file already coincide;
same auto-match applies here). **World A needs no profile file at all** — baseline OFF for every
flag is exactly what `_resolve_profile` falls back to (`"default"`) when no matching file exists,
so its `world.yaml`'s absence of a profile is itself the correct authoring choice (not an
omission to fix). **World B needs one** (`config/simulation_quality/profiles/<world_b_name>.yaml`)
with a `feature_flags: {ENABLE_BELIEF_ASSIMILATION: "ON"}` block, mirroring
`config/simulation_quality/profiles/urban_political.yaml`'s shape (that file additionally sets
`pillar_weights` and `ENABLE_SOCIAL_COOPERATION` — neither is required here; only the one flag
this ticket's AC calls for).

**Important scoring-mechanism clarification (de-risks AC6):** `pillar_weights` in a profile YAML
(e.g. `urban_political.yaml`'s `FACTION: 1.5`) affects only a composite/overall weighting, not
whether an individual pillar's own letter grade moves off `C` — `FactionScorer`/
`InformationScorer` (`src/simulation_quality/scorers/faction.py`, sibling `information.py`) score
named event types (`diplomatic_transition`, `faction_tension_delta`, `belief_assimilated`, ...)
independent of any `pillar_weights` entry. `urban_political`'s FACTION/INFORMATION grades moved
off `C` purely from the tension-override / profile-seed **content**, not from the `pillar_weights`
block. World A therefore needs zero profile changes to show a non-`C` FACTION grade.

---

## 5. Anchor-adding mechanism

Confirmed via `tests/simulation_quality/fixtures/grade_anchors.json` (43 entries today) and
`tests/simulation_quality/test_grade_regression.py`'s `FAST_ANCHOR_KEYS` (`:41-75`): each entry is
keyed `<world_id>_seed<seed>_<ticks>t` (e.g. `wilderness_survival_seed42_200t`) mapping to a
10-pillar `{PILLAR: grade}` dict, extracted verbatim from
`data/calibration/<run_key>/quality_report.json`'s `pillars.*.grade` fields. Adding a new world's
anchors means: (1) run the 3-seed calibration commands above, (2) read each
`quality_report.json`, (3) add 3 new keys to `grade_anchors.json` with the exact 10-pillar dict,
(4) add the same 3 key strings to `FAST_ANCHOR_KEYS` (not `SLOW_ANCHOR_KEYS` — these are 200t
fast-tier runs, matching the precedent set by the 5 worlds `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS`
added, e.g. `wilderness_survival_seed{42,123,456}_200t`). This ticket adds **6 new fast-anchor
entries total** (2 worlds × 3 seeds), following that exact precedent (15 entries for 5 worlds ==
3 per world).

---

## 6. Proposed world names — no collision

`data/worlds/world_index.json` and a directory listing both confirm the existing 10 world IDs:
`urban_political`, `highland_traverse`, `dungeon_crawl`, `simq_routing_test`, `frontier_extended`,
`frontier_living_world`, `swamp_border_world`, `generated_frontier_3_42`, `sandbox_world`,
`wilderness_survival`. Neither of UQ-2's suggested names collides:

- **World A: `unit_faction_tension`**
- **World B: `unit_information_source`**

Both follow the `unit_<mechanic>` naming convention UQ-2 itself proposes and read unambiguously
as unit-tier per the taxonomy doc's own vocabulary ("isolate exactly one gated mechanic").

---

## 7. Genuine risk assessment — brand-new world vs. modifying an existing one

**Overall risk: low, lower than a typical existing-world content edit, for a specific reason:**
both worlds are composed **entirely from module combinations that are exact subsets of
already-anchored, already-calibrated existing worlds** — not novel module combinations. World A
is byte-for-byte `sandbox_world`'s module list (already proven stable to 2000 ticks). World B is
`frontier_village_core` (used stably in 5 existing worlds) + `hero_adventurers` (used stably in
`urban_political`, including with a compile-time-seeded `pop_0`/`pop_1` addressing scheme
identical to what World B needs). Neither combination has ever been run before **as a pairing**,
but each module's individual behavior, hazard-kind completeness, and population-stability profile
is already independently proven — this is meaningfully lower-risk than `TCK-20260703-SIMQ-UPLIFT3-
WORLD-CORPUS`'s own worlds, several of which combined modules for the first time and did hit a
genuine hazard-kind gap (Finding 3/4, catastrophic early-tick collapse in `frontier_extended`/
`frontier_living_world`/`wilderness_survival`) before that ticket's Step 1 fix.

Specific hazard-kind check for these two compositions (the exact failure class from that prior
ticket): World A's only non-zero-hazard regions come from `wolf_den_near_forest`
(`hazard_level: 1.0`/`2.0`), which **already declares `hazard_kind: "NATURAL_TERRAIN"` in its
source YAML today**, and its populating faction `wild_beast_pack` **already declares
`hazard_immunities: ["NATURAL_TERRAIN"]`** in `data/content/social/factions.yaml` — both fixed
under `TCK-20260701-HAZARD-NATIVE-IMMUNITY`, both still present (confirmed by direct read, not
inferred). World B's only region is `frontier_village_core`'s `hometown`
(`hazard_level: 0.0` — no hazard drain mechanism engages at all). **Neither world introduces a new
hazard-kind gap** — the specific failure mode that made brand-new-world authoring genuinely risky
in the prior ticket does not apply here, precisely because no new module pairing with an
unaddressed hazard is being introduced.

**Residual, smaller risks (not blocking, worth noting honestly):**
1. **First-time pairing, not first-time module.** `frontier_village_core` + `hero_adventurers`
   together (without `wolf_den_near_forest`/`trading_company_hub`/`bandit_road_trade_pressure`,
   i.e. urban_political's other modules) has not been run before as a 2-module world. Population
   stability should be verified empirically (per AC/Scope item 4), not assumed purely from
   precedent — the investigation gives high confidence, not proof.
2. **INFORMATION/FACTION grade ceiling is bounded by precedent, not guaranteed identical.**
   `urban_political`'s INFORMATION plateaus at `B` (single-fire `belief_assimilated`, weight-scaled
   but tick-length-invariant) and FACTION reaches `S` at 200t / `A` at 500-1000t. World A/B should
   land in the same neighborhood since the mechanism is unchanged and the content shape is
   near-identical, but the exact letter grade depends on total event counts in a smaller/different
   entity population and must be read from the actual calibration output, not assumed in advance
   — this is explicitly flagged as "confirm honestly, whatever it turns out to be" in the ticket's
   own AC6, and this investigation does not pre-guess it.
3. **`make evaluate --dry-run` (as literally written in ticket Scope item 8) is not the intended
   command and would silently no-op.** GNU Make's own `--dry-run`/`-n` flag means "print recipe
   commands without executing them" — passing it to `make evaluate` does not forward `--dry-run`
   to `tools/evaluate_simq.py` (the Makefile's `evaluate` target already bakes in
   `tools/evaluate_simq.py --dry-run` unconditionally); it instead makes GNU Make itself skip
   *all* recipe execution, i.e. the intended verification step would never actually run. **The
   correct command is plain `make evaluate`** (Makefile: "Diff current calibration data against
   grade anchors (no engine re-run)" — already dry-run w.r.t. the engine). This is flagged here so
   implementation does not silently produce a false-green "0 regressions" from a no-op invocation.

**No population-stability-collapse risk class specific to "brand new" authoring beyond what's
covered above** — the WORLD-CORPUS hazard_kind lesson is fully addressed by the module-reuse
choices in §2/§3 above, not newly introduced.

---

## Open questions requiring a human decision

**None.** UQ-1 (reuse existing catalog content) is resolved by construction — both worlds are
built entirely from already-catalog-registered factions/modules, per the taxonomy doc's own
"template/synthetic content OK" unit-tier philosophy. UQ-2 (naming) is resolved above
(`unit_faction_tension`, `unit_information_source`), matching the ticket's own suggested pattern
with no collision. The one genuine implementation-time judgment call (exact letter grade a fresh
calibration run produces) is not a question requiring a decision — it is a measurement to make
during implementation and record honestly, exactly as AC6 already specifies.


---

## Citation Correction (2026-07-08, TCK-20260707-EPIC-SCOPE-INVESTIGATION-DOC-MISSING)

This doc's citations above to `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md`
and/or its later rename, `staging_artifacts/TCK-20260704-SIMQ-CORPUS-TIERS-EPIC/investigation.md`, point
to a pre-ticket epic-scoping investigation that was never migrated to `stored_artifacts/` and is now
unrecoverable: `staging_artifacts/` is gitignored by repo policy, and full git history confirms no commit
ever added a file at either path. This is a citation/traceability gap only -- every specific fact drawn
from that doc has been independently cross-validated against ground truth
(`world.yaml`/`world_compile_report.json`,
`test_corpus_diversity.py::EXPECTED_DISTINCT_POPULATED_FACTIONS`) by
`TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY` and/or `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION`. See
`tickets/done/TCK-20260707-EPIC-SCOPE-INVESTIGATION-DOC-MISSING.md` for the full root-cause writeup.
