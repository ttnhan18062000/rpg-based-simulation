---
ticket_id: TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS
phase: plan
date: 2026-07-04
---

# Plan: Diversify the SimQ calibration world corpus

## Scope-boundary decision (pre-resolved, not re-flagged)

Per the planning brief for this ticket: the ticket's own Scope item 4 ("if P2-B ... is still
blocking the existing larger worlds from completing full-length calibration runs, either fix it
as part of this ticket or file it as an explicit sub-blocker") pre-authorizes folding the
hazard-kind staleness fix into this ticket, even though `investigation.md`'s own UQ-1 resolution
recommended filing it separately. **This plan folds it in**, per that pre-authorization — this is
not re-litigated below.

## Correction to investigation.md Finding 4 (evidence-based, found during planning)

Finding 4 states: "Of the 5 non-core modules composing [frontier_extended], only
`goblin_camp_conflict`, `wolf_den_near_forest`, and `forest_warden_grove` declare `hazard_kind` in
source YAML." **Direct inspection of `data/content/world_modules/forest_warden_grove.yaml` during
this planning pass shows this is incorrect** — the file has two regions (`sacred_grove`,
`deep_forest`) with `hazard_level: 1.5`/`2.0` and no `hazard_kind` field at all. Grep confirms zero
`hazard_kind` occurrences repo-wide outside `wolf_den_near_forest.yaml` and
`goblin_camp_conflict.yaml`.

Extending the same check to every module used by the worlds this ticket's Step 4 proposes to
anchor (not a blanket 20-module audit) finds the same gap in four more places:

| Module | Used by | hazard_level | Native faction | Faction already has matching `hazard_immunities`? |
|---|---|---|---|---|
| `forest_warden_grove` | frontier_extended | 1.5 / 2.0 | `forest_wardens`, `spirit_court` (both spawn populations here) | No |
| `undead_battlefield` | frontier_extended, frontier_living_world, wilderness_survival | 4.0 | `undead_remnants` (spawns `undead_battlefield_patrol`); `spirit_court` listed but spawns no population here (no-op) | No |
| `nomadic_herd` | highland_traverse | 1.5 / 2.0 | `wild_beast_pack` (spawns `wolf_pack_small`) | **Yes** — `wild_beast_pack.hazard_immunities: ["NATURAL_TERRAIN"]` already covers it |
| `sunken_swamp_border` | swamp_border_world | 2.5 | `swamp_tribe` (spawns `swamp_tribe_patrol`, `swamp_ambush_party`); `wild_beast_pack` listed but spawns no population here (no-op) | No |

