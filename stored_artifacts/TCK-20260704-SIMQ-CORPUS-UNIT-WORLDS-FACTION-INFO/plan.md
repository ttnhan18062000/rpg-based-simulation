---
status: draft
layer: simulation
authority: P1
audience: agent
artifact_type: plan
tags: [simulation-quality, world, faction, information, corpus, calibration]
---

# Plan — TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO

PHASE_TS: 2026-07-06T17:55:58Z

## Decisions carried forward from investigation.md (not re-litigated)

- Composition mechanism: hand-authored `worldcomposition.v1` YAML using the `modules:` shorthand
  (mirrors `sandbox_world`), no generator tool.
- World A = `sandbox_world`'s exact module pair (`frontier_village_core` + `wolf_den_near_forest`,
  18 entities / 3 regions), `faction_tension_overrides` on `town_council: 0.5` /
  `merchant_league: 0.5`. No profile YAML (absence → `_resolve_profile()` falls back to
  `"default"`, all flags OFF — this is correct, not an omission).
- World B = `frontier_village_core` + `hero_adventurers` (13 + 3 = 16 entities, 1 region —
  `hometown`), `hero_adventurers`'s 3 un-ided `population_recipes` produce the positional
  `pop_0`/`pop_1`/`pop_2` addressing fallback needed for `target_population_id`. One
  `information_source_profiles` entry (`town_notice_board`, guide) + one
  `pending_information_responses` entry targeting `pop_0`. New profile YAML with
  `ENABLE_BELIEF_ASSIMILATION: "ON"` (the only flag required; `urban_political.yaml`'s extra
  `pillar_weights`/`ENABLE_SOCIAL_COOPERATION` are not needed here).
- World names: `unit_faction_tension`, `unit_information_source` — no collision with the 10
  existing world IDs.
- Tick count for calibration: **200 ticks**, matching every other fast-tier unit/regression-scale
  anchor in the corpus (`sandbox_world_seed*_200t`, the 5 `WORLD-CORPUS` worlds' `_200t` anchors).
  200t is the established convention for `<20`-entity-scale worlds specifically (`sandbox_world`,
  `wilderness_survival`, `highland_traverse` are all anchored at 200t, not 500t/1000t — those
  longer tiers are reserved for `dungeon_crawl`/`urban_political`/`simq_routing_test`, the
  mid-scale worlds). No adjustment needed — the investigation's proposed 200t is already the
  best-justified number for this entity-count band.
- Compile command sequence, `world_index.json` rebuild via `cli list`, and the corrected
  `make evaluate` (not `--dry-run`) are all confirmed directly against `Makefile`/`cli.py` during
  this planning pass (see Step 4/9 below) — no changes from investigation.md's findings.
- Faction-non-C-signal / information-non-C-signal confirmation: re-read `FactionScorer`
  (`src/simulation_quality/scorers/faction.py`) and `InformationScorer`
  (`src/simulation_quality/scorers/information.py`) directly during planning (see Step 7 below) to
  define exactly what a genuine positive signal looks like vs. an inert/false-positive `C`.
- `urban_political_seed42_200t`'s existing anchor (`FACTION: 'S', INFORMATION: 'B'` — confirmed by
  reading `grade_anchors.json` directly) is the closest existing 200t precedent for both
  mechanisms and is the calibration point World A/B's own 200t grades should be sanity-checked
  against (not asserted in advance — read per AC6/Test Plan Step 3/4).

No open questions remain from investigation.md; none discovered in this planning pass either
(see "Unresolved Questions" at the bottom).

---

## Step 1 — Author World A: `data/worlds/unit_faction_tension/world.yaml`

Full file content (new directory, new file):

