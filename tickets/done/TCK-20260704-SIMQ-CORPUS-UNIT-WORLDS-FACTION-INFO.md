---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO
phase: done
date: 2026-07-04T12:17:33Z
tags: [simulation-quality, world, faction, information, corpus, calibration]
---

# TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO

## Title
Author 2 new unit-tier worlds isolating FACTION tension seeding and INFORMATION source profiles

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` §1 found that
`faction_tension_overrides` (`FACTION` pillar) and `information_source_profiles` /
`pending_information_responses` (`INFORMATION` pillar) are populated in exactly one world today
(`urban_political`) and are both "pure content, additive, no code risk" (investigation.md §3) —
zero schema/compiler/resolver changes required, only new `world.yaml` entries plus a recompile and
recalibration run. Per the hybrid content-authoring decision (template/synthetic content OK at
unit tier), this ticket authors 2 new small unit-tier worlds, each isolating exactly ONE of these
two mechanics with everything else at baseline — the controlled-experiment counterpart to the
richer, bespoke content `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION` authors for the existing
end-to-end worlds.

## Scope
1. Author **world A** (FACTION-isolation unit world): a new small world composition (comparable in
   scale to `wilderness_survival`/`sandbox_world` per investigation.md §2's smallest-world rows,
   11-18 entities) with non-zero `faction_tension_overrides` entries on at least 2 catalog-registered
   factions actually populated in this world (mirroring `urban_political`'s
   `bandit_company: 0.5, town_council: 0.5` pattern in shape, not necessarily the same values or
   factions). Every other Pattern-6 field (`information_source_profiles`,
   `pending_information_responses`, `pending_self_model_information_events`) stays empty/default,
   and `ENABLE_BELIEF_ASSIMILATION`/`ENABLE_SELF_MODEL_COGNITION`/`ENABLE_ADVENTURE_ROUTING` stay
   OFF in its profile YAML (baseline) — this must isolate FACTION alone.
2. Author **world B** (INFORMATION-isolation unit world): a second new small world composition with
   at least 1 `information_source_profiles` entry and 1 `pending_information_responses` entry
   (mirroring `urban_political`'s `town_notice_board` guide-profile / `pop_0`/`bandit_road_danger`
   pattern in shape), plus `ENABLE_BELIEF_ASSIMILATION: "ON"` in its profile YAML (per
   investigation.md §3: "seeding profiles without turning the flag on produces zero signal" — both
   must be seeded together for the mechanic to be observable). Every other Pattern-6 field stays
   empty/default and `faction_tension_overrides` stays at catalog default (0.0 for all factions) —
   this must isolate INFORMATION alone.
3. Template/synthetic content is acceptable for both worlds per the hybrid decision — narrative
   coherence is not a goal here, isolating the mechanic is.
4. Compile both worlds (`python -m src.worldbuilding.cli resolve <world>` +
   `compile --seed <seed> --from-resolved`), verify `world_compile_report.json` shows 0 warnings,
   and verify population stability (>=60% alive floor through at least 200-300 ticks, following the
   verification pattern `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS` established).
5. Run a 3-seed calibration matrix (seeds 42/123/456, following the existing corpus pattern) for
   each world and add grade-anchor entries to `tests/simulation_quality/fixtures/grade_anchors.json`
   / `FAST_ANCHOR_KEYS` in `test_grade_regression.py`, mirroring
   `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS`'s Step 4 anchoring pattern.
6. Confirm world A's FACTION pillar grade shows genuine non-C signal (or document honestly if it
   does not — this is real diagnostic data) and world B's INFORMATION pillar likewise.
7. Update `docs/simulation_quality/eval_matrix_results.md` with both worlds' grade tables, tagged as
   unit-tier per `TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC`'s taxonomy.
8. Run `make evaluate --dry-run` (0 regressions on existing corpus) and
   `make knowledge-index-update` if docs changed.

## Out of Scope
- Authoring self-model/Branch B content (that is
  `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT`)
- Authoring an AGENCY-isolation world (that is `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY`)
- Adding bespoke FACTION/INFORMATION content to any existing end-to-end-tier world (that is
  `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION`)
- Expanding `data/content/social/faction_relationships.yaml`'s global density (that is
  `TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS`)
- Fixing any pillar scoring/emission bug discovered while authoring these worlds — file a follow-up
  ticket instead, per the pattern established in `TCK-20260703-SIMQ-UPLIFT3-PLAYBOOK-DOC`

## Acceptance Criteria
- [ ] World A exists, compiles with 0 warnings, has >=2 non-zero `faction_tension_overrides`
      entries, and has every other Pattern-6 field empty/default
- [ ] World B exists, compiles with 0 warnings, has >=1 `information_source_profiles` entry, >=1
      `pending_information_responses` entry, `ENABLE_BELIEF_ASSIMILATION: "ON"` in its profile YAML,
      and every other Pattern-6 field empty/default
- [ ] Both worlds verified population-stable (>=60% alive floor) through at least 200-300 ticks at
      seed 42
- [ ] Both worlds have 3-seed grade-anchor entries in `grade_anchors.json` and
      `FAST_ANCHOR_KEYS`
- [ ] World A's FACTION grade and world B's INFORMATION grade are documented honestly in
      `eval_matrix_results.md`, whatever they turn out to be
- [ ] `make evaluate --dry-run` exits 0 with 0 regressions on the pre-existing corpus
- [ ] `make knowledge-index-update` run if `docs/` files changed

## Related Tickets
- TCK-20260704-SIMQ-CORPUS-TIERS-EPIC (parent epic)
- TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC — defines the unit-tier criteria these worlds must meet
- TCK-20260704-SIMQ-CORPUS-SCALE-METRIC — should be recompiled with the new
  `distinct_populated_factions` field once that ticket lands, if sequenced after
- TCK-20260702-SIMQ-UPLIFT2-FACTION — prior single-world FACTION activation this ticket's world A
  generalizes the pattern from
- TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS — precedent for compile/verify/anchor workflow this ticket
  follows
- TCK-20260706-SIMQ-STONE-OUTCROP-MATERIAL-VALIDATION-GAP (done) — this ticket's implementation hit
  the exact bug that ticket tracked (a hard `resolve` blocker affecting every world in the catalog)
  and applied its fix directly as a necessary prerequisite; that ticket was closed by the
  orchestrator as resolved via this ticket's commit rather than left open as a duplicate

## Related Docs
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` §1 (mechanic
  inventory, FACTION/INFORMATION rows) and §3 (blast-radius: "pure content, additive, no code risk")