**Consequence:** the originally-named 3-module fix (`orc_clan_territory`,
`bandit_road_trade_pressure`, `old_mine_resource_loop`) is necessary but not sufficient to
stabilize `frontier_extended`/`frontier_living_world`/`wilderness_survival`, and is irrelevant to
`highland_traverse`/`swamp_border_world`'s own (separate) hazard-kind gaps. Since Step 4 below
recommends anchoring all five of these worlds directly (see rationale there), this plan extends
the identical, already-established content pattern (`hazard_kind` on the region +
`hazard_immunities` on the region's *native* faction only) to **7 modules total**, strictly
bounded to modules used by worlds this ticket recompiles/anchors. This is the same bug class
already pre-authorized for this ticket (per the Scope-boundary decision above), not a new/
different fix, and does not touch `moon_cult_ruins`, `scalable_bandit_camp`, `forest_deep_ecology`,
or `survivor_camp_shelter` (the first two aren't used by any world this ticket anchors; the latter
two declare no populations in their own module — nothing spawns there for the mechanism to apply
to, or in `forest_deep_ecology`'s case no regions at all).

---

## Step 1 — Content fix: `hazard_kind` + `hazard_immunities` (7 modules, 6 factions)

Mirrors the exact pattern from `TCK-20260701-HAZARD-NATIVE-IMMUNITY`
(`stored_artifacts/TCK-20260701-HAZARD-NATIVE-IMMUNITY/plan.md`, shipped in
`wolf_den_near_forest.yaml`/`goblin_camp_conflict.yaml` + `factions.yaml`): add
`hazard_kind: "<KIND>"` to each region, add `hazard_immunities: ["<KIND>"]` to the region's
*native* faction only (never to a hostile/visiting faction sharing the same region).

### 1a. Originally-named 3 modules (explicitly instructed)

- `data/content/world_modules/orc_clan_territory.yaml` — region `orc_stronghold`: add
  `hazard_kind: "NATURAL_TERRAIN"`.
  `data/content/social/factions.yaml` — `orc_clan` (populates `orc_clan_warband` →
  `orc_brute`, native to `orc_stronghold`): add `hazard_immunities: ["NATURAL_TERRAIN"]`.
- `data/content/world_modules/bandit_road_trade_pressure.yaml` — region `bandit_road`: add
  `hazard_kind: "NATURAL_TERRAIN"`.
  `data/content/social/factions.yaml` — `bandit_company` (populates `bandit_ambush_group` →
  `bandit_scout`, native): add `hazard_immunities: ["NATURAL_TERRAIN"]`. **Do NOT** add
  immunity to `merchant_league` (populates `merchant_caravan` → `traveling_merchant`/
  `frontier_guard`, faction `town_council`) — these are transient/hostile-encounter targets
  per `relationships: ["bandits_to_merchants"]`, not natives of the bandit road. This mirrors
  the original ticket's AC3 guard ("hostile/visiting entities must NOT be exempt").
- `data/content/world_modules/old_mine_resource_loop.yaml` — region `old_mine`: add
  `hazard_kind: "NATURAL_TERRAIN"`. **No faction file change** — `old_mine_spider_cluster` →
  `cave_spider` → faction `wild_beast_pack`, which already declares
  `hazard_immunities: ["NATURAL_TERRAIN"]` (added by the original ticket for
  `wolf_pack_small`). This is the same free-fix the investigation found.

### 1b. Additional 4 modules (evidence-based extension, see Correction above)

- `data/content/world_modules/forest_warden_grove.yaml` — regions `sacred_grove`,
  `deep_forest`: add `hazard_kind: "NATURAL_TERRAIN"` to both.
  `data/content/social/factions.yaml` — `forest_wardens` (populates `forest_warden_patrol` →
  `forest_ranger`): add `hazard_immunities: ["NATURAL_TERRAIN"]`. `spirit_court` (populates
  `sacred_grove_guardians` → `spirit_guardian`, `preferred_regions: ["sacred_grove",
  "deep_forest"]` — native here): add `hazard_immunities: ["NATURAL_TERRAIN"]`. (`spirit_court`
  is also listed in `undead_battlefield`'s `factions:` but spawns no population there — this
  addition has no effect in that module, confirmed safe.)
- `data/content/world_modules/undead_battlefield.yaml` — region `haunted_battlefield`: add
  `hazard_kind: "UNDEAD_CORRUPTION"` (new value — see rationale below, **not** reusing
  `"NATURAL_TERRAIN"`).
  `data/content/social/factions.yaml` — `undead_remnants` (populates
  `undead_battlefield_patrol` → `undead_sentinel`): add
  `hazard_immunities: ["UNDEAD_CORRUPTION"]`. **Do NOT** add immunity to `spirit_court` here —
  it spawns no population in this module (no-op either way, but the correct semantic reading is
  that spirit_court is not native to a corrupted battlefield).
- `data/content/world_modules/nomadic_herd.yaml` — regions `near_forest`, `wolf_den` (module's
  own region definitions, hazard_level 1.5/2.0): add `hazard_kind: "NATURAL_TERRAIN"` to both.
  **No faction file change** — `wolf_pack_small` → `wild_beast_pack` already immune.
- `data/content/world_modules/sunken_swamp_border.yaml` — region `swamp_border_territory`: add
  `hazard_kind: "NATURAL_TERRAIN"`.
  `data/content/social/factions.yaml` — `swamp_tribe` (populates `swamp_tribe_patrol`,
  `swamp_ambush_party` → `lizardfolk_scout`/`lizardfolk_shaman`): add
  `hazard_immunities: ["NATURAL_TERRAIN"]`. `wild_beast_pack` is listed in `factions:` but
  spawns no population here — no change needed (already covered corpus-wide anyway).

**Why `"UNDEAD_CORRUPTION"` and not reusing `"NATURAL_TERRAIN"` for undead_battlefield:**
`hazard_kind` is a free-form `Optional[str]` (`RegionSpec.hazard_kind`,
`src/worldbuilding/schema.py`) — no enum constraint — so a new value requires no schema change.
`docs/mechanics/05_world_evolution.md`'s own design rationale (and
`TCK-20260701-HAZARD-NATIVE-IMMUNITY`'s Implementation Notes, "fiends endure chaos corruption" as
the motivating illustrative example) frames endurance as each faction declaring immunity for its
*own in-fiction reason* — undead enduring the corruption of their own battlefield is a distinct
reason from wolves/goblins/orcs/bandits/lizardfolk being native to ordinary wilderness terrain.
Reusing `"NATURAL_TERRAIN"` for a haunted ruin would blur that distinction for no benefit (it
doesn't reduce authoring cost — a faction-level `hazard_immunities` entry is required either way).
`docs/mechanics/05_world_evolution.md` §3's parenthetical example list (`"PHYSICAL"`,
`"NATURAL_TERRAIN"`, `"TOXIC_GAS"`) is updated to add `"UNDEAD_CORRUPTION"` as a second real
(non-synthetic) authored value, alongside a one-line note that `TOXIC_GAS` remains
synthetic-test-only while `UNDEAD_CORRUPTION` is now production content (Step 6 below).

**Do not touch:** `src/world/spawn.py`, `src/world/spawn_config.py` (P2-B confirmed resolved,
no code changes needed — see Step 7), `moon_cult_ruins.yaml`, `scalable_bandit_camp.yaml`,
`forest_deep_ecology.yaml`, `survivor_camp_shelter.yaml` (out of the bounded set above).

---

## Step 2 — Recompile all 8 stale worlds

Per `investigation.md`'s provenance table, recompile (resolve + compile) every world whose
`resolved/provenance_manifest.json::created_at` predates 2026-07-01:
`simq_routing_test`, `dungeon_crawl`, `generated_frontier_3_42`, `frontier_extended`,
`frontier_living_world`, `swamp_border_world`, `highland_traverse`, `wilderness_survival`.

For each `<world_id>`:
```bash
python3 -m src.worldbuilding.cli resolve <world_id>
python3 -m src.worldbuilding.cli compile <world_id> --seed 42 --from-resolved
```
(Use each world's existing `generation_seed` from its `world.yaml` if compiling for inspection
purposes only; calibration runs in Step 4 pass their own `--seed` via `calibrate_simq.py`
independent of this compile step, matching existing convention — `compile` here is to refresh
`resolved/world.resolved.yaml`/`world_compile_report.json`/`provenance_manifest.json` on disk.)

Verify after each: `grep hazard_kind data/worlds/<world_id>/resolved/world.resolved.yaml` shows
the newly-authored kinds on the expected regions, and
`resolved/provenance_manifest.json::created_at` now postdates 2026-07-01 (Anti-Drift Hazard from
investigation.md).

**Risk flagged explicitly — `dungeon_crawl` and `simq_routing_test` are both already-anchored
(committed `grade_anchors.json` entries) and both are on the stale list.** `dungeon_crawl` uses
`old_mine_resource_loop` (fixed in Step 1a) and `simq_routing_test` also uses
`old_mine_resource_loop`. Recompiling them is required (they cannot be left permanently stale),
but doing so may change `old_mine_spider_cluster`'s survival dynamics and shift their existing
committed grades. This is exactly the situation `test_grade_regression.py`'s own module docstring
already documents a procedure for ("To update anchors after an intentional scoring change:
re-run calibration ... edit grade_anchors.json ... commit fixture and calibration data
together") and `eval_matrix_results.md`'s D2-fix precedent already did once (24/25 pillar grades
changed after a formula fix; anchors were updated, not left stale). **Step 4a below** (not Step 4,
which covers only the 5 newly-anchored worlds and never touches `dungeon_crawl`/
`simq_routing_test`) re-runs `dungeon_crawl`'s and `simq_routing_test`'s **existing** anchored
seed/tick combinations after recompile and diffs against committed grades — if unchanged, no edit
needed (and this "no drift" outcome must be explicitly recorded, not silently assumed); if changed,
update `grade_anchors.json` for those specific keys with a one-line note in
`eval_matrix_results.md` attributing the shift to the hazard-kind recompile, not a new regression.
`goblin_camp_conflict`/`scalable_bandit_camp` (dungeon_crawl's other modules) already have/don't
need `hazard_kind` changes (unaffected).

`generated_frontier_3_42` is recompiled (it is stale) but **not anchored** in this ticket — see
Step 4's scope boundary.

---

## Step 3 — Population-stability re-verification

For `frontier_extended`, `frontier_living_world`, `wilderness_survival` (the three worlds
`investigation.md` found catastrophically collapsing early), and additionally
`highland_traverse`/`swamp_border_world` (never independently checked before — investigation
flagged `swamp_border_world` explicitly as needing this before anchoring; `highland_traverse` is
being newly anchored per Step 4, so it gets the same guard):

Drive each recompiled world via `Kernel.tick_once()` for ≥300 ticks at seed 42 (mirroring
`investigation.md`'s re-verification method), sampling `alive_count` at 50-tick checkpoints.
Target floor: alive stays ≥60% of starting entity count at every checkpoint (per
`test_plan.md`'s proposed population-stability smoke-test floor) — a materially different result
from Finding 3's table (`frontier_extended` fell to 13/56 = 23% by tick 50 pre-fix).

If any world still shows a collapse below the 60% floor after the Step 1 fix, root-cause it before
proceeding to Step 4 (very likely a hazard-bearing module/faction pairing missed in Step 1's
bounded set — re-check via `grep hazard_level` / `grep hazard_kind` on that world's resolved YAML
for any region with `hazard_level > 0` and no `hazard_kind`, and cross-reference the populating
faction's `hazard_immunities`) rather than silently anchoring an unstable world.

This becomes the permanent regression guard specified in `test_plan.md` item 2
(`tests/unit/worldassembly/test_corpus_diversity.py::test_population_stability_<world>`, one
parametrized case per world in this bounded set) and item 3 (hazard-kind completeness guard,
scoped to these worlds' resolved regions, not all 10 worlds — matches "scope the recalibration to
the worlds actually touched by this ticket").

---

## Step 4a — Existing-anchor drift check: `dungeon_crawl` / `simq_routing_test` (stale-recompile backstop)

Both worlds are already-anchored (committed entries in `grade_anchors.json`) **and** both are on
Step 2's stale-recompile list (both use `old_mine_resource_loop`, which gains a new `hazard_kind`
declaration in Step 1a). Recompiling them in Step 2 could shift their existing, already-committed
grades. Neither `make evaluate` (dry-run diff only, no engine re-run — see corrected Step 8) nor
`pytest -m "not slow"` (excludes `SLOW_ANCHOR_KEYS`, i.e. dungeon_crawl's 1000t/2000t entries
entirely) can catch this drift as a backstop, so this sub-step exists to catch it explicitly,
*before* Step 5's fixture edits are treated as final.

**Confirmed existing anchor keys** (read directly from
`tests/simulation_quality/fixtures/grade_anchors.json`, not assumed):

- `dungeon_crawl`: `seed42_200t` (200t exists **only** for seed42 — there is no seed123/seed456
  200t entry in the existing corpus), plus `seed{42,123,456}_500t`, `seed{42,123,456}_1000t`,
  `seed{42,123,456}_2000t`. **10 entries total.**
- `simq_routing_test`: `seed{42,123,456}_500t` only (all three require
  `ENABLE_ADVENTURE_ROUTING=ON`, per `ROUTING_KEYS` in `tools/evaluate_simq.py`). **3 entries
  total.**

**1. Refresh all 13 existing-anchor calibration reports:**
```bash
python3 tools/calibrate_simq.py --ticks 200  --seed 42  --name dungeon_crawl
python3 tools/calibrate_simq.py --ticks 500  --seed 42  --name dungeon_crawl
python3 tools/calibrate_simq.py --ticks 500  --seed 123 --name dungeon_crawl
python3 tools/calibrate_simq.py --ticks 500  --seed 456 --name dungeon_crawl
python3 tools/calibrate_simq.py --ticks 1000 --seed 42  --name dungeon_crawl
python3 tools/calibrate_simq.py --ticks 1000 --seed 123 --name dungeon_crawl
python3 tools/calibrate_simq.py --ticks 1000 --seed 456 --name dungeon_crawl
python3 tools/calibrate_simq.py --ticks 2000 --seed 42  --name dungeon_crawl
python3 tools/calibrate_simq.py --ticks 2000 --seed 123 --name dungeon_crawl
python3 tools/calibrate_simq.py --ticks 2000 --seed 456 --name dungeon_crawl
ENABLE_ADVENTURE_ROUTING=ON python3 tools/calibrate_simq.py --ticks 500 --seed 42  --name simq_routing_test
ENABLE_ADVENTURE_ROUTING=ON python3 tools/calibrate_simq.py --ticks 500 --seed 123 --name simq_routing_test
ENABLE_ADVENTURE_ROUTING=ON python3 tools/calibrate_simq.py --ticks 500 --seed 456 --name simq_routing_test
```
This overwrites `data/calibration/<run_key>/quality_report.json` for all 13 run_keys with results
computed against the Step 1/2 recompiled (hazard-kind-fixed) content.

**2. Diff against currently-committed values:** before running the above, snapshot the 13 existing
entries from `tests/simulation_quality/fixtures/grade_anchors.json` (e.g. `git show HEAD:tests/
simulation_quality/fixtures/grade_anchors.json`, or a working copy taken before Step 1/2 start).
After the refresh, extract the 10 pillar grades from each of the 13 refreshed
`quality_report.json` files and compare against the pre-refresh committed values, key by key.

**3. If any of the 13 grades changed:** update `grade_anchors.json` in place for that specific
`run_key` only (leave the other, unaffected keys untouched), and record a note in both the
anchor-update commit message and a new `eval_matrix_results.md` entry — mirroring the precedent
already established in this repo for exactly this situation:
`docs/simulation_quality/eval_matrix_results.md` lines 22–30, under
**TCK-20260702-SIMQ-UPLIFT-GRADE-DECAY (D2 formula fix)**, which documents "All 25 anchored
scenarios were re-run; 24 pillar grades changed" and attributes the shift to a named, understood
cause rather than treating it as a silent regression. This ticket's note must likewise attribute
any observed shift here to "hazard-kind recompile of `old_mine_resource_loop` (Step 1a/Step 2)",
not to a new/unexplained regression.

**4. If none of the 13 grades changed:** state that explicitly in the ticket's Implementation
Notes section as a required, positive finding — e.g. "Confirmed no drift: all 13 pre-existing
`dungeon_crawl`/`simq_routing_test` anchor entries re-verified unchanged after the Step 1a/Step 2
`old_mine_resource_loop` hazard-kind recompile." A "no drift" result is not something to skip
silently just because nothing needed editing.

**5. Ordering:** this sub-step's refresh + diff (and any resulting anchor edits) must complete
before Step 5's fixture edits are treated as final, since Step 4's 15 new entries and Step 4a's
(possible) 13 updated entries land in the same `grade_anchors.json` file.

---

## Step 4 — World corpus diversity additions: anchor 5 existing worlds, author 0 new ones

**Decision: do not author brand-new world compositions.** Every gap `investigation.md` and this
plan's own Correction identified is closeable by fixing (Step 1) + recompiling (Step 2) +
verifying (Step 3) + anchoring existing, already-compiled worlds — at zero new-content-authoring
cost. This directly follows the task brief's own framing ("check if ... once fixed, already fill
some of the identified entity-count-band gaps without needing brand-new content") and is a
defensible, evidence-based alternative to `investigation.md`'s UQ-1 suggestion (which predates the
decision, made at the ticket-scope level, to fold the hazard-kind fix into this ticket at all —
once that fold-in happens, authoring new content to fill gaps these worlds already fill would be
redundant effort).

**Worlds newly anchored (5 — satisfies AC2's "≥2 new/substantially-extended" as "substantially
extended," none previously had any anchor entry):**

| World | Entities | Regions | Gap closed | Never-anchored modules newly in corpus |
|---|---|---|---|---|
| `frontier_extended` | 56 | 10 | >50-entity band; ≥6-region spread (10 vs. current anchored max 4, `dungeon_crawl`) | `forest_warden_grove`, `orc_clan_territory`, `undead_battlefield` |
| `frontier_living_world` | 46 | 7 | 35–50-entity band (currently 0 anchored worlds in this band) | `undead_battlefield` (already counted above once) |
| `wilderness_survival` | 11 | 4 | second `<20`-entity data point (alongside `sandbox_world` 18) | `survivor_camp_shelter`, `forest_deep_ecology` |
| `highland_traverse` | 18 | 5 | closes the entire "highland/river/nomad" content family gap `investigation.md` flagged, with zero new authoring (it already composes exactly that family) | `mountain_pass`, `river_crossing`, `nomadic_herd`, `settled_quarter` |
| `swamp_border_world` | 26 | 4 | brings `sunken_swamp_border` (swamp/lizardfolk family) into corpus | `sunken_swamp_border` |

Net module-family coverage: 9/20 anchored today → **19/20** after this ticket (only
`moon_cult_ruins`, used solely by the out-of-scope `generated_frontier_3_42`, remains
unanchored — explicitly deferred, see Step 4 scope boundary below).

**Anchoring procedure per world (mirrors `TCK-20260702-SIMQ-EVAL-MATRIX`'s established
multi-seed pattern):**
```bash
python3 tools/calibrate_simq.py --ticks 200 --seed 42   --name <world_id>
python3 tools/calibrate_simq.py --ticks 200 --seed 123  --name <world_id>
python3 tools/calibrate_simq.py --ticks 200 --seed 456  --name <world_id>
```
Read `data/calibration/<world_id>_seed<seed>_200t/quality_report.json`, extract the 10 pillar
grades, add each as a `<world_id>_seed<seed>_200t` entry to
`tests/simulation_quality/fixtures/grade_anchors.json`, and add the same 3 keys to
`FAST_ANCHOR_KEYS` in `tests/simulation_quality/test_grade_regression.py`. 15 new fast-anchor
entries total (5 worlds × 3 seeds). None of these 5 worlds gate any of the 4 flag-gated pillars
(AGENCY/FACTION/INFORMATION/SOCIAL) — expect uniform `C` there, consistent with every
non-`simq_routing_test`/`urban_political` world today; this is not a regression, it is the
already-documented structural gate (Out of Scope for this ticket, unchanged).

**Scope boundary — explicitly not anchored in this ticket:** `generated_frontier_3_42` (44
entities — would otherwise be an attractive "32→44 gap" candidate) is recompiled in Step 2 but
**not** anchored here. Its `moon_cult_ruins` module (`hazard_level: 4.0`, faction `moon_cult`/
`arcane_circle`) has the same missing-`hazard_kind` gap as the 4 modules in Step 1b, but fixing
it would require authoring a *new* hazard_kind + faction-immunity pairing for factions not used
by any other world this ticket touches (`moon_cult`, `arcane_circle`) — a genuinely separate unit
of investigation (is `moon_cult`/`arcane_circle` "native" to `moon_cult_ruins`, and are there
other missing modules in this world too?) rather than an evidence-supported extension of the
already-bounded fix set above. File as a follow-up (`layer: world`, P2) referencing this
investigation's method, rather than expanding this ticket's content-fix footprint further.

---

## Step 5 — Test/fixture updates

- `tests/simulation_quality/fixtures/grade_anchors.json` — 15 new entries (Step 4) +
  `dungeon_crawl`/`simq_routing_test`'s existing entries updated in place only if Step 4a's
  refresh-then-diff empirically shows their grades shifted (with a change note, not silent; see
  Step 4a for the confirmed-no-drift recording requirement if they did not).
- `tests/simulation_quality/test_grade_regression.py` — `FAST_ANCHOR_KEYS` gains the 15 new keys.
- `tests/integration/worldassembly/test_real_content_world_modules.py::MODULE_MATRIX` — confirm
  the 7 touched modules are present (they already are, per Prior Work — this is a content-value
  change, not a new module); no matrix entries need adding, only the module-family coverage test
  below needs the "now anchored" cross-reference.
- New file `tests/unit/worldassembly/test_corpus_diversity.py`:
  1. `test_entity_count_band(world_id, expected_band)` — parametrized over the 5 anchored worlds,
     asserts `world_compile_report.json::entity_count` falls in the band each was chosen to fill
     (per the table in Step 4).
  2. `test_population_stability(world_id)` — parametrized over the 5 worlds (+ any world touched
     in Step 3), drives `Kernel.tick_once()` ≥300 ticks at seed 42, asserts `alive_count` at every
     50-tick checkpoint ≥60% of starting `entity_count`.
  3. `test_hazard_kind_completeness(world_id)` — parametrized over the 5 worlds, for every region
     in `resolved/world.resolved.yaml` with `hazard_level > 0`, asserts `hazard_kind` is set OR
     every populating archetype's faction declares matching `hazard_immunities`.
  4. `test_module_family_anchored()` — asserts each of the 10 previously-never-anchored modules
     from Step 4's table now appears in `grade_anchors.json`'s covered worlds (via each world's
     `world.yaml::modules` list), leaving only `moon_cult_ruins` in the never-anchored set.

---

## Step 6 — Docs

- `docs/mechanics/05_world_evolution.md` §3 "Native Endurance to a Region's Hazard Kind" —
  add `"UNDEAD_CORRUPTION"` to the parenthetical example list; one sentence noting it is now an
  authored production value (unlike `"TOXIC_GAS"`, which remains synthetic-test-only).
- `docs/parity_ledger/world_dynamics.yaml` — `WORLD-029`/`WORLD-060` (the entries
  `TCK-20260701-HAZARD-NATIVE-IMMUNITY` updated) get their `v2_evidence` extended with a one-line
  note that the mechanism is now exercised corpus-wide (7 modules, 6 factions) rather than only
  `wolf_den_near_forest`/`goblin_camp_conflict`; `test_path` gains
  `tests/unit/worldassembly/test_corpus_diversity.py`.
- `docs/simulation_quality/eval_matrix_results.md` — new section documenting the 15 new anchor
  entries (grade tables per world/seed, mirroring the existing per-world subsections), and an
  explicit note removing `frontier_extended`/`frontier_living_world`/`wilderness_survival`/
  `highland_traverse`/`swamp_border_world` from the "Zero-pillar worlds ... not included" list at
  the top of the doc, replacing it with "now anchored as of TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS
  — see below." If `dungeon_crawl`/`simq_routing_test` grades shifted post-recompile (Step 2
  risk), document the shift here with the same rationale used for the D2 formula-fix precedent
  already in this file.
- `docs/audits/D20_simq_integration.md` — update the corpus-size reference (13-run corpus →
  28-run corpus: 13 + 15 new) and the "5 zero-pillars" table area to reflect the 5 newly-anchored
  worlds' actual grades.
- `docs/guidelines/intentional_divergences.md` — no new entry needed; this is content-only reuse
  of an already-recorded divergence (§2.20), not a new mechanism or behavior change.

---

## Step 7 — `docs/plans/audit_fix_plan.md` P2-B correction

Per `investigation.md`'s Findings 1–4: P2-B's own scope (urban_political late-run spawn/attrition,
tick 800–1000) is genuinely resolved and was misattributed as the cause of
`frontier_extended`/`frontier_living_world`/`wilderness_survival`'s early-tick collapse, which is
actually the hazard-kind staleness bug (now fixed, Steps 1–3). Update, per the Anti-Drift Hazard
in `investigation.md` ("do not conflate [P2-B resolution] with the frontier_extended/
frontier_living_world symptom"):

1. **P2-B narrative section (~line 210-215):** append a resolution note: "**RESOLVED (verified
   2026-07-04, TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS)** — code inspection confirms
   `SpawnService.process_spawns()`'s two-tier cadence (`src/world/spawn.py`) is present and
   functioning exactly as `TCK-20260627-P2B-SPAWN-CADENCE` designed; no logic regression from the
   file relocation. **Distinct finding:** the '159†'/'101‡' early-termination markers recorded in
   the 13-run corpus table below for `frontier_extended`/`frontier_living_world`/
   `wilderness_survival` were NOT caused by spawn cadence (P2-B is a *late*-run, tick 500+
   mechanism; the collapse there happens by tick 50) — they were a stale-compile / missing
   `hazard_kind` content gap, separately root-caused and fixed under this ticket. See
   `stored_artifacts/TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS/investigation.md` Findings 1-4."
2. **13-run corpus table (~line 463-483):** update the `frontier_extended`/`frontier_living_world`/
   `wilderness_survival` rows with their new (post-fix, non-early-terminating) tick counts and
   grades once Step 4's calibration runs land; remove the `†`/`‡` early-termination footnotes (no
   longer accurate) and replace with a one-line pointer to this ticket's fix.
3. **Summary Table (~line 553):** change the P2-B row's status from `UNVERIFIED (2026-07-03)` to
   `**RESOLVED (verified 2026-07-04)** — TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS; two-tier cadence
   intact, frontier_extended/frontier_living_world/wilderness_survival symptom re-attributed to
   hazard-kind staleness (separately fixed, same ticket)`.
4. **Suggested Fix Order section (~line 587-603):** remove P2-B from the "genuinely open" and
   "pending re-verification" lists (both mentions), since it is now resolved, not merely
   unverified.

Do not touch P2-D or P2-K in this pass — they are unrelated UNVERIFIED items outside this
ticket's scope (relationship-coverage % and ContentUsageMatrix auto-generation, respectively).

---

## Step 8 — `make evaluate --dry-run` and scoped test run (AC6, finalize gate)

```bash
pytest tests/simulation_quality/test_grade_regression.py -m "not slow"
pytest tests/simulation_quality/test_grade_regression.py -m "slow"  # SLOW_ANCHOR_KEYS: dungeon_crawl 1000t/2000t, refreshed in Step 4a — previously silently excluded
pytest tests/integration/worldassembly/test_real_content_world_modules.py
pytest tests/unit/world/test_spawn_cadence.py            # P2-B regression guard, untouched code
pytest tests/unit/worldassembly/test_corpus_diversity.py  # new tests from Step 5
pytest tests/unit/content/test_catalog.py tests/unit/content_semantics/test_semantics.py  # hazard_immunities round-trip, unchanged mechanism reused
make evaluate   # 0 regressions against the expanded grade_anchors.json
```
Do not run `pytest tests/` in full, per `test_plan.md`'s scoped-command guidance.

**Correction — `make evaluate` alone is NOT a sufficient backstop for this ticket's specific drift
risk.** `make evaluate` (Makefile: "Diff current calibration data against grade anchors (no engine
re-run)") only diffs whatever `data/calibration/<run_key>/quality_report.json` files already happen
to be on disk against `grade_anchors.json` — it never re-runs the engine, so it cannot by itself
detect that a world's *content* changed since its calibration report was last generated. That is
exactly this ticket's risk: `dungeon_crawl` and `simq_routing_test` are recompiled in Step 2 (their
shared module `old_mine_resource_loop` gains a new `hazard_kind` in Step 1a), so their on-disk
calibration reports are stale relative to the new content until something explicitly re-runs the
engine for them. Running `make evaluate` here in isolation, without Step 4a having already executed,
would just compare pre-recompile (or accidentally-fresh, depending on incidental disk state) reports
against the anchor file and could report "0 regressions" without ever having exercised the recompiled
content. Only an explicit refresh-then-diff — Step 4a above — or `make evaluate-full` (Makefile:
"Re-run engine for all fast (≤500t) scenarios and diff against grade anchors", which forces a fresh
engine run before diffing) actually catches this class of drift. Step 4a must run to completion
before this `make evaluate` invocation for the gate to be meaningful for `dungeon_crawl`/
`simq_routing_test`.

---

## Files Changed (anticipated)

- `data/content/world_modules/orc_clan_territory.yaml`
- `data/content/world_modules/bandit_road_trade_pressure.yaml`
- `data/content/world_modules/old_mine_resource_loop.yaml`
- `data/content/world_modules/forest_warden_grove.yaml`
- `data/content/world_modules/undead_battlefield.yaml`
- `data/content/world_modules/nomadic_herd.yaml`
- `data/content/world_modules/sunken_swamp_border.yaml`
- `data/content/social/factions.yaml` (`orc_clan`, `bandit_company`, `forest_wardens`,
  `spirit_court`, `undead_remnants`, `swamp_tribe` gain `hazard_immunities`)
- `data/worlds/{simq_routing_test,dungeon_crawl,generated_frontier_3_42,frontier_extended,
  frontier_living_world,swamp_border_world,highland_traverse,wilderness_survival}/resolved/*`
  (regenerated, not hand-edited)
- `tests/simulation_quality/fixtures/grade_anchors.json`
- `tests/simulation_quality/test_grade_regression.py`
- `tests/unit/worldassembly/test_corpus_diversity.py` (new)
- `docs/mechanics/05_world_evolution.md`
- `docs/parity_ledger/world_dynamics.yaml`
- `docs/simulation_quality/eval_matrix_results.md`
- `docs/audits/D20_simq_integration.md`
- `docs/plans/audit_fix_plan.md`

## Unresolved Questions

None requiring a human decision. The one item flagged as needing a "planner check-in" in
`investigation.md`'s Risks section (fold the hazard-kind fix into this ticket vs. file separately)
was pre-resolved by the ticket's own Scope item 4 and is treated as decided (see top of this
document). The 3→7-module content-fix expansion and the "anchor 5 existing worlds, author 0 new"
decision are both resolved above with direct file-level evidence, not left open.

## Deviations (recorded during implementation, 2026-07-04)

**Step 4a — `simq_routing_test`'s 3 anchor keys could not be refreshed; pre-existing, unrelated
crash discovered.** The plan assumed all 13 existing-anchor calibration reports (10 `dungeon_crawl`
+ 3 `simq_routing_test`) would refresh cleanly. `dungeon_crawl`'s 10 refreshed without incident
(8 drifted, attributed to the hazard-kind recompile; 2 unchanged — see Implementation Notes in
`tickets/done/TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS.md`). Refreshing `simq_routing_test`'s 3 keys
(`ENABLE_ADVENTURE_ROUTING=ON`, 500t) instead crashed with `KeyError: Resource not found in
ResourceRegistry: STONE`, raised from `ResourceOpportunityProvider.get_opportunities`
(`src/world/providers/resources.py:60`) when `AdventureDecisionPhase` encounters a resource node
whose `kind` was synthesized as `"STONE"`/`"WOOD"`/`"IRON"` by the always-on
`ResourceEcologyService.process_ecology` (`src/world/ecology.py:124`) — a dynamic resource-node
generator whose output kinds were never registered in `ResourceRegistry`
(`data/content/world/resources.yaml` has no `STONE`/`WOOD`/`IRON` entries). This is unrelated to
`hazard_kind`/the 7-module content fix. **Confirmed via `git stash` bisection**: reverting all of
this ticket's Step 1/2 changes and re-running the identical calibration command reproduces the
exact same crash, proving it is 100% pre-existing, not introduced by this ticket. Per the ticket's
own Out-of-Scope guidance ("file a follow-up ticket instead" for discovered-but-unrelated
breakage), this was not fixed in-ticket. `simq_routing_test`'s 3 pre-existing anchor entries were
left unchanged (not silently marked as verified) and the finding was documented in
`docs/simulation_quality/eval_matrix_results.md`'s Step 4a NOTE block and the ticket's
Implementation Notes. A follow-up ticket is recommended for the `ResourceRegistry` STONE/WOOD/IRON
gap.

No other deviations from this plan were required — all other steps executed exactly as specified.