```yaml
schema_version: "worldcomposition.v1"
world_id: "unit_faction_tension"
name: "Unit Test — Faction Tension Isolation"
description: "Unit-tier isolation world for the FACTION pillar. Reuses sandbox_world's exact module pair (frontier_village_core + wolf_den_near_forest, already proven population-stable to 2000 ticks) with non-zero faction_tension_overrides on the two factions this pairing actually populates (town_council, merchant_league); every other Pattern-6 field (information_source_profiles, pending_information_responses, pending_self_model_information_events) stays empty/default, and no profile YAML exists for this world so all feature flags default OFF."
modules:
  - "frontier_village_core"
  - "wolf_den_near_forest"
generation_seed: 501
faction_tension_overrides:
  town_council: 0.5
  merchant_league: 0.5
```

Notes:
- `wild_beast_pack` (the third faction this module pair populates, via `wolf_den_near_forest`) is
  deliberately left untouched at catalog default `0.0` — this keeps the isolation clean (only the
  two settlement-side factions get tension) and satisfies the ">=2 non-zero entries" AC without
  touching every populated faction.
- No `config/simulation_quality/profiles/unit_faction_tension.yaml` file is created. Its absence is
  the correct authoring choice, not an oversight — see Step 3.
- `generation_seed: 501` is an arbitrary non-colliding value (existing compositions use
  `42`/`202`/etc.; no technical dedup is enforced, this only avoids visual confusion with
  `sandbox_world`'s own `42`).

---

## Step 2 — Author World B: `data/worlds/unit_information_source/world.yaml`

Full file content (new directory, new file):

```yaml
schema_version: "worldcomposition.v1"
world_id: "unit_information_source"
name: "Unit Test — Information Source Isolation"
description: "Unit-tier isolation world for the INFORMATION pillar. Composes frontier_village_core + hero_adventurers — hero_adventurers's 3 un-ided population_recipes produce the positional pop_0/pop_1/pop_2 addressing fallback (WorldAssemblyResolver.resolve, mirrors urban_political's own mechanism for this field) needed to target target_population_id. One information_source_profiles entry and one pending_information_responses entry targeting pop_0 are seeded together (seeding one without the other, or without the matching feature flag, produces zero signal). faction_tension_overrides stays at catalog default (all factions 0.0) and pending_self_model_information_events stays empty — every other Pattern-6 field stays at baseline so this isolates INFORMATION alone."
modules:
  - "frontier_village_core"
  - "hero_adventurers"
generation_seed: 502
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
    subject: "hometown_danger"
    query_kind: "danger_rating"
    source_id: "town_notice_board"
    answer_kind: "KNOWN_FACT"
    certainty: 0.8
    details:
      danger_level: "low"
      region: "hometown"
    cost_paid: 0
```

Notes:
- `subject`/`details.region` deliberately reference `"hometown"` (the one real region this
  composition actually has, `hazard_level: 0.0`, confirmed directly from
  `data/content/world_modules/frontier_village_core.yaml`) rather than copy-pasting
  `urban_political`'s `"bandit_road_danger"`/`"bandit_road"` values verbatim — those reference a
  region/module (`bandit_road_trade_pressure`) that does not exist in this composition. `subject`/
  `query_kind`/`source_id`/`details` are free-form, uncatalogued fields
  (`PendingInformationResponseSpec`, `src/worldbuilding/schema.py:75-96`), so this is a cosmetic
  improvement for future debuggability, not a functional requirement — template/synthetic content
  is explicitly acceptable per the unit-tier philosophy either way.
- `target_population_id: "pop_0"` is matched at compile time against
  `properties["population_id"]` on the compiled entity — confirmed mechanism in
  `src/worldbuilding/compiler.py:317,428-439` and `src/worldassembly/resolver.py:452-453`.
  `hero_adventurers`'s 3 recipes resolve to `pop_0`, `pop_1`, `pop_2` in list order; targeting
  `pop_0` picks the first hero recipe, an arbitrary-but-deterministic choice consistent with
  `urban_political`'s own precedent.

---

## Step 3 — Author `config/simulation_quality/profiles/unit_information_source.yaml` (World B only)

Full file content (new file):

```yaml
feature_flags:
  ENABLE_BELIEF_ASSIMILATION: "ON"
```

- No `pillar_weights` block — `urban_political.yaml`'s `pillar_weights`/
  `ENABLE_SOCIAL_COOPERATION` entries affect only composite/overall weighting and a different
  pillar (SOCIAL), not whether FACTION/INFORMATION move off `C` — confirmed directly from
  `FactionScorer`/`InformationScorer`'s scoring logic (Step 7), which scores named event types
  independent of `pillar_weights`. Adding weights here would be unrequested scope creep.
- `tools/calibrate_simq.py`'s `_resolve_profile(name)` matches this file to the `--name
  unit_information_source` calibration invocation automatically (filename == world_id) — no
  `--profile` flag needed.
- **Confirm: World A needs no profile YAML.** Do not create
  `config/simulation_quality/profiles/unit_faction_tension.yaml`. Its absence causes
  `_resolve_profile()` to fall back to `"default"` (`ENABLE_BELIEF_ASSIMILATION`/
  `ENABLE_SELF_MODEL_COGNITION`/`ENABLE_ADVENTURE_ROUTING` all OFF), which is exactly the baseline
  World A's isolation requires. Creating an empty file would work identically but adds a
  maintenance surface with zero benefit — do not add it (matches test_plan.md's Anti-Drift Test
  Guards, explicit on this point).

---

## Step 4 — Compile both worlds and rebuild `world_index.json`

```bash
python3 -m src.worldbuilding.cli resolve unit_faction_tension
python3 -m src.worldbuilding.cli compile unit_faction_tension --seed 42 --from-resolved

python3 -m src.worldbuilding.cli resolve unit_information_source
python3 -m src.worldbuilding.cli compile unit_information_source --seed 42 --from-resolved

python3 -m src.worldbuilding.cli list   # rebuilds data/worlds/world_index.json to include both new worlds
```

Verification after each compile:
- `data/worlds/<world_id>/world_compile_report.json` — `"warnings"` array must be `[]`. `entity_count`
  should read 18/3-regions for `unit_faction_tension` and 16/1-region for `unit_information_source`
  (confirm against actual output; investigation's counts are derived, not yet measured).
- `data/worlds/<world_id>/resolved/world.resolved.yaml` — spot-check the isolation guard directly
  (see Step 7's Test Plan cross-reference: World A's `information_source_profiles`/
  `pending_information_responses` must both resolve to `[]`; World B's every
  `factions[].initial_tension_level` must resolve to `0.0`).
- `data/worlds/world_index.json` — both new world IDs present after the `list` invocation.

---

## Step 5 — Population-stability verification (>=200-300 ticks, seed 42, >=60% alive floor)

Follow `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS`'s Step 3 methodology exactly: drive each compiled
world via `Kernel.tick_once()` for >=300 ticks at seed 42, sample `alive_count` at 50-tick
checkpoints, assert alive stays >=60% of the starting entity count at every checkpoint.

- `unit_faction_tension` — expected to pass without incident: byte-for-byte the same module pair
  as `sandbox_world`, which is already proven stable to 2000 ticks (`sandbox_world_seed42_2000t`
  anchor). This is a re-confirmation under the new `world_id`/tension-override content, not a novel
  risk.
- `unit_information_source` — this is the one genuinely first-time pairing (`frontier_village_core`
  + `hero_adventurers`, without `wolf_den_near_forest`/`trading_company_hub`/
  `bandit_road_trade_pressure` that `urban_political` also has). Both modules are individually
  proven (`frontier_village_core` used stably in 5 existing worlds; `hero_adventurers` used stably
  in `urban_political`), and neither introduces any `hazard_level > 0` region (`hometown`'s
  `hazard_level` is `0.0` — no hazard-drain mechanism engages at all), so risk is low, but this
  must be empirically verified, not assumed.
- If either world's floor is breached, root-cause via the same method
  `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS` used (grep `hazard_level`/`hazard_kind` on the resolved
  YAML for any unaddressed hazard) before proceeding — do not anchor an unstable world.
- Promote this into the permanent regression guard, mirroring
  `tests/unit/worldassembly/test_corpus_diversity.py::test_population_stability`'s existing
  parametrization: add `unit_faction_tension` and `unit_information_source` as two new
  parametrized cases in that same test function (do not fork a new test file — the existing one
  already establishes this exact pattern for 5+ worlds).

---

## Step 6 — 3-seed calibration matrix (seeds 42/123/456, 200 ticks) and anchor additions

```bash
python3 tools/calibrate_simq.py --ticks 200 --seed 42  --name unit_faction_tension
python3 tools/calibrate_simq.py --ticks 200 --seed 123 --name unit_faction_tension
python3 tools/calibrate_simq.py --ticks 200 --seed 456 --name unit_faction_tension

python3 tools/calibrate_simq.py --ticks 200 --seed 42  --name unit_information_source
python3 tools/calibrate_simq.py --ticks 200 --seed 123 --name unit_information_source
python3 tools/calibrate_simq.py --ticks 200 --seed 456 --name unit_information_source
```

For each of the 6 resulting `data/calibration/<world_id>_seed<seed>_200t/quality_report.json`
files:

1. Extract the 10-pillar `{PILLAR: grade}` dict from `pillars.*.grade`.
2. Add a new keyed entry to `tests/simulation_quality/fixtures/grade_anchors.json`:
   `unit_faction_tension_seed{42,123,456}_200t` and
   `unit_information_source_seed{42,123,456}_200t` (6 new keys total, purely additive — do not
   touch any of the 43 existing entries).
3. Add the same 6 key strings to `FAST_ANCHOR_KEYS` in
   `tests/simulation_quality/test_grade_regression.py` (not `SLOW_ANCHOR_KEYS`/`ROUTING_KEYS` —
   these are 200t fast-tier runs with no `ENABLE_ADVENTURE_ROUTING`), placed as a new commented
   block (`# new — TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO: 2 unit-tier worlds, 3 seeds
   each`), following the exact style of the existing `WORLD-CORPUS` block.

This mirrors the precedent exactly (2 worlds x 3 seeds = 6, same ratio as
`WORLD-CORPUS`'s 5 worlds x 3 seeds = 15).

---

## Step 7 — Verify genuine non-C signal (FACTION for World A, INFORMATION for World B)

**What a real positive signal looks like, from direct re-read of the scorers:**

- `FactionScorer` (`src/simulation_quality/scorers/faction.py`) scores `faction_tension_delta`
  events: if `abs(delta) > 0 and payload["threshold_crossed"]` it emits `tension_active`
  (positive weight) — this requires the *live* `FactionState.tension_level` to actually cross a
  threshold during the run, not merely be seeded non-zero in `world.yaml`. It also scores
  `diplomatic_transition` (each transition emits `diplomacy_active`, positive; if zero
  transitions fire by a tick gate with multiple factions present it instead emits the
  **negative** `diplomacy_dormant`). A genuine non-C signal for World A means: the compiled
  `quality_report.json` shows non-zero `tension_active`/`diplomacy_active` hit counts (visible in
  the report's per-event breakdown, mirroring `urban_political`'s documented "29
  `diplomatic_transition` hits/run" in `eval_matrix_results.md`), not just a `FACTION` grade
  string that happens to read `S`/`A`/`B`.
  - **False-positive/inert-C check**: if the grade reads `C` specifically because
    `diplomacy_dormant` fired (zero transitions despite a seeded tension override), that is a
    genuine negative diagnostic (tension seeded but never crossed a threshold in 200 ticks — worth
    recording honestly, exactly as AC6 requires), not a bug to paper over. Distinguish this from a
    grade that reads `C` merely because the world produced *no* FACTION-pillar events at all
    (silence, not activity) — both must be visible in the calibration report's event counts, not
    inferred from the letter grade alone.
- `InformationScorer` (`src/simulation_quality/scorers/information.py`) scores
  `belief_assimilated`: fires `belief_active` (positive) once assimilation happens, or the
  negative `belief_system_silent` if zero updates occur by a dormancy-window tick gate. A genuine
  non-C signal for World B means: `quality_report.json` shows at least one `belief_active` hit
  (mirroring `urban_political`'s documented "calibration_hits=1/run" for this exact mechanism) —
  a single-fire, tick-length-invariant signal per investigation.md, so `INFORMATION` landing at
  `B` (not `S`/`A`) with exactly one hit is the expected honest outcome, not a partial failure.
  - **False-positive check**: if `ENABLE_BELIEF_ASSIMILATION` were accidentally left OFF (missing
    or misnamed profile file), the pending response would compile fine but produce zero
    `belief_assimilated` events — grade stays `C` with zero INFORMATION-pillar hits. Confirm the
    profile file is actually being picked up (`_resolve_profile("unit_information_source")` must
    resolve to the new file, not silently fall back to `"default"` on e.g. a filename typo) by
    checking the calibration run's own log/output for the loaded profile name, and by confirming
    the hit count is non-zero rather than trusting the letter grade in isolation.

**Procedure:**
1. Read `data/calibration/unit_faction_tension_seed{42,123,456}_200t/quality_report.json` →
   `pillars.FACTION.grade` and its event/hit-count breakdown.
2. Read `data/calibration/unit_information_source_seed{42,123,456}_200t/quality_report.json` →
   `pillars.INFORMATION.grade` and its event/hit-count breakdown.
3. Record both honestly in `eval_matrix_results.md` (Step 8) regardless of the actual letter —
   expected in the `S`/`A` neighborhood for FACTION (per `urban_political_seed42_200t`'s `S`) and
   `B` neighborhood for INFORMATION (per `urban_political_seed42_200t`'s `B`), but not to be
   pre-asserted before the real run per AC6's "whatever it turns out to be."
4. If either grade reads `C` with zero hit counts (true inert baseline, not a dormancy-negative
   finding), do not silently anchor it as if it were a success — flag it explicitly in
   Implementation Notes as a genuine diagnostic finding (per AC6) and, if it looks like a scorer or
   compile-time wiring defect rather than an expected/explainable dormancy result, flag it as a
   candidate follow-up ticket per this ticket's Out of Scope guidance — do not fix scoring logic
   in this ticket.

---

## Step 8 — Update `docs/simulation_quality/eval_matrix_results.md`

Add a new section (after the existing per-world sections, following the file's own established
per-world subsection format — see `### urban_political` for the shape to mirror) with two new
`###` subsections: `### unit_faction_tension (unit-tier)` and
`### unit_information_source (unit-tier)`, each with a `#### 200t (seeds 42 / 123 / 456)` grade
table (all 10 pillars x 3 seeds) and a one-paragraph note:
- For `unit_faction_tension`: state the actual FACTION grade/hit-count found in Step 7, and note
  every other Pattern-6-adjacent pillar (INFORMATION) stays `C` (isolation confirmed) as
  expected/correct, not a gap.
- For `unit_information_source`: state the actual INFORMATION grade/hit-count found in Step 7, and
  note FACTION stays `C` (isolation confirmed) as expected/correct.
- Tag both as **unit-tier** explicitly in the section heading or a one-line note, per
  `corpus_tier_taxonomy.md`'s classification criterion ("isolates exactly one gated mechanic, with
  everything else at baseline, using template/synthetic content").

Also update `docs/simulation_quality/corpus_tier_taxonomy.md`'s "Current tier mapping" table and
its stale opening line ("none of the new unit-tier ... worlds exist yet") — the doc's own text
explicitly anticipates this update once these two worlds land (confirmed in test_plan.md's
Regression Surface). Add two new rows to the mapping table:

| World | Tier | Notes |
|---|---|---|
| `unit_faction_tension` | Unit | 18 entities, 3 regions — isolates FACTION only (TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO) |
| `unit_information_source` | Unit | 16 entities, 1 region — isolates INFORMATION only (TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO) |

and replace the "none of the new unit-tier ... worlds exist yet" sentence with a pointer to these
two, now-existing worlds.

This file update is not named in the ticket's own Scope list as a hard requirement, but its own
text explicitly anticipates being updated by this ticket's work (per test_plan.md's flag) — do it
as part of Finalize since it costs one small edit and prevents the doc going stale on day one.