- `docs/guidelines/design_patterns.md` — Pattern 6
- `docs/simulation_quality/eval_matrix_results.md`
- `docs/guides/content_authoring.md`

## Related Stored Artifacts
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/` — source investigation
- `stored_artifacts/TCK-20260702-SIMQ-UPLIFT2-FACTION/` — reference for how
  `faction_tension_overrides` was first seeded in `urban_political`
- `stored_artifacts/TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS/` — compile/verify/anchor workflow
  reference

## Related Code Areas
- `src/worldbuilding/schema.py:52` (`FactionSpec.initial_tension_level`), `:226-227`
  (`information_source_profiles`, `pending_information_responses`)
- `src/worldassembly/schema.py:40,44,48,168,172,176` — composition-level mirrors
- `data/worlds/urban_political/world.yaml` — reference pattern for both fields
- `config/simulation_quality/profiles/urban_political.yaml` — reference `feature_flags:` pattern
- `tests/simulation_quality/fixtures/grade_anchors.json`,
  `tests/simulation_quality/test_grade_regression.py`

## Assumptions / Open Questions
- UQ-1: Should the two new worlds reuse existing catalog factions/module content (faster, lower
  risk) or introduce any new content? Default to reusing existing catalog content exclusively —
  matches the "template/synthetic content OK" unit-tier philosophy and avoids new catalog-ID
  registration risk.
- UQ-2: Exact naming for the two new world directories under `data/worlds/` is left to the
  implementer — should be self-descriptive (e.g. `unit_faction_tension`, `unit_information_source`)
  and consistent with the taxonomy doc's naming guidance if
  `TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC` establishes one.

## Implementation Notes
Followed `staging_artifacts/TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO/plan.md`'s 10 steps
exactly (plan was pre-verified/APPROVED, no plan defects found during implementation).

- **World A** (`data/worlds/unit_faction_tension/world.yaml`): `frontier_village_core` +
  `wolf_den_near_forest` (byte-for-byte `sandbox_world`'s module pair), `faction_tension_overrides:
  {town_council: 0.5, merchant_league: 0.5}`, `generation_seed: 501`. No profile YAML — all feature
  flags default OFF via `_resolve_profile()`'s `"default"` fallback, exactly per plan.
- **World B** (`data/worlds/unit_information_source/world.yaml`): `frontier_village_core` +
  `hero_adventurers`, one `information_source_profiles` entry (`town_notice_board`) + one
  `pending_information_responses` entry targeting `pop_0` (subject `"hometown_danger"`,
  `details.region: "hometown"` — the plan's deviation-corrected content, not `urban_political`'s
  `"bandit_road_danger"`/`"bandit_road"`, since that region doesn't exist in this composition),
  `generation_seed: 502`. New profile YAML
  `config/simulation_quality/profiles/unit_information_source.yaml` with
  `ENABLE_BELIEF_ASSIMILATION: "ON"` — confirmed loaded (calibration output showed
  `profile=unit_information_source`, not `default`).

**Blocking pre-existing repo bug found and fixed to unblock this ticket (not part of the ticket's
own scope, but without it nothing in Steps 4-10 could run for ANY world, not just the two new
ones):** `python3 -m src.worldbuilding.cli resolve <world_id>` failed for every world in the
catalog, including the pre-existing, already-anchored `sandbox_world` (confirmed by direct repro on
`sandbox_world`, then reverted with `git checkout`) with
`[CAT-REL-099] Resource 'stone_outcrop' references non-existent material 'stone'`. Root cause:
`TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP` (2026-07-04, commit `63801b0e`) added a
`stone_outcrop` resource (`data/content/world/resources.yaml`) with `material: "stone"` and a
`stone` **item** (`data/content/world/items.yaml`), but never registered a `stone` **material**
entry in `data/content/foundation/materials.yaml` — a different catalog family the content
reference-graph validator (`ContentValidator._validate_reference_graph`, `CAT-REL-099`,
`src/content/validator.py:613-670`) checks unconditionally (`ERROR` severity, no `--strict` needed,
no bypass) as part of `WorldAssemblyResolver.assemble()`'s catalog-wide validation pass — this runs
regardless of which modules a given world composes, so it blocked every world's `resolve`, not just
ones referencing `stone_outcrop`. This had gone unnoticed since 2026-07-04 because no `resolve` had
been run fresh on any world since that commit (existing worlds' `compile --from-resolved` uses
already-committed `resolved/` artifacts, bypassing the assemble+validate cycle entirely). Fixed by
adding one minimal, additive `stone` material entry to `data/content/foundation/materials.yaml`
(mirrors the existing entries' shape exactly — `id`/`display_name`/`categories`/`common_regions`,
no schema/logic change). Re-verified `sandbox_world` resolves cleanly after the fix, then reverted
the incidental regeneration of its `resolved/*`/`world_compile_report.json` artifacts via `git
checkout` (not this ticket's scope to touch an existing world's compiled output). Full scoped test
suites (`tests/unit/content/`, `tests/unit/worldbuilding/test_world_validator.py`, plus all suites
in Step 9 below) re-run green after the fix — no other content depends on the absence of a `stone`
material. **This is flagged as a candidate follow-up** (see `CANDIDATE_FOLLOWUP_BUGS` in the final
report) since it is, strictly, a defect in an already-closed, unrelated ticket
(`TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP`) — the orchestrator may want a dedicated
hotfix/regression-test ticket (e.g. a permanent "every resource.material has a materials.yaml
entry" catalog-integrity test) even though the immediate breakage is already resolved here.

**Step 7 signal verification (both worlds, all 3 seeds, 200t):**
- World A FACTION: `S` at every seed, 29 `diplomatic_transition`/`tension_active` hits/run
  (identical count across seeds 42/123/456) — matches `urban_political_seed42_200t`'s own
  documented "29 hits/run" for the same mechanism. Genuine signal, not an inert/dormancy false
  positive. INFORMATION stayed `C` with 0 events at every seed — isolation confirmed.
- World B INFORMATION: `B` at every seed, exactly 1 `belief_assimilated` hit/run (identical across
  seeds) — matches `urban_political`'s single-fire, tick-length-invariant precedent for this
  mechanism. FACTION stayed `C` with 0 events at every seed — isolation confirmed.
- Neither grade came back as an inert/structural `C` — both are honest, genuine positive signals as
  expected. No pillar scoring/emission bug discovered in either scorer's own logic.

**Population stability:** both worlds held 100% alive (18/18 and 16/16) at every 50-tick checkpoint
through 300 ticks at seed 42 — well above the 60% floor, no incident, no root-cause investigation
needed.

**Anti-drift guards followed:** no profile YAML for World A; no hand-edited `resolved/*` files (all
regenerated via `resolve`); `FAST_ANCHOR_KEYS`'s existing 43 entries untouched; no
`pending_self_model_information_events` seeded in either world; no new catalog faction/module/
population recipe added (both worlds compose exclusively from pre-existing
`frontier_village_core`/`wolf_den_near_forest`/`hero_adventurers` modules); `make evaluate` run
without `--dry-run` per the plan's correction.

`docs/simulation_quality/eval_matrix_results.md` gained a new "Unit-Tier Isolation Worlds" section
(two `###` subsections, 200t grade tables, tagged unit-tier) and
`docs/simulation_quality/corpus_tier_taxonomy.md`'s "Current tier mapping" table gained two new
rows plus a corrected opening line (no longer claims unit-tier worlds don't exist).

No deviations from `plan.md`'s Step 1-8 content/values — the one deviation from the plan's
anticipated-Files-Changed list is the additional, out-of-plan fix to
`data/content/foundation/materials.yaml` (documented above and in `plan.md`'s own Deviations
section).

## Citation Correction (2026-07-08, TCK-20260707-EPIC-SCOPE-INVESTIGATION-DOC-MISSING)

This ticket's citations above to `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md`
(later renamed to `staging_artifacts/TCK-20260704-SIMQ-CORPUS-TIERS-EPIC/investigation.md`) point to a
pre-ticket epic-scoping investigation that was never migrated to `stored_artifacts/` and is now
unrecoverable: `staging_artifacts/` is gitignored by repo policy, and full git history confirms no commit
ever added a file at either path. This is a citation/traceability gap only -- every specific fact this
ticket drew from that doc has been independently cross-validated against ground truth
(`world.yaml`/`world_compile_report.json`,
`test_corpus_diversity.py::EXPECTED_DISTINCT_POPULATED_FACTIONS`) by this ticket and/or
`TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY` / `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION`. See
`tickets/done/TCK-20260707-EPIC-SCOPE-INVESTIGATION-DOC-MISSING.md` for the full root-cause writeup.

## Test Summary
- `pytest tests/unit/worldassembly/test_corpus_diversity.py -k "population_stability and (unit_faction_tension or unit_information_source)"` — 2 passed
- `pytest tests/unit/worldassembly/test_corpus_diversity.py` (full file, including `@pytest.mark.slow`) — 28 passed
- `pytest tests/simulation_quality/test_grade_regression.py -m "not slow"` — 36 passed
- `pytest tests/integration/worldassembly/test_real_content_world_modules.py tests/integration/worldassembly/test_real_content_world_compositions.py tests/unit/worldbuilding/test_world_compiler.py tests/unit/worldassembly/test_resolver.py` — 86 passed (combined with the grade-regression run above)
- `pytest tests/unit/worldbuilding/test_world_validator.py tests/unit/content -m "not slow"` (extra verification after the `materials.yaml` fix, not in the plan's scoped list but run to confirm no collateral regression from that fix) — 235 passed
- `make evaluate` (not `--dry-run`, per plan's correction) — exit 0, "460 pillars checked — 0 regressions — 0 missing"
- `make knowledge-index-update` — ran successfully (3 files re-embedded: the two doc updates + this ticket file)
- `graphify update .` — ran successfully (test files were touched): 24227 nodes, 51173 edges, 1526 communities

All commands green. No test was weakened or skipped to force a pass.

## Files Changed
- `data/worlds/unit_faction_tension/world.yaml` (new)
- `data/worlds/unit_faction_tension/resolved/*` (generated)
- `data/worlds/unit_faction_tension/world_compile_report.json` (generated)
- `data/worlds/unit_information_source/world.yaml` (new)
- `data/worlds/unit_information_source/resolved/*` (generated)
- `data/worlds/unit_information_source/world_compile_report.json` (generated)
- `config/simulation_quality/profiles/unit_information_source.yaml` (new)
- `data/worlds/world_index.json` (regenerated via `cli list`)
- `data/content/foundation/materials.yaml` (+1 `stone` material entry — pre-existing blocking bug fix, see Implementation Notes)
- `tests/simulation_quality/fixtures/grade_anchors.json` (+6 entries, purely additive)
- `tests/simulation_quality/test_grade_regression.py` (`FAST_ANCHOR_KEYS` +6)
- `tests/unit/worldassembly/test_corpus_diversity.py` (+2 worlds in `POPULATION_STABILITY_WORLDS`, not touching `ANCHORED_WORLD_BANDS`)
- `docs/simulation_quality/eval_matrix_results.md` (+"Unit-Tier Isolation Worlds" section, 2 subsections)
- `docs/simulation_quality/corpus_tier_taxonomy.md` (+2 tier-mapping rows, stale-sentence fix)
- `data/calibration/unit_faction_tension_seed{42,123,456}_200t/*` (generated, gitignored)
- `data/calibration/unit_information_source_seed{42,123,456}_200t/*` (generated, gitignored)

## Completion Summary
Authored the first 2 unit-tier isolation worlds for the SimQ corpus: `unit_faction_tension`
(reuses `sandbox_world`'s exact module pair, `faction_tension_overrides` on `town_council`/
`merchant_league`) and `unit_information_source` (composes `frontier_village_core` +
`hero_adventurers`, one `information_source_profiles` + one `pending_information_responses` entry
targeting `pop_0`, plus a new `ENABLE_BELIEF_ASSIMILATION: "ON"` profile). Both compile with 0
warnings, hold 100% population stability through 300 ticks at seed 42, and produce genuine,
honestly-reported isolation signal across a 3-seed/200-tick calibration matrix: World A grades
FACTION=S (29 hits/run, matching `urban_political`'s own documented precedent) with INFORMATION
correctly inert at C; World B grades INFORMATION=B (1 `belief_assimilated` hit/run, the expected
single-fire signal) with FACTION correctly inert at C. 6 new grade-anchor entries added; `make
evaluate` confirms 0 regressions across all 460 pillars corpus-wide (independently re-confirmed by
the orchestrator, not just trusted from the implementer's report).

While authoring these worlds, hit a genuine, unrelated, pre-existing blocker: `python -m
src.worldbuilding.cli resolve` failed for every world in the catalog (not just this ticket's new
ones) with `[CAT-REL-099] Resource 'stone_outcrop' references non-existent material 'stone'` —
`WorldAssemblyResolver.assemble()` runs this content-graph validation unconditionally,
catalog-wide, regardless of which world is being resolved. This was independently confirmed to be
the exact same bug already tracked as `TCK-20260706-SIMQ-STONE-OUTCROP-MATERIAL-VALIDATION-GAP`
(filed during the prior `HOMETOWN-RESOURCE-GAP` ticket). Root cause traced and confirmed by the
orchestrator: `src/content/reference_graph.py`'s concept-mapping table keys the `"material"` node
concept exclusively to `data/content/foundation/materials.yaml` — a catalog distinct from
`items.yaml`, which is where `TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP` had registered `stone`
without knowing to also register it in the separate materials catalog. Fixed with one minimal,
additive `materials.yaml` entry — a genuine implementation blocker for this ticket's own compile
step, not scope creep. `TCK-20260706-SIMQ-STONE-OUTCROP-MATERIAL-VALIDATION-GAP` has been closed
by the orchestrator as resolved via this ticket's commit, with its own root-cause/fix documentation
filled in for the record, rather than left open as a stale duplicate.
