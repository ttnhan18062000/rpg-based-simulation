---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION
phase: done
date: 2026-07-04T12:17:33Z
tags: [simulation-quality, world, faction, information, corpus, calibration]
---

# TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION

## Title
Author bespoke, archetype-matched FACTION and INFORMATION content into existing end-to-end worlds

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` §1 found FACTION
tension seeding and INFORMATION source profiles populated in exactly 1 of 10 worlds
(`urban_political`) — the direct answer to "why does only urban_political have this content" is
that no one has authored it elsewhere yet, not an architectural constraint (investigation.md §3:
"pure content, additive, no code risk" for both mechanics). Per the hybrid content-authoring
decision, this ticket authors **bespoke, archetype-matched** content (not templated/copy-pasted
from `urban_political`) into the 8 remaining end-to-end-tier worlds: `dungeon_crawl`,
`sandbox_world`, `wilderness_survival`, `highland_traverse`, `swamp_border_world`,
`frontier_living_world`, `frontier_extended`, `generated_frontier_3_42`.

Per investigation.md §4 open question 2, this must respect each world's actual archetype — e.g.
`wilderness_survival`'s "no settlement" framing may make an `urban_political`-style
`town_notice_board` information source archetypally wrong there. This is per-world judgment work,
not a mechanical stamp-and-repeat.

## Scope
1. For each of the 8 worlds, read its existing `world.yaml` description/archetype framing and
   populated-faction list (investigation.md §2 table) before authoring anything.
2. For **FACTION tension seeding**: for each world, judge which of its actually-populated factions
   (per investigation.md §2's per-world faction list) have an archetypally plausible tension
   relationship, and seed `faction_tension_overrides` accordingly (e.g. `dungeon_crawl`'s
   `bandit_company`/`goblin_warband`/`undead_remnants`/`wild_beast_pack` populate a hostile-dungeon
   archetype very differently from `swamp_border_world`'s `merchant_league`/`swamp_tribe`/
   `town_council`/`wild_beast_pack`). Do not copy `urban_political`'s exact faction/value pairs into
   worlds where those factions are not even populated.
3. For **INFORMATION source profiles**: for each world, judge whether an information-source
   archetype fits at all (a `town_notice_board`-style guide profile presumes a settlement;
   `wilderness_survival`'s "no settlement" framing may call for a different profile shape entirely,
   or may justify explicitly skipping this world for INFORMATION content if no archetype-honest fit
   exists — document that judgment call rather than forcing content in). Where a fit exists, author
   `information_source_profiles` and `pending_information_responses` content matched to that
   world's own population and archetype.
4. Where `information_source_profiles` content is seeded, also add
   `ENABLE_BELIEF_ASSIMILATION: "ON"` to that world's profile YAML `feature_flags:` block (per
   investigation.md §3: seeding profiles without the flag produces zero signal).
5. Recompile every touched world and verify 0 warnings.
6. **Re-verify existing calibration anchors with the same discipline
   `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS` Step 4a used**: for every world touched, diff its full
   existing `grade_anchors.json` entries against a fresh calibration run and update any drifted
   entries in place, with the drift attributed and documented (do not silently assume `make
   evaluate`'s dry-run diff alone catches content-driven grade drift — it only compares against
   already-committed anchors, so a stale anchor combined with a changed world will show as a
   "regression" unless the anchor itself is refreshed first).
7. Update `docs/simulation_quality/eval_matrix_results.md` with the new FACTION/INFORMATION grades
   for all 8 worlds and any anchor updates from step 6.
8. Run `make evaluate --dry-run` after anchors are refreshed (0 regressions) and
   `make knowledge-index-update` if docs changed.

## Out of Scope
- Authoring new worlds (that is tickets 4-6, 8 in this batch) — this ticket only extends the 8
  existing end-to-end worlds' content
- Self-model/Branch B or AGENCY content in these 8 worlds — explicitly not part of this ticket's
  scope (self-model has its own dedicated pilot ticket; AGENCY stays OFF in all 9 non-routing
  worlds per the DA ruling)
- Fixing any pillar scoring/emission bug discovered during this pass — file a follow-up ticket
- Expanding `data/content/social/faction_relationships.yaml`'s global density (that is
  `TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS`, though its results will make more of this
  ticket's new tension pairs meaningfully differentiated once it lands)

## Acceptance Criteria
- [x] Each of the 8 worlds has a documented per-world judgment call recorded (in this ticket's
      Implementation Notes) for both FACTION and INFORMATION content — including any world where the
      judgment was "no archetype-honest fit, skip this mechanic for this world"
- [x] `faction_tension_overrides` content authored only uses factions actually populated in that
      world (per investigation.md §2's faction list per world) — no non-populated-faction entries
- [x] Where `information_source_profiles` is seeded, `ENABLE_BELIEF_ASSIMILATION: "ON"` is also set
      in that world's profile YAML
- [x] All touched worlds recompile with 0 warnings
- [x] Every existing `grade_anchors.json` entry for a touched world is re-verified against a fresh
      calibration run; any drift is documented and the anchor updated (not silently left stale or
      silently assumed unaffected)
- [x] `docs/simulation_quality/eval_matrix_results.md` updated with new FACTION/INFORMATION grades
      for all 8 worlds
- [x] `make evaluate --dry-run` exits 0 with 0 regressions after anchor refresh

## Related Tickets
- TCK-20260704-SIMQ-CORPUS-TIERS-EPIC (parent epic)
- TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC — defines end-to-end-tier's bespoke-content requirement
- TCK-20260702-SIMQ-UPLIFT2-FACTION — original single-world (`urban_political`) FACTION activation;
  reference for the mechanism, explicitly not for the exact content values
- TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS — established the drift-check-and-update discipline this
  ticket must reuse (Step 4a pattern)
- TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS — global relationship-density work that makes this
  ticket's new tension pairs more meaningfully differentiated once it lands

## Related Docs
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` §1 (mechanic
  inventory), §2 (per-world faction/scale table), §3 (blast radius), §4 open question 2
  (bespoke-vs-template authoring tradeoff)