---

## Step 9 — Run `make evaluate` (corrected command) and scoped tests

**Do not run `make evaluate --dry-run`** — confirmed directly from the `Makefile` during this
planning pass: the `evaluate` target already runs `$(PYTHON) tools/evaluate_simq.py --dry-run`
internally (`Makefile:289-290`). Passing `--dry-run` as a second, literal argument to `make`
itself (`make evaluate --dry-run`) is interpreted by GNU Make as its own `-n`/`--dry-run` flag,
which makes Make print the recipe line without executing it — a silent no-op that would produce a
false "0 regressions" without ever running `tools/evaluate_simq.py`. The ticket's own Scope item 8
has this defect; this plan uses the corrected command:

```bash
make evaluate
```

Must exit 0 with 0 regressions against the expanded (43 + 6 = 49-entry) `grade_anchors.json`.

Scoped test commands (do not run the full suite):

```bash
pytest tests/simulation_quality/test_grade_regression.py -m "not slow"
pytest tests/integration/worldassembly/test_real_content_world_modules.py
pytest tests/integration/worldassembly/test_real_content_world_compositions.py
pytest tests/unit/worldbuilding/test_world_compiler.py tests/unit/worldassembly/test_resolver.py
pytest tests/unit/worldassembly/test_corpus_diversity.py
```

`MODULE_MATRIX` in `test_real_content_world_modules.py` already contains
`frontier_village_core`, `wolf_den_near_forest`, and `hero_adventurers` (confirmed by
test_plan.md's direct read) — no edit needed there.

---

## Step 10 — `make knowledge-index-update`

Run once at Finalize, since `docs/simulation_quality/eval_matrix_results.md` and
`docs/simulation_quality/corpus_tier_taxonomy.md` are both modified (Step 8):

```bash
make knowledge-index-update
```

---

## Files Changed (anticipated)

- `data/worlds/unit_faction_tension/world.yaml` (new)
- `data/worlds/unit_faction_tension/resolved/*` (generated: `world.resolved.yaml`,
  `compile_context.json`, `provenance_manifest.json`, `assembly_report.json`,
  `validation_report.json`)
- `data/worlds/unit_faction_tension/world_compile_report.json` (generated)
- `data/worlds/unit_information_source/world.yaml` (new)
- `data/worlds/unit_information_source/resolved/*` (generated, same 5 sidecar files)
- `data/worlds/unit_information_source/world_compile_report.json` (generated)
- `config/simulation_quality/profiles/unit_information_source.yaml` (new)
- `data/worlds/world_index.json` (regenerated via `cli list`)
- `tests/simulation_quality/fixtures/grade_anchors.json` (+6 entries)
- `tests/simulation_quality/test_grade_regression.py` (`FAST_ANCHOR_KEYS` +6)
- `tests/unit/worldassembly/test_corpus_diversity.py` (+2 parametrized
  `test_population_stability` cases; possibly +isolation-guard assertions per test_plan.md item 5,
  implementer's call)
- `docs/simulation_quality/eval_matrix_results.md` (+2 sections)
- `docs/simulation_quality/corpus_tier_taxonomy.md` (+2 table rows, stale-sentence fix)
- `data/calibration/unit_faction_tension_seed{42,123,456}_200t/*` (generated)
- `data/calibration/unit_information_source_seed{42,123,456}_200t/*` (generated)

## Explicit scope guards (carried from the ticket, not re-litigated)

- No self-model/Branch-B content in either world (`pending_self_model_information_events` stays
  empty in both) — separate ticket (`...SELFMODEL-PILOT`).
- No AGENCY-isolation world — separate ticket (`...UNIT-WORLD-AGENCY`).
- No content added to any existing end-to-end-tier world — separate ticket
  (`...E2E-CONTENT-EXPANSION`).
- No expansion of `data/content/social/faction_relationships.yaml` — separate ticket
  (`...FACTION-RELATIONSHIPS`).
- If a pillar scoring/emission bug is discovered while authoring these worlds (e.g. an unexpected
  inert `C` that looks structural rather than an honest dormancy finding), do not fix it here —
  flag it as a candidate follow-up ticket for the orchestrator, per the established session
  pattern (`TCK-20260703-SIMQ-UPLIFT3-PLAYBOOK-DOC`'s precedent, and the
  `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS`/`simq_routing_test` `ResourceRegistry: STONE` finding
  as the model example of "discovered, documented, not fixed in-ticket").

## Deviations (recorded during implementation)

**One deviation from this plan's own anticipated Files Changed list, forced by a blocking
pre-existing bug — not a plan defect.** Step 4's `resolve` command failed for *every* world in the
catalog (reproduced directly on `sandbox_world` too, then reverted with `git checkout`) with
`[CAT-REL-099] Resource 'stone_outcrop' references non-existent material 'stone'`. Root cause:
`TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP` (2026-07-04) added a `stone_outcrop` resource and a
`stone` item, but never registered a `stone` entry in `data/content/foundation/materials.yaml` —
`ContentValidator._validate_reference_graph` (`CAT-REL-099`, `ERROR` severity, unconditional, no
`--strict`/bypass) checks this catalog-wide as part of `WorldAssemblyResolver.assemble()`, so it
blocked `resolve` for all worlds, not only ones referencing `stone_outcrop`. This had gone unnoticed
since 2026-07-04 because no world had been freshly `resolve`d since that commit — existing worlds'
`compile --from-resolved` uses pre-committed `resolved/` artifacts and bypasses the assemble+validate
cycle entirely. Fixed with one minimal, additive `stone` material entry (mirrors the file's existing
entry shape exactly, no schema/logic change); re-confirmed `sandbox_world` resolves cleanly after
the fix, then reverted its incidentally-regenerated `resolved/*`/`world_compile_report.json` output
via `git checkout` since touching an existing world's compiled artifacts is out of this ticket's
scope. Flagged as a candidate follow-up ticket in the implementer's final report — a permanent
"every `resource.material` has a `materials.yaml` entry" catalog-integrity regression test would
have caught this at the STONE-GAP ticket's own commit time.

**No other deviation.** Every module choice, tension value, information-source/response content
field, seed, tick count, and command sequence in Steps 1-9 executed exactly as this plan specified,
with zero adjustment. Both worlds' actual FACTION/INFORMATION grades landed exactly in the
neighborhood Step 7 anticipated from the `urban_political_seed42_200t` precedent: World A
FACTION=`S` (29 hits/run, all 3 seeds identical); World B INFORMATION=`B` (1 hit/run, all 3 seeds
identical). Both isolation guards held clean at every seed (World A's INFORMATION stayed `C`/0
events; World B's FACTION stayed `C`/0 events) — neither grade came back as an inert/structural `C`
requiring a follow-up bug flag of its own.

## Unresolved Questions

None requiring a human decision. All forks investigation.md left open (module choice, faction IDs,
world naming, tick count) are resolved above with direct evidence (existing anchor precedent for
200t at this entity-count band; direct scorer re-read confirming what a genuine vs. inert signal
looks like; direct Makefile read confirming the `make evaluate` correction). The one genuine
implementation-time measurement — the actual FACTION/INFORMATION letter grades a fresh calibration
run produces — is not a question to decide now; it is measured and recorded honestly during
implementation per Step 7/8, exactly as the ticket's own AC6 specifies.