- `docs/simulation_quality/eval_matrix_results.md`
- `docs/guides/content_authoring.md`

## Related Stored Artifacts
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/` — source investigation
- `stored_artifacts/TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS/` — drift-check discipline reference
  (Step 4a)
- `stored_artifacts/TCK-20260702-SIMQ-UPLIFT2-FACTION/` — original FACTION mechanism reference

## Related Code Areas
- `data/worlds/{dungeon_crawl,sandbox_world,wilderness_survival,highland_traverse,
  swamp_border_world,frontier_living_world,frontier_extended,generated_frontier_3_42}/world.yaml`
- `config/simulation_quality/profiles/` — new/edited per-world profile YAMLs
- `src/worldbuilding/schema.py:52,226,227`
- `tests/simulation_quality/fixtures/grade_anchors.json`

## Assumptions / Open Questions
- UQ-1: For worlds where no archetype-honest INFORMATION fit exists (e.g. potentially
  `wilderness_survival`), is "skip this mechanic for this world, document why" an acceptable
  outcome, or must every world get some INFORMATION content regardless? Default to "skip and
  document" — per investigation.md §4 open question 2's own framing, forcing content everywhere
  risks the "generic content stamped everywhere" outcome the SimQ Uplift batches originally avoided.
- UQ-2: Order of authoring across the 8 worlds is left to the implementer; no cross-world
  dependency exists (each world's content is independent), but the drift-check step (Scope item 6)
  should be done per-world immediately after that world's content lands, not batched at the end,
  to keep attribution clear.

## Implementation Notes

Implemented all 8 per-world steps of `staging_artifacts/TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION/plan.md`
in order, followed by the 2 consolidation steps. Only `data/worlds/{world}/world.yaml` was ever
edited — `data/content/world_compositions/{world}.yaml` mirrors were never touched.

**Investigation-time correction applied to every world with INFORMATION content (Steps 1, 4-8):**
the plan's placeholder `target_population_id: "pop_0"` does not resolve in any of these 8 worlds.
`pop_0`/`pop_1`/`pop_2` positional addressing only arises from the `hero_adventurers` module's
un-ided population recipes (`compiler.py::pop_key = getattr(pop_spec, "id", f"pop_{pop_idx}")`) —
none of the 8 target worlds compose `hero_adventurers`. Confirmed via each world's own
`resolved/world.resolved.yaml` `entities:` section that `frontier_village_core`'s (and
`settled_quarter`'s, which reuses the same `frontier_village_population` recipe) population entries
carry an explicit id, e.g. `frontier_village_population_frontier_guard`. Every
`pending_information_responses.target_population_id` below was corrected to this real id before
compiling, and 3 `region` placeholders were corrected against resolved region ids: `highland_traverse`
(`mountain_pass` → `mountain_pass_zone`), `swamp_border_world` (`sunken_swamp_border` →
`swamp_border_territory`), `frontier_extended` (`orc_clan_territory` → `orc_stronghold`),
`generated_frontier_3_42` (`moon_cult_ruins` → `moon_cave`). All 6 corrections verified: recompiling
produced 0 "target_population_id matched no compiled entity" warnings for any world.

**Per-world judgment calls (documented per AC bullet 1):**

- **sandbox_world** — FACTION `town_council: 0.5`/`merchant_league: 0.5` (governance-vs-commerce).
  INFORMATION: `town_notice_board` guide + `hometown_danger` response. 0 warnings, 3 factions
  (unchanged). 5/5 anchors refreshed: FACTION C→S/A/B, INFORMATION C→B, COGNITION C→B (200t only;
  already B at 1000t/2000t pre-ticket).
- **dungeon_crawl** — FACTION `goblin_warband: 0.5`/`bandit_company: 0.5` (rival humanoid factions).
  INFORMATION **skipped** — no settlement/service module in composition (documented ticket-named
  skip candidate, confirmed). `pillar_weights:` profile block left untouched, no `feature_flags:`
  added. 0 warnings, 4 factions (unchanged). 10/10 anchors refreshed: FACTION-only drift (C→S at
  200t, C→A at 500t/1000t, C→B at 2000t); INFORMATION/COGNITION held C in all 10 (no content
  seeded, as expected).
- **wilderness_survival** — FACTION `undead_remnants: 0.5`/`wild_beast_pack: 0.5` (both-hazard-type
  territorial rivalry). INFORMATION **skipped** — no settlement-adjacent module (the ticket's own
  named skip candidate, confirmed: `survivor_camp_shelter` spawns no settlement population of its
  own). 0 warnings, 2 factions (unchanged), `test_population_stability` re-passed. 3/3 anchors
  refreshed: FACTION-only C→S; INFORMATION/COGNITION held C.
- **highland_traverse** — FACTION `town_council: 0.5`/`merchant_league: 0.5` (settled_quarter's own
  service-hub archetype). INFORMATION: `route_waystation_guide` + `mountain_pass_conditions`
  response. Recompile surfaced 1 warning (`survey_river_route`/`'river'` region-tag mismatch) —
  confirmed via `git show HEAD` to be pre-existing in the committed baseline, unrelated to this
  ticket's content edit; not a new regression. 3 factions (unchanged), `test_population_stability`
  re-passed. 3/3 anchors refreshed: FACTION C→S, INFORMATION C→B, COGNITION C→B (seed123/456 only;
  seed42 was already B pre-ticket).
- **swamp_border_world** — FACTION `town_council: 0.5`/`swamp_tribe: 0.5` (border tension, matches
  world's own lizardfolk/troll framing; `bandit_company` deliberately excluded, not populated here).
  INFORMATION: `town_notice_board` + `swamp_border_danger` response. 0 warnings, 4 factions
  (unchanged), `test_population_stability` re-passed. 3/3 anchors refreshed: FACTION C→S,
  INFORMATION C→B, COGNITION C→B.
- **frontier_living_world** — FACTION `bandit_company: 0.5`/`merchant_league: 0.5` (the
  `bandit_road_trade_pressure` module's own built-in tension, the most literal fit of all 8 worlds).
  INFORMATION: `town_notice_board` + `trade_road_bandit_activity` response. 0 warnings, 6 factions
  (unchanged), `test_population_stability` re-passed, frozen
  `data/content/world_compositions/frontier_living_world.yaml` mirror re-verified still passing (13
  tests). 3/3 anchors refreshed: FACTION C→S, INFORMATION C→B, COGNITION C→B.
- **frontier_extended** — FACTION `orc_clan: 0.5`/`forest_wardens: 0.5` (this world's own additions
  over frontier_living_world; deliberately not reusing that world's bandit/merchant pair).
  INFORMATION: `town_notice_board` + `orc_clan_encroachment` response (subject text verified
  distinct from `frontier_living_world`'s `trade_road_bandit_activity`). 0 warnings, 9 factions
  (unchanged), `test_population_stability` re-passed. 3/3 anchors refreshed: FACTION C→S,
  INFORMATION C→B, COGNITION C→B.
- **generated_frontier_3_42** — FACTION `arcane_circle: 0.5`/`orc_clan: 0.5` (moon_cult_ruins'
  arcane circle under orc_clan_territory pressure, a pairing unique to this world; `moon_cult` itself
  left untouched — declared by `moon_cult_ruins` but not actually populated). INFORMATION:
  `town_notice_board` + `moon_cult_ruins_mystery` response. 0 warnings, 7 factions (unchanged,
  confirmed via the existing parametrized `test_distinct_populated_factions` case — it was already
  in `EXPECTED_DISTINCT_POPULATED_FACTIONS`, contrary to the plan's "likely not parametrized" caveat).
  Per Resolution 1: **no new `grade_anchors.json` entries added** — 3-seed 200t run is
  documentation-only evidence of a genuine non-inert signal (FACTION=S/29 hits, INFORMATION=B/1 hit,
  COGNITION=B/2 hits), recorded in `eval_matrix_results.md` with an explicit "outside the anchored
  corpus by design" note.

**Cross-world drift pattern confirmed clean in every case:** only FACTION, INFORMATION, and (via the
same documented `PP-04` dual-emission mechanism already governing `urban_political`'s own baseline —
`belief_assimilated` + `belief_updated` fire from the same assimilated response) COGNITION ever
drifted. No other pillar (COMBAT/ECONOMY/SOCIAL/WORLD/NARRATIVE/PROGRESSION/AGENCY) moved in any of
the 33 anchor comparisons performed — confirmed individually before each anchor update, per the
plan's "stop and investigate if an unrelated pillar drifts" guard.

**Docs (Step 9):** Added a new "FACTION/INFORMATION Content Expansion" section to
`docs/simulation_quality/eval_matrix_results.md` with full per-world judgment calls, before/after
grade tables, and the cross-world drift-pattern attribution; added superseding pointer notes to the
pre-existing "Zero-Pillar World Confirmation" section rather than rewriting historical tables in
place (matches the doc's own established "historical, superseded" convention). Updated
`corpus_tier_taxonomy.md`'s "Current tier mapping" table to move all 8 target worlds from
Regression/baseline to End-to-end tier; left `urban_political`/`simq_routing_test` as
Regression/baseline (neither is one of this ticket's 8 target worlds). Did not fix the doc's
pre-existing broken citation to the missing `EPIC-SCOPE-full-feature-world-coverage/investigation.md`
path, per plan's explicit deferral to a documentation-hygiene follow-up.

**Final gate (Step 10):** `make evaluate` exited 0 — 340 pillars checked, 0 regressions, 0 missing.
Full scoped pytest sweep (8 commands from test_plan.md) all passed: worldspec schema/compiler (43),
assembly (30), faction state/diplomacy (37), corpus diversity incl. population stability (30),
frozen-mirror composition/module integration (30+19), faction/information scorer units (28), grade
regression fast-tier (27 passed, 15 skipped — pre-existing skips for scenarios without fresh
calibration data, unrelated to this ticket).

`make knowledge-index-update` (Step 11) ran clean: 5 files re-embedded, 1931 unchanged, 5429 chunks
total.

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
All commands below were run against the working tree after all 8 worlds' content landed (final
gate, Step 10 of plan.md) and passed with exit code 0 / 0 failures:
- `pytest tests/unit/worldbuilding/test_worldspec_schema.py tests/unit/worldbuilding/test_world_compiler.py` — 43 passed
- `pytest tests/unit/worldassembly/test_assembly.py` — 30 passed
- `pytest tests/unit/faction/test_faction_state.py tests/unit/faction/test_diplomacy.py` — 37 passed
- `pytest tests/unit/worldassembly/test_corpus_diversity.py` — 30 passed (incl. `test_distinct_populated_factions` for all 8 worlds + `test_population_stability` for the 5 parametrized worlds)
- `pytest tests/integration/worldassembly/test_real_content_world_compositions.py` — 13 passed
- `pytest tests/integration/worldassembly/test_real_content_world_modules.py` — 19 passed
- `pytest tests/simulation_quality/test_faction_scorer.py tests/simulation_quality/test_information_scorer.py` — 28 passed
- `pytest tests/simulation_quality/test_grade_regression.py -m "not slow"` — 27 passed, 15 skipped (pre-existing, unrelated)
- `make evaluate` — 340 pillars checked, 0 regressions, 0 missing

## Files Changed
- `data/worlds/sandbox_world/world.yaml`
- `data/worlds/dungeon_crawl/world.yaml`
- `data/worlds/wilderness_survival/world.yaml`
- `data/worlds/highland_traverse/world.yaml`
- `data/worlds/swamp_border_world/world.yaml`
- `data/worlds/frontier_living_world/world.yaml`
- `data/worlds/frontier_extended/world.yaml`
- `data/worlds/generated_frontier_3_42/world.yaml`
- `config/simulation_quality/profiles/sandbox_world.yaml` (new)
- `config/simulation_quality/profiles/highland_traverse.yaml` (new)
- `config/simulation_quality/profiles/swamp_border_world.yaml` (new)
- `config/simulation_quality/profiles/frontier_living_world.yaml` (new)
- `config/simulation_quality/profiles/frontier_extended.yaml` (new)
- `config/simulation_quality/profiles/generated_frontier_3_42.yaml` (new)
- `tests/simulation_quality/fixtures/grade_anchors.json` (33 entries updated across 7 worlds; 0 added for `generated_frontier_3_42`)
- `docs/simulation_quality/eval_matrix_results.md`
- `docs/simulation_quality/corpus_tier_taxonomy.md`
- `data/worlds/{sandbox_world,dungeon_crawl,wilderness_survival,highland_traverse,swamp_border_world,frontier_living_world,frontier_extended,generated_frontier_3_42}/resolved/*` and `world_compile_report.json` (regenerated by resolve/compile, not hand-edited)

## Completion Summary
All 8 end-to-end-tier worlds now carry bespoke, archetype-matched `faction_tension_overrides`; 6 of
8 also carry `information_source_profiles`/`pending_information_responses` (the other 2 —
`dungeon_crawl`, `wilderness_survival` — have documented, archetype-honest INFORMATION skips). Every
touched world recompiles with 0 new warnings. Every pre-existing calibration anchor for the 7
anchor-bearing worlds was re-verified against a fresh calibration run and updated in place where
drifted (33 entries updated, all drift attributable to FACTION/INFORMATION activation and its
documented COGNITION side-effect); `generated_frontier_3_42` deliberately received content but no new
anchor, per an explicit, documented scope decision. Docs updated (`eval_matrix_results.md`,
`corpus_tier_taxonomy.md`, `docs/parity_ledger/infrastructure.yaml` INFRA-256/257 additive
extensions). Final gate (`make evaluate` + full scoped pytest sweep, 214 passed/0 failed) passed
clean. All Acceptance Criteria met.

**Two real, deliberately out-of-scope gaps found during Verify, tracked, not left unstated:**
1. `test_population_stability`/`test_hazard_kind_completeness` in `test_corpus_diversity.py` don't
   parametrize `dungeon_crawl`, `sandbox_world`, or `generated_frontier_3_42` — a pre-existing
   test-coverage gap this ticket surfaced (by touching those worlds) but did not create and is out
   of scope to fix here (a test-infrastructure change, not a content-authoring one). Filed as
   `tickets/todos/TCK-20260707-CORPUS-POPULATION-STABILITY-COVERAGE-GAP.md`.
2. The epic's shared source investigation doc
   (`staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md`, cited by this ticket
   and ~9 siblings) does not exist anywhere in `staging_artifacts/` or `stored_artifacts/` — first
   flagged non-blocking in the sibling AGENCY ticket's plan.md (OQ-3), hit again independently here.
   Every specific fact attributed to it has cross-validated cleanly against ground truth in both
   tickets' investigations, so this is a citation/traceability gap, not a correctness risk. Filed as
   `tickets/todos/TCK-20260707-EPIC-SCOPE-INVESTIGATION-DOC-MISSING.md`.
